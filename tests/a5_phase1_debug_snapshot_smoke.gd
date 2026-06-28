extends SceneTree

const MARKER := "WT_TERRAIN_A5_PHASE1_GODOT_PASS"
const TerrainWorld := preload("res://addons/world_transvoxel_terrain/runtime/wt_terrain_world.gd")
const TerrainProfile := preload("res://addons/world_transvoxel_terrain/api/wt_terrain_profile.gd")
const GenerationProfile := preload("res://addons/world_transvoxel_terrain/generation/wt_terrain_generation_profile.gd")
const MaterialProfile := preload("res://addons/world_transvoxel_terrain/material/wt_terrain_material_profile.gd")
const StorageProfile := preload("res://addons/world_transvoxel_terrain/storage/wt_terrain_storage_profile.gd")
const RecoveryPolicy := preload("res://addons/world_transvoxel_terrain/storage/wt_terrain_recovery_policy.gd")
const DebugSnapshot := preload("res://addons/world_transvoxel_terrain/debug/wt_terrain_debug_snapshot.gd")

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


func _init() -> void:
	var errors: Array[String] = []
	var world = TerrainWorld.new()
	world.terrain_profile = TerrainProfile.new()
	world.generation_profile = GenerationProfile.new()
	world.storage_profile = StorageProfile.new()
	world.recovery_policy = RecoveryPolicy.new()
	world.material_profile = MaterialProfile.new()

	var snapshot: Dictionary = DebugSnapshot.capture(world)
	for category in REQUIRED_CATEGORIES:
		if not snapshot.has(category):
			errors.append("debug snapshot missing category: %s" % category)
	if str(snapshot.get("implementation", "")) != "debug_snapshot_contract":
		errors.append("debug snapshot implementation marker drifted")

	var terrain_profile := Dictionary(snapshot.get("terrain_profile", {}))
	if int(terrain_profile.get("horizontal_cells", 0)) != 2048 or \
			int(terrain_profile.get("vertical_cells", 0)) != 64:
		errors.append("debug snapshot reference profile drifted")
	var generation_profile := Dictionary(snapshot.get("generation_profile", {}))
	if str(generation_profile.get("profile_id", "")) != "deterministic_reference" or \
			str(generation_profile.get("source_mode", "")) != "DETERMINISTIC_REFERENCE":
		errors.append("debug snapshot generation profile drifted")
	var world_summary := Dictionary(snapshot.get("world", {}))
	if bool(world_summary.get("backend_running", true)):
		errors.append("debug snapshot should not start backend work")
	var budget := Dictionary(snapshot.get("budget", {}))
	if bool(budget.get("world_running", true)) or \
			int(budget.get("queued_render", -1)) != 0 or \
			int(budget.get("queued_collision", -1)) != 0:
		errors.append("debug snapshot cold default budget drifted")
	var material := Dictionary(snapshot.get("material", {}))
	if not bool(material.get("configured", false)) or \
			str(material.get("status", "")) != "material_profile_configured" or \
			str(material.get("profile_id", "")) != "debug_checker_palette":
		errors.append("debug snapshot material profile drifted")

	world.free()
	if not errors.is_empty():
		for error in errors:
			push_error(error)
		quit(1)
		return

	print(
		"%s categories=%d profile=2048x64 implementation=debug_snapshot_contract"
		% [MARKER, REQUIRED_CATEGORIES.size()]
	)
	quit(0)
