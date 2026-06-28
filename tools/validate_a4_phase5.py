#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "docs/A4_PROFILE_EDIT_STORAGE_RECOVERY_PHASE5_EXIT_REVIEW.md",
    "tools/a4_phase5_exit_review.py",
    "tools/validate_a4_phase5.py",
)

REQUIRED_PHRASES = {
    "docs/A4_PROFILE_EDIT_STORAGE_RECOVERY_PHASE5_EXIT_REVIEW.md": (
        "Status: complete",
        "WT_TERRAIN_A4_PHASE5_CONTRACT_PASS",
        "WT_TERRAIN_A4_PHASE5_EXIT_REVIEW_PASS",
        "A4 closes at the terrain-addon API",
        "next valid milestone is A5",
        "2048 x 2048 x 64 reference profile",
        "carve, construct, fill, paint, and restore-to-base",
        "edit persistence is verified",
        "cold idle",
        "A5 owns the local reference scene and debug UI",
    ),
    "IMPLEMENTATION_CHARTER.md": (
        "Definition of done for A4 phase 5",
        "A4 is complete",
        "WT_TERRAIN_A4_PHASE5_EXIT_REVIEW_PASS",
    ),
    "docs/ROADMAP.md": (
        "## A4 - Terrain profile, edit, storage, and recovery",
        "Status: complete",
        "Phase 5 exit",
        "## A5 - Local reference scene and debug UI",
        "WT_TERRAIN_A5_PHASE5_EXIT_REVIEW_PASS",
    ),
    "README.md": (
        "WT_TERRAIN_A4_PHASE5_CONTRACT_PASS",
        "WT_TERRAIN_A4_PHASE5_EXIT_REVIEW_PASS",
        "python tools/a4_phase5_exit_review.py",
    ),
    "tools/a4_phase5_exit_review.py": (
        "WT_TERRAIN_A4_PHASE5_EXIT_REVIEW_PASS",
        "WT_TERRAIN_A4_PHASE5_CONTRACT_PASS",
        "WT_TERRAIN_A4_PHASE4_SMOKE_PASS",
        "a5_local_reference_scene_debug_ui",
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
            errors.append(f"missing A4 phase 5 file: {relative}")

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
                errors.append(f"source file exceeds A4 phase 5 limit: {rel}")

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        raise SystemExit(1)

    print(
        "WT_TERRAIN_A4_PHASE5_CONTRACT_PASS "
        "next=a5_local_reference_scene_debug_ui implementation=a4_exit_review"
    )


if __name__ == "__main__":
    main()
