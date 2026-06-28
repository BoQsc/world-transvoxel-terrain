#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "docs/A5_LOCAL_REFERENCE_SCENE_DEBUG_UI_PHASE4.md",
    "addons/world_transvoxel_terrain/debug/wt_terrain_debug_overlay_formatter.gd",
    "addons/world_transvoxel_terrain/debug/wt_terrain_debug_overlay_formatter.gd.uid",
    "tests/a5_phase4_debug_overlay_categories_smoke.gd",
    "tests/a5_phase4_debug_overlay_categories_smoke.gd.uid",
    "tools/a5_phase4_debug_overlay_categories_smoke.py",
    "tools/validate_a5_phase4.py",
)

REQUIRED_PHRASES = {
    "docs/A5_LOCAL_REFERENCE_SCENE_DEBUG_UI_PHASE4.md": (
        "Status: complete",
        "WT_TERRAIN_A5_PHASE4_CONTRACT_PASS",
        "WT_TERRAIN_A5_PHASE4_GODOT_PASS",
        "WT_TERRAIN_A5_PHASE4_SMOKE_PASS",
        "debug_overlay_category_rendering",
        "Next valid action is A5 phase 5",
    ),
    "addons/world_transvoxel_terrain/debug/wt_terrain_debug_overlay_formatter.gd": (
        "class_name WtTerrainDebugOverlayFormatter",
        "debug_overlay_category_rendering",
        "CATEGORY_ORDER",
        "world",
        "terrain_profile",
        "storage_profile",
        "budget",
        "collision",
        "streaming",
        "edit",
        "material",
    ),
    "addons/world_transvoxel_terrain/debug/wt_terrain_reference_scene.gd": (
        "DebugOverlayFormatter",
        "get_debug_overlay_categories",
        "debug_overlay_category_rendering",
    ),
    "tests/a5_phase4_debug_overlay_categories_smoke.gd": (
        "WT_TERRAIN_A5_PHASE4_GODOT_PASS",
        "REQUIRED_SECTIONS",
        "render_resources=1",
        "collision_resources=1",
        "overlay_implementation=debug_overlay_category_rendering",
    ),
    "tools/a5_phase4_debug_overlay_categories_smoke.py": (
        "WT_TERRAIN_A5_PHASE4_SMOKE_PASS",
        "WT_TERRAIN_A5_PHASE4_GODOT_PASS",
        "production-lifecycle-fixture",
        "a5_phase4_debug_overlay_categories_report.json",
    ),
    "IMPLEMENTATION_CHARTER.md": (
        "Current phase: A5 phase 4 debug overlay category rendering complete",
        "Next phase is A5 phase 5 A5 exit review",
        "Definition of done for A5 phase 4",
    ),
    "docs/ROADMAP.md": (
        "phase 4 complete by `WT_TERRAIN_A5_PHASE4_SMOKE_PASS`",
        "Phase 4 exit",
        "Phase 5 next",
    ),
    "README.md": (
        "Status: A5 phase 4 debug overlay category rendering complete",
        "WT_TERRAIN_A5_PHASE4_CONTRACT_PASS",
        "WT_TERRAIN_A5_PHASE4_SMOKE_PASS",
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
            errors.append(f"missing A5 phase 4 file: {relative}")

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
                errors.append(f"source file exceeds A5 phase 4 limit: {rel}")

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        raise SystemExit(1)

    print(
        "WT_TERRAIN_A5_PHASE4_CONTRACT_PASS "
        "next=a5_phase5_a5_exit_review implementation=debug_overlay_category_rendering"
    )


if __name__ == "__main__":
    main()
