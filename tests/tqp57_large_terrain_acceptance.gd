extends SceneTree

const MARKER := "WT_TERRAIN_TQP57_LARGE_ACCEPTANCE_GODOT_PASS"
const CONTRACT_PATH := "res://TQP57_LARGE_TERRAIN_ACCEPTANCE_CONTRACT.json"
const RESULT_PATH := "res://tqp57_large_terrain_acceptance_result.json"
const CAPTURE_ROOT := "res://tqp57_large_terrain_acceptance_captures"
const AcceptanceScene := preload(
	"res://addons/world_transvoxel_terrain/debug/wt_terrain_large_acceptance_scene.tscn"
)

var failures: Array[String] = []
var sample_results := {}
var queue_peaks := {"scheduler": 0, "storage": 0, "render": 0, "collision": 0}
var observed_lod_counts := {}
var memory_peak_bytes := 0


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var contract = JSON.parse_string(FileAccess.get_file_as_string(CONTRACT_PATH))
	if not contract is Dictionary:
		_fail_now("acceptance contract could not be loaded")
		return
	get_root().get_window().size = Vector2i(1280, 720)
	RenderingServer.viewport_set_measure_render_time(get_root().get_viewport_rid(), true)
	var scene: Node = AcceptanceScene.instantiate()
	root.add_child(scene)
	scene.call("set_automatic_viewer_tracking", false)
	var terrain_world: Node = scene.call("get_terrain_world")
	terrain_world.authoritative_sample_ready.connect(_on_sample_ready)
	var initial: Dictionary = await scene.call("wait_until_ready", 2400)
	if str(initial.get("status", "")) != "PASS":
		_fail_now("production-addon large terrain did not become ready")
		return
	var profile: Dictionary = scene.call("get_acceptance_profile")
	_validate_profile(contract, profile)
	var initial_snapshot: Dictionary = scene.call("get_validation_snapshot")
	var initial_audit: Dictionary = scene.call("collect_lod_audit")
	_observe_audit(initial_audit)
	var captures: Array[Dictionary] = []
	captures.append(await _capture(scene, "initial_lod", Vector3(1024.0, 116.0, 1120.0), Vector3(1024.0, 34.0, 1024.0)))

	var scenarios: Array[Dictionary] = []
	var edited_samples := {}
	for value in contract.get("scenarios", []):
		var scenario: Dictionary = value
		print("TQP57_LARGE_SCENARIO_START id=%s" % str(scenario.get("id", "")))
		var result := await _run_scenario(scene, terrain_world, scenario, contract, edited_samples, captures)
		scenarios.append(result)
		print("TQP57_LARGE_SCENARIO_END id=%s status=%s" % [str(scenario.get("id", "")), str(result.get("status", ""))])
		if str(result.get("status", "")) != "PASS":
			failures.append("scenario failed: %s" % str(scenario.get("id", "")))

	var final_audit: Dictionary = scene.call("collect_lod_audit", Vector3(1796.0, 27.0, 1792.0), 20.0)
	_observe_audit(final_audit)
	var lod_seam_audit: Dictionary = scene.call(
		"collect_lod_audit", Vector3(1792.0, 27.0, 1792.0), 24.0, true
	)
	_observe_audit(lod_seam_audit)
	var seam := lod_seam_audit.get("lod_seam", {}) as Dictionary
	if bool(seam.get("found", false)):
		var center_value := seam.get("center", {}) as Dictionary
		var seam_center := Vector3(
			float(center_value.get("x", 0.0)),
			float(center_value.get("y", 0.0)),
			float(center_value.get("z", 0.0))
		)
		captures.append(await _capture(
			scene, "lod_seam", seam_center + Vector3(-42.0, 30.0, -48.0), seam_center
		))
	var collision := await _collision_probe(scene, Vector3(1800.0, 80.0, 1792.0), Vector3(1800.0, -80.0, 1792.0))
	var persistence := await _restart_and_verify(scene, terrain_world, edited_samples)
	var final_snapshot: Dictionary = scene.call("get_validation_snapshot")
	var aggregate := _aggregate(scenarios)
	_evaluate(contract, scenarios, aggregate, initial_snapshot, final_snapshot, final_audit, lod_seam_audit, collision, persistence, captures)
	var shutdown: Dictionary = await scene.call("shutdown_for_validation")
	if str(shutdown.get("status", "")) != "PASS":
		failures.append("production-addon world did not shut down cleanly")
	var report := {
		"schema": "world_transvoxel_terrain.tqp57_large_terrain_acceptance_evidence.v1",
		"milestone": "TQP-57",
		"status": "PASS" if failures.is_empty() else "FAIL",
		"retained_complete": failures.is_empty(),
		"engine": Engine.get_version_info(),
		"renderer": RenderingServer.get_current_rendering_driver_name(),
		"profile": profile,
		"backend_identity": terrain_world.call("get_backend_identity"),
		"initial_snapshot": initial_snapshot,
		"scenarios": scenarios,
		"aggregate": aggregate,
		"observed_lod_counts": observed_lod_counts,
		"final_lod_audit": final_audit,
		"lod_seam_audit": lod_seam_audit,
		"collision": collision,
		"persistence": persistence,
		"captures": captures,
		"queue_peaks": queue_peaks,
		"memory": {
			"static_bytes": int(Performance.get_monitor(Performance.MEMORY_STATIC)),
			"peak_static_bytes": memory_peak_bytes,
			"video_bytes": int(Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED)),
		},
		"shutdown": shutdown,
		"qualified_scope": contract.get("qualified_scope", []),
		"explicitly_unqualified_scope": contract.get("explicitly_unqualified_scope", []),
		"failures": failures,
	}
	_write_json(RESULT_PATH, report)
	if not failures.is_empty():
		push_error("WT_TERRAIN_TQP57_LARGE_ACCEPTANCE_GODOT_FAIL: " + "; ".join(failures))
		quit(1)
		return
	print("%s scenarios=%d lod0=%d lod1=%d lod2=%d overlaps=0 generation_errors=0 topology_edges=0 persistence=1 collision=1" % [
		MARKER,
		scenarios.size(),
		int(observed_lod_counts.get("0", 0)),
		int(observed_lod_counts.get("1", 0)),
		int(observed_lod_counts.get("2", 0)),
	])
	scene.queue_free()
	await process_frame
	quit(0)


func _run_scenario(
	scene: Node,
	terrain_world: Node,
	scenario: Dictionary,
	contract: Dictionary,
	edited_samples: Dictionary,
	captures: Array[Dictionary]
) -> Dictionary:
	var profile: Dictionary = contract.get("runtime_profile", {})
	var kind := str(scenario.get("kind", ""))
	var start := _vector3(scenario.get("start", []))
	var finish := _vector3(scenario.get("end", []))
	var initial_settlement: Dictionary = {"status": "PASS"}
	if kind in ["teleport", "far_return"]:
		initial_settlement = await scene.call("move_viewer_and_wait", start, 2400)
		if str(initial_settlement.get("status", "")) == "PASS":
			initial_settlement = await scene.call("move_viewer_and_wait", finish, 2400)
	else:
		initial_settlement = await scene.call("move_viewer_and_wait", start, 2400)

	var edit_result := {}
	if kind in ["dig", "construct"]:
		var center := _vector3(scenario.get("edit_center", []))
		var before = await _query_sample(terrain_world, Vector3i(roundi(center.x), roundi(center.y), roundi(center.z)))
		edit_result = await scene.call("submit_edit_and_wait", StringName("carve" if kind == "dig" else "construct"), center, 2400)
		var after = await _query_sample(terrain_world, Vector3i(roundi(center.x), roundi(center.y), roundi(center.z)))
		edit_result["sample_before"] = _sample_state(before)
		edit_result["sample_after"] = _sample_state(after)
		edit_result["sample_changed"] = not _same_sample_value(edit_result["sample_before"], edit_result["sample_after"])
		edited_samples[str(Vector3i(roundi(center.x), roundi(center.y), roundi(center.z)))] = edit_result["sample_after"]
		if kind == "construct":
			captures.append(await _capture(scene, "edited_site", center + Vector3(-54.0, 46.0, -72.0), center))

	var frame_values: Array[float] = []
	var process_values: Array[float] = []
	var physics_values: Array[float] = []
	var render_cpu_values: Array[float] = []
	var render_gpu_values: Array[float] = []
	var draw_values: Array[float] = []
	var primitive_values: Array[float] = []
	var over_100ms := 0
	var frame_count := int(profile.get("frames_per_scenario", 90))
	var camera := scene.get_node("Camera3D") as Camera3D
	for frame in range(frame_count):
		var frame_started := Time.get_ticks_usec()
		var t := float(frame) / float(maxi(frame_count - 1, 1))
		var position := start.lerp(finish, t)
		if kind == "lod_churn":
			position = start.lerp(finish, 0.5 + 0.5 * sin(t * TAU * 4.0))
		if kind in ["motion", "lod_churn"] and frame % 12 == 0:
			scene.call("publish_view", position, true)
		camera.position = position + Vector3(0.0, 48.0, 72.0)
		camera.look_at(position, Vector3.UP)
		await process_frame
		var elapsed := float(Time.get_ticks_usec() - frame_started)
		frame_values.append(elapsed)
		over_100ms += 1 if elapsed > 100000.0 else 0
		process_values.append(Performance.get_monitor(Performance.TIME_PROCESS) * 1000000.0)
		physics_values.append(Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000000.0)
		render_cpu_values.append(RenderingServer.viewport_get_measured_render_time_cpu(get_root().get_viewport_rid()) * 1000.0)
		render_gpu_values.append(RenderingServer.viewport_get_measured_render_time_gpu(get_root().get_viewport_rid()) * 1000.0)
		draw_values.append(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
		primitive_values.append(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME))
		_observe_metrics(terrain_world.call("get_runtime_metrics"))

	var final_settlement: Dictionary = await scene.call("wait_until_ready", 2400)
	var audit: Dictionary = scene.call("collect_lod_audit")
	_observe_audit(audit)
	var metrics: Dictionary = terrain_world.call("get_runtime_metrics")
	var rendered := _maximum(draw_values) > 0.0 and _maximum(primitive_values) > 0.0
	var edit_pass := edit_result.is_empty() or (
		str(edit_result.get("status", "")) == "PASS" and bool(edit_result.get("sample_changed", false))
	)
	if kind == "far_return":
		for key in edited_samples:
			var point := _vector3i_from_string(str(key))
			var sample = await _query_sample(terrain_world, point)
			if not _same_sample_value(edited_samples[key], _sample_state(sample)):
				edit_pass = false
		captures.append(await _capture(scene, "far_return", finish + Vector3(-72.0, 58.0, -90.0), Vector3(1796.0, 27.0, 1792.0)))
	return {
		"id": scenario.get("id", ""),
		"kind": kind,
		"initial_settlement": initial_settlement,
		"final_settlement": final_settlement,
		"status": "PASS" if str(initial_settlement.get("status", "")) == "PASS" and \
				str(final_settlement.get("status", "")) == "PASS" and rendered and \
				str(audit.get("status", "")) == "PASS" and edit_pass else "FAIL",
		"frame": _distribution(frame_values),
		"stutter_over_100ms_count": over_100ms,
		"stutter_fraction_over_100ms": float(over_100ms) / float(maxi(frame_count, 1)),
		"process": _distribution(process_values),
		"physics": _distribution(physics_values),
		"render_cpu": _distribution(render_cpu_values),
		"render_gpu": _distribution(render_gpu_values),
		"draw_calls": _distribution(draw_values),
		"primitives": _distribution(primitive_values),
		"resources": {
			"active_chunks": metrics.get("active_chunk_records", -1),
			"render_resources": metrics.get("render_resources", -1),
			"collision_resources": metrics.get("collision_resources", -1),
		},
		"loading_state": _loading_state(metrics),
		"lod_audit": audit,
		"edit": edit_result,
	}


func _restart_and_verify(scene: Node, terrain_world: Node, edited_samples: Dictionary) -> Dictionary:
	var before_revision := int(terrain_world.call("get_world_revision"))
	var restart: Dictionary = await scene.call("restart_preserving_storage", 2400)
	var mismatches: Array[String] = []
	for key in edited_samples:
		var sample = await _query_sample(terrain_world, _vector3i_from_string(str(key)))
		if not _same_sample_value(edited_samples[key], _sample_state(sample)):
			mismatches.append(str(key))
	return {
		"status": "PASS" if str(restart.get("status", "")) == "PASS" and \
				int(terrain_world.call("get_world_revision")) == before_revision and mismatches.is_empty() else "FAIL",
		"world_revision_before": before_revision,
		"world_revision_after": terrain_world.call("get_world_revision"),
		"sample_mismatches": mismatches,
		"restart": restart,
	}


func _collision_probe(scene: Node, from: Vector3, to: Vector3) -> Dictionary:
	for _frame in range(3):
		await physics_frame
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(from, to)
	var hit: Dictionary = scene.get_world_3d().direct_space_state.intersect_ray(query)
	var metrics: Dictionary = scene.call("get_terrain_world").call("get_runtime_metrics")
	return {
		"status": "PASS" if not hit.is_empty() and int(metrics.get("collision_resources", 0)) > 0 and \
				int(metrics.get("collision_resources", 0)) < int(metrics.get("active_chunk_records", 0)) and \
				int(metrics.get("collision_required_not_ready_chunk_records", 0)) == 0 else "FAIL",
		"ray_hit": not hit.is_empty(),
		"position": _vector_summary(hit.get("position", Vector3.ZERO)),
		"collision_resources": metrics.get("collision_resources", 0),
		"active_chunk_records": metrics.get("active_chunk_records", 0),
		"collision_required_not_ready": metrics.get("collision_required_not_ready_chunk_records", 0),
		"targeted_residency": int(metrics.get("collision_resources", 0)) < int(metrics.get("active_chunk_records", 0)),
	}


func _capture(scene: Node, id: String, camera_position: Vector3, target: Vector3) -> Dictionary:
	var directory := ProjectSettings.globalize_path(CAPTURE_ROOT)
	DirAccess.make_dir_recursive_absolute(directory)
	var camera := scene.get_node("Camera3D") as Camera3D
	var hidden_nodes: Array[Node3D] = []
	for path in ["WorldBounds", "ResidentBounds", "ViewerMarker"]:
		var node := scene.get_node(path) as Node3D
		if node != null and node.visible:
			hidden_nodes.append(node)
			node.visible = false
	camera.position = camera_position
	camera.look_at(target, Vector3.UP)
	camera.current = true
	for _frame in range(12):
		await process_frame
	var image := get_root().get_viewport().get_texture().get_image()
	var path := CAPTURE_ROOT.path_join(id + ".png")
	var error := image.save_png(ProjectSettings.globalize_path(path))
	for node in hidden_nodes:
		node.visible = true
	return {
		"id": id,
		"path": path,
		"status": "PASS" if error == OK and image.get_width() >= 1280 and image.get_height() >= 720 else "FAIL",
		"width": image.get_width(),
		"height": image.get_height(),
		"camera": _vector_summary(camera_position),
		"target": _vector_summary(target),
	}


func _query_sample(terrain_world: Node, point: Vector3i):
	sample_results.clear()
	var request_id := int(terrain_world.call("request_authoritative_sample", point, 0))
	if request_id <= 0:
		return null
	for _frame in range(1800):
		if sample_results.has(request_id):
			return sample_results[request_id]
		await process_frame
	return null


func _on_sample_ready(request_id: int, sample: RefCounted) -> void:
	sample_results[request_id] = sample


func _observe_metrics(metrics: Dictionary) -> void:
	queue_peaks.scheduler = maxi(int(queue_peaks.scheduler), int(metrics.get("scheduler_queued_jobs", 0)))
	queue_peaks.storage = maxi(int(queue_peaks.storage), int(metrics.get("storage_queued_requests", 0)))
	queue_peaks.render = maxi(int(queue_peaks.render), int(metrics.get("queued_render", 0)))
	queue_peaks.collision = maxi(int(queue_peaks.collision), int(metrics.get("total_collision_backlog", 0)))
	memory_peak_bytes = maxi(memory_peak_bytes, int(Performance.get_monitor(Performance.MEMORY_STATIC)))


func _observe_audit(audit: Dictionary) -> void:
	var counts := audit.get("lod_counts", {}) as Dictionary
	for lod in counts:
		observed_lod_counts[lod] = maxi(int(observed_lod_counts.get(lod, 0)), int(counts[lod]))


func _evaluate(
	contract: Dictionary,
	scenarios: Array[Dictionary],
	aggregate: Dictionary,
	initial: Dictionary,
	final: Dictionary,
	audit: Dictionary,
	lod_seam_audit: Dictionary,
	collision: Dictionary,
	persistence: Dictionary,
	captures: Array[Dictionary]
) -> void:
	var budgets: Dictionary = contract.get("budgets", {})
	_expect(int(initial.get("catalog_page_count", 0)) >= int(budgets.get("minimum_catalog_pages", 0)), "large catalog page count is incomplete")
	for lod in contract.get("required_lod_levels", []):
		_expect(int(observed_lod_counts.get(str(int(lod)), 0)) > 0, "required LOD%d was never active" % int(lod))
	for scenario in scenarios:
		var frame := scenario.get("frame", {}) as Dictionary
		_expect(int(frame.get("sample_count", 0)) >= int(budgets.get("minimum_frame_samples_per_scenario", 0)), "frame evidence incomplete: %s" % scenario.get("id", ""))
		_expect(float(frame.get("p99_usec", INF)) <= float(budgets.get("maximum_frame_p99_usec", 0)), "frame p99 exceeded: %s" % scenario.get("id", ""))
		_expect(float(frame.get("worst_usec", INF)) <= float(budgets.get("maximum_frame_worst_usec", 0)), "frame worst exceeded: %s" % scenario.get("id", ""))
		_expect(float(scenario.get("stutter_fraction_over_100ms", INF)) <= float(budgets.get("maximum_stutter_fraction_over_100ms", 0)), "stutter fraction exceeded: %s" % scenario.get("id", ""))
		var edit := scenario.get("edit", {}) as Dictionary
		if not edit.is_empty():
			_expect(float(edit.get("latency_usec", INF)) <= float(budgets.get("maximum_edit_visual_latency_usec", 0)), "edit settlement latency exceeded")
	_expect(int(queue_peaks.scheduler) <= int(budgets.get("maximum_scheduler_queue_depth", 0)), "scheduler queue exceeded")
	_expect(int(queue_peaks.storage) <= int(budgets.get("maximum_storage_queue_depth", 0)), "storage queue exceeded")
	_expect(int(queue_peaks.render) <= int(budgets.get("maximum_render_queue_depth", 0)), "render queue exceeded")
	_expect(int(queue_peaks.collision) <= int(budgets.get("maximum_collision_queue_depth", 0)), "collision queue exceeded")
	_expect(memory_peak_bytes <= int(budgets.get("maximum_peak_process_memory_bytes", 0)), "memory ceiling exceeded")
	_expect(int(audit.get("coverage_overlap_count", -1)) <= int(budgets.get("maximum_coverage_overlaps", 0)), "adaptive coverage overlaps detected")
	_expect((audit.get("visual_generation_mismatches", []) as Array).is_empty(), "visual generation mismatches detected")
	_expect((audit.get("collision_generation_mismatches", []) as Array).is_empty(), "collision generation mismatches detected")
	var topology := audit.get("topology", {}) as Dictionary
	_expect(int(topology.get("boundary_edges", -1)) <= int(budgets.get("maximum_topology_boundary_edges", 0)), "topology boundary edges detected")
	_expect(int(topology.get("nonmanifold_edges", -1)) <= int(budgets.get("maximum_topology_nonmanifold_edges", 0)), "topology nonmanifold edges detected")
	_expect(int(topology.get("orientation_inconsistent_edges", -1)) <= int(budgets.get("maximum_topology_orientation_inconsistent_edges", 0)), "topology shared-edge orientation inconsistency detected")
	_expect(int(topology.get("zero_area_triangles", -1)) <= int(budgets.get("maximum_topology_zero_area_triangles", 0)), "topology zero-area triangles detected")
	_expect(bool((lod_seam_audit.get("lod_seam", {}) as Dictionary).get("found", false)), "live mixed-LOD seam was not located")
	_expect(str(lod_seam_audit.get("status", "")) == "PASS", "mixed-LOD seam audit failed")
	var seam_topology := lod_seam_audit.get("topology", {}) as Dictionary
	_expect(int(seam_topology.get("boundary_edges", -1)) <= int(budgets.get("maximum_topology_boundary_edges", 0)), "LOD seam boundary edges detected")
	_expect(int(seam_topology.get("nonmanifold_edges", -1)) <= int(budgets.get("maximum_topology_nonmanifold_edges", 0)), "LOD seam nonmanifold edges detected")
	_expect(int(seam_topology.get("orientation_inconsistent_edges", -1)) <= int(budgets.get("maximum_topology_orientation_inconsistent_edges", 0)), "LOD seam shared-edge orientation inconsistency detected")
	_expect(int(seam_topology.get("zero_area_triangles", -1)) <= int(budgets.get("maximum_topology_zero_area_triangles", 0)), "LOD seam zero-area triangles detected")
	_expect(str(collision.get("status", "")) == "PASS", "targeted collision acceptance failed")
	_expect(str(persistence.get("status", "")) == "PASS", "far-return restart persistence failed")
	var capture_ids := {}
	for capture in captures:
		capture_ids[str(capture.get("id", ""))] = capture.get("status", "")
	for id in contract.get("required_capture_ids", []):
		_expect(str(capture_ids.get(str(id), "")) == "PASS", "required visual capture failed: %s" % str(id))
	_expect(str(final.get("status", "")) == "READY", "final terrain state was not ready")
	_expect(int(aggregate.get("rendered_scenarios", 0)) == scenarios.size(), "one or more scenarios rendered no geometry")


static func _aggregate(scenarios: Array[Dictionary]) -> Dictionary:
	var frames: Array[float] = []
	var rendered := 0
	for scenario in scenarios:
		var frame := scenario.get("frame", {}) as Dictionary
		frames.append(float(frame.get("p50_usec", 0.0)))
		frames.append(float(frame.get("p95_usec", 0.0)))
		frames.append(float(frame.get("p99_usec", 0.0)))
		frames.append(float(frame.get("worst_usec", 0.0)))
		if float((scenario.get("primitives", {}) as Dictionary).get("worst_usec", 0.0)) > 0.0:
			rendered += 1
	return {"frame_envelope": _distribution(frames), "rendered_scenarios": rendered}


static func _distribution(values: Array[float]) -> Dictionary:
	if values.is_empty():
		return {"sample_count": 0, "p50_usec": 0.0, "p95_usec": 0.0, "p99_usec": 0.0, "worst_usec": 0.0}
	var sorted := values.duplicate()
	sorted.sort()
	return {
		"sample_count": sorted.size(),
		"p50_usec": sorted[_percentile_index(sorted.size(), 0.50)],
		"p95_usec": sorted[_percentile_index(sorted.size(), 0.95)],
		"p99_usec": sorted[_percentile_index(sorted.size(), 0.99)],
		"worst_usec": sorted[-1],
	}


static func _percentile_index(size: int, percentile: float) -> int:
	return clampi(ceili(float(size) * percentile) - 1, 0, size - 1)


static func _loading_state(metrics: Dictionary) -> Dictionary:
	return {
		"world_running": metrics.get("world_running", false),
		"scheduler_queued_jobs": metrics.get("scheduler_queued_jobs", -1),
		"storage_queued_requests": metrics.get("storage_queued_requests", -1),
		"queued_render": metrics.get("queued_render", -1),
		"collision_backlog": metrics.get("total_collision_backlog", -1),
		"pending_replacements": metrics.get("pending_chunk_replacements", -1),
		"pending_retirements": metrics.get("pending_chunk_retirements", -1),
	}


static func _sample_state(sample) -> Dictionary:
	if sample == null:
		return {}
	return {
		"density": float(sample.call("get_density")),
		"material": int(sample.call("get_material")),
		"world_revision": int(sample.call("get_world_revision")),
	}


static func _same_sample_value(expected: Dictionary, actual: Dictionary) -> bool:
	return not expected.is_empty() and not actual.is_empty() and \
			is_equal_approx(float(expected.get("density", INF)), float(actual.get("density", -INF))) and \
			int(expected.get("material", -1)) == int(actual.get("material", -2))


static func _vector3(value: Variant) -> Vector3:
	var array := value as Array
	return Vector3(float(array[0]), float(array[1]), float(array[2])) if array.size() == 3 else Vector3.ZERO


static func _vector3i_from_string(value: String) -> Vector3i:
	var clean := value.trim_prefix("(").trim_suffix(")")
	var parts := clean.split(",")
	return Vector3i(int(parts[0]), int(parts[1]), int(parts[2])) if parts.size() == 3 else Vector3i.ZERO


static func _vector_summary(value: Variant) -> Dictionary:
	var vector := value as Vector3
	return {"x": vector.x, "y": vector.y, "z": vector.z}


static func _maximum(values: Array[float]) -> float:
	var maximum := 0.0
	for value in values:
		maximum = maxf(maximum, value)
	return maximum


func _validate_profile(contract: Dictionary, profile: Dictionary) -> void:
	var expected := contract.get("runtime_profile", {}) as Dictionary
	_expect(_int_array_equal(profile.get("volume_cells", []), expected.get("volume_cells", [])), "acceptance volume drifted")
	_expect(int(profile.get("maximum_lod", -1)) == int(expected.get("maximum_lod", -2)), "acceptance maximum LOD drifted")
	_expect(profile.get("fallback", true) is bool and not bool(profile.get("fallback", true)), "fallback terrain is forbidden")


static func _int_array_equal(left_value: Variant, right_value: Variant) -> bool:
	var left := left_value as Array
	var right := right_value as Array
	if left.size() != right.size():
		return false
	for index in range(left.size()):
		if int(left[index]) != int(right[index]):
			return false
	return true


func _expect(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)


func _write_json(path: String, payload: Dictionary) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(JSON.stringify(payload, "\t") + "\n")


func _fail_now(message: String) -> void:
	push_error("WT_TERRAIN_TQP57_LARGE_ACCEPTANCE_GODOT_FAIL: " + message)
	quit(1)
