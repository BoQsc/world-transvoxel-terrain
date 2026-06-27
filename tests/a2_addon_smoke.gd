extends SceneTree

const MARKER := "WT_TERRAIN_A2_GODOT_SMOKE_PASS"
const ADDON_ROOT := "res://addons/world_transvoxel_terrain"


func _init() -> void:
	var errors: Array[String] = []

	var config := ConfigFile.new()
	var config_error := config.load("%s/plugin.cfg" % ADDON_ROOT)
	if config_error != OK:
		errors.append("plugin.cfg failed to load: %s" % config_error)
	else:
		var script_path := str(config.get_value("plugin", "script", ""))
		if script_path != "editor/world_transvoxel_terrain_plugin.gd":
			errors.append("plugin.cfg script path drifted: %s" % script_path)
		if load("%s/%s" % [ADDON_ROOT, script_path]) == null:
			errors.append("editor plugin script failed to load")

	var dependency_script := load("%s/api/wt_terrain_dependency_status.gd" % ADDON_ROOT)
	var profile_script := load("%s/api/wt_terrain_profile.gd" % ADDON_ROOT)
	var generation_script := load("%s/generation/wt_terrain_generation_profile.gd" % ADDON_ROOT)
	var world_script := load("%s/runtime/wt_terrain_world.gd" % ADDON_ROOT)

	if dependency_script == null:
		errors.append("dependency status script failed to load")
	if profile_script == null:
		errors.append("terrain profile script failed to load")
	if generation_script == null:
		errors.append("generation profile script failed to load")
	if world_script == null:
		errors.append("terrain world script failed to load")

	var dependency_status := {}
	if dependency_script != null:
		dependency_status = dependency_script.new().get_status()
		if not dependency_status.has("installed"):
			errors.append("dependency status missing installed flag")

	if profile_script != null:
		var profile = profile_script.new()
		if profile.horizontal_cells != 2048:
			errors.append("terrain profile horizontal_cells default drifted")
		if profile.vertical_cells != 64:
			errors.append("terrain profile vertical_cells default drifted")

	if generation_script != null:
		var generation = generation_script.new()
		if not bool(generation.supports_underground_volume):
			errors.append("generation profile must default to volumetric underground support")

	if world_script != null:
		var world = world_script.new()
		if not world.has_method("get_dependency_status"):
			errors.append("terrain world missing dependency status method")
		if not world.has_method("get_contract_summary"):
			errors.append("terrain world missing contract summary method")
		world.free()

	if not errors.is_empty():
		for error in errors:
			push_error(error)
		quit(1)
		return

	print(
		"%s dependency_installed=%s profile=2048x64 implementation=placeholder_contract_only"
		% [MARKER, str(dependency_status.get("installed", false)).to_lower()]
	)
	quit(0)
