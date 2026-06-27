#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "docs/A4_PROFILE_EDIT_STORAGE_RECOVERY_PHASE1.md",
    "addons/world_transvoxel_terrain/edit/wt_terrain_edit_operation.gd",
    "addons/world_transvoxel_terrain/edit/wt_terrain_edit_operation.gd.uid",
    "addons/world_transvoxel_terrain/edit/wt_terrain_edit_batch.gd",
    "addons/world_transvoxel_terrain/edit/wt_terrain_edit_batch.gd.uid",
    "addons/world_transvoxel_terrain/storage/wt_terrain_storage_profile.gd",
    "addons/world_transvoxel_terrain/storage/wt_terrain_storage_profile.gd.uid",
    "addons/world_transvoxel_terrain/storage/wt_terrain_recovery_policy.gd",
    "addons/world_transvoxel_terrain/storage/wt_terrain_recovery_policy.gd.uid",
    "tests/a4_phase1_resources_smoke.gd",
    "tests/a4_phase1_resources_smoke.gd.uid",
    "tools/a4_phase1_resources_smoke.py",
    "tools/validate_a4_phase1.py",
)

REQUIRED_PHRASES = {
    "docs/A4_PROFILE_EDIT_STORAGE_RECOVERY_PHASE1.md": (
        "Status: complete",
        "WT_TERRAIN_A4_PHASE1_CONTRACT_PASS",
        "WT_TERRAIN_A4_PHASE1_GODOT_PASS",
        "WT_TERRAIN_A4_PHASE1_SMOKE_PASS",
        "resource_semantics_only",
        "A4 is not complete",
        "Next valid action is A4 phase 2",
    ),
    "addons/world_transvoxel_terrain/edit/wt_terrain_edit_operation.gd": (
        "class_name WtTerrainEditOperation",
        "CARVE",
        "CONSTRUCT",
        "FILL",
        "PAINT",
        "RESTORE_TO_BASE",
        "estimate_affected_aabb",
        "to_bridge_command",
        "resource_semantics_only",
    ),
    "addons/world_transvoxel_terrain/edit/wt_terrain_edit_batch.gd": (
        "class_name WtTerrainEditBatch",
        "add_operation",
        "to_bridge_commands",
    ),
    "addons/world_transvoxel_terrain/storage/wt_terrain_storage_profile.gd": (
        "class_name WtTerrainStorageProfile",
        "world_manifest_path",
        "edit_journal_path",
        "journal_format_version",
        "res://",
    ),
    "addons/world_transvoxel_terrain/storage/wt_terrain_recovery_policy.gd": (
        "class_name WtTerrainRecoveryPolicy",
        "allows_restore_to_base",
        "is_cold_idle_default",
        "automatic_timed_regeneration_enabled",
        "fluid_equilibrium_enabled",
    ),
    "addons/world_transvoxel_terrain/runtime/wt_terrain_world.gd": (
        "storage_profile",
        "recovery_policy",
        "get_a4_phase1_summary",
        "a4_phase1_resource_semantics_only",
    ),
    "tests/a4_phase1_resources_smoke.gd": (
        "WT_TERRAIN_A4_PHASE1_GODOT_PASS",
        "operations=5",
        "storage=valid",
        "recovery=cold_idle",
        "resource_semantics_only",
    ),
    "tools/a4_phase1_resources_smoke.py": (
        "WT_TERRAIN_A4_PHASE1_SMOKE_PASS",
        "WT_TERRAIN_A4_PHASE1_GODOT_PASS",
        "a4_phase1_resources_report.json",
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
            errors.append(f"missing A4 phase 1 file: {relative}")

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
                errors.append(f"source file exceeds A4 phase 1 limit: {rel}")

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        raise SystemExit(1)

    print(
        "WT_TERRAIN_A4_PHASE1_CONTRACT_PASS "
        "next=a4_phase2_bridge_edit_submission implementation=resource_semantics_only"
    )


if __name__ == "__main__":
    main()
