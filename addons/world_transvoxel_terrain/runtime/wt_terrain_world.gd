@tool
extends Node3D
class_name WtTerrainWorld

const DependencyStatus := preload("res://addons/world_transvoxel_terrain/api/wt_terrain_dependency_status.gd")
const BackendBridge := preload("res://addons/world_transvoxel_terrain/runtime/wt_world_transvoxel_bridge.gd")
const EditBridge := preload("res://addons/world_transvoxel_terrain/runtime/wt_terrain_edit_bridge.gd")
const RuntimeAudit := preload("res://addons/world_transvoxel_terrain/runtime/wt_terrain_runtime_audit.gd")

const BACKEND_TERRAIN_NODE_NAME := "WT_BackendTerrain"

@export var terrain_profile: Resource
@export var generation_profile: Resource
@export var storage_profile: Resource
@export var recovery_policy: Resource
@export var auto_report_dependency_status: bool = false

var _backend_terrain: Node
var _backend_config: Resource
var _last_error: String = "ok"
var _last_edit_submission_summary: Dictionary = {}


func _ready() -> void:
	if Engine.is_editor_hint() and auto_report_dependency_status:
		print(get_dependency_status().get("message", ""))


func get_dependency_status() -> Dictionary:
	return DependencyStatus.new().get_status()


func get_bridge_status() -> Dictionary:
	return BackendBridge.new().get_bridge_status()


func get_backend_identity() -> Dictionary:
	return BackendBridge.new().get_backend_identity()


func get_last_error() -> String:
	return _last_error


func get_backend_terrain() -> Node:
	return _backend_terrain


func get_backend_world_state_name() -> String:
	if _backend_terrain == null or not _backend_terrain.has_method("get_world_state_name"):
		return "stopped"
	return str(_backend_terrain.call("get_world_state_name"))


func get_backend_world_revision() -> int:
	if _backend_terrain == null or not _backend_terrain.has_method("get_world_revision"):
		return 0
	return int(_backend_terrain.call("get_world_revision"))


func get_backend_world_error() -> String:
	if _backend_terrain == null or not _backend_terrain.has_method("get_world_error"):
		return _last_error
	return str(_backend_terrain.call("get_world_error"))


func is_backend_world_running() -> bool:
	if _backend_terrain == null or not _backend_terrain.has_method("is_world_running"):
		return false
	return bool(_backend_terrain.call("is_world_running"))


func start_backend_world() -> bool:
	_last_error = "ok"
	if is_backend_world_running():
		_last_error = "backend world is already running"
		return false
	if not _validate_storage_profile():
		return false
	if not _ensure_backend_terrain():
		return false
	var manifest_path := str(storage_profile.get("world_manifest_path"))
	var object_root := str(storage_profile.get("object_root_path"))
	if not bool(_backend_terrain.call("start_world", manifest_path, object_root)):
		_last_error = get_backend_world_error()
		return false
	_last_error = "ok"
	return true


func stop_backend_world() -> bool:
	if _backend_terrain == null:
		_last_error = "backend terrain is not instantiated"
		return false
	if not _backend_terrain.has_method("stop_world"):
		_last_error = "backend terrain cannot stop worlds"
		return false
	if not bool(_backend_terrain.call("stop_world")):
		_last_error = get_backend_world_error()
		return false
	_last_error = "ok"
	return true


func submit_edit_batch(batch: Resource, author_id: int = 0) -> bool:
	if not is_backend_world_running():
		_last_error = "backend world must be running before edit submission"
		return false
	var edit_bridge := EditBridge.new()
	if not edit_bridge.commit_batch(_backend_terrain, batch, author_id):
		_last_error = edit_bridge.get_last_error()
		_last_edit_submission_summary = edit_bridge.get_last_submission_summary()
		return false
	_last_edit_submission_summary = edit_bridge.get_last_submission_summary()
	_last_error = "ok"
	return true


func get_last_edit_submission_summary() -> Dictionary:
	return _last_edit_submission_summary


func update_viewer(
	viewer_id: int,
	revision: int,
	position: Vector3,
	radius_chunks: int,
	maximum_lod: int = 0
) -> bool:
	if not is_backend_world_running():
		_last_error = "backend world must be running before viewer updates"
		return false
	if not _backend_terrain.has_method("update_viewer"):
		_last_error = "backend terrain cannot update viewers"
		return false
	if not bool(_backend_terrain.call(
		"update_viewer", viewer_id, revision, position, radius_chunks, maximum_lod
	)):
		_last_error = get_backend_world_error()
		return false
	_last_error = "ok"
	return true


func remove_viewer(viewer_id: int, revision: int) -> bool:
	if not is_backend_world_running():
		_last_error = "backend world must be running before viewer removal"
		return false
	if not _backend_terrain.has_method("remove_viewer"):
		_last_error = "backend terrain cannot remove viewers"
		return false
	if not bool(_backend_terrain.call("remove_viewer", viewer_id, revision)):
		_last_error = get_backend_world_error()
		return false
	_last_error = "ok"
	return true


func query_chunk_state(chunk_coordinate: Vector3i, lod: int) -> RefCounted:
	if _backend_terrain == null or not _backend_terrain.has_method("query_chunk_state"):
		_last_error = "backend terrain cannot query chunk state"
		return null
	return _backend_terrain.call("query_chunk_state", chunk_coordinate, lod)


func get_runtime_metrics() -> Dictionary:
	return RuntimeAudit.get_runtime_metrics(_backend_terrain)


func is_cold_idle() -> bool:
	return RuntimeAudit.is_cold_idle(get_runtime_metrics())


func get_cold_idle_summary() -> Dictionary:
	return RuntimeAudit.get_cold_idle_summary(get_runtime_metrics())


func get_contract_summary() -> Dictionary:
	return {
		"terrain_world": "WtTerrainWorld",
		"has_terrain_profile": terrain_profile != null,
		"has_generation_profile": generation_profile != null,
		"has_storage_profile": storage_profile != null,
		"has_recovery_policy": recovery_policy != null,
		"dependency": get_dependency_status(),
		"bridge": get_bridge_status(),
		"backend_world_state": get_backend_world_state_name(),
		"cold_idle": is_cold_idle(),
		"implementation": "a4_phase4_reference_profile_runtime_cold_idle",
		"phase_history": [
			"a4_phase1_resource_semantics_only",
			"terrain_world_lifecycle",
		],
	}


func get_a4_phase1_summary() -> Dictionary:
	return {
		"terrain_profile": _resource_summary(terrain_profile),
		"generation_profile": _resource_summary(generation_profile),
		"storage_profile": _resource_summary(storage_profile),
		"recovery_policy": _resource_summary(recovery_policy),
		"backend_identity": get_backend_identity(),
		"implementation": "resource_semantics_only",
	}


func get_a4_phase3_summary() -> Dictionary:
	return {
		"terrain_profile": _resource_summary(terrain_profile),
		"storage_profile": _resource_summary(storage_profile),
		"backend_identity": get_backend_identity(),
		"backend_world_state": get_backend_world_state_name(),
		"backend_world_revision": get_backend_world_revision(),
		"last_error": _last_error,
		"last_edit_submission": _last_edit_submission_summary,
		"implementation": "terrain_world_lifecycle",
	}


func get_a4_phase4_summary() -> Dictionary:
	return {
		"terrain_profile": _resource_summary(terrain_profile),
		"storage_profile": _resource_summary(storage_profile),
		"backend_world_state": get_backend_world_state_name(),
		"backend_world_revision": get_backend_world_revision(),
		"runtime_metrics": get_runtime_metrics(),
		"cold_idle": get_cold_idle_summary(),
		"implementation": "reference_profile_runtime_cold_idle",
	}


func _resource_summary(resource: Resource) -> Dictionary:
	if resource == null:
		return {"assigned": false}
	if resource.has_method("get_contract_summary"):
		var summary := Dictionary(resource.call("get_contract_summary"))
		summary["assigned"] = true
		return summary
	return {
		"assigned": true,
		"class": resource.get_class(),
	}


func _validate_storage_profile() -> bool:
	if storage_profile == null:
		_last_error = "storage_profile is required"
		return false
	if not storage_profile.has_method("get_validation_error"):
		_last_error = "storage_profile must expose validation"
		return false
	var validation_error := str(storage_profile.call("get_validation_error"))
	if not validation_error.is_empty():
		_last_error = validation_error
		return false
	if not _resource_has_property(storage_profile, "object_root_path"):
		_last_error = "storage_profile must expose object_root_path"
		return false
	return true


func _ensure_backend_terrain() -> bool:
	if _backend_terrain != null and is_instance_valid(_backend_terrain):
		return true
	var bridge := BackendBridge.new()
	var status := bridge.get_bridge_status()
	if not bool(status.get("bridge_ready", false)):
		_last_error = "world-transvoxel bridge is not ready: %s" % str(status)
		return false
	var terrain = bridge.instantiate_backend_terrain()
	var config = bridge.instantiate_backend_config()
	if terrain == null or config == null:
		_last_error = "failed to instantiate world-transvoxel backend terrain/config"
		if terrain is Node:
			terrain.free()
		return false
	if not (terrain is Node):
		_last_error = "world-transvoxel backend terrain is not a Node"
		return false
	_backend_terrain = terrain
	_backend_config = config
	_backend_terrain.name = BACKEND_TERRAIN_NODE_NAME
	_backend_terrain.set("configuration", _backend_config)
	add_child(_backend_terrain)
	return true


func _resource_has_property(resource: Resource, property_name: String) -> bool:
	for property in resource.get_property_list():
		if str(property.get("name", "")) == property_name:
			return true
	return false
