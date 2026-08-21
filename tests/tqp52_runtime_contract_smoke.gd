extends SceneTree

const MARKER := "WT_TERRAIN_TQP52_GODOT_PASS"
const RuntimeScene := preload("res://addons/world_transvoxel_terrain/runtime/wt_terrain_runtime_scene.tscn")
const TerrainWorld := preload("res://addons/world_transvoxel_terrain/runtime/wt_terrain_world.gd")
const RuntimeProfile := preload("res://addons/world_transvoxel_terrain/api/wt_terrain_runtime_profile.gd")
const StorageProfile := preload("res://addons/world_transvoxel_terrain/storage/wt_terrain_storage_profile.gd")
const EditOperation := preload("res://addons/world_transvoxel_terrain/edit/wt_terrain_edit_operation.gd")
const EditBatch := preload("res://addons/world_transvoxel_terrain/edit/wt_terrain_edit_batch.gd")

var completed_requests: Array[int] = []
var cancelled_requests: Array[int] = []
var committed_revisions: Array[int] = []
var sample_results: Dictionary = {}


func _initialize() -> void:
	call_deferred("_run_test")


func _run_test() -> void:
	if not _validate_builtin_profiles():
		return
	var runtime_scene = RuntimeScene.instantiate()
	root.add_child(runtime_scene)
	if not runtime_scene.call("ensure_runtime_defaults") or \
			runtime_scene.call("get_terrain_world") == null or \
			runtime_scene.find_child("DebugOverlay", true, false) != null:
		_fail("production runtime scene boundary is invalid")
		return
	runtime_scene.queue_free()
	await process_frame
	var world = TerrainWorld.new()
	var profile = RuntimeProfile.create_builtin(RuntimeProfile.Preset.REFERENCE)
	profile.maximum_async_requests = 1
	world.runtime_profile = profile
	world.storage_profile = _fixture_storage_profile()
	root.add_child(world)
	world.terrain_request_completed.connect(_on_request_completed)
	world.terrain_request_cancelled.connect(_on_request_cancelled)
	world.authoritative_sample_ready.connect(_on_sample_ready)
	world.edit_committed.connect(_on_edit_committed)

	_remove_fixture_journal()
	if not world.start_world() or not await _wait_for_state(world, "running"):
		_fail("world start failed: %s" % world.get_last_error())
		return
	if world.get_api_generation() != 1:
		_fail("start did not publish API generation 1")
		return
	var config: Resource = world.get_backend_terrain().call("get_configuration")
	if int(config.get("active_chunk_capacity")) != profile.active_chunk_capacity or \
			int(config.get("render_apply_budget")) != profile.render_apply_budget:
		_fail("runtime profile did not reach native configuration")
		return
	if not world.update_viewer(1, 1, Vector3(8, 8, 8), 1, 0):
		_fail("viewer update failed: %s" % world.get_last_error())
		return
	if world.update_viewer(1, 1, Vector3(9, 8, 8), 1, 0) or \
			"monotonic" not in world.get_last_error():
		_fail("stale viewer revision was not rejected")
		return
	if not world.update_collision_viewer(2, 1, Vector3(8, 8, 8), 1):
		_fail("collision viewer update failed: %s" % world.get_last_error())
		return

	var first_request := world.request_authoritative_sample(Vector3i(8, 8, 8), 0)
	var rejected_request := world.request_authoritative_sample(Vector3i(9, 8, 8), 0)
	if first_request <= 0 or rejected_request != 0 or \
			"capacity" not in world.get_last_error():
		_fail("bounded query back-pressure contract failed")
		return
	if not await _wait_for_sample(first_request):
		_fail("authoritative sample did not complete")
		return
	if not completed_requests.has(first_request):
		_fail("generation-aware completion signal missing")
		return

	var before_revision := world.get_world_revision()
	if not world.submit_edit_batch(_smooth_construct_batch(), 5200):
		_fail("smooth edit submission failed: %s" % world.get_last_error())
		return
	if not await _wait_for_commit(world, before_revision + 1):
		_fail("smooth edit did not commit")
		return
	var edit_summary := world.get_last_edit_submission_summary()
	if Array(edit_summary.get("operation_summaries", [])).is_empty():
		_fail("edit diagnostics omitted operation summaries")
		return

	var readiness := world.get_readiness_snapshot()
	if int(readiness.get("api_generation", 0)) != 1 or \
			not readiness.has("render") or not readiness.has("collision") or \
			not readiness.has("edit") or not readiness.has("query"):
		_fail("readiness snapshot is incomplete")
		return
	var chunk := world.get_chunk_readiness(Vector3i(0, 0, 0), 0)
	if not chunk.has("generation") or not chunk.has("render_state") or \
			not chunk.has("collision_state"):
		_fail("chunk readiness is not generation-aware")
		return

	var cancelled_id := world.request_authoritative_sample(Vector3i(10, 8, 8), 0)
	if cancelled_id <= 0 or not world.stop_world():
		_fail("stop/cancellation setup failed: %s" % world.get_last_error())
		return
	if world.get_api_generation() != 2 or not cancelled_requests.has(cancelled_id):
		_fail("world stop did not cancel the prior API generation")
		return
	if str(Dictionary(world.get_readiness_snapshot().get("query", {})).get("state", "")) != "unavailable":
		_fail("stopped query readiness did not fail closed")
		return

	_remove_fixture_journal()
	print("%s profiles=4 runtime_scene=production generation=2 backpressure=1 stale_viewer=1 smooth_edit=1 cancellation=1" % MARKER)
	world.queue_free()
	await process_frame
	quit(0)


func _validate_builtin_profiles() -> bool:
	for kind in RuntimeProfile.Preset.values():
		var profile = RuntimeProfile.create_builtin(kind)
		var summary: Dictionary = profile.get_contract_summary()
		if not profile.is_valid() or not summary.has("resolution") or \
				not summary.has("distance") or not summary.has("queues") or \
				not summary.has("memory") or not summary.has("collision") or \
				not summary.has("power"):
			_fail("runtime profile contract failed for preset %s" % str(kind))
			return false
	var storage = StorageProfile.new()
	storage.object_root_path = "user://worlds/tqp52-storage"
	if storage.is_valid() or "object-root journal path" not in storage.get_validation_error():
		_fail("custom native journal path was not rejected")
		return false
	storage.edit_journal_path = storage.get_effective_edit_journal_path()
	if not storage.is_valid():
		_fail("native object-root journal path was rejected")
		return false
	storage.persist_edits = false
	if storage.is_valid() or "always journals" not in storage.get_validation_error():
		_fail("disabled native edit persistence was not rejected")
		return false
	return true


func _fixture_storage_profile() -> Resource:
	var storage = StorageProfile.new()
	storage.world_manifest_path = "res://build/production-lifecycle-fixture/streaming.wtworld"
	storage.object_root_path = "res://build/production-lifecycle-fixture"
	storage.edit_journal_path = "res://build/production-lifecycle-fixture/world.wtedit"
	storage.snapshot_directory = "res://build/production-lifecycle-fixture/snapshots"
	storage.allow_res_paths_for_test_fixtures = true
	return storage


func _smooth_construct_batch() -> Resource:
	var operation = EditOperation.new()
	operation.mode = EditOperation.Mode.CONSTRUCT
	operation.center = Vector3(12, 8, 8)
	operation.radius = 1.25
	operation.smooth_radius = 0.25
	operation.material_id = 3
	var batch = EditBatch.new()
	batch.add_operation(operation)
	return batch


func _wait_for_state(world: Node, state: String) -> bool:
	for _frame in range(900):
		if world.get_world_state_name() == state:
			return true
		await process_frame
	return false


func _wait_for_sample(request_id: int) -> bool:
	for _frame in range(900):
		if sample_results.has(request_id):
			return true
		await process_frame
	return false


func _wait_for_commit(world: Node, revision: int) -> bool:
	for _frame in range(900):
		if committed_revisions.has(revision) and world.get_world_revision() == revision:
			return true
		await process_frame
	return false


func _on_request_completed(request_id: int, _kind: String, _generation: int, _revision: int) -> void:
	completed_requests.append(request_id)


func _on_request_cancelled(request_id: int, _kind: String, _generation: int, _reason: String) -> void:
	cancelled_requests.append(request_id)


func _on_sample_ready(request_id: int, sample: RefCounted) -> void:
	sample_results[request_id] = sample


func _on_edit_committed(revision: int) -> void:
	committed_revisions.append(revision)


func _remove_fixture_journal() -> void:
	var path := ProjectSettings.globalize_path("res://build/production-lifecycle-fixture/world.wtedit")
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(path)


func _fail(message: String) -> void:
	push_error("WT_TERRAIN_TQP52_GODOT_FAIL: " + message)
	quit(1)
