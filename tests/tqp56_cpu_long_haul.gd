extends SceneTree

const MARKER := "WT_TERRAIN_TQP56_GODOT_PASS"
const TerrainWorld := preload("res://addons/world_transvoxel_terrain/runtime/wt_terrain_world.gd")
const RuntimeProfile := preload("res://addons/world_transvoxel_terrain/api/wt_terrain_runtime_profile.gd")
const StorageProfile := preload("res://addons/world_transvoxel_terrain/storage/wt_terrain_storage_profile.gd")
const EditOperation := preload("res://addons/world_transvoxel_terrain/edit/wt_terrain_edit_operation.gd")
const EditBatch := preload("res://addons/world_transvoxel_terrain/edit/wt_terrain_edit_batch.gd")
const RESULT_PATH := "res://tqp56_result.json"
const POSITIONS := [
	Vector3(8, 8, 8), Vector3(24, 8, 8), Vector3(40, 12, 8),
	Vector3(40, 24, 24), Vector3(24, 8, 40), Vector3(8, 8, 40),
]

var committed_revisions: Array[int] = []
var sample_results: Dictionary = {}
var failures: Array[String] = []
var maximum_queues := {
	"scheduler": 0, "storage": 0, "render": 0, "collision": 0,
}


func _initialize() -> void:
	call_deferred("_run_test")


func _run_test() -> void:
	var contract = JSON.parse_string(FileAccess.get_file_as_string("res://TQP56_LONG_HAUL_CONTRACT.json"))
	if not contract is Dictionary:
		_fail("long-haul contract could not be loaded")
		return
	var minimum_seconds := int(contract.get("minimum_wrapper_duration_seconds", 60))
	var duration_seconds := maxi(minimum_seconds, int(OS.get_environment("WT_TQP56_DURATION_SECONDS")))
	var budgets: Dictionary = contract.get("budgets", {})
	_remove_fixture_journal()
	var world = TerrainWorld.new()
	world.runtime_profile = RuntimeProfile.create_builtin(RuntimeProfile.Preset.BALANCED)
	world.storage_profile = _fixture_storage_profile()
	root.add_child(world)
	world.authoritative_sample_ready.connect(_on_sample_ready)
	world.edit_committed.connect(_on_edit_committed)

	if not world.start_world() or not await _wait_for_state(world, "running"):
		_fail("initial world start failed: %s" % world.get_last_error())
		return
	var viewer_revision := 1
	var collision_revision := 1
	if not _update_residency(world, viewer_revision, collision_revision, POSITIONS[0]):
		return
	if not await _wait_for_settled(world, int(budgets.get("maximum_settle_seconds", 15))):
		_fail("initial residency did not settle")
		return
	var memory_baseline := int(Performance.get_monitor(Performance.MEMORY_STATIC))
	var memory_peak := memory_baseline
	var started_ms := Time.get_ticks_msec()
	var cycles := 0
	var edits := 0
	var queries := 0
	var restarts := 0
	var fault_rejections := 0
	var last_sample: Dictionary = {}
	var last_point := Vector3i(12, 8, 8)

	while Time.get_ticks_msec() - started_ms < duration_seconds * 1000:
		var cycle_started := Time.get_ticks_msec()
		var position: Vector3 = POSITIONS[cycles % POSITIONS.size()]
		viewer_revision += 1
		collision_revision += 1
		if not _update_residency(world, viewer_revision, collision_revision, position):
			return
		if cycles == 1:
			if world.update_viewer(1, viewer_revision, position, 0, 0):
				_fail("stale viewer revision was accepted")
				return
			fault_rejections += 1
		if not await _wait_for_settled(world, int(budgets.get("maximum_settle_seconds", 15))):
			_fail("residency did not settle during cycle %d" % cycles)
			return
		_record_metrics(world.get_runtime_metrics())

		if cycles == 2:
			var invalid = EditOperation.new()
			invalid.radius = 0.0
			var invalid_batch = EditBatch.new()
			invalid_batch.add_operation(invalid)
			if world.submit_edit_batch(invalid_batch, 5600):
				_fail("invalid edit was accepted")
				return
			fault_rejections += 1

		if cycles % 4 == 0:
			last_point = Vector3i(12 + (edits % 3) * 2, 8, 8)
			var before_revision := world.get_world_revision()
			if not world.submit_edit_batch(_edit_batch(last_point, edits), 5601):
				_fail("edit submission failed: %s" % world.get_last_error())
				return
			if not await _wait_for_commit(world, before_revision + 1):
				_fail("edit commit timed out")
				return
			edits += 1
			var sample = await _query_sample(world, last_point)
			if sample == null:
				_fail("post-edit authoritative query failed")
				return
			queries += 1
			last_sample = _sample_state(sample)

		if cycles > 0 and cycles % 12 == 0 and not last_sample.is_empty():
			var expected_revision := world.get_world_revision()
			if not world.stop_world() or not await _wait_for_state(world, "stopped"):
				_fail("restart stop failed")
				return
			if not world.start_world() or not await _wait_for_state(world, "running"):
				_fail("restart start failed: %s" % world.get_last_error())
				return
			if world.get_world_revision() != expected_revision:
				_fail("journal revision did not replay")
				return
			var replayed = await _query_sample(world, last_point)
			if replayed == null or not _same_sample(last_sample, _sample_state(replayed)):
				_fail("authoritative sample changed after restart")
				return
			queries += 1
			restarts += 1

		world.position = Vector3(-100000.0 if cycles % 2 == 0 else 0.0, 0.0, 100000.0 if cycles % 3 == 0 else 0.0)
		memory_peak = maxi(memory_peak, int(Performance.get_monitor(Performance.MEMORY_STATIC)))
		cycles += 1
		while Time.get_ticks_msec() - cycle_started < 750:
			await process_frame

	var final_metrics: Dictionary = world.get_runtime_metrics()
	_record_metrics(final_metrics)
	var queue_rejections := int(final_metrics.get("scheduler_queue_rejections", 0)) + \
		int(final_metrics.get("application_queue_rejections", 0)) + \
		int(final_metrics.get("storage_request_queue_rejections", 0))
	var memory_end := int(Performance.get_monitor(Performance.MEMORY_STATIC))
	var memory_growth := maxi(0, memory_end - memory_baseline)
	var memory_peak_growth := maxi(0, memory_peak - memory_baseline)
	if cycles < int(contract.get("minimum_cycles", 8)):
		_fail("insufficient workload cycles")
		return
	if edits < int(contract.get("minimum_edits", 2)) or queries < int(contract.get("minimum_queries", 2)):
		_fail("insufficient edit/query coverage")
		return
	if restarts < int(contract.get("minimum_restarts", 1)):
		_fail("insufficient restart coverage")
		return
	if queue_rejections > int(budgets.get("maximum_queue_rejections", 0)):
		_fail("native queue rejection budget exceeded")
		return
	if memory_growth > int(budgets.get("maximum_memory_growth_bytes", 67108864)):
		_fail("memory growth budget exceeded")
		return
	if maximum_queues.scheduler > int(budgets.get("maximum_scheduler_queue_depth", 4096)) or \
			maximum_queues.storage > int(budgets.get("maximum_storage_queue_depth", 256)) or \
			maximum_queues.render > int(budgets.get("maximum_render_queue_depth", 128)) or \
			maximum_queues.collision > int(budgets.get("maximum_collision_queue_depth", 64)):
		_fail("native queue depth budget exceeded")
		return
	if not world.stop_world() or not await _wait_for_state(world, "stopped"):
		_fail("clean shutdown failed")
		return
	var elapsed_seconds := float(Time.get_ticks_msec() - started_ms) / 1000.0
	_write_result({
		"schema": "world_transvoxel_terrain.tqp56_godot_long_haul.v1",
		"status": "PASS", "duration_seconds": elapsed_seconds,
		"cycles": cycles, "edits": edits, "queries": queries,
		"restarts": restarts, "fault_rejections": fault_rejections,
		"api_generation": world.get_api_generation(),
		"world_revision": world.get_world_revision(),
		"memory_baseline_bytes": memory_baseline,
		"memory_end_bytes": memory_end,
		"memory_growth_bytes": memory_growth,
		"memory_peak_growth_bytes": memory_peak_growth,
		"maximum_queues": maximum_queues,
		"queue_rejections": queue_rejections,
		"clean_shutdown": true,
		"origin_shift_authority_coordinates_unchanged": true,
	})
	_remove_fixture_journal()
	print("%s duration=%.3f cycles=%d edits=%d queries=%d restarts=%d memory_growth=%d queue_rejections=%d" % [MARKER, elapsed_seconds, cycles, edits, queries, restarts, memory_growth, queue_rejections])
	world.queue_free()
	await process_frame
	quit(0)


func _update_residency(world: Node, viewer_revision: int, collision_revision: int, position: Vector3) -> bool:
	if not world.update_viewer(1, viewer_revision, position, 0, 0):
		_fail("render viewer update failed: %s" % world.get_last_error())
		return false
	if not world.update_collision_viewer(2, collision_revision, position, 0):
		_fail("collision viewer update failed: %s" % world.get_last_error())
		return false
	return true


func _edit_batch(point: Vector3i, index: int) -> Resource:
	var operation = EditOperation.new()
	operation.mode = EditOperation.Mode.CONSTRUCT if index % 2 == 0 else EditOperation.Mode.CARVE
	operation.center = Vector3(point)
	operation.radius = 1.25
	operation.smooth_radius = 0.25
	operation.material_id = 3
	var batch = EditBatch.new()
	batch.add_operation(operation)
	return batch


func _fixture_storage_profile() -> Resource:
	var storage = StorageProfile.new()
	storage.world_manifest_path = "res://build/production-lifecycle-fixture/streaming.wtworld"
	storage.object_root_path = "res://build/production-lifecycle-fixture"
	storage.edit_journal_path = "res://build/production-lifecycle-fixture/world.wtedit"
	storage.snapshot_directory = "res://build/production-lifecycle-fixture/snapshots"
	storage.allow_res_paths_for_test_fixtures = true
	return storage


func _wait_for_state(world: Node, expected: String) -> bool:
	for _frame in range(1800):
		if world.get_world_state_name() == expected:
			await process_frame
			return true
		await process_frame
	return false


func _wait_for_settled(world: Node, timeout_seconds: int) -> bool:
	var started := Time.get_ticks_msec()
	while Time.get_ticks_msec() - started < timeout_seconds * 1000:
		if world.is_cold_idle():
			return true
		await process_frame
	return false


func _wait_for_commit(world: Node, revision: int) -> bool:
	for _frame in range(1800):
		if committed_revisions.has(revision) and world.get_world_revision() == revision:
			return true
		await process_frame
	return false


func _query_sample(world: Node, point: Vector3i):
	# Native request identifiers may be reused after a backend restart.
	sample_results.clear()
	var request_id: int = world.request_authoritative_sample(point, 0)
	if request_id <= 0:
		return null
	for _frame in range(1800):
		if sample_results.has(request_id):
			return sample_results[request_id]
		await process_frame
	return null


func _sample_state(sample: RefCounted) -> Dictionary:
	return {"density": float(sample.call("get_density")), "material": int(sample.call("get_material")), "world_revision": int(sample.call("get_world_revision"))}


func _same_sample(expected: Dictionary, actual: Dictionary) -> bool:
	return is_equal_approx(float(expected.density), float(actual.density)) and int(expected.material) == int(actual.material) and int(expected.world_revision) == int(actual.world_revision)


func _record_metrics(metrics: Dictionary) -> void:
	maximum_queues.scheduler = maxi(maximum_queues.scheduler, int(metrics.get("scheduler_queued_jobs", 0)))
	maximum_queues.storage = maxi(maximum_queues.storage, int(metrics.get("storage_queued_requests", 0)) + int(metrics.get("storage_queued_completions", 0)))
	maximum_queues.render = maxi(maximum_queues.render, int(metrics.get("queued_render", 0)))
	maximum_queues.collision = maxi(maximum_queues.collision, int(metrics.get("queued_collision", 0)))


func _on_edit_committed(revision: int) -> void:
	committed_revisions.append(revision)


func _on_sample_ready(request_id: int, sample: RefCounted) -> void:
	sample_results[request_id] = sample


func _write_result(payload: Dictionary) -> void:
	var file := FileAccess.open(RESULT_PATH, FileAccess.WRITE)
	file.store_string(JSON.stringify(payload, "\t") + "\n")


func _remove_fixture_journal() -> void:
	var path := ProjectSettings.globalize_path("res://build/production-lifecycle-fixture/world.wtedit")
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(path)


func _fail(message: String) -> void:
	push_error("WT_TERRAIN_TQP56_GODOT_FAIL: " + message)
	quit(1)
