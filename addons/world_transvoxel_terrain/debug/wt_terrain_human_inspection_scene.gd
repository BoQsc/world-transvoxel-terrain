@tool
extends "res://addons/world_transvoxel_terrain/debug/wt_terrain_large_acceptance_scene.gd"
class_name WtTerrainHumanInspectionScene

const HUMAN_SURFACE_STREAMING_CEILING := 40.0
const HUMAN_LOOK_AHEAD_DISTANCE := 32.0
const HUMAN_VISUAL_UPDATE_DISTANCE := 16.0
const HUMAN_COLLISION_UPDATE_DISTANCE := 4.0
const HUMAN_VISUAL_RADIUS_CHUNKS := 1
const HUMAN_COLLISION_RADIUS_CHUNKS := 2
const HUMAN_EDIT_TIMEOUT_FRAMES := 1800
const HUMAN_MAXIMUM_FPS := 60
const HUMAN_ACTIVE_CHUNK_CAPACITY := 384
const HUMAN_CACHE_ENTRY_CAPACITY := 768
@onready var edit_target_marker: MeshInstance3D = %EditTargetMarker
@onready var human_player: CharacterBody3D = %HumanPlayer
@onready var human_player_shape: CollisionShape3D = %HumanPlayerShape
@onready var human_status_label: Label = %HumanStatusLabel
@onready var performance_label: Label = %PerformanceLabel
@onready var fly_button: Button = %FlyButton
@onready var walk_button: Button = %WalkButton
@onready var apply_button: Button = %ApplyButton
@onready var issue_recorder: Node = %IssueRecorder

var _human_brush_kind: StringName = &"carve"
var _human_target := Vector3.ZERO
var _human_target_normal := Vector3.UP
var _human_target_valid := false
var _human_edit_busy := false
var _human_message := "LOCAL COLLISION PENDING"
var _human_walk_mode := false
var _auto_start_walk_pending := true
var _human_target_accumulator := 0.0
var _human_overlay_accumulator := 0.0
var _human_message_hold_until_usec := 0
var _human_edit_sequence := 0
var _last_edit_timing: Dictionary = {}
var _published_human_collision_position := Vector3(INF, INF, INF)
var _brush_group: ButtonGroup
var _movement_group: ButtonGroup
var _previous_maximum_fps := 0


func _configure_profiles() -> void:
	super._configure_profiles()
	var runtime = terrain_world.get("runtime_profile")
	runtime.profile_id = &"human_inspection_bounded_cpu"
	runtime.viewer_radius_chunks = HUMAN_VISUAL_RADIUS_CHUNKS
	runtime.global_coarse_lod_coverage = false
	runtime.active_chunk_capacity = HUMAN_ACTIVE_CHUNK_CAPACITY
	runtime.maximum_async_requests = 16
	runtime.demand_capacity_per_viewer = 2048
	runtime.procedural_generation_worker_count = 1
	runtime.meshing_worker_count = 1
	runtime.storage_request_capacity = 2048
	runtime.storage_completion_capacity = 2048
	runtime.encoded_page_entry_capacity = HUMAN_CACHE_ENTRY_CAPACITY
	runtime.decoded_page_entry_capacity = HUMAN_CACHE_ENTRY_CAPACITY
	runtime.mesh_entry_capacity = HUMAN_ACTIVE_CHUNK_CAPACITY
	runtime.render_entry_capacity = HUMAN_ACTIVE_CHUNK_CAPACITY
	runtime.collision_entry_capacity = 128
	runtime.render_apply_budget = 4
	runtime.collision_apply_budget = 2
	runtime.power_intent = &"bounded_human_inspection"


func get_acceptance_profile() -> Dictionary:
	var profile := super.get_acceptance_profile()
	profile["schema"] = "world_transvoxel_terrain.human_inspection_profile.v1"
	profile["active_chunk_capacity"] = HUMAN_ACTIVE_CHUNK_CAPACITY
	profile["viewer_radius_chunks"] = HUMAN_VISUAL_RADIUS_CHUNKS
	profile["encoded_page_cache_entries"] = HUMAN_CACHE_ENTRY_CAPACITY
	profile["decoded_page_cache_entries"] = HUMAN_CACHE_ENTRY_CAPACITY
	profile["global_coarse_lod_coverage"] = false
	profile["global_coarse_root_count"] = 0
	profile["full_world_lod0_coverage"] = 0
	profile["cpu_profile"] = "bounded_human_inspection"
	profile["procedural_generation_worker_count"] = 1
	profile["meshing_worker_count"] = 1
	return profile


func get_global_coverage_bootstrap_summary() -> Dictionary:
	var summary := super.get_global_coverage_bootstrap_summary()
	summary["implementation"] = "bounded_local_coarse_then_refinement_v1"
	summary["global_coarse_lod_coverage"] = false
	summary["expected_coarse_roots"] = 0
	summary["expected_lod0_coverage"] = 0
	return summary


func _request_viewer(
	position: Vector3,
	force: bool,
	radius_chunks: int = HUMAN_VISUAL_RADIUS_CHUNKS,
	maximum_lod: int = MAXIMUM_LOD,
	collision_radius_chunks: int = HUMAN_COLLISION_RADIUS_CHUNKS
) -> bool:
	return super._request_viewer(
		position, force, radius_chunks, maximum_lod, collision_radius_chunks
	)


func _advance_global_coarse_bootstrap() -> void:
	if not _coarse_bootstrap_requested or _refinement_requested or not _runtime_is_settled():
		return
	if not _coarse_stage_ready:
		_coarse_ready_latency_usec = Time.get_ticks_usec() - _bootstrap_started_usec
		_coarse_stage_ready = true
	if _hold_after_coarse:
		return
	_refinement_request_viewer_updates = int(_last_metrics.get("viewer_updates", 0))
	_refinement_requested = true
	if not _request_viewer(
		_viewer_position, true, HUMAN_VISUAL_RADIUS_CHUNKS, MAXIMUM_LOD
	):
		_fail_preview("bounded local refinement request rejected")


func _ready() -> void:
	_previous_maximum_fps = Engine.max_fps
	if not Engine.is_editor_hint() and (Engine.max_fps == 0 or Engine.max_fps > HUMAN_MAXIMUM_FPS):
		Engine.max_fps = HUMAN_MAXIMUM_FPS
	_viewer_position = TELEPORTS[0]
	super._ready()
	get_node("Interface/Dock/Content/Title").text = "Terrain Human Inspection"
	get_node("Interface/Dock/Content/Subtitle").text = "bounded authority-backed inspection"
	get_node("Interface/Dock/Content").add_theme_constant_override("separation", 4)
	profile_label.visible = false
	track_toggle.visible = false
	get_node("Interface/Dock/Content/Scope").visible = false
	get_node("Interface/SceneBadge").visible = false
	viewer_marker.visible = false
	human_player_shape.disabled = true
	human_player.collision_layer = 0
	human_player.collision_mask = 0
	issue_recorder.call("configure", self)
	issue_recorder.connect("status_changed", _on_issue_status_changed)
	_refresh_human_overlay()
	if not Engine.is_editor_hint():
		call_deferred("_activate_human_gameplay")


func _exit_tree() -> void:
	issue_recorder.call("shutdown")
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	if not Engine.is_editor_hint():
		Engine.max_fps = _previous_maximum_fps
	super._exit_tree()


func _stop_preview(cleanup: bool) -> Dictionary:
	var result := await super._stop_preview(cleanup)
	_published_human_collision_position = Vector3(INF, INF, INF)
	return result


func _process(delta: float) -> void:
	super._process(delta)
	if Engine.is_editor_hint():
		return
	_human_target_accumulator += delta
	_human_overlay_accumulator += delta
	if _human_target_accumulator >= 0.05:
		_human_target_accumulator = 0.0
		_update_human_target()
		if _auto_start_walk_pending and _human_target_valid:
			_set_walk_mode(true)
	if _human_overlay_accumulator >= 0.2:
		_human_overlay_accumulator = 0.0
		_refresh_human_overlay()


func _configure_edit_controls() -> void:
	_brush_group = ButtonGroup.new()
	_brush_group.allow_unpress = false
	%CarveButton.toggle_mode = true
	%CarveButton.button_group = _brush_group
	%CarveButton.button_pressed = true
	%ConstructButton.toggle_mode = true
	%ConstructButton.button_group = _brush_group
	%CarveButton.pressed.connect(_select_human_brush.bind(&"carve"))
	%ConstructButton.pressed.connect(_select_human_brush.bind(&"construct"))
	_movement_group = ButtonGroup.new()
	_movement_group.allow_unpress = false
	fly_button.button_group = _movement_group
	fly_button.button_pressed = true
	walk_button.button_group = _movement_group
	fly_button.pressed.connect(_set_walk_mode.bind(false))
	walk_button.pressed.connect(_set_walk_mode.bind(true))
	apply_button.pressed.connect(_submit_human_target_edit)


func _focus_camera(target: Vector3) -> void:
	camera.position = target + Vector3(-36.0, 24.0, -48.0)
	camera.look_at(target + Vector3(0.0, -8.0, 0.0), Vector3.UP)
	_camera_pitch = camera.rotation.x
	_camera_yaw = camera.rotation.y


func _update_runtime_camera(delta: float) -> void:
	if not bool(issue_recorder.call("is_playing")):
		if _human_walk_mode:
			_update_walk_player(delta)
		else:
			_update_fly_camera(delta)
	if not _runtime_follow_camera:
		return
	if not _refinement_requested:
		return
	var focus := human_player.global_position if _human_walk_mode else _fly_streaming_focus()
	var tracked := _clamp_viewer_position(focus)
	_publish_human_streaming_focus(tracked)


func _publish_human_streaming_focus(position: Vector3) -> void:
	if position.distance_to(_published_viewer_position) >= HUMAN_VISUAL_UPDATE_DISTANCE:
		_viewer_revision += 1
		if bool(terrain_world.call(
			"update_viewer", VIEWER_ID, _viewer_revision, position,
			HUMAN_VISUAL_RADIUS_CHUNKS, MAXIMUM_LOD
		)):
			_viewer_position = position
			_published_viewer_position = position
			viewer_marker.position = position
		else:
			status_label.text = "FAIL: visual viewer update"
	if position.distance_to(_published_human_collision_position) >= \
			HUMAN_COLLISION_UPDATE_DISTANCE:
		_collision_revision += 1
		if bool(terrain_world.call(
			"update_collision_viewer", COLLISION_VIEWER_ID, _collision_revision,
			position, HUMAN_COLLISION_RADIUS_CHUNKS
		)):
			_published_human_collision_position = position
		else:
			status_label.text = "FAIL: collision viewer update"


func _update_fly_camera(delta: float) -> void:
	var direction := Vector3.ZERO
	if Input.is_key_pressed(KEY_W): direction -= camera.global_basis.z
	if Input.is_key_pressed(KEY_S): direction += camera.global_basis.z
	if Input.is_key_pressed(KEY_A): direction -= camera.global_basis.x
	if Input.is_key_pressed(KEY_D): direction += camera.global_basis.x
	if Input.is_key_pressed(KEY_C) or Input.is_key_pressed(KEY_CTRL):
		direction -= Vector3.UP
	if Input.is_key_pressed(KEY_SPACE):
		direction += Vector3.UP
	if direction.length_squared() > 0.0:
		var speed := 180.0 if Input.is_key_pressed(KEY_SHIFT) else 54.0
		camera.global_position += direction.normalized() * speed * delta


func _update_walk_player(delta: float) -> void:
	var forward := -camera.global_basis.z
	forward.y = 0.0
	forward = forward.normalized() if forward.length_squared() > 0.0 else Vector3.FORWARD
	var right := camera.global_basis.x
	right.y = 0.0
	right = right.normalized() if right.length_squared() > 0.0 else Vector3.RIGHT
	var direction := Vector3.ZERO
	if Input.is_key_pressed(KEY_W): direction += forward
	if Input.is_key_pressed(KEY_S): direction -= forward
	if Input.is_key_pressed(KEY_A): direction -= right
	if Input.is_key_pressed(KEY_D): direction += right
	var speed := 14.0 if Input.is_key_pressed(KEY_SHIFT) else 7.0
	if direction.length_squared() > 0.0:
		direction = direction.normalized()
	human_player.velocity.x = direction.x * speed
	human_player.velocity.z = direction.z * speed
	if human_player.is_on_floor():
		if Input.is_key_pressed(KEY_SPACE):
			human_player.velocity.y = 9.0
		else:
			human_player.velocity.y = -0.5
	else:
		human_player.velocity.y -= 28.0 * delta
	human_player.move_and_slide()
	camera.global_position = human_player.global_position + Vector3.UP * 1.45


func _fly_streaming_focus() -> Vector3:
	var forward := -camera.global_basis.z
	forward.y = 0.0
	if forward.length_squared() > 0.0:
		forward = forward.normalized()
	var focus := camera.global_position + forward * HUMAN_LOOK_AHEAD_DISTANCE
	focus.y = minf(focus.y, HUMAN_SURFACE_STREAMING_CEILING)
	return focus


func _unhandled_input(event: InputEvent) -> void:
	if Engine.is_editor_hint():
		return
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_ESCAPE:
				_set_mouse_look(false)
			KEY_1:
				_select_human_brush(&"carve")
			KEY_2:
				_select_human_brush(&"construct")
			KEY_ENTER, KEY_KP_ENTER:
				_submit_human_target_edit()
			KEY_F:
				_set_walk_mode(not _human_walk_mode)
			KEY_F8:
				issue_recorder.call("toggle")
			KEY_F9:
				issue_recorder.call("mark")
			KEY_F10:
				issue_recorder.call("replay")
			_:
				return
		get_viewport().set_input_as_handled()
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_RIGHT and event.pressed:
		_set_mouse_look(not _looking)
		get_viewport().set_input_as_handled()
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and \
			event.pressed and _looking:
		_submit_human_target_edit()
		get_viewport().set_input_as_handled()
	elif event is InputEventMouseMotion and _looking:
		_camera_yaw -= event.relative.x * 0.0035
		_camera_pitch = clampf(_camera_pitch - event.relative.y * 0.0035, -1.48, 1.48)
		camera.rotation = Vector3(_camera_pitch, _camera_yaw, 0.0)
		get_viewport().set_input_as_handled()


func _set_mouse_look(enabled: bool) -> void:
	_looking = enabled
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED if enabled else Input.MOUSE_MODE_VISIBLE


func _activate_human_gameplay() -> void:
	if DisplayServer.get_name() != "headless":
		DisplayServer.window_move_to_foreground()
	_set_mouse_look(true)


func _select_human_brush(kind: StringName) -> void:
	_human_brush_kind = kind
	%CarveButton.button_pressed = kind == &"carve"
	%ConstructButton.button_pressed = kind == &"construct"
	_human_message = "AIM AT READY LOCAL COLLISION"
	_refresh_human_overlay()


func _set_walk_mode(enabled: bool) -> void:
	if enabled and not _human_target_valid:
		_human_message = "WALK NEEDS A READY TERRAIN TARGET"
		fly_button.button_pressed = true
		return
	if enabled and _human_target_normal.y < 0.6:
		_human_message = "WALK NEEDS AN UPWARD-FACING SURFACE"
		fly_button.button_pressed = true
		return
	_auto_start_walk_pending = false
	_human_walk_mode = enabled
	edit_target_marker.scale = Vector3.ONE * (0.2 if enabled else 1.0)
	human_player_shape.disabled = not enabled
	human_player.collision_layer = 1 if enabled else 0
	human_player.collision_mask = 1 if enabled else 0
	if enabled:
		human_player.global_position = _human_target + Vector3.UP * 1.25
		human_player.velocity = Vector3.ZERO
		camera.global_position = human_player.global_position + Vector3.UP * 1.45
		_human_message = "WALK COLLISION ACTIVE"
	else:
		_human_message = "FREE FLIGHT ACTIVE"
	_refresh_human_overlay()


func _update_human_target() -> void:
	_human_target_valid = false
	edit_target_marker.visible = false
	if not _world_started:
		return
	var origin := camera.global_position
	var ray_end := origin - camera.global_basis.z * 384.0
	var query := PhysicsRayQueryParameters3D.create(origin, ray_end)
	query.collide_with_areas = false
	query.exclude = [human_player.get_rid()]
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	if hit.is_empty():
		if _may_replace_human_message():
			_human_message = "NO LOCAL COLLISION HIT"
		return
	var position := hit.get("position", Vector3.ZERO) as Vector3
	if not _is_current_collision_ready(position):
		if _may_replace_human_message():
			_human_message = "LOCAL COLLISION UPDATING"
		return
	_human_target = position
	_human_target_normal = hit.get("normal", Vector3.UP) as Vector3
	_human_target_valid = true
	edit_target_marker.global_position = position
	edit_target_marker.visible = true
	if _may_replace_human_message() and not bool(issue_recorder.call("is_recording")) and \
			not bool(issue_recorder.call("is_playing")):
		_human_message = "TARGET %.1f, %.1f, %.1f" % [position.x, position.y, position.z]


func _may_replace_human_message() -> bool:
	return not _human_edit_busy and Time.get_ticks_usec() >= _human_message_hold_until_usec


func _is_current_collision_ready(position: Vector3) -> bool:
	var coordinate := Vector3i(
		floori(position.x / 16.0),
		floori(position.y / 16.0),
		floori(position.z / 16.0)
	)
	var state := terrain_world.call("query_chunk_state", coordinate, 0) as RefCounted
	if state == null or not bool(state.call("is_present")):
		return false
	var generation := int(state.call("get_generation"))
	return bool(state.call("is_collision_required")) and \
			bool(state.call("is_collision_ready")) and \
			int(state.call("get_collision_generation")) in [0, generation]


func _submit_human_target_edit() -> void:
	if _human_edit_busy or bool(issue_recorder.call("is_playing")):
		_human_message = "EDIT UNAVAILABLE"
		_refresh_human_overlay()
		return
	if not _human_target_valid:
		_human_message = "NO READY COLLISION TARGET"
		_refresh_human_overlay()
		return
	_human_edit_busy = true
	_human_edit_sequence += 1
	var edit_sequence := _human_edit_sequence
	var kind := _human_brush_kind
	var center := _human_target
	var coordinate := _lod0_coordinate(center)
	var before_state := terrain_world.call("query_chunk_state", coordinate, 0) as RefCounted
	var before_generation := int(before_state.call("get_generation")) if before_state != null else -1
	var started_usec := Time.get_ticks_usec()
	var submission := submit_edit(kind, center)
	if str(submission.get("status", "")) != "PASS":
		_human_message = "EDIT REJECTED: %s" % str(submission.get("error", "unknown"))
		_human_edit_busy = false
		_refresh_human_overlay()
		return
	var expected_revision := int(submission.get("expected_world_revision", 0))
	_human_message = "%s SUBMITTED / REVISION %d" % [str(kind).to_upper(), expected_revision]
	_human_message_hold_until_usec = started_usec + 30000000
	_refresh_human_overlay()
	var commit_latency_usec := -1
	var visual_latency_usec := -1
	var collision_latency_usec := -1
	for _frame in range(HUMAN_EDIT_TIMEOUT_FRAMES):
		var elapsed_usec := Time.get_ticks_usec() - started_usec
		if commit_latency_usec < 0 and int(terrain_world.call("get_world_revision")) >= expected_revision:
			commit_latency_usec = elapsed_usec
			if edit_sequence == _human_edit_sequence:
				_human_message = "%s COMMIT %.1f ms / REBUILDING" % [
					str(kind).to_upper(), float(commit_latency_usec) / 1000.0,
				]
				_refresh_human_overlay()
		var state := terrain_world.call("query_chunk_state", coordinate, 0) as RefCounted
		if state != null and bool(state.call("is_present")):
			var generation := int(state.call("get_generation"))
			if generation > before_generation:
				if visual_latency_usec < 0 and bool(state.call("is_visual_ready")) and \
						int(state.call("get_render_generation")) == generation and \
						int(state.call("get_staged_render_generation")) == 0:
					visual_latency_usec = elapsed_usec
				if collision_latency_usec < 0 and bool(state.call("is_collision_required")) and \
						bool(state.call("is_collision_ready")) and \
						int(state.call("get_collision_generation")) == generation and \
						int(state.call("get_staged_collision_generation")) == 0:
					collision_latency_usec = elapsed_usec
		if commit_latency_usec >= 0 and visual_latency_usec >= 0 and collision_latency_usec >= 0:
			break
		await get_tree().process_frame
	if edit_sequence == _human_edit_sequence:
		_human_edit_busy = false
	var timing := {
		"schema": "world_transvoxel_terrain.human_edit_timing.v1",
		"status": "PASS" if commit_latency_usec >= 0 and visual_latency_usec >= 0 and \
				collision_latency_usec >= 0 else "TIMEOUT",
		"kind": str(kind),
		"center": Support.vector_summary(center),
		"chunk_coordinate": [coordinate.x, coordinate.y, coordinate.z],
		"before_generation": before_generation,
		"world_revision": expected_revision,
		"commit_latency_usec": maxi(commit_latency_usec, 0),
		"visual_latency_usec": maxi(visual_latency_usec, 0),
		"collision_latency_usec": maxi(collision_latency_usec, 0),
	}
	issue_recorder.call("record_edit_timing", timing)
	if edit_sequence == _human_edit_sequence:
		_last_edit_timing = timing
		if str(timing.get("status", "")) == "PASS":
			_human_message = "%s  COMMIT %.1f / VISUAL %.1f / COLLISION %.1f ms" % [
				str(kind).to_upper(),
				float(commit_latency_usec) / 1000.0,
				float(visual_latency_usec) / 1000.0,
				float(collision_latency_usec) / 1000.0,
			]
		else:
			_human_message = "%s LOCAL REPLACEMENT TIMED OUT" % str(kind).to_upper()
		_human_message_hold_until_usec = Time.get_ticks_usec() + 5000000
		_refresh_human_overlay()


static func _lod0_coordinate(position: Vector3) -> Vector3i:
	return Vector3i(
		floori(position.x / 16.0),
		floori(position.y / 16.0),
		floori(position.z / 16.0)
	)


func _refresh_human_overlay() -> void:
	if Engine.is_editor_hint():
		return
	var mode := "WALK" if _human_walk_mode else "FLY"
	human_status_label.text = "%s / %s  |  %s" % [
		mode, str(_human_brush_kind).to_upper(), _human_message,
	]
	var fps := Engine.get_frames_per_second()
	var frame_ms := 1000.0 / float(fps) if fps > 0 else 0.0
	performance_label.text = "FPS  %d    Frame  %.2f ms    Marks  %d" % [
		fps, frame_ms, int(issue_recorder.call("get_mark_count")),
	]
	apply_button.disabled = not _human_target_valid or _human_edit_busy or \
			bool(issue_recorder.call("is_playing"))


func _on_issue_status_changed(message: String) -> void:
	_human_message = message
	_refresh_human_overlay()


func capture_human_issue_sample() -> Dictionary:
	var metrics: Dictionary = {}
	if _world_started:
		metrics = terrain_world.call("get_runtime_metrics") as Dictionary
	return {
		"elapsed_usec": int(issue_recorder.call("elapsed_usec")),
		"camera_position": Support.vector_summary(camera.global_position),
		"camera_rotation": Support.vector_summary(camera.global_rotation),
		"viewer_position": Support.vector_summary(_viewer_position),
		"walk_mode": _human_walk_mode,
		"brush": str(_human_brush_kind),
		"readiness": _readiness_status(),
		"world_revision": terrain_world.call("get_world_revision") if _world_started else 0,
		"last_edit_timing": _last_edit_timing.duplicate(true),
		"lod_counts": (_last_audit.get("lod_counts", {}) as Dictionary).duplicate(true),
		"metrics": {
			"active": metrics.get("non_retiring_chunk_records", 0),
			"ready": metrics.get("non_retiring_fully_ready_chunk_records", 0),
			"render": metrics.get("render_resources", 0),
			"collision": metrics.get("collision_resources", 0),
			"scheduler": metrics.get("scheduler_queued_jobs", 0),
			"storage": metrics.get("storage_queued_requests", 0),
			"storage_active": metrics.get("storage_active_requests", 0),
			"mesh_worker_active": metrics.get("mesh_worker_active_jobs", 0),
			"mesh_worker_queued": metrics.get("mesh_worker_queued_jobs", 0),
			"mesh_completions": metrics.get("mesh_worker_queued_completions", 0),
			"publications": metrics.get("publication_queue_count", 0),
			"priority_publications": metrics.get("priority_publication_queue_count", 0),
			"queued_render": metrics.get("queued_render", 0),
			"collision_backlog": metrics.get("total_collision_backlog", 0),
			"pending_replacements": metrics.get("pending_chunk_replacements", 0),
			"pending_retirements": metrics.get("pending_chunk_retirements", 0),
		},
	}


func capture_lod0_chunk_state(coordinate: Vector3i) -> Dictionary:
	var state := terrain_world.call("query_chunk_state", coordinate, 0) as RefCounted
	if state == null or not bool(state.call("is_present")):
		return {"present": false, "coordinate": [coordinate.x, coordinate.y, coordinate.z]}
	return {
		"present": true,
		"coordinate": [coordinate.x, coordinate.y, coordinate.z],
		"generation": state.call("get_generation"),
		"visual_required": state.call("is_visual_required"),
		"visual_ready": state.call("is_visual_ready"),
		"render_generation": state.call("get_render_generation"),
		"staged_render_generation": state.call("get_staged_render_generation"),
		"collision_required": state.call("is_collision_required"),
		"collision_ready": state.call("is_collision_ready"),
		"collision_generation": state.call("get_collision_generation"),
		"staged_collision_generation": state.call("get_staged_collision_generation"),
	}


func apply_human_issue_camera_sample(sample: Dictionary) -> void:
	if _human_walk_mode:
		_set_walk_mode(false)
	_runtime_follow_camera = true
	track_toggle.button_pressed = true
	camera.global_position = _dictionary_vector3(sample.get("camera_position", {}))
	camera.global_rotation = _dictionary_vector3(sample.get("camera_rotation", {}))
	_camera_pitch = camera.rotation.x
	_camera_yaw = camera.rotation.y


static func _dictionary_vector3(value: Variant) -> Vector3:
	var data := value as Dictionary
	return Vector3(
		float(data.get("x", 0.0)),
		float(data.get("y", 0.0)),
		float(data.get("z", 0.0))
	)
