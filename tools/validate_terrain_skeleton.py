#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    ".gitignore",
    "LICENSE",
    "LICENSE_SCOPE.md",
    "README.md",
    "IMPLEMENTATION_CHARTER.md",
    "project.godot",
    "addons/world_transvoxel_terrain/plugin.cfg",
    "addons/world_transvoxel_terrain/editor/world_transvoxel_terrain_plugin.gd",
    "addons/world_transvoxel_terrain/LICENSE_SCOPE.md",
    "addons/world_transvoxel_terrain/README.md",
    "addons/world_transvoxel_terrain/src/README.md",
    "docs/ROADMAP.md",
    "references/README.md",
    "tests/README.md",
    "tools/validate_terrain_skeleton.py",
)

REQUIRED_PHRASES = {
    "README.md": (
        "Reusable Godot terrain addon built above `world-transvoxel`",
        "Status: A2 smoke harness complete",
        "It does not vendor or copy",
        "no separate game repository yet",
        "no large GDScript terrain hot paths",
        "WT_TERRAIN_SKELETON_PASS",
    ),
    "IMPLEMENTATION_CHARTER.md": (
        "Status: canonical project direction for the terrain addon",
        "Current phase: A2 addon-local smoke harness complete",
        "Use the official MIT-backed `world-transvoxel` backend first",
        "The independent 0BSD Transvoxel backend is deferred",
        "GDScript is not allowed for",
        "Avoid the old single-large-source-file failure mode",
        "2048 x 2048 x 64 reference-scale terrain",
        "carve, construct, fill, paint, and restore-to-base",
        "settled cold-idle behavior",
        "A1 - Public API and source-layout contract",
    ),
    "LICENSE_SCOPE.md": (
        "Project-owned code and documentation",
        "does not vendor",
        "do not copy MIT Transvoxel tables",
        "references/downloaded/",
    ),
    "addons/world_transvoxel_terrain/plugin.cfg": (
        'name="World Transvoxel Terrain"',
        'version="0.0.0-dev"',
        'script="editor/world_transvoxel_terrain_plugin.gd"',
    ),
    "docs/ROADMAP.md": (
        "A0 - Repository skeleton and contract",
        "A1 - Public API and source-layout contract",
        "A6 - Game repository readiness decision",
    ),
}

FORBIDDEN_PATH_PARTS = (
    "addons/world_transvoxel/",
    "thirdparty/transvoxel_mit/",
)

FORBIDDEN_NAMES = {
    "Transvoxel.cpp",
    "Transvoxel.h",
}


def normalized(relative: Path) -> str:
    return relative.as_posix()


def has_phrase(text: str, phrase: str) -> bool:
    return phrase in text or phrase in " ".join(text.split())


def iter_repo_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if ".git" in relative.parts:
            continue
        if "__pycache__" in relative.parts:
            continue
        if relative.as_posix().startswith("artifacts/"):
            continue
        if relative.as_posix().startswith("references/downloaded/"):
            continue
        if path.is_file():
            files.append(relative)
    return files


def main() -> None:
    errors: list[str] = []

    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")

    for relative, phrases in REQUIRED_PHRASES.items():
        path = ROOT / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if not has_phrase(text, phrase):
                errors.append(f"{relative} missing phrase: {phrase}")

    for relative in iter_repo_files():
        rel = normalized(relative)
        for part in FORBIDDEN_PATH_PARTS:
            if part in rel:
                errors.append(f"forbidden vendored dependency path present: {rel}")
        if relative.name in FORBIDDEN_NAMES:
            errors.append(f"forbidden MIT Transvoxel source name present: {rel}")
        if relative.stat().st_size > 256 * 1024:
            errors.append(f"skeleton file is unexpectedly large: {rel}")

    plugin_text = (ROOT / "addons/world_transvoxel_terrain/plugin.cfg").read_text(
        encoding="utf-8"
    )
    editor_script = "addons/world_transvoxel_terrain/editor/world_transvoxel_terrain_plugin.gd"
    if editor_script not in plugin_text and "editor/world_transvoxel_terrain_plugin.gd" not in plugin_text:
        errors.append("plugin.cfg does not point at the terrain editor plugin")

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        raise SystemExit(1)

    print(
        "WT_TERRAIN_SKELETON_PASS "
        "addon=world-transvoxel-terrain implementation=deferred "
        "game_repository=deferred"
    )


if __name__ == "__main__":
    main()
