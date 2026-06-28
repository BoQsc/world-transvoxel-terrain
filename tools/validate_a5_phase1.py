#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "docs/A5_LOCAL_REFERENCE_SCENE_DEBUG_UI_PHASE1.md",
    "addons/world_transvoxel_terrain/debug/wt_terrain_debug_snapshot.gd",
    "addons/world_transvoxel_terrain/debug/wt_terrain_debug_snapshot.gd.uid",
    "tests/a5_phase1_debug_snapshot_smoke.gd",
    "tests/a5_phase1_debug_snapshot_smoke.gd.uid",
    "tools/a5_phase1_debug_snapshot_smoke.py",
    "tools/validate_a5_phase1.py",
)

REQUIRED_PHRASES = {
    "docs/A5_LOCAL_REFERENCE_SCENE_DEBUG_UI_PHASE1.md": (
        "Status: complete",
        "WT_TERRAIN_A5_PHASE1_CONTRACT_PASS",
        "WT_TERRAIN_A5_PHASE1_GODOT_PASS",
        "WT_TERRAIN_A5_PHASE1_SMOKE_PASS",
        "debug_snapshot_contract",
        "A5 is not complete",
        "Next valid action is A5 phase 2",
    ),
    "addons/world_transvoxel_terrain/debug/wt_terrain_debug_snapshot.gd": (
        "class_name WtTerrainDebugSnapshot",
        "debug_snapshot_contract",
        "terrain_profile",
        "generation_profile",
        "storage_profile",
        "recovery_policy",
        "budget",
        "collision",
        "streaming",
        "edit",
        "material",
    ),
    "tests/a5_phase1_debug_snapshot_smoke.gd": (
        "WT_TERRAIN_A5_PHASE1_GODOT_PASS",
        "DebugSnapshot.capture",
        "categories=%d",
        "profile=2048x64",
        "a5_phase1_material_policy_not_configured",
    ),
    "tools/a5_phase1_debug_snapshot_smoke.py": (
        "WT_TERRAIN_A5_PHASE1_SMOKE_PASS",
        "WT_TERRAIN_A5_PHASE1_GODOT_PASS",
        "a5_phase1_debug_snapshot_report.json",
    ),
    "IMPLEMENTATION_CHARTER.md": (
        "Current phase: A5 phase 1 debug snapshot contract complete",
        "Next phase is A5 phase 2 local reference scene scaffold",
        "Definition of done for A5 phase 1",
    ),
    "docs/ROADMAP.md": (
        "Status: active. Phase 1 complete by `WT_TERRAIN_A5_PHASE1_SMOKE_PASS`",
        "Phase 1 exit",
        "Phase 2 next",
    ),
    "README.md": (
        "Status: A5 phase 1 debug snapshot contract complete",
        "WT_TERRAIN_A5_PHASE1_CONTRACT_PASS",
        "WT_TERRAIN_A5_PHASE1_SMOKE_PASS",
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
            errors.append(f"missing A5 phase 1 file: {relative}")

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
                errors.append(f"source file exceeds A5 phase 1 limit: {rel}")

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        raise SystemExit(1)

    print(
        "WT_TERRAIN_A5_PHASE1_CONTRACT_PASS "
        "next=a5_phase2_local_reference_scene_scaffold implementation=debug_snapshot_contract"
    )


if __name__ == "__main__":
    main()
