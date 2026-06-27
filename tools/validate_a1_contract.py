#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "docs/A1_PUBLIC_API_SOURCE_LAYOUT_CONTRACT.md",
    "docs/A1_MARCHING_CUBES_AUDIT.md",
    "references/MANIFEST.md",
    "addons/world_transvoxel_terrain/api/README.md",
    "addons/world_transvoxel_terrain/runtime/README.md",
    "addons/world_transvoxel_terrain/generation/README.md",
    "addons/world_transvoxel_terrain/streaming/README.md",
    "addons/world_transvoxel_terrain/edit/README.md",
    "addons/world_transvoxel_terrain/storage/README.md",
    "addons/world_transvoxel_terrain/material/README.md",
    "addons/world_transvoxel_terrain/collision/README.md",
    "addons/world_transvoxel_terrain/debug/README.md",
    "addons/world_transvoxel_terrain/tests/README.md",
)

REQUIRED_PHRASES = {
    "docs/A1_PUBLIC_API_SOURCE_LAYOUT_CONTRACT.md": (
        "Status: complete",
        "WT_TERRAIN_A1_CONTRACT_PASS",
        "WtTerrainWorld",
        "WtTerrainProfile",
        "WtTerrainEditOperation",
        "Edits are commands, not unbounded additive density deltas",
        "Settled terrain must be cold",
        "addons/world_transvoxel_terrain/",
        "A2 must detect the dependency",
        "next work is A2 addon-local smoke harness",
    ),
    "docs/A1_MARCHING_CUBES_AUDIT.md": (
        "Status: complete for A1 contract input",
        "chunk_manager.gd",
        "9,116 lines",
        "356 `func` declarations",
        "109 exported properties",
        "One node owns too many subsystems",
        "Hot terrain policy lives in GDScript",
        "Optional systems are fused into core terrain",
        "Physical overlap is used as a seam fix",
        "validate its source layout in Python",
    ),
    "references/MANIFEST.md": (
        "Status: A1 pinned/downloaded references",
        "https://transvoxel.org/",
        "Lengyel-VoxelTerrain.pdf",
        "gdextension_cpp_example.html",
        "Compute remains",
        "old_marching_cubes_project",
        "Do not copy MIT Transvoxel lookup data",
    ),
    "IMPLEMENTATION_CHARTER.md": (
        "A1 - Public API and source-layout contract",
        "inspect the old marching-cubes project",
        "download/reference required papers",
    ),
    "docs/ROADMAP.md": (
        "A1 - Public API and source-layout contract",
        "required references are downloaded or pinned",
    ),
}

REQUIRED_IGNORES = (
    "references/downloaded/",
)

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
        if ".git" in relative.parts:
            continue
        if "__pycache__" in relative.parts:
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
            errors.append(f"missing A1 file: {relative}")

    for relative, phrases in REQUIRED_PHRASES.items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing phrase input: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if not has_phrase(text, phrase):
                errors.append(f"{relative} missing phrase: {phrase}")

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for ignore in REQUIRED_IGNORES:
        if ignore not in gitignore:
            errors.append(f".gitignore missing required ignore: {ignore}")

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
                errors.append(f"source file exceeds A1 skeleton limit: {rel}")

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        raise SystemExit(1)

    print(
        "WT_TERRAIN_A1_CONTRACT_PASS "
        "next=a2_addon_local_smoke_harness implementation=contract_only"
    )


if __name__ == "__main__":
    main()
