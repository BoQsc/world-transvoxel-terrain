extends Node

signal finished(exit_code: int)

const RESULT_PATH := "res://cpu_visual_defect_investigation_result.json"
const CAPTURE_ROOT := "res://cpu_visual_defect_investigation_captures"
const AcceptanceScene := preload(
	"res://addons/world_transvoxel_terrain/debug/wt_terrain_large_acceptance_scene.tscn"
)
const WatertightnessProbe := preload(
	"res://addons/world_transvoxel_terrain/debug/wt_terrain_watertightness_probe.gd"
)
const CAPTURE_FRAMES := [3, 12, 30, 72]
const STATIONS := [
	{
		"id": "reported_area",
		"viewer": Vector3(1169.7, 79.9, 1220.5),
		"target": Vector3(1276.0, 27.0, 1344.0),
	},
	{
		"id": "cross_lod_return",
		"viewer": Vector3(1456.0, 80.0, 1216.0),
		"target": Vector3(1344.0, 26.0, 1344.0),
	},
]

var captures: Array[Dictionary] = []
var failures: Array[String] = []
var capture_root := CAPTURE_ROOT
var _diagnostic_material: StandardMaterial3D


func _ready() -> void:
	call_deferred("_run")


func _run() -> void:
	var result_path := OS.get_environment("WT_VISUAL_DEFECT_RESULT") if \
			OS.has_environment("WT_VISUAL_DEFECT_RESULT") else RESULT_PATH
	capture_root = OS.get_environment("WT_VISUAL_DEFECT_CAPTURE_ROOT") if \
			OS.has_environment("WT_VISUAL_DEFECT_CAPTURE_ROOT") else CAPTURE_ROOT
	get_tree().root.get_window().size = Vector2i(1280, 720)
	var scene: Node = AcceptanceScene.instantiate()
	get_tree().root.add_child(scene)
	scene.call("set_automatic_viewer_tracking", false)
	scene.call("set_hold_after_coarse", true)
	_configure_scene(scene)
	print("WT_VISUAL_DEFECT_STAGE coarse_bootstrap")
	var coarse: Dictionary = await scene.call("wait_until_global_coarse_ready", 2400)
	if str(coarse.get("status", "")) != "PASS":
		_finish_now(result_path, "global coarse bootstrap failed", coarse)
		return
	if not bool(scene.call("release_local_refinement")):
		_finish_now(result_path, "initial local refinement was rejected")
		return
	var initial: Dictionary = await scene.call("wait_until_ready", 1800)
	if str(initial.get("status", "")) != "PASS":
		_finish_now(result_path, "initial local refinement did not settle")
		return
	var station_reports: Array[Dictionary] = []
	for station in STATIONS:
		station_reports.append(await _run_station(scene, station))
	var shutdown: Dictionary = await scene.call("shutdown_for_validation")
	if str(shutdown.get("status", "")) != "PASS":
		failures.append("visual defect fixture did not shut down cleanly")
	var report := {
		"schema": "world_transvoxel_terrain.cpu_visual_defect_investigation.v1",
		"status": "PASS" if failures.is_empty() else "FAIL",
		"engine": Engine.get_version_info(),
		"renderer": RenderingServer.get_current_rendering_driver_name(),
		"coarse_bootstrap": coarse,
		"initial_settlement": initial,
		"stations": station_reports,
		"captures": captures,
		"shutdown": shutdown,
		"failures": failures,
	}
	_write_json(result_path, report)
	if failures.is_empty():
		print("WT_TERRAIN_CPU_VISUAL_DEFECT_INVESTIGATION_PASS captures=%d" % captures.size())
	else:
		push_error("WT_TERRAIN_CPU_VISUAL_DEFECT_INVESTIGATION_FAIL: " + "; ".join(failures))
	scene.queue_free()
	await get_tree().process_frame
	finished.emit(0 if failures.is_empty() else 1)


func _run_station(scene: Node, station: Dictionary) -> Dictionary:
	var station_id := str(station.get("id", "station"))
	var viewer := station.get("viewer", Vector3.ZERO) as Vector3
	var target := station.get("target", Vector3.ZERO) as Vector3
	_set_camera(scene, viewer, target)
	_set_production_mode(scene, true)
	var baseline_updates := _viewer_updates(scene)
	var accepted := bool(scene.call("publish_view", viewer, true))
	if not accepted:
		failures.append("viewer request was rejected for " + station_id)
		return {"id": station_id, "status": "FAIL", "accepted": false}
	print("WT_VISUAL_DEFECT_STAGE " + station_id)
	var samples: Array[Dictionary] = []
	var capture_index := 0
	for frame in range(180):
		await get_tree().process_frame
		if capture_index < CAPTURE_FRAMES.size() and frame >= CAPTURE_FRAMES[capture_index]:
			samples.append(await _capture_triplet(scene, station_id, frame, false))
			capture_index += 1
		var snapshot := scene.call("get_validation_snapshot") as Dictionary
		var metrics := snapshot.get("metrics", {}) as Dictionary
		if capture_index >= CAPTURE_FRAMES.size() and \
				_viewer_updates(scene) > baseline_updates and \
				str(snapshot.get("status", "")) == "READY" and \
				int(metrics.get("pending_chunk_replacements", -1)) == 0 and \
				int(metrics.get("pending_chunk_retirements", -1)) == 0:
			break
	var settled: Dictionary = await scene.call("wait_until_ready", 1800)
	if str(settled.get("status", "")) != "PASS":
		failures.append("station did not settle: " + station_id)
	samples.append(await _capture_triplet(scene, station_id, 9999, true))
	var seam_probe := {}
	var seam_chunks: Array[Dictionary] = []
	if station_id == "cross_lod_return":
		var backend := scene.call("get_terrain_world").call("get_backend_terrain") as Node
		seam_probe = WatertightnessProbe.collect(
			backend,
			"cpu_visual_defect_x1408",
			Vector3(1408.0, 30.0, 1320.0),
			72.0
		)
		if not bool(seam_probe.get("ok", false)):
			failures.append("exact x=1408 seam probe failed")
		_collect_seam_chunks(backend, 1408.0, 1248.0, 1392.0, seam_chunks)
		_set_camera(
			scene,
			Vector3(1408.0, 280.0, 1320.0),
			Vector3(1408.0, 24.0, 1320.0)
		)
		samples.append(await _capture_triplet(
			scene, station_id + "_top_down", 9999, true
		))
	return {
		"id": station_id,
		"status": "PASS" if accepted and str(settled.get("status", "")) == "PASS" else "FAIL",
		"viewer": _vector_summary(viewer),
		"camera_target": _vector_summary(target),
		"samples": samples,
		"settlement": settled,
		"seam_probe": seam_probe,
		"seam_chunks": seam_chunks,
	}


func _capture_triplet(
	scene: Node,
	station_id: String,
	frame: int,
	settled: bool
) -> Dictionary:
	var terrain_world := scene.call("get_terrain_world") as Node
	terrain_world.process_mode = Node.PROCESS_MODE_DISABLED
	await get_tree().process_frame
	var suffix := "settled" if settled else "frame_%04d" % frame
	var prefix := station_id + "_" + suffix
	var snapshot := scene.call("get_validation_snapshot") as Dictionary
	var overlap := _visible_ancestor_overlap_audit(scene)
	if int(overlap.get("count", -1)) != 0:
		failures.append("visible ancestor overlap at " + prefix)
	_set_production_mode(scene, true)
	await _wait_render_frames(6)
	var shadow_on := await _capture(scene, prefix + "_shadow_on", "shadow_on", snapshot, overlap)
	_set_production_mode(scene, false)
	await _wait_render_frames(6)
	var shadow_off := await _capture(scene, prefix + "_shadow_off", "shadow_off", snapshot, overlap)
	_set_diagnostic_mode(scene)
	await _wait_render_frames(3)
	var unshaded := await _capture(scene, prefix + "_unshaded", "unshaded", snapshot, overlap)
	_set_production_mode(scene, true)
	terrain_world.process_mode = Node.PROCESS_MODE_INHERIT
	return {
		"id": prefix,
		"settled": settled,
		"source_frame": frame,
		"snapshot_status": snapshot.get("status", "UNKNOWN"),
		"metrics": _selected_metrics(snapshot.get("metrics", {}) as Dictionary),
		"visible_coverage": overlap,
		"capture_ids": [shadow_on.get("id", ""), shadow_off.get("id", ""), unshaded.get("id", "")],
	}


func _configure_scene(scene: Node) -> void:
	for path in ["Interface", "WorldBounds", "ResidentBounds", "ViewerMarker"]:
		var node := scene.get_node_or_null(path)
		if node is CanvasLayer:
			(node as CanvasLayer).visible = false
		elif node is CanvasItem:
			(node as CanvasItem).visible = false
		elif node is Node3D:
			(node as Node3D).visible = false
	var applicator := scene.get_node("MaterialApplicator")
	applicator.set("auto_apply", false)
	applicator.set_process(false)
	_diagnostic_material = StandardMaterial3D.new()
	_diagnostic_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_diagnostic_material.albedo_color = Color(0.92, 0.92, 0.92, 1.0)
	_set_production_mode(scene, true)


func _set_production_mode(scene: Node, shadows: bool) -> void:
	var applicator := scene.get_node("MaterialApplicator")
	applicator.set("visual_mode", &"production")
	applicator.call("apply_materials_now")
	var environment := (scene.get_node("WorldEnvironment") as WorldEnvironment).environment
	environment.background_mode = Environment.BG_SKY
	var sun := scene.get_node("Sun") as DirectionalLight3D
	var fill := scene.get_node("Fill") as DirectionalLight3D
	sun.visible = true
	fill.visible = true
	sun.shadow_enabled = shadows


func _set_diagnostic_mode(scene: Node) -> void:
	var backend := scene.call("get_terrain_world").call("get_backend_terrain") as Node
	backend.call("set_render_material_override", _diagnostic_material)
	backend.call("set_water_material_override", _diagnostic_material)
	var environment := (scene.get_node("WorldEnvironment") as WorldEnvironment).environment
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(1.0, 0.0, 1.0, 1.0)
	(scene.get_node("Sun") as DirectionalLight3D).visible = false
	(scene.get_node("Fill") as DirectionalLight3D).visible = false


func _set_camera(scene: Node, position: Vector3, target: Vector3) -> void:
	var camera := scene.get_node("Camera3D") as Camera3D
	camera.position = position
	var direction := (target - position).normalized()
	var up := Vector3.FORWARD if absf(direction.dot(Vector3.UP)) > 0.999 else Vector3.UP
	camera.look_at(target, up)
	camera.current = true


func _wait_render_frames(count: int) -> void:
	for _frame in range(count):
		await get_tree().process_frame
	await RenderingServer.frame_post_draw


func _capture(
	scene: Node,
	id: String,
	mode: String,
	snapshot: Dictionary,
	overlap: Dictionary
) -> Dictionary:
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(capture_root))
	var path := capture_root.path_join(id + ".png")
	var image := get_tree().root.get_viewport().get_texture().get_image()
	var error := image.save_png(ProjectSettings.globalize_path(path))
	var metrics := snapshot.get("metrics", {}) as Dictionary
	var capture := {
		"id": id,
		"mode": mode,
		"path": path,
		"status": "PASS" if error == OK and image.get_width() == 1280 and image.get_height() == 720 else "FAIL",
		"width": image.get_width(),
		"height": image.get_height(),
		"snapshot_status": snapshot.get("status", "UNKNOWN"),
		"pending_chunk_replacements": metrics.get("pending_chunk_replacements", -1),
		"pending_chunk_retirements": metrics.get("pending_chunk_retirements", -1),
		"visible_ancestor_overlaps": overlap.get("count", -1),
	}
	captures.append(capture)
	return capture


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


func _collect_seam_chunks(
	node: Node,
	plane_x: float,
	minimum_z: float,
	maximum_z: float,
	output: Array[Dictionary]
) -> void:
	if node is MeshInstance3D and str(node.name).begins_with("WT_Render_"):
		var instance := node as MeshInstance3D
		var key := _parse_chunk_key(str(instance.name))
		if key.w >= 0:
			var extent := 16.0 * pow(2.0, float(key.w))
			var minimum := Vector3(key.x, key.y, key.z) * extent
			var maximum := minimum + Vector3.ONE * extent
			if minimum.x <= plane_x and maximum.x >= plane_x and \
					minimum.z < maximum_z and maximum.z > minimum_z and \
					minimum.y < 80.0 and maximum.y > -16.0:
				var vertices := 0
				var indices := 0
				if instance.mesh is ArrayMesh:
					var mesh := instance.mesh as ArrayMesh
					for surface in range(mesh.get_surface_count()):
						var arrays := mesh.surface_get_arrays(surface)
						vertices += (arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()
						indices += (arrays[Mesh.ARRAY_INDEX] as PackedInt32Array).size()
				output.append({
					"name": str(instance.name),
					"key": _chunk_key_text(key),
					"minimum": _vector_summary(minimum),
					"maximum": _vector_summary(maximum),
					"vertices": vertices,
					"indices": indices,
				})
	for child in node.get_children():
		if child is Node:
			_collect_seam_chunks(child, plane_x, minimum_z, maximum_z, output)


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


static func _selected_metrics(metrics: Dictionary) -> Dictionary:
	return {
		"active": metrics.get("non_retiring_chunk_records", -1),
		"fully_ready": metrics.get("non_retiring_fully_ready_chunk_records", -1),
		"render_resources": metrics.get("render_resources", -1),
		"pending_replacements": metrics.get("pending_chunk_replacements", -1),
		"pending_retirements": metrics.get("pending_chunk_retirements", -1),
		"queued_render": metrics.get("queued_render", -1),
		"scheduler_jobs": metrics.get("scheduler_queued_jobs", -1),
		"storage_requests": metrics.get("storage_queued_requests", -1),
	}


func _finish_now(
	result_path: String,
	error: String,
	details: Dictionary = {}
) -> void:
	failures.append(error)
	_write_json(result_path, {
		"schema": "world_transvoxel_terrain.cpu_visual_defect_investigation.v1",
		"status": "FAIL",
		"captures": captures,
		"failures": failures,
		"details": details,
	})
	push_error(error)
	finished.emit(1)


static func _viewer_updates(scene: Node) -> int:
	var world := scene.call("get_terrain_world") as Node
	return int((world.call("get_runtime_metrics") as Dictionary).get("viewer_updates", 0))


static func _vector_summary(value: Vector3) -> Array[float]:
	return [value.x, value.y, value.z]


static func _write_json(path: String, value: Dictionary) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify(value, "  ") + "\n")
