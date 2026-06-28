@tool
extends Resource
class_name WtTerrainMaterialProfile

@export var profile_id: StringName = &"debug_checker_palette"
@export_range(2, 64, 1) var texture_resolution: int = 16
@export var shader_mode: StringName = &"uv2_material_id_checker"
@export var material_ids: Array[int] = [1, 2, 3, 4, 7]
@export var triplanar_projection: bool = true
@export var debug_view_enabled: bool = true


func get_contract_summary() -> Dictionary:
	return {
		"profile_id": str(profile_id),
		"texture_resolution": texture_resolution,
		"shader_mode": str(shader_mode),
		"material_count": material_ids.size(),
		"triplanar_projection": triplanar_projection,
		"debug_view_enabled": debug_view_enabled,
	}
