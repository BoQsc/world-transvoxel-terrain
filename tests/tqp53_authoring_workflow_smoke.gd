extends SceneTree

const MARKER := "WT_TERRAIN_TQP53_GODOT_PASS"
const Document := preload("res://addons/world_transvoxel_terrain/editor/wt_terrain_authoring_document.gd")
const EditOperation := preload("res://addons/world_transvoxel_terrain/edit/wt_terrain_edit_operation.gd")
const Exporter := preload("res://addons/world_transvoxel_terrain/editor/wt_terrain_repro_exporter.gd")
const Preview := preload("res://addons/world_transvoxel_terrain/editor/wt_terrain_brush_preview.gd")

const IMPORT_PATH := "user://world_transvoxel_terrain/tqp53_import.json"
const REPRO_PATH := "user://world_transvoxel_terrain/tqp53_repro.json"


class FakeWorld extends Node3D:
	func get_terrain_api_contract_summary() -> Dictionary:
		return {"api_name": "WtTerrainWorld", "api_version": 2}

	func get_readiness_snapshot() -> Dictionary:
		return {"api_generation": 7, "render": {"state": "ready"}}

	func get_debug_snapshot() -> Dictionary:
		return {"implementation": "tqp53_fake_world"}

	func get_last_error() -> String:
		return "ok"


func _initialize() -> void:
	call_deferred("_run_test")


func _run_test() -> void:
	var document = Document.new()
	document.mode = 1
	document.center = Vector3(12.5, 8.0, -3.25)
	document.radius = 3.0
	document.smooth_radius = 0.5
	document.material_id = 8
	if not document.is_valid():
		_fail("valid construction draft was rejected: %s" % document.get_validation_error())
		return
	var operation: Resource = document.create_operation()
	if str(operation.call("get_mode_name")) != "construct" or \
			float(operation.get("smooth_radius")) != 0.5:
		_fail("authoring document did not create the declared operation")
		return
	var batch: Resource = document.create_batch(5301)
	if not batch.call("is_valid") or int(batch.get("batch_id")) != 5301:
		_fail("authoring document did not create a valid batch")
		return
	var water = EditOperation.new()
	water.mode = EditOperation.Mode.PLACE_STATIC_WATER
	water.material_id = 9
	water.radius = 2.0
	if not water.is_valid() or water.get_mode_name() != &"place_static_water":
		_fail("authoritative static-water operation was rejected")
		return
	water.material_id = 8
	if water.is_valid():
		_fail("static-water operation accepted a non-water material")
		return

	_write_import_fixture()
	if not document.import_json(IMPORT_PATH) or document.material_id != 10 or \
			document.center != Vector3(1, 2, 3):
		_fail("authoring JSON import failed")
		return
	var before := document.to_dictionary()
	var changed := before.duplicate(true)
	changed["radius"] = 6.0
	changed["draft_revision"] = int(before["draft_revision"]) + 1
	if not document.apply_dictionary(changed) or document.radius != 6.0:
		_fail("draft redo application failed")
		return
	if not document.apply_dictionary(before) or document.radius == 6.0:
		_fail("draft undo application failed")
		return

	var world := FakeWorld.new()
	root.add_child(world)
	var preview: MeshInstance3D = Preview.update(world, document)
	if preview == null or not bool(preview.get_meta("world_transvoxel_editor_preview", false)):
		_fail("brush preview was not created")
		return
	Preview.clear(world)
	await process_frame
	if world.get_node_or_null("WT_TerrainAuthoringPreview") != null:
		_fail("brush preview cleanup failed")
		return

	var exported := Exporter.export_repro(world, document, REPRO_PATH)
	if not bool(exported.get("exported", false)) or not FileAccess.file_exists(REPRO_PATH):
		_fail("one-action repro export failed: %s" % str(exported))
		return
	var payload = JSON.parse_string(FileAccess.get_file_as_string(REPRO_PATH))
	if not payload is Dictionary or payload.get("schema", "") != "world_transvoxel_terrain.repro.v1" or \
			int(Dictionary(payload.get("readiness", {})).get("api_generation", 0)) != 7:
		_fail("repro payload omitted authoritative contract/readiness data")
		return

	world.queue_free()
	_remove_file(IMPORT_PATH)
	_remove_file(REPRO_PATH)
	print("%s draft=1 undo_redo=1 import=1 preview=1 repro=1 dock=static" % MARKER)
	await process_frame
	quit(0)


func _write_import_fixture() -> void:
	var absolute := ProjectSettings.globalize_path(IMPORT_PATH)
	DirAccess.make_dir_recursive_absolute(absolute.get_base_dir())
	var file := FileAccess.open(IMPORT_PATH, FileAccess.WRITE)
	file.store_string(JSON.stringify({
		"document_id": "imported",
		"mode": 0,
		"brush_shape": 0,
		"center": [1, 2, 3],
		"radius": 2.5,
		"smooth_radius": 0.0,
		"material_id": 10,
		"material_palette": [1, 2, 3, 4, 5, 7, 8, 10],
		"draft_revision": 2,
	}))


func _remove_file(path: String) -> void:
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(path))


func _fail(message: String) -> void:
	push_error("WT_TERRAIN_TQP53_GODOT_FAIL: " + message)
	quit(1)
