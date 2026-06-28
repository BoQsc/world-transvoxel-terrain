extends SceneTree

const MARKER := "WT_TERRAIN_A5_PHASE4_GODOT_PASS"
const SCENE_PATH := "res://addons/world_transvoxel_terrain/debug/wt_terrain_reference_scene.tscn"
const StorageProfile := preload("res://addons/world_transvoxel_terrain/storage/wt_terrain_storage_profile.gd")
const REQUIRED_SECTIONS := [
	"[world]",
	"[terrain_profile]",
	"[generation_profile]",
	"[storage_profile]",
	"[recovery_policy]",
	"[budget]",
	"[collision]",
	"[streaming]",
	"[edit]",
	"[material]",
]


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
		_fail("reference scene did not settle runtime")
		return

	var categories: Array = scene.call("get_debug_overlay_categories")
	if categories.size() != REQUIRED_SECTIONS.size():
		_fail("debug overlay category count mismatch: %s" % str(categories))
		return
	var text := str(scene.call("get_debug_status_text"))
	for section in REQUIRED_SECTIONS:
		if not text.contains(section):
			_fail("debug overlay missing section: %s" % section)
			return
	for required_line in [
		"profile=2048x64",
		"backend_state=running",
		"source_mode=DETERMINISTIC_REFERENCE",
		"seed=1",
		"cold_idle=true",
		"queued_render=0",
		"queued_collision=0",
		"render_resources=1",
		"collision_resources=1",
		"configured=true",
		"profile_id=debug_checker_palette",
		"shader_mode=uv2_material_id_checker",
		"overlay_implementation=debug_overlay_category_rendering",
	]:
		if not text.contains(required_line):
			_fail("debug overlay missing live line: %s in %s" % [required_line, text])
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
		"%s sections=10 overlay=live resources=1 implementation=debug_overlay_category_rendering"
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
	push_error("WT_TERRAIN_A5_PHASE4_GODOT_FAIL: " + message)
	quit(1)
