#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "docs/A5_LOCAL_REFERENCE_SCENE_DEBUG_UI_PHASE5_EXIT_REVIEW.md",
    "tools/a5_phase5_exit_review.py",
    "tools/validate_a5_phase5.py",
)

REQUIRED_PHRASES = {
    "docs/A5_LOCAL_REFERENCE_SCENE_DEBUG_UI_PHASE5_EXIT_REVIEW.md": (
        "Status: complete",
        "WT_TERRAIN_A5_PHASE5_CONTRACT_PASS",
        "WT_TERRAIN_A5_PHASE5_EXIT_REVIEW_PASS",
        "A5 closes at the addon-local reference scene",
        "next valid milestone is A6",
        "WtTerrainDebugSnapshot",
        "wt_terrain_reference_scene.tscn",
        "does not vendor `world-transvoxel`",
        "A6 owns the decision",
    ),
    "IMPLEMENTATION_CHARTER.md": (
        "Definition of done for A5 phase 5",
        "A5 is complete",
        "Definition of done for A6",
    ),
    "docs/ROADMAP.md": (
        "## A5 - Local reference scene and debug UI",
        "Status: complete",
        "Phase 5 exit",
        "## A6 - Game repository readiness decision",
        "WT_TERRAIN_A6_READINESS_DECISION_PASS",
    ),
    "README.md": (
        "WT_TERRAIN_A5_PHASE5_CONTRACT_PASS",
        "WT_TERRAIN_A5_PHASE5_EXIT_REVIEW_PASS",
        "python tools/a5_phase5_exit_review.py",
    ),
    "tools/a5_phase5_exit_review.py": (
        "WT_TERRAIN_A5_PHASE5_EXIT_REVIEW_PASS",
        "WT_TERRAIN_A5_PHASE5_CONTRACT_PASS",
        "WT_TERRAIN_A5_PHASE4_SMOKE_PASS",
        "a6_game_repository_readiness_decision",
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
            errors.append(f"missing A5 phase 5 file: {relative}")

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
                errors.append(f"source file exceeds A5 phase 5 limit: {rel}")

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        raise SystemExit(1)

    print(
        "WT_TERRAIN_A5_PHASE5_CONTRACT_PASS "
        "next=a6_game_repository_readiness_decision implementation=a5_exit_review"
    )


if __name__ == "__main__":
    main()
