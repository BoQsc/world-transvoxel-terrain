extends SceneTree

const MARKER := "WT_TERRAIN_A4_PHASE3_GODOT_PASS"
const TerrainWorld := preload("res://addons/world_transvoxel_terrain/runtime/wt_terrain_world.gd")
const StorageProfile := preload("res://addons/world_transvoxel_terrain/storage/wt_terrain_storage_profile.gd")
const EditOperation := preload("res://addons/world_transvoxel_terrain/edit/wt_terrain_edit_operation.gd")
const EditBatch := preload("res://addons/world_transvoxel_terrain/edit/wt_terrain_edit_batch.gd")

var committed_revisions: Array[int] = []
var edit_failures: Array[String] = []
var sample_results: Dictionary = {}
var sample_failures: Dictionary = {}


func _initialize() -> void:
	call_deferred("_run_test")


func _run_test() -> void:
	var terrain_world = TerrainWorld.new()
	terrain_world.storage_profile = _fixture_storage_profile()
	root.add_child(terrain_world)

	var journal_path := "res://build/production-lifecycle-fixture/world.wtedit"
	var journal_absolute := ProjectSettings.globalize_path(journal_path)
	if FileAccess.file_exists(journal_path):
		DirAccess.remove_absolute(journal_absolute)

	if not terrain_world.start_backend_world() or \
			not await _wait_for_state(terrain_world, "running"):
		_fail("terrain world did not start backend: %s" % terrain_world.get_last_error())
		return
	if terrain_world.get_backend_world_revision() != 12:
		_fail("fixture world base revision drifted")
		return

	var backend := terrain_world.get_backend_terrain()
	if backend == null:
		_fail("terrain world did not expose owned backend terrain")
		return
	backend.connect("edit_committed", _on_edit_committed)
	backend.connect("edit_failed", _on_edit_failed)
	backend.connect("authoritative_sample_ready", _on_sample_ready)
	backend.connect("authoritative_sample_failed", _on_sample_failed)

	if not terrain_world.submit_edit_batch(_make_edit_batch(), 303):
		_fail("terrain world edit submission failed: %s" % terrain_world.get_last_error())
		return
	var summary := terrain_world.get_last_edit_submission_summary()
	if int(summary.get("backend_command_count", 0)) != 1 or \
			not bool(summary.get("submitted", false)):
		_fail("terrain world edit summary mismatch: %s" % str(summary))
		return
	if not await _wait_for_commit(terrain_world, 13):
		_fail("terrain world edit did not commit revision 13")
		return
	if not FileAccess.file_exists(journal_path):
		_fail("terrain world did not produce native edit journal")
		return

	var edited_id: int = backend.call("request_authoritative_sample", Vector3i(12, 8, 8), 0)
	if edited_id <= 0 or not await _wait_for_sample(edited_id):
		_fail("edited sample query did not complete")
		return
	var edited: RefCounted = sample_results[edited_id]
	if edited.call("get_density") != -1.5 or \
			edited.call("get_material") != 3 or \
			edited.call("get_world_revision") != 13:
		_fail("edited sample mismatch before restart")
		return

	if not terrain_world.stop_backend_world() or \
			not await _wait_for_state(terrain_world, "stopped"):
		_fail("terrain world did not stop backend")
		return
	sample_results.clear()
	sample_failures.clear()
	if not terrain_world.start_backend_world() or \
			not await _wait_for_state(terrain_world, "running"):
		_fail("terrain world did not restart backend")
		return
	if terrain_world.get_backend_world_revision() != 13:
		_fail("terrain world restart did not replay journal")
		return

	var replayed_id: int = backend.call("request_authoritative_sample", Vector3i(12, 8, 8), 0)
	if replayed_id <= 0 or not await _wait_for_sample(replayed_id):
		_fail("replayed sample query did not complete")
		return
	var replayed: RefCounted = sample_results[replayed_id]
	if replayed.call("get_density") != -1.5 or \
			replayed.call("get_material") != 3 or \
			replayed.call("get_world_revision") != 13:
		_fail("journal replay sample mismatch")
		return
	if not terrain_world.stop_backend_world() or \
			not await _wait_for_state(terrain_world, "stopped"):
		_fail("terrain world did not stop after replay")
		return

	DirAccess.remove_absolute(journal_absolute)
	print(
		"%s lifecycle=start_stop_restart edit_commit=1 journal=replayed implementation=terrain_world_lifecycle"
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


func _make_edit_batch() -> Resource:
	var batch = EditBatch.new()
	var construct = EditOperation.new()
	construct.mode = EditOperation.Mode.CONSTRUCT
	construct.brush_shape = EditOperation.BrushShape.SPHERE
	construct.center = Vector3(12, 8, 8)
	construct.radius = 1.5
	construct.material_id = 3
	construct.density_value = 1.0
	batch.add_operation(construct)
	return batch


func _wait_for_state(terrain_world: Node, expected: String) -> bool:
	for _frame in range(900):
		if terrain_world.get_backend_world_state_name() == expected:
			await process_frame
			return true
		await process_frame
	return false


func _wait_for_commit(terrain_world: Node, revision: int) -> bool:
	for _frame in range(900):
		if committed_revisions.has(revision) and \
				terrain_world.get_backend_world_revision() == revision:
			return true
		if not edit_failures.is_empty():
			return false
		await process_frame
	return false


func _wait_for_sample(request_id: int) -> bool:
	for _frame in range(900):
		if sample_results.has(request_id):
			return true
		if sample_failures.has(request_id):
			return false
		await process_frame
	return false


func _on_edit_committed(world_revision: int) -> void:
	committed_revisions.push_back(world_revision)


func _on_edit_failed(error: String) -> void:
	edit_failures.push_back(error)


func _on_sample_ready(request_id: int, sample: RefCounted) -> void:
	sample_results[request_id] = sample


func _on_sample_failed(request_id: int, error: String) -> void:
	sample_failures[request_id] = error


func _fail(message: String) -> void:
	push_error("WT_TERRAIN_A4_PHASE3_GODOT_FAIL: " + message)
	quit(1)
