extends SceneTree

const MARKER := "WT_TERRAIN_A4_PHASE4_GODOT_PASS"
const TerrainWorld := preload("res://addons/world_transvoxel_terrain/runtime/wt_terrain_world.gd")
const TerrainProfile := preload("res://addons/world_transvoxel_terrain/api/wt_terrain_profile.gd")
const StorageProfile := preload("res://addons/world_transvoxel_terrain/storage/wt_terrain_storage_profile.gd")
const STABLE_COUNTERS := [
	"viewer_updates",
	"viewer_removals",
	"planned_demands",
	"sample_jobs",
	"mesh_jobs",
	"storage_completions",
	"mesh_completions",
	"transition_mesh_completions",
	"edit_commits",
	"edit_replacements",
	"sample_queries",
	"world_snapshots",
	"published_events",
	"queued_render",
	"queued_collision",
	"pending_chunk_retirements",
	"active_chunk_records",
	"fully_ready_chunk_records",
	"render_resources",
	"collision_resources",
]


func _initialize() -> void:
	call_deferred("_run_test")


func _run_test() -> void:
	var terrain_world = TerrainWorld.new()
	terrain_world.terrain_profile = TerrainProfile.new()
	terrain_world.storage_profile = _fixture_storage_profile()
	root.add_child(terrain_world)

	if not _profile_is_reference(terrain_world.terrain_profile):
		_fail("reference terrain profile defaults drifted")
		return
	if not terrain_world.start_backend_world() or \
			not await _wait_for_state(terrain_world, "running"):
		_fail("terrain world did not start backend: %s" % terrain_world.get_last_error())
		return

	if not terrain_world.update_viewer(1, 1, Vector3(8, 8, 8), 0, 0):
		_fail("terrain world viewer update failed: %s" % terrain_world.get_last_error())
		return
	if not await _wait_for_settled(terrain_world, 1, 1):
		_fail("terrain world did not settle initial viewer: %s" % str(
			terrain_world.get_cold_idle_summary()
		))
		return

	var chunk := terrain_world.query_chunk_state(Vector3i.ZERO, 0)
	if not _is_ready_snapshot(chunk):
		_fail("public terrain-world chunk query did not report ready origin chunk")
		return

	var stable_before: Dictionary = terrain_world.get_runtime_metrics()
	if not await _hold_idle_and_compare(terrain_world, stable_before, 60):
		return

	if not terrain_world.remove_viewer(1, 2):
		_fail("terrain world viewer removal failed: %s" % terrain_world.get_last_error())
		return
	if not await _wait_for_settled(terrain_world, 0, 0):
		_fail("terrain world did not settle viewer removal: %s" % str(
			terrain_world.get_cold_idle_summary()
		))
		return
	if not terrain_world.stop_backend_world() or \
			not await _wait_for_state(terrain_world, "stopped"):
		_fail("terrain world did not stop backend")
		return

	print(
		"%s profile=2048x64 viewer=settled cold_idle=stable remove=settled implementation=reference_profile_runtime_cold_idle"
		% MARKER
	)
	terrain_world.queue_free()
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


func _profile_is_reference(profile: Resource) -> bool:
	var summary := Dictionary(profile.call("get_contract_summary"))
	return int(summary.get("horizontal_cells", 0)) == 2048 and \
		int(summary.get("vertical_cells", 0)) == 64 and \
		bool(summary.get("plus_y_is_up", false)) and \
		bool(summary.get("finite_closed_boundary", false))


func _is_ready_snapshot(snapshot: RefCounted) -> bool:
	return snapshot != null and snapshot.call("is_present") and \
		snapshot.call("is_visual_ready") and \
		snapshot.call("is_collision_ready") and \
		snapshot.call("is_fully_ready")


func _wait_for_state(terrain_world: Node, expected: String) -> bool:
	for _frame in range(900):
		if terrain_world.get_backend_world_state_name() == expected:
			await process_frame
			return true
		await process_frame
	return false


func _wait_for_settled(terrain_world: Node, render_count: int, collision_count: int) -> bool:
	for _frame in range(900):
		var summary: Dictionary = terrain_world.get_cold_idle_summary()
		if bool(summary.get("cold_idle", false)) and \
				int(summary.get("render_resources", -1)) == render_count and \
				int(summary.get("collision_resources", -1)) == collision_count:
			await process_frame
			return true
		if terrain_world.get_backend_world_state_name() == "failed":
			return false
		await process_frame
	return false


func _hold_idle_and_compare(
	terrain_world: Node,
	stable_before: Dictionary,
	frame_count: int
) -> bool:
	for _frame in range(frame_count):
		if not terrain_world.is_cold_idle():
			_fail("terrain world stopped being cold idle during hold")
			return false
		await process_frame
	var stable_after: Dictionary = terrain_world.get_runtime_metrics()
	for key in STABLE_COUNTERS:
		if stable_before.get(key) != stable_after.get(key):
			_fail(
				"idle counter changed for %s before=%s after=%s" %
				[key, str(stable_before.get(key)), str(stable_after.get(key))]
			)
			return false
	return true


func _fail(message: String) -> void:
	push_error("WT_TERRAIN_A4_PHASE4_GODOT_FAIL: " + message)
	quit(1)
