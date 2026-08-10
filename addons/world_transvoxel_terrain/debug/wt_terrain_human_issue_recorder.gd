@tool
extends Node
class_name WtTerrainHumanIssueRecorder

signal status_changed(message: String)

const SAMPLE_INTERVAL := 0.1
const MAXIMUM_SECONDS := 30.0

var _host: Node
var _recording := false
var _playback := false
var _started_usec := 0
var _sample_accumulator := 0.0
var _samples: Array[Dictionary] = []
var _mark_count := 0
var _issue_root := ""
var _last_issue_root := ""


func _ready() -> void:
	set_process(false)


func configure(host: Node) -> void:
	_host = host


func _process(delta: float) -> void:
	if not _recording or _host == null:
		return
	_sample_accumulator += delta
	if _sample_accumulator >= SAMPLE_INTERVAL:
		_sample_accumulator = 0.0
		_samples.append(_host.call("capture_human_issue_sample"))
	if float(Time.get_ticks_usec() - _started_usec) / 1000000.0 >= MAXIMUM_SECONDS:
		stop()


func is_recording() -> bool:
	return _recording


func is_playing() -> bool:
	return _playback


func get_mark_count() -> int:
	return _mark_count


func toggle() -> void:
	if _recording:
		stop()
	else:
		start()


func start() -> void:
	if _host == null or _playback:
		return
	_issue_root = "user://world_transvoxel_terrain/human_issues/issue_%d" % \
			int(Time.get_unix_time_from_system() * 1000.0)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(_issue_root))
	_last_issue_root = _issue_root
	_samples.clear()
	_mark_count = 0
	_started_usec = Time.get_ticks_usec()
	_sample_accumulator = 0.0
	_recording = true
	set_process(true)
	_samples.append(_host.call("capture_human_issue_sample"))
	_save_screenshot("start")
	status_changed.emit("ISSUE RECORDING")


func stop() -> void:
	if not _recording or _host == null:
		return
	_recording = false
	set_process(false)
	_samples.append(_host.call("capture_human_issue_sample"))
	_save_screenshot("stop")
	_write_json(_issue_root.path_join("recording.json"), {
		"schema": "world_transvoxel_terrain.human_issue_recording.v1",
		"authority": "world-transvoxel",
		"fallback": false,
		"sample_interval_seconds": SAMPLE_INTERVAL,
		"mark_count": _mark_count,
		"samples": _samples,
		"final_validation": _host.call("get_validation_snapshot"),
	})
	status_changed.emit("ISSUE SAVED: %s" % _issue_root)
	print("WT_TERRAIN_HUMAN_ISSUE_SAVED path=%s" % ProjectSettings.globalize_path(_issue_root))


func mark() -> void:
	if _host == null:
		return
	if not _recording:
		start()
	_mark_count += 1
	var id := "mark_%02d" % _mark_count
	_save_screenshot(id)
	_write_json(_issue_root.path_join(id + ".json"), {
		"schema": "world_transvoxel_terrain.human_issue_mark.v1",
		"id": id,
		"sample": _host.call("capture_human_issue_sample"),
		"validation": _host.call("get_validation_snapshot"),
	})
	status_changed.emit("MARKED %s" % id.to_upper())


func replay() -> void:
	if _host == null or _recording or _playback or _last_issue_root.is_empty():
		status_changed.emit("NO STOPPED ISSUE RECORDING TO REPLAY")
		return
	var file := FileAccess.open(_last_issue_root.path_join("recording.json"), FileAccess.READ)
	if file == null:
		status_changed.emit("ISSUE RECORDING COULD NOT BE READ")
		return
	var payload = JSON.parse_string(file.get_as_text())
	if not payload is Dictionary:
		status_changed.emit("ISSUE RECORDING IS INVALID")
		return
	var samples := (payload as Dictionary).get("samples", []) as Array
	if samples.is_empty():
		status_changed.emit("ISSUE RECORDING HAS NO CAMERA SAMPLES")
		return
	_playback = true
	status_changed.emit("ISSUE PLAYBACK")
	for index in range(samples.size()):
		var sample := samples[index] as Dictionary
		_host.call("apply_human_issue_camera_sample", sample)
		if index + 1 < samples.size():
			var next_sample := samples[index + 1] as Dictionary
			var delay := clampf(
				float(int(next_sample.get("elapsed_usec", 0)) - int(sample.get("elapsed_usec", 0))) /
						1000000.0,
				0.0,
				0.25
			)
			await get_tree().create_timer(delay).timeout
	_playback = false
	status_changed.emit("ISSUE PLAYBACK COMPLETE")


func shutdown() -> void:
	if _recording:
		stop()


func elapsed_usec() -> int:
	return Time.get_ticks_usec() - _started_usec if _started_usec > 0 else 0


func record_edit_timing(timing: Dictionary) -> void:
	var root := "user://world_transvoxel_terrain/human_performance"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(root))
	var path := root.path_join("edit_timings.jsonl")
	var file := FileAccess.open(
		path,
		FileAccess.READ_WRITE if FileAccess.file_exists(path) else FileAccess.WRITE
	)
	if file == null:
		return
	file.seek_end()
	var record := timing.duplicate(true)
	record["recorded_unix_msec"] = int(Time.get_unix_time_from_system() * 1000.0)
	file.store_line(JSON.stringify(record))


func _save_screenshot(id: String) -> void:
	var image := get_viewport().get_texture().get_image()
	image.save_png(ProjectSettings.globalize_path(_issue_root.path_join(id + ".png")))


func _write_json(path: String, payload: Dictionary) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify(payload, "\t") + "\n")
