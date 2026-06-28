#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "docs/A4_PROFILE_EDIT_STORAGE_RECOVERY_PHASE4.md",
    "tests/a4_phase4_reference_runtime_cold_idle_smoke.gd",
    "tests/a4_phase4_reference_runtime_cold_idle_smoke.gd.uid",
    "tools/a4_phase4_reference_runtime_cold_idle_smoke.py",
    "tools/validate_a4_phase4.py",
    "addons/world_transvoxel_terrain/runtime/wt_terrain_runtime_audit.gd",
    "addons/world_transvoxel_terrain/runtime/wt_terrain_runtime_audit.gd.uid",
)

REQUIRED_PHRASES = {
    "docs/A4_PROFILE_EDIT_STORAGE_RECOVERY_PHASE4.md": (
        "Status: complete",
        "WT_TERRAIN_A4_PHASE4_CONTRACT_PASS",
        "WT_TERRAIN_A4_PHASE4_GODOT_PASS",
        "WT_TERRAIN_A4_PHASE4_SMOKE_PASS",
        "reference_profile_runtime_cold_idle",
        "A4 is not complete",
        "Next valid action is A4 phase 5",
    ),
    "addons/world_transvoxel_terrain/runtime/wt_terrain_world.gd": (
        "class_name WtTerrainWorld",
        "update_viewer",
        "remove_viewer",
        "query_chunk_state",
        "get_runtime_metrics",
        "is_cold_idle",
        "get_cold_idle_summary",
        "reference_profile_runtime_cold_idle",
    ),
    "addons/world_transvoxel_terrain/runtime/wt_terrain_runtime_audit.gd": (
        "class_name WtTerrainRuntimeAudit",
        "terrain_world_runtime_metrics",
        "terrain_world_cold_idle",
        "pending_chunk_retirements",
        "fully_ready_chunk_records",
    ),
    "tests/a4_phase4_reference_runtime_cold_idle_smoke.gd": (
        "WT_TERRAIN_A4_PHASE4_GODOT_PASS",
        "TerrainProfile.new",
        "update_viewer",
        "query_chunk_state",
        "is_cold_idle",
        "remove_viewer",
        "cold_idle=stable",
    ),
    "tools/a4_phase4_reference_runtime_cold_idle_smoke.py": (
        "WT_TERRAIN_A4_PHASE4_SMOKE_PASS",
        "WT_TERRAIN_A4_PHASE4_GODOT_PASS",
        "production-lifecycle-fixture",
        "a4_phase4_reference_runtime_cold_idle_report.json",
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
            errors.append(f"missing A4 phase 4 file: {relative}")

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
                errors.append(f"source file exceeds A4 phase 4 limit: {rel}")

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        raise SystemExit(1)

    print(
        "WT_TERRAIN_A4_PHASE4_CONTRACT_PASS "
        "next=a4_phase5_a4_exit_review implementation=reference_profile_runtime_cold_idle"
    )


if __name__ == "__main__":
    main()
