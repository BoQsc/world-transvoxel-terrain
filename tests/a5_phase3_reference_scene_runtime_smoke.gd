extends SceneTree

const MARKER := "WT_TERRAIN_A5_PHASE3_GODOT_PASS"
const SCENE_PATH := "res://addons/world_transvoxel_terrain/debug/wt_terrain_reference_scene.tscn"
const StorageProfile := preload("res://addons/world_transvoxel_terrain/storage/wt_terrain_storage_profile.gd")


func _initialize() -> void:
	call_deferred("_run_test")


func _run_test() -> void:
	var packed: PackedScene = load(SCENE_PATH)
	if packed == null:
		_fail("reference scene could not be loaded")
		return
	var scene: Node = packed.instantiate()
	if scene == null:
		_fail("reference scene could not be instantiated")
		return
	root.add_child(scene)
	await process_frame

	var terrain_world: Node = scene.call("get_terrain_world")
	if terrain_world == null:
		_fail("reference scene did not expose terrain world")
		return
	terrain_world.set("storage_profile", _fixture_storage_profile())

	if not scene.call("start_reference_backend_world") or \
			not await _wait_for_state(terrain_world, "running"):
		_fail("reference scene did not start backend world")
		return
	if not scene.call("update_reference_viewer", 1, 1, Vector3(8, 8, 8), 0, 0):
		_fail("reference scene viewer update failed")
		return
	if not await _wait_for_scene_settled(scene, 1, 1):
		_fail("reference scene did not report settled runtime")
		return

	var snapshot: Dictionary = scene.call("refresh_debug_snapshot")
	var runtime := Dictionary(snapshot.get("reference_runtime", {}))
	if str(runtime.get("implementation", "")) != "backend_reference_scene_runtime_smoke" or \
			not bool(runtime.get("backend_running", false)) or \
			not bool(runtime.get("cold_idle", false)):
		_fail("reference runtime summary mismatch: %s" % str(runtime))
		return
	var status_text := str(scene.call("get_debug_status_text"))
	if not status_text.contains("backend_state=running") or \
			not status_text.contains("render_resources=1") or \
			not status_text.contains("collision_resources=1"):
		_fail("reference scene status text did not show live runtime: %s" % status_text)
		return

	if not scene.call("remove_reference_viewer", 1, 2) or \
			not await _wait_for_scene_settled(scene, 0, 0):
		_fail("reference scene viewer removal did not settle")
		return
	if not scene.call("stop_reference_backend_world") or \
			not await _wait_for_state(terrain_world, "stopped"):
		_fail("reference scene did not stop backend world")
		return

	print(
		"%s scene=backend_running overlay=live cold_idle=stable implementation=backend_reference_scene_runtime_smoke"
		% MARKER
	)
	scene.queue_free()
	await process_frame
	quit(0)


func _fixture_storage_profile() -> Resource:
	var storage = StorageProfile.new()
	storage.world_manifest_path = "res://build/production-lifecycle-fixture/streaming.wtworld"
	storage.object_root_path = "res://build/production-lifecycle-fixture"
	storage.edit_journal_path = "res://build/production-lifecycle-fixture/world.wtedit"
	storage.snapshot_directory = "res://build/production-lifecycle-fixture/snapshots"
	storage.allow_res_paths_for_test_fixtures = true
	return storage


func _wait_for_state(terrain_world: Node, expected: String) -> bool:
	for _frame in range(900):
		if terrain_world.call("get_backend_world_state_name") == expected:
			await process_frame
			return true
		await process_frame
	return false


func _wait_for_scene_settled(scene: Node, render_count: int, collision_count: int) -> bool:
	for _frame in range(900):
		var snapshot: Dictionary = scene.call("refresh_debug_snapshot")
		var runtime := Dictionary(snapshot.get("reference_runtime", {}))
		if bool(runtime.get("cold_idle", false)) and \
				int(runtime.get("render_resources", -1)) == render_count and \
				int(runtime.get("collision_resources", -1)) == collision_count:
			await process_frame
			return true
		await process_frame
	return false


func _fail(message: String) -> void:
	push_error("WT_TERRAIN_A5_PHASE3_GODOT_FAIL: " + message)
	quit(1)
