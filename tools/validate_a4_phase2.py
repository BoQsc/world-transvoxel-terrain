#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "docs/A4_PROFILE_EDIT_STORAGE_RECOVERY_PHASE2.md",
    "addons/world_transvoxel_terrain/runtime/wt_terrain_edit_bridge.gd",
    "addons/world_transvoxel_terrain/runtime/wt_terrain_edit_bridge.gd.uid",
    "tests/a4_phase2_bridge_storage_smoke.gd",
    "tests/a4_phase2_bridge_storage_smoke.gd.uid",
    "tools/a4_phase2_bridge_storage_smoke.py",
    "tools/validate_a4_phase2.py",
)

REQUIRED_PHRASES = {
    "docs/A4_PROFILE_EDIT_STORAGE_RECOVERY_PHASE2.md": (
        "Status: complete",
        "WT_TERRAIN_A4_PHASE2_CONTRACT_PASS",
        "WT_TERRAIN_A4_PHASE2_GODOT_PASS",
        "WT_TERRAIN_A4_PHASE2_SMOKE_PASS",
        "bridge_storage_fixture",
        "A4 is not complete",
        "Next valid action is A4 phase 3",
    ),
    "addons/world_transvoxel_terrain/runtime/wt_terrain_edit_bridge.gd": (
        "class_name WtTerrainEditBridge",
        "begin_batch_transaction",
        "commit_batch",
        "begin_edit_transaction",
        "commit_edit_transaction",
        "set_density_sphere",
        "paint_material_box",
        "bridge_edit_submission",
    ),
    "addons/world_transvoxel_terrain/edit/wt_terrain_edit_operation.gd": (
        "density_value",
        "is_nan",
        "to_bridge_command",
    ),
    "tests/a4_phase2_bridge_storage_smoke.gd": (
        "WT_TERRAIN_A4_PHASE2_GODOT_PASS",
        "WorldTransvoxelTerrain",
        "begin_batch_transaction",
        "get_command_count",
        "world.wtedit",
        "journal=replayed",
    ),
    "tools/a4_phase2_bridge_storage_smoke.py": (
        "WT_TERRAIN_A4_PHASE2_SMOKE_PASS",
        "WT_TERRAIN_A4_PHASE2_GODOT_PASS",
        "production-lifecycle-fixture",
        "world.wtedit",
        "a4_phase2_bridge_storage_report.json",
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
            errors.append(f"missing A4 phase 2 file: {relative}")

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
                errors.append(f"source file exceeds A4 phase 2 limit: {rel}")

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        raise SystemExit(1)

    print(
        "WT_TERRAIN_A4_PHASE2_CONTRACT_PASS "
        "next=a4_phase3_public_terrain_world_lifecycle implementation=bridge_storage_fixture"
    )


if __name__ == "__main__":
    main()
