#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "TQP53_AUTHORING_CONTRACT.json"
REQUIRED = {
    "addons/world_transvoxel_terrain/editor/world_transvoxel_terrain_plugin.gd": (
        "InspectorDock.new()", "add_control_to_dock", "remove_control_from_docks"
    ),
    "addons/world_transvoxel_terrain/editor/wt_terrain_inspector_dock.gd": (
        "get_selection().selection_changed", "Change Terrain Authoring Draft",
        "Set Terrain Runtime Profile", "ReproExporter.export_repro", "BrushPreview.update"
    ),
    "addons/world_transvoxel_terrain/editor/wt_terrain_authoring_document.gd": (
        "class_name WtTerrainAuthoringDocument", "func create_operation",
        "func create_batch", "func import_json"
    ),
    "addons/world_transvoxel_terrain/editor/wt_terrain_repro_exporter.gd": (
        "world_transvoxel_terrain.repro.v1", "get_readiness_snapshot",
        "get_debug_snapshot", "authoring_document"
    ),
    "addons/world_transvoxel_terrain/editor/wt_terrain_brush_preview.gd": (
        "world_transvoxel_editor_preview", "SphereMesh.new()", "BoxMesh.new()"
    ),
    "addons/world_transvoxel_terrain/material/wt_terrain_weighted_palette.gdshader": (
        "generated_material_weights_low = CUSTOM0;",
        "authored_material_weights_high = CUSTOM3;", "weighted_albedo"
    ),
    "tests/tqp53_authoring_workflow_smoke.gd": (
        "WT_TERRAIN_TQP53_GODOT_PASS", "draft undo application failed",
        "one-action repro export failed"
    ),
    "docs/TQP53_AUTHORING_AND_INSPECTION_WORKFLOW.md": (
        "does not advertise a fake inverse operation", "editor-only",
        "does not reproduce procedural terrain fields"
    ),
}


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["schema"] == "world_transvoxel_terrain.tqp53_authoring_contract.v1"
    assert contract["undo_redo"]["durable_edit_commit_reversible"] is False
    assert contract["boundaries"]["lab_runtime_dependency"] is False
    assert contract["boundaries"]["procedural_field_duplication"] is False
    assert contract["editor_workflow"]["repro_export"] == "world_transvoxel_terrain.repro.v1"
    for relative, markers in REQUIRED.items():
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"missing TQP-53 file: {relative}")
        source = path.read_text(encoding="utf-8")
        missing = [marker for marker in markers if marker not in source]
        if missing:
            raise RuntimeError(f"{relative} missing markers: {missing}")
        if path.suffix in {".gd", ".gdshader", ".glsl"} and len(source.splitlines()) > 300:
            raise RuntimeError(f"oversized TQP-53 source: {relative}")
    shader = (ROOT / "addons/world_transvoxel_terrain/material/wt_terrain_weighted_palette.gdshader").read_text(encoding="utf-8")
    forbidden = ("procedural_road_field", "procedural_source_height", "procedural_ore_worldspace_weight")
    if any(marker in shader for marker in forbidden):
        raise RuntimeError("production addon shader duplicates procedural field authority")
    print(
        "WT_TERRAIN_TQP53_CONTRACT_PASS "
        "dock=1 draft_undo=1 durable_inverse=0 preview=1 import=1 repro=1"
    )


if __name__ == "__main__":
    main()
