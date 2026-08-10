@tool
extends "res://addons/world_transvoxel_terrain/debug/wt_terrain_large_acceptance_scene.gd"
class_name WtTerrainHumanInspectionScene

const HUMAN_SURFACE_STREAMING_CEILING := 40.0
const HUMAN_LOOK_AHEAD_DISTANCE := 32.0
const HUMAN_COLLISION_RADIUS_CHUNKS := 2
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
var _human_target_accumulator := 0.0
var _human_overlay_accumulator := 0.0
var _brush_group: ButtonGroup
var _movement_group: ButtonGroup

func _ready() -> void:
	_viewer_position = TELEPORTS[0]
	super._ready()
	get_node("Interface/Dock/Content/Title").text = "Terrain Human Inspection"
	get_node("Interface/Dock/Content/Subtitle").text = "authority-backed defect reproduction"
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


func _exit_tree() -> void:
	issue_recorder.call("shutdown")
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	super._exit_tree()


func _process(delta: float) -> void:
	super._process(delta)
	if Engine.is_editor_hint():
		return
	_human_target_accumulator += delta
	_human_overlay_accumulator += delta
	if _human_target_accumulator >= 0.05:
		_human_target_accumulator = 0.0
		_update_human_target()
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
	if tracked.distance_to(_viewer_position) >= 4.0:
		_request_viewer(
			tracked,
			false,
			VIEWER_RADIUS_CHUNKS,
			MAXIMUM_LOD,
			HUMAN_COLLISION_RADIUS_CHUNKS
		)


func _update_fly_camera(delta: float) -> void:
	var direction := Vector3.ZERO
	if Input.is_key_pressed(KEY_W): direction -= camera.global_basis.z
	if Input.is_key_pressed(KEY_S): direction += camera.global_basis.z
	if Input.is_key_pressed(KEY_A): direction -= camera.global_basis.x
	if Input.is_key_pressed(KEY_D): direction += camera.global_basis.x
	if Input.is_key_pressed(KEY_Q): direction -= Vector3.UP
	if Input.is_key_pressed(KEY_E): direction += Vector3.UP
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
		if not _human_edit_busy:
			_human_message = "NO LOCAL COLLISION HIT"
		return
	var position := hit.get("position", Vector3.ZERO) as Vector3
	if not _is_current_collision_ready(position):
		if not _human_edit_busy:
			_human_message = "LOCAL COLLISION UPDATING"
		return
	_human_target = position
	_human_target_normal = hit.get("normal", Vector3.UP) as Vector3
	_human_target_valid = true
	edit_target_marker.global_position = position
	edit_target_marker.visible = true
	if not _human_edit_busy and not bool(issue_recorder.call("is_recording")) and \
			not bool(issue_recorder.call("is_playing")):
		_human_message = "TARGET %.1f, %.1f, %.1f" % [position.x, position.y, position.z]


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
			int(state.call("get_collision_generation")) in [0, generation] and \
			int(state.call("get_staged_collision_generation")) == 0


func _submit_human_target_edit() -> void:
	if _human_edit_busy or bool(issue_recorder.call("is_playing")):
		_human_message = "EDIT UNAVAILABLE"
		return
	if not _human_target_valid:
		_human_message = "NO READY COLLISION TARGET"
		return
	_human_edit_busy = true
	var submission := submit_edit(_human_brush_kind, _human_target)
	if str(submission.get("status", "")) != "PASS":
		_human_message = "EDIT REJECTED: %s" % str(submission.get("error", "unknown"))
		_human_edit_busy = false
		return
	var expected_revision := int(submission.get("expected_world_revision", 0))
	_human_message = "%s COMMIT %d PENDING" % [str(_human_brush_kind).to_upper(), expected_revision]
	for _frame in range(1800):
		if int(terrain_world.call("get_world_revision")) >= expected_revision:
			_human_message = "%s COMMITTED AT REVISION %d" % [
				str(_human_brush_kind).to_upper(), expected_revision,
			]
			_human_edit_busy = false
			return
		await get_tree().process_frame
	_human_message = "EDIT COMMIT TIMED OUT"
	_human_edit_busy = false


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
		"lod_counts": (_last_audit.get("lod_counts", {}) as Dictionary).duplicate(true),
		"metrics": {
			"active": metrics.get("non_retiring_chunk_records", 0),
			"ready": metrics.get("non_retiring_fully_ready_chunk_records", 0),
			"render": metrics.get("render_resources", 0),
			"collision": metrics.get("collision_resources", 0),
			"scheduler": metrics.get("scheduler_queued_jobs", 0),
			"storage": metrics.get("storage_queued_requests", 0),
			"queued_render": metrics.get("queued_render", 0),
			"collision_backlog": metrics.get("total_collision_backlog", 0),
			"pending_replacements": metrics.get("pending_chunk_replacements", 0),
			"pending_retirements": metrics.get("pending_chunk_retirements", 0),
		},
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
