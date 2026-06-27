extends SceneTree

const MARKER := "WT_TERRAIN_A4_PHASE1_GODOT_PASS"
const TerrainProfile := preload("res://addons/world_transvoxel_terrain/api/wt_terrain_profile.gd")
const GenerationProfile := preload("res://addons/world_transvoxel_terrain/generation/wt_terrain_generation_profile.gd")
const EditOperation := preload("res://addons/world_transvoxel_terrain/edit/wt_terrain_edit_operation.gd")
const EditBatch := preload("res://addons/world_transvoxel_terrain/edit/wt_terrain_edit_batch.gd")
const StorageProfile := preload("res://addons/world_transvoxel_terrain/storage/wt_terrain_storage_profile.gd")
const RecoveryPolicy := preload("res://addons/world_transvoxel_terrain/storage/wt_terrain_recovery_policy.gd")
const TerrainWorld := preload("res://addons/world_transvoxel_terrain/runtime/wt_terrain_world.gd")


func _init() -> void:
	var errors: Array[String] = []

	var terrain_profile = TerrainProfile.new()
	if terrain_profile.horizontal_cells != 2048 or terrain_profile.vertical_cells != 64:
		errors.append("reference terrain profile is not 2048 x 2048 x 64")
	if not terrain_profile.plus_y_is_up:
		errors.append("reference terrain profile must use +Y up")
	if not terrain_profile.finite_closed_boundary:
		errors.append("reference terrain profile must keep a finite closed boundary")

	var operations := _make_operations()
	var batch = EditBatch.new()
	for operation in operations:
		if not operation.is_valid():
			errors.append("operation invalid: %s" % operation.get_validation_error())
		var affected: AABB = operation.estimate_affected_aabb()
		if affected.size.x <= 0.0 or affected.size.y <= 0.0 or affected.size.z <= 0.0:
			errors.append("operation affected AABB is empty: %s" % str(operation.get_mode_name()))
		if not batch.add_operation(operation):
			errors.append("batch rejected operation: %s" % str(operation.get_mode_name()))

	if batch.get_operation_count() != 5:
		errors.append("edit batch should contain all five standard operations")
	if not batch.is_valid():
		errors.append("edit batch invalid: %s" % batch.get_validation_error())
	var commands := batch.to_bridge_commands()
	if commands.size() != 5:
		errors.append("edit batch did not emit five bridge commands")
	for command in commands:
		if int(command.get("schema_version", 0)) != 1:
			errors.append("bridge command missing schema version 1")
		if str(command.get("implementation", "")) != "resource_semantics_only":
			errors.append("bridge command implementation boundary missing")

	var storage = StorageProfile.new()
	if not storage.is_valid():
		errors.append("default storage profile invalid: %s" % storage.get_validation_error())
	for key in ["world_manifest_path", "edit_journal_path", "snapshot_directory"]:
		if str(storage.get(key)).begins_with("res://"):
			errors.append("storage write path must not use res://: %s" % key)

	var recovery = RecoveryPolicy.new()
	if not recovery.is_valid():
		errors.append("default recovery policy invalid: %s" % recovery.get_validation_error())
	if not recovery.is_cold_idle_default():
		errors.append("default recovery policy must be cold while idle")
	if not recovery.allows_restore_to_base():
		errors.append("default recovery policy must allow manual restore-to-base")
	if recovery.automatic_timed_regeneration_enabled or recovery.fluid_equilibrium_enabled:
		errors.append("automatic regeneration and fluid equilibrium must be disabled by default")

	var world = TerrainWorld.new()
	world.terrain_profile = terrain_profile
	world.generation_profile = GenerationProfile.new()
	world.storage_profile = storage
	world.recovery_policy = recovery
	var summary := world.get_a4_phase1_summary()
	if str(summary.get("implementation", "")) != "resource_semantics_only":
		errors.append("terrain world A4 summary has wrong implementation boundary")
	if not bool(Dictionary(summary.get("storage_profile", {})).get("assigned", false)):
		errors.append("terrain world did not report assigned storage profile")
	world.free()

	if not errors.is_empty():
		for error in errors:
			push_error(error)
		quit(1)
		return

	print(
		"%s profile=2048x64 operations=5 storage=valid recovery=cold_idle implementation=resource_semantics_only"
		% MARKER
	)
	quit(0)


func _make_operations() -> Array:
	var carve = EditOperation.new()
	carve.mode = EditOperation.Mode.CARVE
	carve.brush_shape = EditOperation.BrushShape.SPHERE
	carve.center = Vector3(32.0, 20.0, 32.0)
	carve.radius = 4.0
	carve.material_id = 0

	var construct = EditOperation.new()
	construct.mode = EditOperation.Mode.CONSTRUCT
	construct.brush_shape = EditOperation.BrushShape.SPHERE
	construct.center = Vector3(36.0, 18.0, 32.0)
	construct.radius = 3.0
	construct.material_id = 2

	var fill = EditOperation.new()
	fill.mode = EditOperation.Mode.FILL
	fill.brush_shape = EditOperation.BrushShape.BOX
	fill.center = Vector3(40.0, 16.0, 32.0)
	fill.box_extents = Vector3(2.0, 3.0, 2.0)
	fill.material_id = 3

	var paint = EditOperation.new()
	paint.mode = EditOperation.Mode.PAINT
	paint.brush_shape = EditOperation.BrushShape.SPHERE
	paint.center = Vector3(44.0, 18.0, 32.0)
	paint.radius = 2.0
	paint.material_id = 4

	var restore = EditOperation.new()
	restore.mode = EditOperation.Mode.RESTORE_TO_BASE
	restore.brush_shape = EditOperation.BrushShape.BOX
	restore.center = Vector3(48.0, 20.0, 32.0)
	restore.box_extents = Vector3(3.0, 3.0, 3.0)

	return [carve, construct, fill, paint, restore]
