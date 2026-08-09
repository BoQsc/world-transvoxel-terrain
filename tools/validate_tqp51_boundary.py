#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT / "addons/world_transvoxel_terrain"
CONTRACT_PATH = ADDON / "BOUNDARY_CONTRACT.json"
EXPECTED_CANDIDATE = "world-transvoxel-terrain-cpu-tqp51-1"
EXPECTED_UPSTREAM = "f0d88fe9f2d844190d11f26cbe9ed9919f7244d1"

REQUIRED_FILES = (
    "addons/world_transvoxel_terrain/BOUNDARY_CONTRACT.json",
    "addons/world_transvoxel_terrain/plugin.cfg",
    "addons/world_transvoxel_terrain/runtime/wt_terrain_world.gd",
    "addons/world_transvoxel_terrain/runtime/wt_world_transvoxel_bridge.gd",
    "addons/world_transvoxel_terrain/runtime/wt_terrain_edit_bridge.gd",
    "docs/TQP51_PRODUCTION_ADDON_BOUNDARY.md",
)

REQUIRED_PHRASES = {
    "docs/TQP51_PRODUCTION_ADDON_BOUNDARY.md": (
        "Status: candidate boundary frozen",
        "There is no addon-local fallback mesher",
        "Native `world-transvoxel` owns worker scheduling",
        "Requests fail closed",
        "remains unqualified until TQP-53",
        "does not declare the addon production-ready",
    ),
    "addons/world_transvoxel_terrain/runtime/wt_terrain_world.gd": (
        "class_name WtTerrainWorld",
        "func start_world()",
        "func stop_world()",
        "func submit_edit_batch(",
        "func update_viewer(",
        "func remove_viewer(",
        "func request_authoritative_sample(",
        "func get_runtime_metrics()",
        "func get_hot_path_boundary_summary()",
    ),
    "addons/world_transvoxel_terrain/runtime/wt_world_transvoxel_bridge.gd": (
        'const TERRAIN_CLASS := "WorldTransvoxelTerrain"',
        'const CONFIG_CLASS := "WorldTransvoxelConfig"',
        "instantiate_backend_terrain",
        "instantiate_backend_config",
    ),
    "addons/world_transvoxel_terrain/runtime/wt_terrain_edit_bridge.gd": (
        'backend_terrain.call("begin_edit_transaction"',
        'backend_terrain.call("commit_edit_transaction"',
        "unsupported terrain edit operation",
    ),
}

FORBIDDEN_PATH_PARTS = (
    "addons/world_transvoxel/",
    "world-transvoxel-sandbox",
    "thirdparty/transvoxel_mit/",
)

FORBIDDEN_ADDON_SOURCE = (
    "ArrayMesh.new",
    "SurfaceTool.new",
    "MeshDataTool.new",
    "add_surface_from_arrays",
    "sample_surface_height",
    "res://labs/",
    "res://world-transvoxel-sandbox/",
)


def nested(value: dict, *keys: str):
    current = value
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def main() -> None:
    errors: list[str] = []

    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            errors.append(f"missing TQP-51 file: {relative}")

    contract: dict = {}
    if CONTRACT_PATH.is_file():
        try:
            contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid boundary contract: {exc}")

    expected_values = {
        ("schema",): "world_transvoxel.terrain.production_addon_boundary.v1",
        ("milestone",): "TQP-51",
        ("candidate_id",): EXPECTED_CANDIDATE,
        ("status",): "CANDIDATE_BOUNDARY_FROZEN",
        ("release_claim",): False,
        ("addon_root",): "addons/world_transvoxel_terrain",
        ("dependency", "name"): "world-transvoxel",
        ("dependency", "required_revision"): EXPECTED_UPSTREAM,
        ("dependency", "vendored"): False,
        ("dependency", "fallback_mesher"): False,
        ("dependency", "missing_dependency_policy"): "FAIL_CLOSED",
        ("threading", "addon_worker_threads"): False,
        ("threading", "gdscript_hot_paths"): False,
        ("failure_policy", "silent_fallback"): False,
        ("presentation_scaffolding", "status"): "DIAGNOSTIC_UNQUALIFIED_UNTIL_TQP53",
        ("presentation_scaffolding", "terrain_authority"): False,
        ("presentation_scaffolding", "geometry_authority"): False,
        ("next_milestone",): "TQP-52",
    }
    for keys, expected in expected_values.items():
        actual = nested(contract, *keys)
        if actual != expected:
            errors.append(f"contract {'.'.join(keys)} expected {expected!r}, got {actual!r}")

    required_classes = nested(contract, "dependency", "required_classes") or []
    for class_name in (
        "WorldTransvoxelTerrain",
        "WorldTransvoxelConfig",
        "WorldTransvoxelEditTransaction",
    ):
        if class_name not in required_classes:
            errors.append(f"contract missing dependency class: {class_name}")

    for owner in ("world_transvoxel", "terrain_addon", "game", "labs"):
        claims = nested(contract, "ownership", owner)
        if not isinstance(claims, list) or not claims:
            errors.append(f"contract missing ownership claims: {owner}")

    unsupported = nested(contract, "unsupported") or []
    if "synthetic terrain surfaces or fallback meshers" not in unsupported:
        errors.append("contract does not explicitly reject synthetic terrain fallback")

    for relative, phrases in REQUIRED_PHRASES.items():
        path = ROOT / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        compact = " ".join(text.split())
        for phrase in phrases:
            if phrase not in text and phrase not in compact:
                errors.append(f"{relative} missing phrase: {phrase}")

    for path in ADDON.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT).as_posix()
        for forbidden in FORBIDDEN_PATH_PARTS:
            if forbidden in relative:
                errors.append(f"forbidden authority path in addon: {relative}")
        if path.name in {"Transvoxel.cpp", "Transvoxel.h"}:
            errors.append(f"forbidden Transvoxel topology source in addon: {relative}")
        if path.suffix not in {".gd", ".gdshader", ".glsl"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if len(text.splitlines()) > 300:
            errors.append(f"source file exceeds TQP-51 limit: {relative}")
        for forbidden in FORBIDDEN_ADDON_SOURCE:
            if forbidden in text:
                errors.append(f"forbidden addon terrain path {forbidden!r}: {relative}")

    visual_sources = sorted((ADDON / "visual").glob("*.gd"))
    if visual_sources:
        errors.append("visual directory contains unqualified runtime terrain helper")

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        raise SystemExit(1)

    print(
        "WT_TERRAIN_TQP51_BOUNDARY_PASS "
        f"candidate={EXPECTED_CANDIDATE} "
        "next=tqp52_runtime_api_profiles_readiness"
    )


if __name__ == "__main__":
    main()
