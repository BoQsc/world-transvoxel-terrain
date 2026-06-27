@tool
extends Node3D
class_name WtTerrainWorld

const DependencyStatus := preload("res://addons/world_transvoxel_terrain/api/wt_terrain_dependency_status.gd")
const BackendBridge := preload("res://addons/world_transvoxel_terrain/runtime/wt_world_transvoxel_bridge.gd")

@export var terrain_profile: Resource
@export var generation_profile: Resource
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
		"dependency": get_dependency_status(),
		"bridge": get_bridge_status(),
		"implementation": "placeholder_contract_only",
	}
