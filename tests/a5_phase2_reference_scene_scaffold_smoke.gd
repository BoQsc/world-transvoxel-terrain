extends SceneTree

const MARKER := "WT_TERRAIN_A5_PHASE2_GODOT_PASS"
const SCENE_PATH := "res://addons/world_transvoxel_terrain/debug/wt_terrain_reference_scene.tscn"
const REQUIRED_CATEGORIES := [
	"world",
	"terrain_profile",
	"generation_profile",
	"storage_profile",
	"recovery_policy",
	"budget",
	"collision",
	"streaming",
	"edit",
	"material",
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

	if not scene.has_method("refresh_debug_snapshot"):
		_fail("reference scene missing refresh_debug_snapshot")
		return
	var snapshot: Dictionary = scene.call("refresh_debug_snapshot")
	for category in REQUIRED_CATEGORIES:
		if not snapshot.has(category):
			_fail("reference scene snapshot missing category: %s" % category)
			return

	var summary: Dictionary = scene.call("get_reference_scene_summary")
	if not bool(summary.get("has_terrain_world", false)) or \
			not bool(summary.get("has_debug_overlay", false)):
		_fail("reference scene ownership incomplete: %s" % str(summary))
		return
	if str(summary.get("implementation", "")) != "local_reference_scene_scaffold":
		_fail("reference scene implementation marker drifted")
		return

	var terrain_profile := Dictionary(snapshot.get("terrain_profile", {}))
	if int(terrain_profile.get("horizontal_cells", 0)) != 2048 or \
			int(terrain_profile.get("vertical_cells", 0)) != 128:
		_fail("reference scene profile drifted")
		return
	var world := Dictionary(snapshot.get("world", {}))
	if bool(world.get("backend_running", true)):
		_fail("reference scene scaffold should not start backend work")
		return
	var status_text := str(scene.call("get_debug_status_text"))
	if not status_text.contains("profile=2048x128") or \
			not status_text.contains("implementation=local_reference_scene_scaffold"):
		_fail("reference scene status text mismatch: %s" % status_text)
		return

	print(
		"%s scene=instanced overlay=ready profile=2048x128 implementation=local_reference_scene_scaffold"
		% MARKER
	)
	scene.queue_free()
	await process_frame
	quit(0)


func _fail(message: String) -> void:
	push_error("WT_TERRAIN_A5_PHASE2_GODOT_FAIL: " + message)
	quit(1)
