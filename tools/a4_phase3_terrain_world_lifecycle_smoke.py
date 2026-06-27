#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
WORLD_TRANSVOXEL_REPO = ROOT.parent / "world-transvoxel"
WORLD_TRANSVOXEL_ADDON = WORLD_TRANSVOXEL_REPO / "addons" / "world_transvoxel"
LIFECYCLE_FIXTURE = WORLD_TRANSVOXEL_REPO / "build" / "production-lifecycle-fixture"
ARTIFACT_ROOT = ROOT / "artifacts" / "a4_phase3_terrain_world_lifecycle"
FIXTURE_ROOT = ARTIFACT_ROOT / "project"
SCRIPT = "res://tests/a4_phase3_terrain_world_lifecycle_smoke.gd"
MARKER = "WT_TERRAIN_A4_PHASE3_GODOT_PASS"
ENGINE_VERSIONS = ("4.6.3", "4.7")

DEPENDENCY_FILES = (
    "plugin.cfg",
    "world_transvoxel.gdextension",
    "world_transvoxel.gdextension.uid",
    "LICENSE_SCOPE.md",
    "PUBLIC_API.md",
    "README.md",
    "OPERATING_LIMITS.md",
    "thirdparty/transvoxel_mit/LICENSE",
    "bin/world_transvoxel.windows.template_debug.x86_64.dll",
    "bin/world_transvoxel.windows.template_release.x86_64.dll",
)


def discover_engines(explicit: list[Path]) -> list[tuple[str, Path]]:
    if explicit:
        return [(path.stem, path.resolve()) for path in explicit]

    sibling = WORLD_TRANSVOXEL_REPO / ".tools" / "godot"
    discovered: list[tuple[str, Path]] = []
    for version in ENGINE_VERSIONS:
        folder = sibling / version
        candidates = sorted(folder.glob("Godot*_win64.exe"))
        if candidates:
            discovered.append((version, candidates[0].resolve()))
    if discovered:
        return discovered

    environment = os.environ.get("GODOT")
    if environment:
        return [("environment", Path(environment).resolve())]

    executable = shutil.which("godot")
    if executable:
        return [("path", Path(executable).resolve())]

    raise RuntimeError("No Godot executable found. Pass --godot or set GODOT.")


def copy_file(source: Path, target: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def prepare_fixture() -> None:
    if not LIFECYCLE_FIXTURE.is_dir() or not (LIFECYCLE_FIXTURE / "streaming.wtworld").is_file():
        raise RuntimeError(f"Missing world-transvoxel lifecycle fixture: {LIFECYCLE_FIXTURE}")
    if FIXTURE_ROOT.exists():
        shutil.rmtree(FIXTURE_ROOT)
    (FIXTURE_ROOT / "addons").mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        ROOT / "addons" / "world_transvoxel_terrain",
        FIXTURE_ROOT / "addons" / "world_transvoxel_terrain",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    for relative in DEPENDENCY_FILES:
        copy_file(
            WORLD_TRANSVOXEL_ADDON / relative,
            FIXTURE_ROOT / "addons" / "world_transvoxel" / relative,
        )
    shutil.copytree(
        LIFECYCLE_FIXTURE,
        FIXTURE_ROOT / "build" / "production-lifecycle-fixture",
        ignore=shutil.ignore_patterns("world.wtedit"),
    )
    copy_file(
        ROOT / "tests" / "a4_phase3_terrain_world_lifecycle_smoke.gd",
        FIXTURE_ROOT / "tests" / "a4_phase3_terrain_world_lifecycle_smoke.gd",
    )
    (FIXTURE_ROOT / "project.godot").write_text(
        "\n".join(
            [
                "config_version=5",
                "",
                "[application]",
                'config/name="World Transvoxel Terrain A4 Phase 3 Fixture"',
                'config/features=PackedStringArray("4.6", "Forward Plus")',
                "",
                "[editor_plugins]",
                'enabled=PackedStringArray("res://addons/world_transvoxel_terrain/plugin.cfg")',
                "",
            ]
        ),
        encoding="utf-8",
    )


def has_godot_error(combined: str) -> bool:
    return (
        "SCRIPT ERROR:" in combined
        or combined.startswith("ERROR:")
        or "\nERROR:" in combined
    )


def run_import(version: str, engine: Path) -> None:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    extension_cache = FIXTURE_ROOT / ".godot" / "extension_list.cfg"
    attempts: list[str] = []
    result: subprocess.CompletedProcess[str] | None = None
    for _attempt in range(2):
        result = subprocess.run(
            [str(engine), "--headless", "--path", str(FIXTURE_ROOT), "--import"],
            cwd=FIXTURE_ROOT,
            check=False,
            text=True,
            capture_output=True,
            errors="replace",
            timeout=120,
        )
        combined_attempt = result.stdout + result.stderr
        attempts.append(combined_attempt)
        cache_valid = (
            extension_cache.is_file()
            and "res://addons/world_transvoxel/world_transvoxel.gdextension"
            in extension_cache.read_text(encoding="utf-8")
        )
        if result.returncode == 0 and cache_valid and not has_godot_error(combined_attempt):
            break
        if has_godot_error(combined_attempt) or not cache_valid:
            break
    combined = "\n".join(attempts)
    (ARTIFACT_ROOT / f"godot-{version}-import.stdout.txt").write_text(
        combined, encoding="utf-8"
    )
    (ARTIFACT_ROOT / f"godot-{version}-import.stderr.txt").write_text(
        result.stderr if result is not None else "", encoding="utf-8"
    )
    if (
        result is None
        or result.returncode != 0
        or has_godot_error(combined)
        or not extension_cache.is_file()
        or "res://addons/world_transvoxel/world_transvoxel.gdextension"
        not in extension_cache.read_text(encoding="utf-8")
    ):
        raise RuntimeError(f"A4 phase 3 fixture import failed on {version}")


def run_smoke(version: str, engine: Path) -> dict[str, object]:
    result = subprocess.run(
        [str(engine), "--headless", "--path", str(FIXTURE_ROOT), "--script", SCRIPT],
        cwd=FIXTURE_ROOT,
        check=False,
        text=True,
        capture_output=True,
        errors="replace",
        timeout=180,
    )
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    (ARTIFACT_ROOT / f"godot-{version}-smoke.stdout.txt").write_text(
        result.stdout, encoding="utf-8"
    )
    (ARTIFACT_ROOT / f"godot-{version}-smoke.stderr.txt").write_text(
        result.stderr, encoding="utf-8"
    )
    combined = result.stdout + result.stderr
    print(combined, end="" if combined.endswith("\n") else "\n")
    if result.returncode != 0 or MARKER not in combined or has_godot_error(combined):
        raise RuntimeError(f"A4 phase 3 terrain-world smoke failed on {version}")
    marker_line = next(
        line for line in combined.splitlines() if line.startswith(MARKER)
    )
    return {
        "engine": version,
        "executable": str(engine),
        "marker": marker_line,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the world-transvoxel-terrain A4 phase 3 terrain-world lifecycle smoke harness."
    )
    parser.add_argument("--godot", type=Path, action="append", default=[])
    arguments = parser.parse_args()

    prepare_fixture()
    engines = discover_engines(arguments.godot)
    results: list[dict[str, object]] = []
    for version, engine in engines:
        run_import(version, engine)
        results.append(run_smoke(version, engine))

    report_path = ARTIFACT_ROOT / "a4_phase3_terrain_world_lifecycle_report.json"
    report_path.write_text(
        json.dumps(
            {
                "fixture_root": str(FIXTURE_ROOT.relative_to(ROOT).as_posix()),
                "world_transvoxel_fixture": str(LIFECYCLE_FIXTURE),
                "engines": results,
                "implementation": "terrain_world_lifecycle",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        "WT_TERRAIN_A4_PHASE3_SMOKE_PASS "
        f"engines={len(results)} report={report_path.relative_to(ROOT).as_posix()}"
    )


if __name__ == "__main__":
    main()
