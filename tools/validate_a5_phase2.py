#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "docs/A5_LOCAL_REFERENCE_SCENE_DEBUG_UI_PHASE2.md",
    "addons/world_transvoxel_terrain/debug/wt_terrain_reference_scene.gd",
    "addons/world_transvoxel_terrain/debug/wt_terrain_reference_scene.gd.uid",
    "addons/world_transvoxel_terrain/debug/wt_terrain_reference_scene.tscn",
    "tests/a5_phase2_reference_scene_scaffold_smoke.gd",
    "tests/a5_phase2_reference_scene_scaffold_smoke.gd.uid",
    "tools/a5_phase2_reference_scene_scaffold_smoke.py",
    "tools/validate_a5_phase2.py",
)

REQUIRED_PHRASES = {
    "docs/A5_LOCAL_REFERENCE_SCENE_DEBUG_UI_PHASE2.md": (
        "Status: complete",
        "WT_TERRAIN_A5_PHASE2_CONTRACT_PASS",
        "WT_TERRAIN_A5_PHASE2_GODOT_PASS",
        "WT_TERRAIN_A5_PHASE2_SMOKE_PASS",
        "local_reference_scene_scaffold",
        "A5 is not complete",
        "Next valid action is A5 phase 3",
    ),
    "addons/world_transvoxel_terrain/debug/wt_terrain_reference_scene.gd": (
        "class_name WtTerrainReferenceScene",
        "local_reference_scene_scaffold",
        "refresh_debug_snapshot",
        "get_reference_scene_summary",
        "get_debug_status_text",
        "DebugSnapshot",
    ),
    "addons/world_transvoxel_terrain/debug/wt_terrain_reference_scene.tscn": (
        "WtTerrainReferenceScene",
        "TerrainWorld",
        "DebugOverlay",
        "StatusLabel",
        "wt_terrain_reference_scene.gd",
    ),
    "tests/a5_phase2_reference_scene_scaffold_smoke.gd": (
        "WT_TERRAIN_A5_PHASE2_GODOT_PASS",
        "wt_terrain_reference_scene.tscn",
        "refresh_debug_snapshot",
        "profile=2048x128",
        "local_reference_scene_scaffold",
    ),
    "tools/a5_phase2_reference_scene_scaffold_smoke.py": (
        "WT_TERRAIN_A5_PHASE2_SMOKE_PASS",
        "WT_TERRAIN_A5_PHASE2_GODOT_PASS",
        "a5_phase2_reference_scene_scaffold_report.json",
    ),
    "IMPLEMENTATION_CHARTER.md": (
        "Definition of done for A5 phase 2",
        "the next finite task is A5 phase 3",
    ),
    "docs/ROADMAP.md": (
        "phase 2 complete by `WT_TERRAIN_A5_PHASE2_SMOKE_PASS`",
        "Phase 2 exit",
        "Phase 3 next",
    ),
    "README.md": (
        "WT_TERRAIN_A5_PHASE2_CONTRACT_PASS",
        "WT_TERRAIN_A5_PHASE2_SMOKE_PASS",
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
            errors.append(f"missing A5 phase 2 file: {relative}")

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
                errors.append(f"source file exceeds A5 phase 2 limit: {rel}")

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        raise SystemExit(1)

    print(
        "WT_TERRAIN_A5_PHASE2_CONTRACT_PASS "
        "next=a5_phase3_backend_reference_scene_runtime_smoke "
        "implementation=local_reference_scene_scaffold"
    )


if __name__ == "__main__":
    main()
