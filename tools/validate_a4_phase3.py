#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "docs/A4_PROFILE_EDIT_STORAGE_RECOVERY_PHASE3.md",
    "tests/a4_phase3_terrain_world_lifecycle_smoke.gd",
    "tests/a4_phase3_terrain_world_lifecycle_smoke.gd.uid",
    "tools/a4_phase3_terrain_world_lifecycle_smoke.py",
    "tools/validate_a4_phase3.py",
)

REQUIRED_PHRASES = {
    "docs/A4_PROFILE_EDIT_STORAGE_RECOVERY_PHASE3.md": (
        "Status: complete",
        "WT_TERRAIN_A4_PHASE3_CONTRACT_PASS",
        "WT_TERRAIN_A4_PHASE3_GODOT_PASS",
        "WT_TERRAIN_A4_PHASE3_SMOKE_PASS",
        "terrain_world_lifecycle",
        "A4 is not complete",
        "Next valid action is A4 phase 4",
    ),
    "addons/world_transvoxel_terrain/runtime/wt_terrain_world.gd": (
        "class_name WtTerrainWorld",
        "start_backend_world",
        "stop_backend_world",
        "submit_edit_batch",
        "get_backend_terrain",
        "get_backend_world_state_name",
        "terrain_world_lifecycle",
    ),
    "addons/world_transvoxel_terrain/storage/wt_terrain_storage_profile.gd": (
        "object_root_path",
        "allow_res_paths_for_test_fixtures",
    ),
    "tests/a4_phase3_terrain_world_lifecycle_smoke.gd": (
        "WT_TERRAIN_A4_PHASE3_GODOT_PASS",
        "start_backend_world",
        "submit_edit_batch",
        "stop_backend_world",
        "journal=replayed",
    ),
    "tools/a4_phase3_terrain_world_lifecycle_smoke.py": (
        "WT_TERRAIN_A4_PHASE3_SMOKE_PASS",
        "WT_TERRAIN_A4_PHASE3_GODOT_PASS",
        "production-lifecycle-fixture",
        "a4_phase3_terrain_world_lifecycle_report.json",
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
            errors.append(f"missing A4 phase 3 file: {relative}")

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
                errors.append(f"source file exceeds A4 phase 3 limit: {rel}")

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        raise SystemExit(1)

    print(
        "WT_TERRAIN_A4_PHASE3_CONTRACT_PASS "
        "next=a4_phase4_reference_profile_runtime_cold_idle implementation=terrain_world_lifecycle"
    )


if __name__ == "__main__":
    main()
