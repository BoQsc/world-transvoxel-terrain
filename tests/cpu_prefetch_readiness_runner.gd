extends Node

signal finished(exit_code: int)

const CONTRACT_PATH := "res://CPU_PREFETCH_READINESS_CONTRACT.json"
const RESULT_PATH := "res://cpu_prefetch_readiness_result.json"
const CAPTURE_ROOT := "res://cpu_prefetch_readiness_captures"
const AcceptanceScene := preload(
	"res://addons/world_transvoxel_terrain/debug/wt_terrain_large_acceptance_scene.tscn"
)
const WORK_COUNTERS := [
	"storage_accepted_requests",
	"mesh_jobs",
	"application_applied_render",
	"application_applied_collision",
	"collision_viewer_updates",
	"viewer_updates",
]

var failures: Array[String] = []
var captures: Array[Dictionary] = []
var capture_root := CAPTURE_ROOT


func _ready() -> void:
	call_deferred("_run")


func _run() -> void:
	var contract_path := OS.get_environment("WT_PREFETCH_CONTRACT") if \
			OS.has_environment("WT_PREFETCH_CONTRACT") else CONTRACT_PATH
	var result_path := OS.get_environment("WT_PREFETCH_RESULT") if \
			OS.has_environment("WT_PREFETCH_RESULT") else RESULT_PATH
	capture_root = OS.get_environment("WT_PREFETCH_CAPTURE_ROOT") if \
			OS.has_environment("WT_PREFETCH_CAPTURE_ROOT") else CAPTURE_ROOT
	var contract = JSON.parse_string(FileAccess.get_file_as_string(contract_path))
	if not contract is Dictionary:
		_finish_now(result_path, {}, "prefetch readiness contract could not be loaded")
		return
	get_tree().root.get_window().size = Vector2i(960, 540)
	var scene: Node = AcceptanceScene.instantiate()
	get_tree().root.add_child(scene)
	scene.call("set_automatic_viewer_tracking", false)
	scene.call("set_hold_after_coarse", true)
	print("WT_PREFETCH_STAGE coarse_bootstrap")
	var coarse: Dictionary = await scene.call("wait_until_global_coarse_ready", 900)
	if str(coarse.get("status", "")) != "PASS":
		_finish_now(result_path, contract, "global coarse bootstrap failed", coarse)
		return
	if not bool(scene.call("release_local_refinement")):
		_finish_now(result_path, contract, "initial local refinement was rejected")
		return
	print("WT_PREFETCH_STAGE initial_refinement")
	var initial_settlement: Dictionary = await scene.call("wait_until_ready", 900)
	if str(initial_settlement.get("status", "")) != "PASS":
		_finish_now(result_path, contract, "initial refinement failed")
		return
	var world_contract := contract.get("world", {}) as Dictionary
	var target := _vector3(world_contract.get("prefetch_position", []))
	var cold: Dictionary = initial_settlement
	var terrain_world := scene.call("get_terrain_world") as Node
	var prefetch_id := int(world_contract.get("prefetch_viewer_id", 5799))
	var prefetch_before := _metrics(terrain_world)
	var prefetch_started := Time.get_ticks_usec()
	print("WT_PREFETCH_STAGE visual_prefetch")
	var prefetch_accepted := bool(terrain_world.call(
		"update_viewer",
		prefetch_id,
		1,
		target,
		int(world_contract.get("visual_radius_chunks", 2)),
		int(world_contract.get("maximum_lod", 3))
	))
	var prefetch_settlement: Dictionary
	if prefetch_accepted:
		var prefetch_acknowledged := await _wait_for_metric_increase(
			terrain_world, "viewer_updates", prefetch_before, 300
		)
		if prefetch_acknowledged:
			prefetch_settlement = await scene.call(
				"wait_until_ready", 900, prefetch_before, prefetch_started
			)
		else:
			prefetch_settlement = {"status": "FAIL", "error": "prefetch event was not acknowledged"}
	else:
		prefetch_settlement = {"status": "FAIL", "error": "prefetch viewer rejected"}
	var prefetch_after := _metrics(terrain_world)
	var prefetched_state := _target_state_summary(
		terrain_world, target, int(world_contract.get("visual_radius_chunks", 2))
	)
	_set_camera(scene, target)
	captures.append(await _capture("prefetch_ready"))
	var arrival_before := _metrics(terrain_world)
	print("WT_PREFETCH_STAGE authoritative_arrival")
	var arrival_started := Time.get_ticks_usec()
	var collision_accepted := bool(scene.call("publish_collision_only", target))
	var collision_acknowledged := false
	if collision_accepted:
		collision_acknowledged = await _wait_for_metric_increase(
			terrain_world, "collision_viewer_updates", arrival_before, 300
		)
	var arrival: Dictionary
	if collision_acknowledged:
		arrival = await _wait_for_target_collision(
			scene,
			terrain_world,
			target,
			int(world_contract.get("collision_radius_chunks", 1)),
			arrival_before,
			arrival_started,
			600
		)
	else:
		arrival = {"status": "FAIL", "error": "collision arrival was not acknowledged"}
	var arrival_after := _metrics(terrain_world)
	var arrival_work := _metric_delta(arrival_before, arrival_after)
	var arrival_state := _target_state_summary(
		terrain_world, target, int(world_contract.get("collision_radius_chunks", 1))
	)
	captures.append(await _capture("arrival_ready"))
	var handoff_before := _metrics(terrain_world)
	print("WT_PREFETCH_STAGE visual_handoff")
	var handoff_accepted := bool(scene.call("release_primary_visual_viewer"))
	var handoff_started := Time.get_ticks_usec()
	var handoff: Dictionary
	if handoff_accepted:
		var handoff_acknowledged := await _wait_for_metric_increase(
			terrain_world, "viewer_removals", handoff_before, 300
		)
		if handoff_acknowledged:
			handoff = await scene.call(
				"wait_until_ready", 600, handoff_before, handoff_started
			)
		else:
			handoff = {"status": "FAIL", "error": "visual handoff was not acknowledged"}
	else:
		handoff = {"status": "FAIL", "error": "visual handoff rejected"}
	var final_snapshot := scene.call("get_validation_snapshot") as Dictionary
	var final_audit := final_snapshot.get("lod_audit", {}) as Dictionary
	var final_metrics := final_snapshot.get("metrics", {}) as Dictionary
	_evaluate(
		contract,
		coarse,
		cold,
		prefetch_settlement,
		_metric_delta(prefetch_before, prefetch_after),
		prefetched_state,
		arrival,
		arrival_work,
		arrival_state,
		handoff,
		final_audit,
		final_metrics
	)
	var cleanup_before := _metrics(terrain_world)
	var cleanup_accepted := bool(terrain_world.call("remove_viewer", prefetch_id, 2))
	if cleanup_accepted:
		await _wait_for_metric_increase(terrain_world, "viewer_removals", cleanup_before, 300)
	var shutdown: Dictionary = await scene.call("shutdown_for_validation")
	print("WT_PREFETCH_STAGE shutdown")
	if str(shutdown.get("status", "")) != "PASS":
		failures.append("prefetch fixture did not shut down cleanly")
	var report := {
		"schema": "world_transvoxel_terrain.cpu_prefetch_readiness_evidence.v1",
		"milestone": str(contract.get("milestone", "TQP-R04")),
		"status": "PASS" if failures.is_empty() else "FAIL",
		"engine": Engine.get_version_info(),
		"renderer": RenderingServer.get_current_rendering_driver_name(),
		"coarse_bootstrap": coarse,
		"cold_settlement": cold,
		"prefetch": {
			"accepted": prefetch_accepted,
			"settlement": prefetch_settlement,
			"work_delta": _metric_delta(prefetch_before, prefetch_after),
			"target_state_before_arrival": prefetched_state,
		},
		"arrival": {
			"settlement": arrival,
			"work_delta": arrival_work,
			"target_state": arrival_state,
		},
		"visual_handoff": handoff,
		"final_snapshot": final_snapshot,
		"captures": captures,
		"shutdown": shutdown,
		"qualified_scope": contract.get("qualified_scope", []),
		"explicitly_unqualified_scope": contract.get("explicitly_unqualified_scope", []),
		"failures": failures,
	}
	_write_json(result_path, report)
	if failures.is_empty():
		print("WT_TERRAIN_CPU_PREFETCH_READINESS_GODOT_PASS visual=%d collision=%d storage=%d mesh=%d" % [
			int(prefetched_state.get("visual_ready_lod0", 0)),
			int(arrival_state.get("collision_ready_lod0", 0)),
			int(arrival_work.get("storage_accepted_requests", -1)),
			int(arrival_work.get("mesh_jobs", -1)),
		])
	else:
		push_error("WT_TERRAIN_CPU_PREFETCH_READINESS_GODOT_FAIL: " + "; ".join(failures))
	scene.queue_free()
	await get_tree().process_frame
	finished.emit(0 if failures.is_empty() else 1)


func _evaluate(
	contract: Dictionary,
	coarse: Dictionary,
	cold: Dictionary,
	prefetch_settlement: Dictionary,
	prefetch_work: Dictionary,
	prefetched_state: Dictionary,
	arrival: Dictionary,
	arrival_work: Dictionary,
	arrival_state: Dictionary,
	handoff: Dictionary,
	final_audit: Dictionary,
	final_metrics: Dictionary
) -> void:
	var budget := contract.get("budgets", {}) as Dictionary
	if str(coarse.get("status", "")) != "PASS": failures.append("coarse bootstrap failed")
	if str(cold.get("status", "")) != "PASS": failures.append("cold settlement failed")
	if str(prefetch_settlement.get("status", "")) != "PASS": failures.append("visual prefetch did not settle")
	if int((coarse.get("bootstrap", {}) as Dictionary).get("coarse_ready_latency_usec", 0)) > int(float(budget.get("maximum_bootstrap_seconds", 0.0)) * 1000000.0):
		failures.append("coarse bootstrap exceeded its latency budget")
	if int(cold.get("settlement_latency_usec", 0)) > int(float(budget.get("maximum_cold_settlement_seconds", 0.0)) * 1000000.0):
		failures.append("cold settlement exceeded its latency budget")
	if int(prefetch_settlement.get("settlement_latency_usec", 0)) > int(float(budget.get("maximum_prefetch_settlement_seconds", 0.0)) * 1000000.0):
		failures.append("prefetch exceeded its latency budget")
	if int(prefetch_work.get("collision_viewer_updates", -1)) > int(budget.get("maximum_prefetch_collision_viewer_updates", 0)):
		failures.append("visual-only prefetch changed collision demand")
	if int(prefetched_state.get("visual_ready_lod0", 0)) < int(budget.get("minimum_prefetched_lod0_visual_chunks", 1)):
		failures.append("target LOD0 visuals were not ready before arrival")
	if int(prefetched_state.get("collision_required_lod0", -1)) != 0:
		failures.append("prefetch target acquired collision before arrival")
	if str(arrival.get("status", "")) != "PASS": failures.append("prefetched arrival did not settle")
	if int(arrival.get("settlement_latency_usec", 0)) > int(float(budget.get("maximum_arrival_settlement_seconds", 0.0)) * 1000000.0):
		failures.append("prefetched arrival exceeded its settlement budget")
	if int(arrival.get("first_collision_latency_usec", 0)) > int(float(budget.get("maximum_arrival_first_collision_seconds", 0.0)) * 1000000.0):
		failures.append("prefetched arrival collision exceeded its latency budget")
	if not bool(arrival.get("visual_already_resident", false)):
		failures.append("prefetched target visual was republished on arrival")
	if int(arrival_work.get("storage_accepted_requests", -1)) > int(budget.get("maximum_arrival_storage_requests", 0)):
		failures.append("prefetched arrival requested storage")
	if int(arrival_work.get("mesh_jobs", -1)) > int(budget.get("maximum_arrival_mesh_jobs", 0)):
		failures.append("prefetched arrival requested meshing")
	if int(arrival_work.get("application_applied_render", -1)) > int(budget.get("maximum_arrival_render_publications", 0)):
		failures.append("prefetched arrival republished visual terrain")
	if int(arrival_state.get("collision_ready_lod0", 0)) < int(budget.get("minimum_arrival_lod0_collision_chunks", 1)):
		failures.append("localized collision was not ready after arrival")
	if str(handoff.get("status", "")) != "PASS": failures.append("prior visual viewer retirement did not settle")
	if int(final_audit.get("coverage_overlap_count", -1)) > int(budget.get("maximum_coverage_overlaps", 0)):
		failures.append("final LOD coverage overlapped")
	if int(final_metrics.get("generation_errors", -1)) > int(budget.get("maximum_generation_errors", 0)):
		failures.append("generation errors were recorded")


static func _target_state_summary(terrain_world: Node, target: Vector3, radius: int) -> Dictionary:
	var center := Vector3i(floori(target.x / 16.0), floori(target.y / 16.0), floori(target.z / 16.0))
	var visual_required := 0
	var visual_ready := 0
	var collision_required := 0
	var collision_ready := 0
	for value in terrain_world.call("query_active_chunk_states"):
		var state := value as RefCounted
		if state == null or not bool(state.call("is_present")) or int(state.call("get_lod")) != 0:
			continue
		var coordinate := state.call("get_chunk_coordinate") as Vector3i
		if absi(coordinate.x - center.x) > radius or absi(coordinate.y - center.y) > radius or absi(coordinate.z - center.z) > radius:
			continue
		if bool(state.call("is_visual_required")):
			visual_required += 1
			if bool(state.call("is_visual_ready")): visual_ready += 1
		if bool(state.call("is_collision_required")):
			collision_required += 1
			if bool(state.call("is_collision_ready")): collision_ready += 1
	return {
		"visual_required_lod0": visual_required,
		"visual_ready_lod0": visual_ready,
		"collision_required_lod0": collision_required,
		"collision_ready_lod0": collision_ready,
	}


static func _metrics(terrain_world: Node) -> Dictionary:
	return terrain_world.call("get_runtime_metrics") as Dictionary


func _wait_for_metric_increase(
	terrain_world: Node,
	metric: String,
	baseline: Dictionary,
	maximum_frames: int
) -> bool:
	var initial := int(baseline.get(metric, 0))
	for _frame in range(maximum_frames):
		if int(_metrics(terrain_world).get(metric, 0)) > initial:
			return true
		await get_tree().process_frame
	return false


func _wait_for_target_collision(
	scene: Node,
	terrain_world: Node,
	target: Vector3,
	radius: int,
	baseline: Dictionary,
	started_usec: int,
	maximum_frames: int
) -> Dictionary:
	var first_collision_latency_usec := -1
	for frame in range(maximum_frames):
		var metrics := _metrics(terrain_world)
		if first_collision_latency_usec < 0 and int(metrics.get(
			"application_applied_collision", 0
		)) > int(baseline.get("application_applied_collision", 0)):
			first_collision_latency_usec = Time.get_ticks_usec() - started_usec
		var target_state := _target_state_summary(terrain_world, target, radius)
		var required := int(target_state.get("collision_required_lod0", 0))
		var ready := int(target_state.get("collision_ready_lod0", 0))
		var snapshot := scene.call("get_validation_snapshot") as Dictionary
		if required > 0 and ready == required and str(snapshot.get("status", "")) == "READY":
			return {
				"status": "PASS",
				"frames": frame,
				"settlement_latency_usec": Time.get_ticks_usec() - started_usec,
				"first_visual_latency_usec": 0,
				"first_collision_latency_usec": maxi(first_collision_latency_usec, 0),
				"visual_already_resident": int(metrics.get(
					"application_applied_render", 0
				)) == int(baseline.get("application_applied_render", 0)),
				"collision_already_resident": first_collision_latency_usec < 0,
				"target_state": target_state,
				"snapshot": snapshot,
			}
		await get_tree().process_frame
	return {"status": "FAIL", "error": "target collision readiness timed out"}


static func _metric_delta(before: Dictionary, after: Dictionary) -> Dictionary:
	var result := {}
	for key in WORK_COUNTERS:
		result[key] = maxi(0, int(after.get(key, 0)) - int(before.get(key, 0)))
	return result


static func _set_camera(scene: Node, target: Vector3) -> void:
	var camera := scene.get_node("Camera3D") as Camera3D
	camera.position = target + Vector3(-72.0, 54.0, -96.0)
	camera.look_at(target + Vector3(0.0, -8.0, 0.0), Vector3.UP)


func _capture(id: String) -> Dictionary:
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(capture_root))
	var path := capture_root.path_join(id + ".png")
	var image := get_tree().root.get_texture().get_image()
	var error := image.save_png(ProjectSettings.globalize_path(path))
	return {
		"id": id,
		"status": "PASS" if error == OK and image.get_width() > 0 else "FAIL",
		"path": path,
		"width": image.get_width(),
		"height": image.get_height(),
	}


func _finish_now(
	result_path: String,
	contract: Dictionary,
	error: String,
	details: Dictionary = {}
) -> void:
	failures.append(error)
	_write_json(result_path, {
		"schema": "world_transvoxel_terrain.cpu_prefetch_readiness_evidence.v1",
		"milestone": str(contract.get("milestone", "TQP-R04")),
		"status": "FAIL",
		"failures": failures,
		"details": details,
	})
	push_error(error)
	finished.emit(1)


static func _vector3(value: Variant) -> Vector3:
	var array := value as Array
	return Vector3(float(array[0]), float(array[1]), float(array[2])) if array.size() == 3 else Vector3.ZERO


static func _write_json(path: String, value: Dictionary) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify(value, "  ") + "\n")
