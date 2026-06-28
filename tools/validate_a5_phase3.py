#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "docs/A5_LOCAL_REFERENCE_SCENE_DEBUG_UI_PHASE3.md",
    "tests/a5_phase3_reference_scene_runtime_smoke.gd",
    "tests/a5_phase3_reference_scene_runtime_smoke.gd.uid",
    "tools/a5_phase3_reference_scene_runtime_smoke.py",
    "tools/validate_a5_phase3.py",
)

REQUIRED_PHRASES = {
    "docs/A5_LOCAL_REFERENCE_SCENE_DEBUG_UI_PHASE3.md": (
        "Status: complete",
        "WT_TERRAIN_A5_PHASE3_CONTRACT_PASS",
        "WT_TERRAIN_A5_PHASE3_GODOT_PASS",
        "WT_TERRAIN_A5_PHASE3_SMOKE_PASS",
        "backend_reference_scene_runtime_smoke",
        "A5 is not complete",
        "Next valid action is A5 phase 4",
    ),
    "addons/world_transvoxel_terrain/debug/wt_terrain_reference_scene.gd": (
        "start_reference_backend_world",
        "stop_reference_backend_world",
        "update_reference_viewer",
        "remove_reference_viewer",
        "get_reference_runtime_summary",
        "backend_reference_scene_runtime_smoke",
        "render_resources",
        "collision_resources",
    ),
    "tests/a5_phase3_reference_scene_runtime_smoke.gd": (
        "WT_TERRAIN_A5_PHASE3_GODOT_PASS",
        "wt_terrain_reference_scene.tscn",
        "start_reference_backend_world",
        "update_reference_viewer",
        "remove_reference_viewer",
        "backend_reference_scene_runtime_smoke",
        "render_resources=1",
    ),
    "tools/a5_phase3_reference_scene_runtime_smoke.py": (
        "WT_TERRAIN_A5_PHASE3_SMOKE_PASS",
        "WT_TERRAIN_A5_PHASE3_GODOT_PASS",
        "production-lifecycle-fixture",
        "a5_phase3_reference_scene_runtime_report.json",
    ),
    "IMPLEMENTATION_CHARTER.md": (
        "Current phase: A5 phase 3 backend reference-scene runtime smoke complete",
        "Next phase is A5 phase 4 debug overlay category rendering",
        "Definition of done for A5 phase 3",
    ),
    "docs/ROADMAP.md": (
        "phase 3 complete by `WT_TERRAIN_A5_PHASE3_SMOKE_PASS`",
        "Phase 3 exit",
        "Phase 4 next",
    ),
    "README.md": (
        "Status: A5 phase 3 backend reference-scene runtime smoke complete",
        "WT_TERRAIN_A5_PHASE3_CONTRACT_PASS",
        "WT_TERRAIN_A5_PHASE3_SMOKE_PASS",
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
            errors.append(f"missing A5 phase 3 file: {relative}")

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
                errors.append(f"source file exceeds A5 phase 3 limit: {rel}")

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        raise SystemExit(1)

    print(
        "WT_TERRAIN_A5_PHASE3_CONTRACT_PASS "
        "next=a5_phase4_debug_overlay_category_rendering "
        "implementation=backend_reference_scene_runtime_smoke"
    )


if __name__ == "__main__":
    main()
