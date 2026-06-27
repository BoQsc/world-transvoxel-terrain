extends SceneTree

const MARKER := "WT_TERRAIN_A4_PHASE2_GODOT_PASS"
const EditOperation := preload("res://addons/world_transvoxel_terrain/edit/wt_terrain_edit_operation.gd")
const EditBatch := preload("res://addons/world_transvoxel_terrain/edit/wt_terrain_edit_batch.gd")
const EditBridge := preload("res://addons/world_transvoxel_terrain/runtime/wt_terrain_edit_bridge.gd")

var committed_revisions: Array[int] = []
var edit_failures: Array[String] = []
var sample_results: Dictionary = {}
var sample_failures: Dictionary = {}


func _initialize() -> void:
	call_deferred("_run_test")


func _run_test() -> void:
	if not ClassDB.class_exists("WorldTransvoxelTerrain") or \
			not ClassDB.class_exists("WorldTransvoxelConfig"):
		_fail("world-transvoxel backend classes are missing")
		return

	var config: Resource = ClassDB.instantiate("WorldTransvoxelConfig")
	var terrain: Node = ClassDB.instantiate("WorldTransvoxelTerrain")
	if config == null or terrain == null:
		_fail("world-transvoxel backend could not instantiate")
		return
	_configure_small_fixture(config)
	root.add_child(terrain)
	terrain.set("configuration", config)
	terrain.connect("edit_committed", _on_edit_committed)
	terrain.connect("edit_failed", _on_edit_failed)
	terrain.connect("authoritative_sample_ready", _on_sample_ready)
	terrain.connect("authoritative_sample_failed", _on_sample_failed)

	const fixture_root := "res://build/production-lifecycle-fixture"
	const world_path := fixture_root + "/streaming.wtworld"
	const journal_path := fixture_root + "/world.wtedit"
	var journal_absolute := ProjectSettings.globalize_path(journal_path)
	if FileAccess.file_exists(journal_path):
		DirAccess.remove_absolute(journal_absolute)

	if not terrain.call("start_world", world_path, fixture_root) or \
			not await _wait_for_state(terrain, "running"):
		_fail("phase 2 fixture world did not reach running: %s" % terrain.call("get_world_error"))
		return
	if terrain.call("get_world_revision") != 12:
		_fail("fixture world base revision drifted")
		return

	var batch := _make_standard_batch()
	var bridge := EditBridge.new()
	var transaction: Object = bridge.begin_batch_transaction(terrain, batch, 202)
	if transaction == null:
		_fail("bridge did not build native transaction: %s" % bridge.get_last_error())
		return
	if int(transaction.call("get_command_count")) != 8:
		_fail("native transaction command count mismatch: %s" % transaction.call("get_command_count"))
		return
	var summary := bridge.get_last_submission_summary()
	if int(summary.get("backend_command_count", 0)) != 8:
		_fail("bridge summary command count mismatch: %s" % str(summary))
		return
	if not terrain.call("commit_edit_transaction", transaction):
		_fail("native transaction commit failed: %s" % terrain.call("get_world_error"))
		return
	if not await _wait_for_commit(terrain, 13):
		_fail("native transaction did not commit revision 13")
		return
	if not FileAccess.file_exists(journal_path):
		_fail("native edit journal was not created")
		return
	var journal := FileAccess.open(journal_path, FileAccess.READ)
	if journal == null or journal.get_length() <= 0:
		_fail("native edit journal is empty")
		return
	journal.close()

	var edited_id: int = terrain.call("request_authoritative_sample", Vector3i(12, 8, 8), 0)
	if edited_id <= 0 or not await _wait_for_sample(edited_id):
		_fail("edited sample query did not complete")
		return
	var edited: RefCounted = sample_results[edited_id]
	if edited.call("get_density") != -1.0 or \
			edited.call("get_material") != 3 or \
			edited.call("get_world_revision") != 13:
		_fail("edited sample mismatch before restart")
		return

	if not terrain.call("stop_world") or not await _wait_for_state(terrain, "stopped"):
		_fail("phase 2 fixture world did not stop")
		return
	sample_results.clear()
	sample_failures.clear()
	if not terrain.call("start_world", world_path, fixture_root) or \
			not await _wait_for_state(terrain, "running"):
		_fail("phase 2 fixture world did not restart")
		return
	if terrain.call("get_world_revision") != 13:
		_fail("journal replay did not restore world revision 13")
		return
	var replayed_id: int = terrain.call("request_authoritative_sample", Vector3i(12, 8, 8), 0)
	if replayed_id <= 0 or not await _wait_for_sample(replayed_id):
		_fail("replayed sample query did not complete")
		return
	var replayed: RefCounted = sample_results[replayed_id]
	if replayed.call("get_density") != -1.0 or \
			replayed.call("get_material") != 3 or \
			replayed.call("get_world_revision") != 13:
		_fail("journal replay sample mismatch")
		return

	if not terrain.call("stop_world") or not await _wait_for_state(terrain, "stopped"):
		_fail("phase 2 fixture world did not stop after replay")
		return
	DirAccess.remove_absolute(journal_absolute)
	print(
		"%s operations=5 backend_commands=8 commit=1 journal=replayed implementation=bridge_storage_fixture"
		% MARKER
	)
	terrain.queue_free()
	await process_frame
	quit(0)


func _make_standard_batch() -> Resource:
	var batch = EditBatch.new()
	batch.add_operation(_make_operation(
		EditOperation.Mode.CARVE,
		EditOperation.BrushShape.BOX,
		Vector3(8, 8, 8),
		Vector3(1, 1, 1),
		1.0,
		0,
		10.0
	))
	batch.add_operation(_make_operation(
		EditOperation.Mode.CONSTRUCT,
		EditOperation.BrushShape.SPHERE,
		Vector3(12, 8, 8),
		Vector3.ONE,
		1.5,
		3,
		1.0
	))
	batch.add_operation(_make_operation(
		EditOperation.Mode.FILL,
		EditOperation.BrushShape.BOX,
		Vector3(14, 8, 8),
		Vector3(1, 1, 1),
		1.0,
		5,
		1.0
	))
	batch.add_operation(_make_operation(
		EditOperation.Mode.PAINT,
		EditOperation.BrushShape.SPHERE,
		Vector3(8, 8, 8),
		Vector3.ONE,
		1.0,
		4,
		1.0
	))
	batch.add_operation(_make_operation(
		EditOperation.Mode.RESTORE_TO_BASE,
		EditOperation.BrushShape.BOX,
		Vector3(8, 8, 8),
		Vector3(1, 1, 1),
		1.0,
		7,
		-0.25
	))
	return batch


func _make_operation(
	mode: int,
	shape: int,
	center: Vector3,
	box_extents: Vector3,
	radius: float,
	material_id: int,
	density_value: float
) -> Resource:
	var operation = EditOperation.new()
	operation.mode = mode
	operation.brush_shape = shape
	operation.center = center
	operation.box_extents = box_extents
	operation.radius = radius
	operation.material_id = material_id
	operation.density_value = density_value
	return operation


func _configure_small_fixture(config: Resource) -> void:
	config.set("active_chunk_capacity", 8)
	config.set("viewer_capacity", 2)
	config.set("demand_capacity_per_viewer", 125)
	config.set("storage_request_capacity", 16)
	config.set("storage_completion_capacity", 16)
	config.set("encoded_page_entry_capacity", 8)
	config.set("decoded_page_entry_capacity", 8)
	config.set("mesh_entry_capacity", 8)
	config.set("render_entry_capacity", 8)
	config.set("collision_entry_capacity", 8)


func _wait_for_state(terrain: Node, expected: String) -> bool:
	for _frame in range(900):
		if terrain.call("get_world_state_name") == expected:
			await process_frame
			return true
		await process_frame
	return false


func _wait_for_commit(terrain: Node, revision: int) -> bool:
	for _frame in range(900):
		if committed_revisions.has(revision) and terrain.call("get_world_revision") == revision:
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
	push_error("WT_TERRAIN_A4_PHASE2_GODOT_FAIL: " + message)
	quit(1)
