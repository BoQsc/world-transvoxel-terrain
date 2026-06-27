extends SceneTree

const MARKER := "WT_TERRAIN_A3_GODOT_BRIDGE_PASS"
const ADDON_ROOT := "res://addons/world_transvoxel_terrain"
const Bridge := preload("res://addons/world_transvoxel_terrain/runtime/wt_world_transvoxel_bridge.gd")


func _init() -> void:
	var errors: Array[String] = []

	if not ClassDB.class_exists("WorldTransvoxelTerrain"):
		errors.append("WorldTransvoxelTerrain class is missing")
	if not ClassDB.class_exists("WorldTransvoxelConfig"):
		errors.append("WorldTransvoxelConfig class is missing")

	var bridge = Bridge.new()
	var status := bridge.get_bridge_status()
	if not bool(status.get("bridge_ready", false)):
		errors.append("bridge is not ready: %s" % str(status))

	var identity := bridge.get_backend_identity()
	if not bool(identity.get("bridge_ready", false)):
		errors.append("backend identity is not ready: %s" % str(identity))
	if str(identity.get("addon_version", "")).is_empty():
		errors.append("backend addon version is empty")
	if not bool(identity.get("mit_backend_available", false)):
		errors.append("MIT backend should be available in official world-transvoxel")
	if str(identity.get("backend_license", "")).find("MIT") < 0:
		errors.append("backend license should report MIT scope")
	if int(identity.get("config_schema_version", 0)) <= 0:
		errors.append("config schema version should be positive")
	if not bool(identity.get("config_valid", false)):
		errors.append("default WorldTransvoxelConfig should be valid")
	if not Array(identity.get("missing_methods", [])).is_empty():
		errors.append("missing bridge methods: %s" % str(identity.get("missing_methods", [])))

	if not errors.is_empty():
		for error in errors:
			push_error(error)
		quit(1)
		return

	print(
		"%s version=%s backend_id=%s license=%s config_schema=%d implementation=bridge_only"
		% [
			MARKER,
			str(identity.get("addon_version", "")),
			str(identity.get("backend_id", "")),
			str(identity.get("backend_license", "")),
			int(identity.get("config_schema_version", 0)),
		]
	)
	quit(0)
