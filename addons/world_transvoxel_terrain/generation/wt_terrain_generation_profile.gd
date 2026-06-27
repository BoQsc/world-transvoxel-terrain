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


func get_contract_summary() -> Dictionary:
	return {
		"source_mode": SourceMode.keys()[source_mode],
		"seed": seed,
		"default_solid_material": default_solid_material,
		"supports_underground_volume": supports_underground_volume,
	}
