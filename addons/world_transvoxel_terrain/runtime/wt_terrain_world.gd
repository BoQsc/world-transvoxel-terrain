@tool
extends Node3D
class_name WtTerrainWorld

const DependencyStatus := preload("res://addons/world_transvoxel_terrain/api/wt_terrain_dependency_status.gd")
const BackendBridge := preload("res://addons/world_transvoxel_terrain/runtime/wt_world_transvoxel_bridge.gd")

@export var terrain_profile: Resource
@export var generation_profile: Resource
@export var storage_profile: Resource
@export var recovery_policy: Resource
@export var auto_report_dependency_status: bool = false


func _ready() -> void:
	if Engine.is_editor_hint() and auto_report_dependency_status:
		print(get_dependency_status().get("message", ""))


func get_dependency_status() -> Dictionary:
	return DependencyStatus.new().get_status()


func get_bridge_status() -> Dictionary:
	return BackendBridge.new().get_bridge_status()


func get_backend_identity() -> Dictionary:
	return BackendBridge.new().get_backend_identity()


func get_contract_summary() -> Dictionary:
	return {
		"terrain_world": "WtTerrainWorld",
		"has_terrain_profile": terrain_profile != null,
		"has_generation_profile": generation_profile != null,
		"has_storage_profile": storage_profile != null,
		"has_recovery_policy": recovery_policy != null,
		"dependency": get_dependency_status(),
		"bridge": get_bridge_status(),
		"implementation": "a4_phase1_resource_semantics_only",
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
