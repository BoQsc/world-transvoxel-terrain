#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "docs/A2_ADDON_SMOKE_HARNESS.md",
    "addons/world_transvoxel_terrain/api/wt_terrain_dependency_status.gd",
    "addons/world_transvoxel_terrain/api/wt_terrain_dependency_status.gd.uid",
    "addons/world_transvoxel_terrain/api/wt_terrain_profile.gd",
    "addons/world_transvoxel_terrain/api/wt_terrain_profile.gd.uid",
    "addons/world_transvoxel_terrain/generation/wt_terrain_generation_profile.gd",
    "addons/world_transvoxel_terrain/generation/wt_terrain_generation_profile.gd.uid",
    "addons/world_transvoxel_terrain/runtime/wt_terrain_world.gd",
    "addons/world_transvoxel_terrain/runtime/wt_terrain_world.gd.uid",
    "addons/world_transvoxel_terrain/editor/world_transvoxel_terrain_plugin.gd.uid",
    "tests/a2_addon_smoke.gd",
    "tests/a2_addon_smoke.gd.uid",
    "tools/a2_addon_smoke.py",
    "tools/validate_a2_smoke.py",
)

REQUIRED_PHRASES = {
    "docs/A2_ADDON_SMOKE_HARNESS.md": (
        "Status: complete",
        "WT_TERRAIN_A2_SMOKE_PASS",
        "WT_TERRAIN_A2_GODOT_SMOKE_PASS",
        "dependency detection",
        "without vendoring",
        "placeholder_contract_only",
        "`.gd.uid` files",
        "Next valid action is A3",
    ),
    "addons/world_transvoxel_terrain/api/wt_terrain_dependency_status.gd": (
        "class_name WtTerrainDependencyStatus",
        "WORLD_TRANSVOXEL_PLUGIN_CFG",
        "res://addons/world_transvoxel/plugin.cfg",
        "installed",
    ),
    "addons/world_transvoxel_terrain/api/wt_terrain_profile.gd": (
        "class_name WtTerrainProfile",
        "horizontal_cells: int = 2048",
        "vertical_cells: int = 64",
        "finite_closed_boundary",
    ),
    "addons/world_transvoxel_terrain/generation/wt_terrain_generation_profile.gd": (
        "class_name WtTerrainGenerationProfile",
        "DETERMINISTIC_REFERENCE",
        "supports_underground_volume",
    ),
    "addons/world_transvoxel_terrain/runtime/wt_terrain_world.gd": (
        "class_name WtTerrainWorld",
        "get_dependency_status",
        "get_contract_summary",
    ),
    "tests/a2_addon_smoke.gd": (
        "WT_TERRAIN_A2_GODOT_SMOKE_PASS",
        "dependency_installed",
        "profile=2048x64",
        "placeholder_contract_only",
    ),
    "tools/a2_addon_smoke.py": (
        "WT_TERRAIN_A2_SMOKE_PASS",
        "WT_TERRAIN_A2_GODOT_SMOKE_PASS",
        "--headless",
        "--script",
    ),
}

FORBIDDEN_PATH_PARTS = (
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
        if relative.as_posix().startswith("artifacts/"):
            continue
        if path.is_file():
            files.append(relative)
    return files


def main() -> None:
    errors: list[str] = []

    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            errors.append(f"missing A2 file: {relative}")

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
        for forbidden in FORBIDDEN_PATH_PARTS:
            if forbidden in rel:
                errors.append(f"forbidden dependency path in repo: {rel}")
        if relative.name in {"Transvoxel.cpp", "Transvoxel.h"}:
            errors.append(f"forbidden MIT Transvoxel source name in repo: {rel}")
        if relative.suffix in {".gd", ".glsl", ".gdshader"}:
            lines = (ROOT / relative).read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()
            if len(lines) > 300:
                errors.append(f"source file exceeds A2 smoke limit: {rel}")

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        raise SystemExit(1)

    print(
        "WT_TERRAIN_A2_CONTRACT_PASS "
        "next=a3_world_transvoxel_bridge implementation=smoke_only"
    )


if __name__ == "__main__":
    main()
