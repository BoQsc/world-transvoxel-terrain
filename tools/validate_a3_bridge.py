#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "docs/A3_WORLD_TRANSVOXEL_BRIDGE.md",
    "addons/world_transvoxel_terrain/runtime/wt_world_transvoxel_bridge.gd",
    "addons/world_transvoxel_terrain/runtime/wt_world_transvoxel_bridge.gd.uid",
    "tests/a3_bridge_smoke.gd",
    "tests/a3_bridge_smoke.gd.uid",
    "tools/a3_bridge_smoke.py",
    "tools/validate_a3_bridge.py",
)

REQUIRED_PHRASES = {
    "docs/A3_WORLD_TRANSVOXEL_BRIDGE.md": (
        "Status: complete",
        "WT_TERRAIN_A3_BRIDGE_PASS",
        "WT_TERRAIN_A3_GODOT_BRIDGE_PASS",
        "temporary ignored Godot fixture",
        "WorldTransvoxelTerrain",
        "WorldTransvoxelConfig",
        "without vendoring",
        "`.gd.uid` files",
        "Next valid action is A4",
    ),
    "addons/world_transvoxel_terrain/runtime/wt_world_transvoxel_bridge.gd": (
        "class_name WtWorldTransvoxelBridge",
        "WorldTransvoxelTerrain",
        "WorldTransvoxelConfig",
        "get_backend_identity",
        "get_backend_license",
        "get_runtime_metrics",
    ),
    "addons/world_transvoxel_terrain/runtime/wt_terrain_world.gd": (
        "get_bridge_status",
        "get_backend_identity",
        "wt_world_transvoxel_bridge.gd",
    ),
    "tests/a3_bridge_smoke.gd": (
        "WT_TERRAIN_A3_GODOT_BRIDGE_PASS",
        "WorldTransvoxelTerrain",
        "WorldTransvoxelConfig",
        "backend_license",
        "implementation=bridge_only",
    ),
    "tools/a3_bridge_smoke.py": (
        "WT_TERRAIN_A3_BRIDGE_PASS",
        "WT_TERRAIN_A3_GODOT_BRIDGE_PASS",
        "artifacts",
        "DEPENDENCY_FILES",
        "thirdparty/transvoxel_mit/LICENSE",
    ),
}

FORBIDDEN_TRACKED_PATHS = (
    "addons/world_transvoxel/",
    "thirdparty/transvoxel_mit/",
)


def has_phrase(text: str, phrase: str) -> bool:
    return phrase in text or phrase in " ".join(text.split())


def iter_repo_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        rel = relative.as_posix()
        if ".git" in relative.parts:
            continue
        if "__pycache__" in relative.parts:
            continue
        if rel.startswith("references/downloaded/"):
            continue
        if rel.startswith("artifacts/"):
            continue
        if path.is_file():
            files.append(relative)
    return files


def main() -> None:
    errors: list[str] = []

    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            errors.append(f"missing A3 file: {relative}")

    for relative, phrases in REQUIRED_PHRASES.items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing phrase input: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if not has_phrase(text, phrase):
                errors.append(f"{relative} missing phrase: {phrase}")

    for relative in iter_repo_files():
        rel = relative.as_posix()
        for forbidden in FORBIDDEN_TRACKED_PATHS:
            if forbidden in rel:
                errors.append(f"forbidden dependency path in repo: {rel}")
        if relative.name in {"Transvoxel.cpp", "Transvoxel.h"}:
            errors.append(f"forbidden MIT Transvoxel source name in repo: {rel}")
        if relative.suffix in {".gd", ".glsl", ".gdshader"}:
            lines = (ROOT / relative).read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()
            if len(lines) > 300:
                errors.append(f"source file exceeds A3 bridge limit: {rel}")

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        raise SystemExit(1)

    print(
        "WT_TERRAIN_A3_CONTRACT_PASS "
        "next=a4_terrain_profile_edit_storage_recovery implementation=bridge_only"
    )


if __name__ == "__main__":
    main()
