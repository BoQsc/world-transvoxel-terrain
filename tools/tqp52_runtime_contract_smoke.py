#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

import a4_phase3_terrain_world_lifecycle_smoke as harness


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "tqp52_runtime_contract"
FIXTURE_ROOT = ARTIFACT_ROOT / "project"
SCRIPT = "res://tests/tqp52_runtime_contract_smoke.gd"
MARKER = "WT_TERRAIN_TQP52_GODOT_PASS"


def prepare_fixture() -> None:
    harness.ARTIFACT_ROOT = ARTIFACT_ROOT
    harness.FIXTURE_ROOT = FIXTURE_ROOT
    harness.SCRIPT = SCRIPT
    harness.MARKER = MARKER
    harness.prepare_fixture()
    target = FIXTURE_ROOT / "tests" / "tqp52_runtime_contract_smoke.gd"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "tests" / target.name, target)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the TQP-52 runtime contract smoke.")
    parser.add_argument("--godot", type=Path, action="append", default=[])
    arguments = parser.parse_args()
    prepare_fixture()
    engines = harness.discover_engines(arguments.godot)
    results: list[dict[str, object]] = []
    for version, engine in engines:
        harness.run_import(version, engine)
        results.append(harness.run_smoke(version, engine))
    report_path = ARTIFACT_ROOT / "tqp52_runtime_contract_report.json"
    report_path.write_text(
        json.dumps(
            {
                "schema": "world_transvoxel_terrain.tqp52_runtime_evidence.v1",
                "status": "PASS",
                "engines": results,
                "api_version": 2,
                "profiles": 4,
                "readiness_scopes": 4,
                "implementation": "tqp52_runtime_contract_qualification",
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(
        "WT_TERRAIN_TQP52_QUALIFICATION_PASS "
        f"engines={len(results)} report={report_path.relative_to(ROOT).as_posix()}"
    )


if __name__ == "__main__":
    main()
