#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

import a4_phase3_terrain_world_lifecycle_smoke as harness
from tqp_release_common import ROOT, load_json, run_python


ARTIFACT_ROOT = ROOT / "artifacts" / "tqp56_long_haul"
FIXTURE_ROOT = ARTIFACT_ROOT / "project"
SCRIPT = "res://tests/tqp56_cpu_long_haul.gd"
MARKER = "WT_TERRAIN_TQP56_GODOT_PASS"
REPORT_PATH = ARTIFACT_ROOT / "tqp56_long_haul_report.json"


def prepare_fixture() -> None:
    harness.ARTIFACT_ROOT = ARTIFACT_ROOT
    harness.FIXTURE_ROOT = FIXTURE_ROOT
    harness.SCRIPT = SCRIPT
    harness.MARKER = MARKER
    harness.prepare_fixture()
    target = FIXTURE_ROOT / "tests" / "tqp56_cpu_long_haul.gd"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "tests" / target.name, target)
    shutil.copy2(ROOT / "TQP56_LONG_HAUL_CONTRACT.json", FIXTURE_ROOT)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", type=Path, action="append", default=[])
    arguments = parser.parse_args()
    run_python("tools/validate_tqp55_release_matrix.py", "--require-report")
    prepare_fixture()
    engines = harness.discover_engines(arguments.godot)
    if [version for version, _engine in engines] != ["4.7"]:
        raise RuntimeError("TQP-56 requires the sole Godot 4.7 qualification target")
    version, engine = engines[0]
    harness.run_import(version, engine)
    contract = load_json(ROOT / "TQP56_LONG_HAUL_CONTRACT.json")
    environment = os.environ.copy()
    environment["WT_TQP56_DURATION_SECONDS"] = str(contract["minimum_wrapper_duration_seconds"])
    result = subprocess.run(
        [str(engine), "--headless", "--path", str(FIXTURE_ROOT), "--script", SCRIPT],
        cwd=FIXTURE_ROOT,
        text=True,
        capture_output=True,
        errors="replace",
        timeout=int(contract["minimum_wrapper_duration_seconds"]) + 240,
        env=environment,
    )
    output = result.stdout + result.stderr
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    (ARTIFACT_ROOT / f"godot-{version}-long-haul.log").write_text(output, encoding="utf-8")
    print(output, end="" if output.endswith("\n") else "\n")
    if result.returncode != 0 or MARKER not in output or harness.has_godot_error(output):
        raise RuntimeError("TQP-56 Godot long-haul workload failed")
    result_path = FIXTURE_ROOT / "tqp56_result.json"
    if not result_path.is_file():
        raise RuntimeError("TQP-56 Godot result is missing")
    workload = load_json(result_path)
    report = {
        "schema": "world_transvoxel_terrain.tqp56_long_haul_evidence.v1",
        "milestone": "TQP-56",
        "status": "PASS",
        "engine": version,
        "marker": next(line for line in output.splitlines() if line.startswith(MARKER)),
        "workload": workload,
        "tqp55_report": "artifacts/tqp55_release_matrix/tqp55_release_matrix_report.json",
        "retained_long_run": contract["retained_long_run"],
        "qualification_boundary": "bounded_production_wrapper_plus_retained_1800_second_native_drift",
        "explicitly_unqualified_scope": contract["explicitly_unqualified_scope"],
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    run_python("tools/validate_tqp56_long_haul.py")
    print(
        "WT_TERRAIN_TQP56_QUALIFICATION_PASS "
        f"duration={workload['duration_seconds']:.3f} cycles={workload['cycles']} "
        f"restarts={workload['restarts']} queue_rejections={workload['queue_rejections']}"
    )


if __name__ == "__main__":
    main()
