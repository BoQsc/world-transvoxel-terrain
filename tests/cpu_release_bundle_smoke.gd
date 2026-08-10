extends SceneTree

const MARKER := "WT_TERRAIN_CPU_RELEASE_BUNDLE_GODOT_PASS"
const Bridge := preload("res://addons/world_transvoxel_terrain/runtime/wt_world_transvoxel_bridge.gd")
const TerrainWorld := preload("res://addons/world_transvoxel_terrain/runtime/wt_terrain_world.gd")


func _init() -> void:
	var errors: Array[String] = []
	for native_class in ["WorldTransvoxelTerrain", "WorldTransvoxelConfig"]:
		if not ClassDB.class_exists(native_class):
			errors.append("native authority class is missing: %s" % native_class)

	var bridge = Bridge.new()
	var identity := bridge.get_backend_identity()
	if not bool(identity.get("bridge_ready", false)):
		errors.append("authority bridge is not ready: %s" % str(identity))
	if not bool(identity.get("mit_backend_available", false)):
		errors.append("official MIT backend is unavailable")
	if not Array(identity.get("missing_methods", [])).is_empty():
		errors.append("authority bridge methods are missing")

	var world = TerrainWorld.new()
	var dependency := world.get_dependency_status()
	if not bool(dependency.get("installed", false)):
		errors.append("terrain addon did not detect the bundled authority")
	if not world.has_method("start_world") or not world.has_method("submit_edit_batch"):
		errors.append("terrain public API is incomplete")
	world.free()

	if not errors.is_empty():
		for error in errors:
			push_error(error)
		quit(1)
		return

	print(
		"%s authority=%s backend=%s fallback=false"
		% [MARKER, identity.get("addon_version", ""), identity.get("backend_id", "")]
	)
	quit(0)
