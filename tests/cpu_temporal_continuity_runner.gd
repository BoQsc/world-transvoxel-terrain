extends Node

signal finished(exit_code: int)

const CONTRACT_PATH := "res://CPU_TEMPORAL_CONTINUITY_CONTRACT.json"
const RESULT_PATH := "res://cpu_temporal_continuity_result.json"
const CAPTURE_ROOT := "res://cpu_temporal_continuity_captures"
const AcceptanceScene := preload(
	"res://addons/world_transvoxel_terrain/debug/wt_terrain_large_acceptance_scene.tscn"
)
const WatertightnessProbe := preload(
	"res://addons/world_transvoxel_terrain/debug/wt_terrain_watertightness_probe.gd"
)
const WORK_COUNTERS := [
	"storage_accepted_requests",
	"storage_load_time_ns_total",
	"page_cache_encoded_hits",
	"page_cache_encoded_misses",
	"page_cache_decoded_hits",
	"page_cache_decoded_misses",
	"page_cache_encoded_evictions",
	"page_cache_decoded_evictions",
	"mesh_jobs",
	"mesh_worker_execute_time_ns_total",
]

var failures: Array[String] = []
var captures: Array[Dictionary] = []
var topology_samples: Array[Dictionary] = []
var monitored_frames := 0
var maximum_visible_ancestor_overlaps := 0
var first_overlap_example := ""
var capture_root := CAPTURE_ROOT
var _diagnostic_material: StandardMaterial3D


func _ready() -> void:
	call_deferred("_run")


func _run() -> void:
	var contract_path := OS.get_environment("WT_TEMPORAL_CONTRACT") if \
			OS.has_environment("WT_TEMPORAL_CONTRACT") else CONTRACT_PATH
	var result_path := OS.get_environment("WT_TEMPORAL_RESULT") if \
			OS.has_environment("WT_TEMPORAL_RESULT") else RESULT_PATH
	capture_root = OS.get_environment("WT_TEMPORAL_CAPTURE_ROOT") if \
			OS.has_environment("WT_TEMPORAL_CAPTURE_ROOT") else CAPTURE_ROOT
	var contract = JSON.parse_string(FileAccess.get_file_as_string(contract_path))
	if not contract is Dictionary:
		_finish_now(result_path, {}, "temporal continuity contract could not be loaded")
		return
	get_tree().root.get_window().size = Vector2i(960, 540)
	var scene: Node = AcceptanceScene.instantiate()
	get_tree().root.add_child(scene)
	scene.call("set_automatic_viewer_tracking", false)
	scene.call("set_hold_after_coarse", true)
	var coarse: Dictionary = await scene.call("wait_until_global_coarse_ready", 2400)
	if str(coarse.get("status", "")) != "PASS":
		_finish_now(result_path, contract, "global coarse bootstrap failed: %s" % JSON.stringify(coarse))
		return
	_configure_diagnostic_scene(scene)
	_set_camera(scene, _camera_site(contract))
	captures.append(await _capture("coarse_diagnostic", true))

	var cases: Array[Dictionary] = []
	var baseline := _viewer_updates(scene)
	var case_start_metrics := _runtime_metrics(scene)
	if not bool(scene.call("release_local_refinement")):
		failures.append("initial refinement request was rejected")
	else:
		cases.append(await _monitor_case(
			scene,
			contract.get("cases", [])[0],
			baseline,
			_camera_site(contract),
			case_start_metrics
		))
	for case_index in range(1, (contract.get("cases", []) as Array).size()):
		var case := (contract.get("cases", []) as Array)[case_index] as Dictionary
		var position := _vector3(case.get("position", []))
		baseline = _viewer_updates(scene)
		case_start_metrics = _runtime_metrics(scene)
		if not bool(scene.call("publish_view", position, true)):
			failures.append("viewer request was rejected: %s" % str(case.get("id", "")))
			continue
		cases.append(await _monitor_case(
			scene, case, baseline, _camera_site(contract), case_start_metrics
		))

	await _capture_shadow_pair(scene)
	var budgets := contract.get("budgets", {}) as Dictionary
	if maximum_visible_ancestor_overlaps > int(budgets.get("maximum_visible_ancestor_overlaps", 0)):
		failures.append("visible parent-child coverage overlapped during publication")
	var topology_failures := 0
	for sample in topology_samples:
		if not bool(sample.get("ok", false)):
			topology_failures += 1
	if topology_failures > int(budgets.get("maximum_topology_failures", 0)):
		failures.append("visible topology failed during temporal publication")
	if monitored_frames < int(budgets.get("minimum_monitored_frames", 0)):
		failures.append("temporal frame evidence is incomplete")
	for case in cases:
		if str(case.get("status", "")) != "PASS":
			failures.append("temporal case failed: %s" % str(case.get("id", "")))
	var shutdown: Dictionary = await scene.call("shutdown_for_validation")
	if str(shutdown.get("status", "")) != "PASS":
		failures.append("temporal fixture did not shut down cleanly")
	var report := {
		"schema": "world_transvoxel_terrain.cpu_temporal_continuity_evidence.v1",
		"milestone": str(contract.get("milestone", "TQP-R02")),
		"status": "PASS" if failures.is_empty() else "FAIL",
		"engine": Engine.get_version_info(),
		"renderer": RenderingServer.get_current_rendering_driver_name(),
		"coarse_bootstrap": coarse,
		"cases": cases,
		"monitored_frames": monitored_frames,
		"maximum_visible_ancestor_overlaps": maximum_visible_ancestor_overlaps,
		"first_overlap_example": first_overlap_example,
		"topology_samples": topology_samples,
		"topology_failures": topology_failures,
		"captures": captures,
		"shutdown": shutdown,
		"qualified_scope": contract.get("qualified_scope", []),
		"explicitly_unqualified_scope": contract.get("explicitly_unqualified_scope", []),
		"failures": failures,
	}
	_write_json(result_path, report)
	if failures.is_empty():
		print("WT_TERRAIN_CPU_TEMPORAL_CONTINUITY_GODOT_PASS frames=%d topology=%d overlaps=%d captures=%d" % [
			monitored_frames, topology_samples.size(), maximum_visible_ancestor_overlaps, captures.size()
		])
	else:
		push_error("WT_TERRAIN_CPU_TEMPORAL_CONTINUITY_GODOT_FAIL: " + "; ".join(failures))
	scene.queue_free()
	await get_tree().process_frame
	finished.emit(0 if failures.is_empty() else 1)


func _monitor_case(
	scene: Node,
	case: Dictionary,
	baseline_viewer_updates: int,
	topology_center: Vector3,
	start_metrics: Dictionary
) -> Dictionary:
	var case_id := str(case.get("id", "unnamed"))
	var maximum_frames := int(case.get("maximum_frames", 1200))
	var started_usec := Time.get_ticks_usec()
	var transition_captured := false
	var settled := false
	var maximum_overlaps := 0
	var topology_failures := 0
	var frames_elapsed := 0
	for frame in range(maximum_frames):
		monitored_frames += 1
		frames_elapsed += 1
		var overlap := _visible_ancestor_overlap_audit(scene)
		var overlap_count := int(overlap.get("count", 0))
		maximum_overlaps = maxi(maximum_overlaps, overlap_count)
		maximum_visible_ancestor_overlaps = maxi(
			maximum_visible_ancestor_overlaps, overlap_count
		)
		if first_overlap_example.is_empty() and overlap_count > 0:
			first_overlap_example = str(overlap.get("example", ""))
		if frame % 30 == 0:
			var topology := WatertightnessProbe.collect(
				scene.call("get_terrain_world").call("get_backend_terrain"),
				"cpu_temporal_continuity",
				topology_center,
				24.0
			)
			topology["case"] = case_id
			topology["frame"] = frame
			topology_samples.append(topology)
			if not bool(topology.get("ok", false)):
				topology_failures += 1
		if not transition_captured and frame >= 12:
			captures.append(await _capture(case_id + "_transition", true))
			transition_captured = true
		var snapshot := scene.call("get_validation_snapshot") as Dictionary
		var metrics := snapshot.get("metrics", {}) as Dictionary
		if _viewer_updates(scene) > baseline_viewer_updates and \
				str(snapshot.get("status", "")) == "READY" and \
				int(metrics.get("pending_chunk_replacements", -1)) == 0 and \
				int(metrics.get("pending_chunk_retirements", -1)) == 0:
			settled = true
			break
		await get_tree().process_frame
	if not transition_captured:
		captures.append(await _capture(case_id + "_transition", true))
	captures.append(await _capture(case_id + "_settled", true))
	var end_metrics := _runtime_metrics(scene)
	return {
		"id": case_id,
		"status": "PASS" if settled and maximum_overlaps == 0 and topology_failures == 0 else "FAIL",
		"settled": settled,
		"frames": frames_elapsed,
		"latency_usec": Time.get_ticks_usec() - started_usec,
		"maximum_visible_ancestor_overlaps": maximum_overlaps,
		"topology_failures": topology_failures,
		"work_delta": _metric_delta(start_metrics, end_metrics),
	}


func _configure_diagnostic_scene(scene: Node) -> void:
	for path in ["Interface", "WorldBounds", "ResidentBounds", "ViewerMarker"]:
		var node := scene.get_node_or_null(path)
		if node is CanvasItem:
			(node as CanvasItem).visible = false
		elif node is Node3D:
			(node as Node3D).visible = false
	var applicator := scene.get_node("MaterialApplicator")
	applicator.set("auto_apply", false)
	applicator.set_process(false)
	_diagnostic_material = StandardMaterial3D.new()
	_diagnostic_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_diagnostic_material.albedo_color = Color(0.92, 0.92, 0.92, 1.0)
	var backend := scene.call("get_terrain_world").call("get_backend_terrain") as Node
	backend.call("set_render_material_override", _diagnostic_material)
	backend.call("set_water_material_override", _diagnostic_material)
	var world_environment := scene.get_node("WorldEnvironment") as WorldEnvironment
	world_environment.environment.background_mode = Environment.BG_COLOR
	world_environment.environment.background_color = Color(1.0, 0.0, 1.0, 1.0)
	world_environment.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	world_environment.environment.ambient_light_color = Color.WHITE
	world_environment.environment.ambient_light_energy = 1.0
	(scene.get_node("Sun") as DirectionalLight3D).visible = false
	(scene.get_node("Fill") as DirectionalLight3D).visible = false


func _capture_shadow_pair(scene: Node) -> void:
	var applicator := scene.get_node("MaterialApplicator")
	applicator.set("visual_mode", &"production")
	applicator.call("apply_materials_now")
	var world_environment := scene.get_node("WorldEnvironment") as WorldEnvironment
	world_environment.environment.background_color = Color(0.15, 0.18, 0.17, 1.0)
	var sun := scene.get_node("Sun") as DirectionalLight3D
	var fill := scene.get_node("Fill") as DirectionalLight3D
	sun.visible = true
	fill.visible = true
	sun.shadow_enabled = true
	await get_tree().process_frame
	captures.append(await _capture("shadow_on", false))
	sun.shadow_enabled = false
	await get_tree().process_frame
	captures.append(await _capture("shadow_off", false))


func _set_camera(scene: Node, target: Vector3) -> void:
	var camera := scene.get_node("Camera3D") as Camera3D
	camera.position = target + Vector3(0.0, 156.0, 92.0)
	camera.look_at(target, Vector3.UP)


func _visible_ancestor_overlap_audit(scene: Node) -> Dictionary:
	var backend := scene.call("get_terrain_world").call("get_backend_terrain") as Node
	var visible := {}
	_collect_visible_chunk_keys(backend, visible)
	var count := 0
	var example := ""
	for value in visible.values():
		var key := value as Vector4i
		var parent := key
		while parent.w < 3:
			parent = Vector4i(
				floori(float(parent.x) / 2.0),
				floori(float(parent.y) / 2.0),
				floori(float(parent.z) / 2.0),
				parent.w + 1
			)
			var parent_text := _chunk_key_text(parent)
			if visible.has(parent_text):
				count += 1
				if example.is_empty():
					example = "%s overlaps ancestor %s" % [_chunk_key_text(key), parent_text]
	return {"count": count, "example": example, "visible_chunk_meshes": visible.size()}


func _collect_visible_chunk_keys(node: Node, output: Dictionary) -> void:
	if node is MeshInstance3D:
		var instance := node as MeshInstance3D
		if instance.is_visible_in_tree() and str(instance.name).begins_with("WT_Render_"):
			var key := _parse_chunk_key(str(instance.name))
			if key.w >= 0:
				output[_chunk_key_text(key)] = key
	for child in node.get_children():
		if child is Node:
			_collect_visible_chunk_keys(child, output)


static func _parse_chunk_key(value: String) -> Vector4i:
	var text := value.trim_prefix("WT_Render_")
	var lod_marker := text.find("_L")
	if lod_marker < 0:
		return Vector4i(0, 0, 0, -1)
	var coordinates := text.substr(0, lod_marker).split("_")
	var lod_text := text.substr(lod_marker + 2).split("_")[0]
	if coordinates.size() != 3 or not lod_text.is_valid_int():
		return Vector4i(0, 0, 0, -1)
	return Vector4i(int(coordinates[0]), int(coordinates[1]), int(coordinates[2]), int(lod_text))


static func _chunk_key_text(key: Vector4i) -> String:
	return "%d,%d,%d@L%d" % [key.x, key.y, key.z, key.w]


func _capture(id: String, diagnostic: bool) -> Dictionary:
	await RenderingServer.frame_post_draw
	var absolute_root := ProjectSettings.globalize_path(capture_root)
	DirAccess.make_dir_recursive_absolute(absolute_root)
	var path := capture_root.path_join(id + ".png")
	var image := get_tree().root.get_texture().get_image()
	var error := image.save_png(ProjectSettings.globalize_path(path))
	return {
		"id": id,
		"status": "PASS" if error == OK and image.get_width() > 0 and image.get_height() > 0 else "FAIL",
		"path": path,
		"diagnostic": diagnostic,
		"width": image.get_width(),
		"height": image.get_height(),
	}


func _finish_now(result_path: String, contract: Dictionary, error: String) -> void:
	failures.append(error)
	_write_json(result_path, {
		"schema": "world_transvoxel_terrain.cpu_temporal_continuity_evidence.v1",
		"milestone": str(contract.get("milestone", "TQP-R02")),
		"status": "FAIL",
		"failures": failures,
	})
	push_error(error)
	finished.emit(1)


static func _viewer_updates(scene: Node) -> int:
	return int(_runtime_metrics(scene).get("viewer_updates", 0))


static func _runtime_metrics(scene: Node) -> Dictionary:
	var world := scene.call("get_terrain_world") as Node
	return world.call("get_runtime_metrics") as Dictionary


static func _metric_delta(before: Dictionary, after: Dictionary) -> Dictionary:
	var delta := {}
	for key in WORK_COUNTERS:
		delta[key] = maxi(0, int(after.get(key, 0)) - int(before.get(key, 0)))
	return delta


static func _camera_site(contract: Dictionary) -> Vector3:
	return _vector3((contract.get("world", {}) as Dictionary).get("camera_site", []))


static func _vector3(value: Variant) -> Vector3:
	var array := value as Array
	return Vector3(float(array[0]), float(array[1]), float(array[2])) if array.size() == 3 else Vector3.ZERO


static func _write_json(path: String, value: Dictionary) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify(value, "  ") + "\n")
