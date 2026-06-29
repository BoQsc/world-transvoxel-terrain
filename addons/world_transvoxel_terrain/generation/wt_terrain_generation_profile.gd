@tool
extends Resource
class_name WtTerrainGenerationProfile

enum SourceMode {
	FLAT,
	DETERMINISTIC_REFERENCE,
	BAKED_WORLD,
}

@export var source_mode: SourceMode = SourceMode.DETERMINISTIC_REFERENCE
@export var seed: int = 1
@export var default_solid_material: int = 1
@export var supports_underground_volume: bool = true
@export var profile_id: StringName = &"deterministic_reference"
@export_range(1, 4096, 1) var world_chunk_count_x: int = 128
@export_range(1, 4096, 1) var world_chunk_count_z: int = 128
@export var source_revision: int = 190001


func get_contract_summary() -> Dictionary:
	return {
		"profile_id": str(profile_id),
		"source_mode": SourceMode.keys()[source_mode],
		"seed": seed,
		"default_solid_material": default_solid_material,
		"supports_underground_volume": supports_underground_volume,
		"world_chunk_count_x": world_chunk_count_x,
		"world_chunk_count_z": world_chunk_count_z,
		"source_revision": source_revision,
	}
