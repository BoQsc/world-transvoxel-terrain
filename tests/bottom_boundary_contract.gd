extends SceneTree

const MARKER := "WT_TERRAIN_BOTTOM_BOUNDARY_CONTRACT_PASS"
const GenerationProfile := preload(
	"res://addons/world_transvoxel_terrain/generation/wt_terrain_generation_profile.gd"
)
const GenerationBackend := preload(
	"res://addons/world_transvoxel_terrain/runtime/wt_terrain_generation_backend.gd"
)


class BoundaryBackend:
	extends Node

	var arguments: Array = []

	func start_procedural_world_preset_with_vertical_origin_and_bottom_boundary(
		chunk_count_x: int,
		chunk_count_y: int,
		chunk_origin_y: int,
		chunk_count_z: int,
		seed: int,
		source_revision: int,
		preset_id: String,
		bottom_boundary_policy: int,
		bottom_boundary_thickness_cells: int,
		object_root: String
	) -> bool:
		arguments = [
			chunk_count_x,
			chunk_count_y,
			chunk_origin_y,
			chunk_count_z,
			seed,
			source_revision,
			preset_id,
			bottom_boundary_policy,
			bottom_boundary_thickness_cells,
			object_root,
		]
		return true


class LegacyBackend:
	extends Node

	func start_procedural_world_preset_with_vertical_origin(
		_chunk_count_x: int,
		_chunk_count_y: int,
		_chunk_origin_y: int,
		_chunk_count_z: int,
		_seed: int,
		_source_revision: int,
		_preset_id: String,
		_object_root: String
	) -> bool:
		return true


func _initialize() -> void:
	call_deferred("_run_test")


func _run_test() -> void:
	var profile = GenerationProfile.new()
	profile.profile_id = &"bottom_boundary_contract"
	profile.procedural_preset_id = &"four_biomes_lakes_caves_roads"
	profile.world_chunk_count_x = 128
	profile.world_chunk_count_y = 16
	profile.world_chunk_origin_y = -8
	profile.world_chunk_count_z = 128
	profile.seed = 19023
	profile.source_revision = 190326
	profile.bottom_boundary_policy = GenerationProfile.BottomBoundaryPolicy.BEDROCK
	profile.bottom_boundary_thickness_cells = 16

	var summary := profile.get_contract_summary()
	if str(summary.get("bottom_boundary_policy", "")) != "BEDROCK" or \
			int(summary.get("bottom_boundary_top_cell", 0)) != -112 or \
			not bool(summary.get("bottom_boundary_non_carvable", false)):
		_fail("bedrock profile summary mismatch: %s" % str(summary))
		return

	var backend = BoundaryBackend.new()
	root.add_child(backend)
	var result := GenerationBackend.start_backend_world(
		backend, profile, "", "user://bottom-boundary-contract"
	)
	if not bool(result.get("started", false)) or backend.arguments.size() != 10 or \
			int(backend.arguments[7]) != GenerationProfile.BottomBoundaryPolicy.BEDROCK or \
			int(backend.arguments[8]) != 16:
		_fail("authoritative boundary dispatch mismatch: %s" % str(result))
		return

	var legacy_backend = LegacyBackend.new()
	root.add_child(legacy_backend)
	var legacy_result := GenerationBackend.start_backend_world(
		legacy_backend, profile, "", "user://bottom-boundary-contract"
	)
	if bool(legacy_result.get("started", false)) or \
			"lacks authoritative bottom-boundary support" not in str(legacy_result.get("error", "")):
		_fail("legacy backend did not fail closed: %s" % str(legacy_result))
		return

	profile.bottom_boundary_policy = GenerationProfile.BottomBoundaryPolicy.OPEN
	var invalid_result := GenerationBackend.start_backend_world(
		backend, profile, "", "user://bottom-boundary-contract"
	)
	if bool(invalid_result.get("started", false)) or \
			"zero thickness" not in str(invalid_result.get("error", "")):
		_fail("invalid open boundary configuration was accepted: %s" % str(invalid_result))
		return

	backend.queue_free()
	legacy_backend.queue_free()
	profile = null
	await process_frame
	print("%s modes=open,sealed,bedrock native_dispatch=1 fail_closed=1" % MARKER)
	quit(0)


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
