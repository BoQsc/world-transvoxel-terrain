extends SceneTree

const MARKER := "WT_TERRAIN_HUMAN_INSPECTION_SMOKE_PASS"
const MAXIMUM_POST_FLIGHT_TARGET_READY_USEC := 100000
const InspectionScene := preload(
	"res://addons/world_transvoxel_terrain/debug/wt_terrain_human_inspection_scene.tscn"
)


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var scene: Node = InspectionScene.instantiate()
	root.add_child(scene)
	if not await _wait_for(scene, "_human_walk_mode", true, 1800):
		_fail("inspection did not enter walk mode")
		return
	if not bool(scene.get("_human_target_valid")):
		_fail("inspection entered walk mode without a valid terrain target")
		return
	var world: Node = scene.call("get_terrain_world")
	var revision_before := int(world.call("get_world_revision"))
	scene.call("_submit_human_target_edit")
	var first_timing := await _wait_for_edit(scene, revision_before + 1, 1800)
	if first_timing.is_empty():
		_fail("initial inspection edit timing did not complete")
		return
	if str(first_timing.get("status", "")) != "PASS":
		_fail("initial inspection edit timing failed: %s" % str(first_timing))
		return

	scene.call("_set_walk_mode", false)
	var camera := scene.get_node("Camera3D") as Camera3D
	var start_camera := camera.global_position
	var start_target := scene.get("_human_target") as Vector3
	var destination_target := Vector3(start_target.x + 192.0, 32.0, start_target.z)
	var destination_camera := destination_target + Vector3(-36.0, 24.0, -48.0)
	for frame in range(240):
		var weight := float(frame + 1) / 240.0
		camera.global_position = start_camera.lerp(destination_camera, weight)
		camera.look_at(destination_target + Vector3(0.0, -8.0, 0.0), Vector3.UP)
		await process_frame
	var arrival_usec := Time.get_ticks_usec()
	var arrival_sample := scene.call("capture_human_issue_sample") as Dictionary
	var destination_coordinate := Vector3i(
		floori(float(arrival_sample.viewer_position.x) / 16.0),
		floori(float(arrival_sample.viewer_position.y) / 16.0),
		floori(float(arrival_sample.viewer_position.z) / 16.0)
	)
	var arrival_chunk := scene.call(
		"capture_lod0_chunk_state", destination_coordinate
	) as Dictionary
	for _frame in range(600):
		var target := scene.get("_human_target") as Vector3
		if bool(scene.get("_human_target_valid")) and target.x > start_target.x + 128.0:
			break
		await process_frame
	if not bool(scene.get("_human_target_valid")):
		_fail("post-flight destination did not expose a ready edit target")
		return
	var target_ready_latency_usec := Time.get_ticks_usec() - arrival_usec
	if target_ready_latency_usec > MAXIMUM_POST_FLIGHT_TARGET_READY_USEC:
		_fail("post-flight target readiness exceeded 100 ms: %d usec" % \
			target_ready_latency_usec)
		return
	var ready_sample := scene.call("capture_human_issue_sample") as Dictionary
	var ready_chunk := scene.call(
		"capture_lod0_chunk_state", destination_coordinate
	) as Dictionary
	scene.set("_last_edit_timing", {})
	scene.call("_submit_human_target_edit")
	var second_timing := await _wait_for_edit(scene, revision_before + 2, 1800)
	if second_timing.is_empty() or str(second_timing.get("status", "")) != "PASS":
		_fail("post-flight inspection edit timing failed: %s" % str(second_timing))
		return
	var result := {
		"schema": "world_transvoxel_terrain.human_inspection_smoke.v1",
		"status": "PASS",
		"initial_edit": first_timing,
		"post_flight_target_ready_usec": target_ready_latency_usec,
		"arrival_sample": arrival_sample,
		"arrival_chunk": arrival_chunk,
		"ready_sample": ready_sample,
		"ready_chunk": ready_chunk,
		"post_flight_edit": second_timing,
	}
	var result_file := FileAccess.open(
		"res://human_terrain_inspection_smoke_result.json", FileAccess.WRITE
	)
	if result_file != null:
		result_file.store_string(JSON.stringify(result, "\t") + "\n")
	print("%s initial=%s post_flight_target_ready_usec=%d post_flight=%s" % [
		MARKER,
		JSON.stringify(first_timing),
		target_ready_latency_usec,
		JSON.stringify(second_timing),
	])
	await scene.call("shutdown_for_validation")
	scene.queue_free()
	await process_frame
	quit(0)


func _wait_for(scene: Node, property: StringName, expected: Variant, frames: int) -> bool:
	for _frame in range(frames):
		if scene.get(property) == expected:
			return true
		await process_frame
	return false


func _wait_for_edit(scene: Node, revision: int, frames: int) -> Dictionary:
	for _frame in range(frames):
		var timing := scene.get("_last_edit_timing") as Dictionary
		if int(timing.get("world_revision", 0)) == revision:
			return timing.duplicate(true)
		await process_frame
	return {}


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
