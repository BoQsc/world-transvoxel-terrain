#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "TQP52_RUNTIME_CONTRACT.json"

REQUIRED = {
    "addons/world_transvoxel_terrain/api/wt_terrain_runtime_profile.gd": (
        "class_name WtTerrainRuntimeProfile",
        "LOW_POWER, BALANCED, QUALITY, REFERENCE",
        "get_backend_config_overrides",
        "unqualified_profile_intent_only",
    ),
    "addons/world_transvoxel_terrain/runtime/wt_terrain_runtime_state.gd": (
        "tqp52_generation_aware_readiness_v1",
        "async request capacity reached",
        "viewer revision must be monotonic",
        "stale_api_generation",
        '"render_state"',
        '"collision_state"',
    ),
    "addons/world_transvoxel_terrain/runtime/wt_terrain_world.gd": (
        "signal runtime_generation_changed",
        "signal terrain_request_cancelled",
        "func get_readiness_snapshot",
        "func get_chunk_readiness",
        "func update_collision_viewer",
        "func remove_collision_viewer",
    ),
    "addons/world_transvoxel_terrain/runtime/wt_terrain_world_backend_ops.gd": (
        "get_backend_config_overrides",
        '"runtime_viewer_capacity"',
        '"runtime_collision_apply_deadline_us"',
        '["edit_committed", "_on_backend_edit_committed"]',
    ),
    "addons/world_transvoxel_terrain/runtime/wt_terrain_world_contracts.gd": (
        '"api_version": 2',
        '"readiness"',
        '"runtime_profile"',
    ),
    "addons/world_transvoxel_terrain/material/wt_terrain_weighted_palette.gdshader": (
        "generated_material_weights_low = CUSTOM0;",
        "authored_material_weights_high = CUSTOM3;",
        "material_weight_sum",
    ),
    "tests/tqp52_runtime_contract_smoke.gd": (
        "WT_TERRAIN_TQP52_GODOT_PASS",
        "bounded query back-pressure contract failed",
        "world stop did not cancel the prior API generation",
    ),
    "docs/TQP52_RUNTIME_API_PROFILES_READINESS.md": (
        "Power intent is",
        "late native completions",
        "separate states",
    ),
}


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["schema"] == "world_transvoxel_terrain.tqp52_runtime_contract.v1"
    assert contract["engine_policy"]["minimum_version"] == "4.7"
    assert contract["engine_policy"]["current_qualification_matrix"] == ["4.7"]
    assert contract["authority"]["fallback_mesher"] is False
    assert contract["authority"]["fallback_field"] is False
    assert contract["api"]["version"] == 2
    assert contract["profiles"]["builtins"] == [
        "LOW_POWER", "BALANCED", "QUALITY", "REFERENCE"
    ]
    assert set(contract["readiness"]["scopes"]) == {
        "render", "collision", "edit", "query"
    }

    for relative, markers in REQUIRED.items():
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"missing TQP-52 file: {relative}")
        source = path.read_text(encoding="utf-8")
        missing = [marker for marker in markers if marker not in source]
        if missing:
            raise RuntimeError(f"{relative} missing markers: {missing}")
        if path.suffix in {".gd", ".gdshader", ".glsl"} and len(source.splitlines()) > 300:
            raise RuntimeError(f"oversized TQP-52 source: {relative}")

    addon = ROOT / "addons" / "world_transvoxel_terrain"
    forbidden = ("marching_cubes_fallback", "fallback_mesher", "fallback_density_field")
    for path in addon.rglob("*"):
        if path.is_file() and path.suffix in {".gd", ".gdshader", ".glsl"}:
            source = path.read_text(encoding="utf-8", errors="replace").lower()
            if any(marker in source for marker in forbidden):
                raise RuntimeError(f"forbidden terrain fallback marker in {path}")

    print(
        "WT_TERRAIN_TQP52_CONTRACT_PASS "
        "api=2 profiles=4 readiness=4 bounded=1 authority=world-transvoxel"
    )


if __name__ == "__main__":
    main()
