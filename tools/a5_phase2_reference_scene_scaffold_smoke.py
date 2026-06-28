#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "a5_phase2_reference_scene_scaffold"
SCRIPT = "res://tests/a5_phase2_reference_scene_scaffold_smoke.gd"
MARKER = "WT_TERRAIN_A5_PHASE2_GODOT_PASS"
ENGINE_VERSIONS = ("4.6.3", "4.7")


def discover_engines(explicit: list[Path]) -> list[tuple[str, Path]]:
    if explicit:
        return [(path.stem, path.resolve()) for path in explicit]

    sibling = ROOT.parent / "world-transvoxel" / ".tools" / "godot"
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


def has_godot_error(combined: str) -> bool:
    return (
        "SCRIPT ERROR:" in combined
        or combined.startswith("ERROR:")
        or "\nERROR:" in combined
    )


def run_import(version: str, engine: Path) -> None:
    result = subprocess.run(
        [str(engine), "--headless", "--path", str(ROOT), "--import"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        errors="replace",
        timeout=120,
    )
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    (ARTIFACT_ROOT / f"godot-{version}-import.stdout.txt").write_text(
        result.stdout, encoding="utf-8"
    )
    (ARTIFACT_ROOT / f"godot-{version}-import.stderr.txt").write_text(
        result.stderr, encoding="utf-8"
    )
    combined = result.stdout + result.stderr
    if result.returncode != 0 or has_godot_error(combined):
        raise RuntimeError(f"A5 phase 2 import failed on {version}")


def run_smoke(version: str, engine: Path) -> dict[str, object]:
    result = subprocess.run(
        [str(engine), "--headless", "--path", str(ROOT), "--script", SCRIPT],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        errors="replace",
        timeout=120,
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
        raise RuntimeError(f"A5 phase 2 reference scene smoke failed on {version}")
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
        description="Run the world-transvoxel-terrain A5 phase 2 reference scene scaffold smoke harness."
    )
    parser.add_argument("--godot", type=Path, action="append", default=[])
    arguments = parser.parse_args()

    engines = discover_engines(arguments.godot)
    results: list[dict[str, object]] = []
    for version, engine in engines:
        run_import(version, engine)
        results.append(run_smoke(version, engine))

    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    report_path = ARTIFACT_ROOT / "a5_phase2_reference_scene_scaffold_report.json"
    report_path.write_text(
        json.dumps(
            {
                "engines": results,
                "implementation": "local_reference_scene_scaffold",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        "WT_TERRAIN_A5_PHASE2_SMOKE_PASS "
        f"engines={len(results)} report={report_path.relative_to(ROOT).as_posix()}"
    )


if __name__ == "__main__":
    main()
