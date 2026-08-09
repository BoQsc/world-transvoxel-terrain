#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

import a4_phase3_terrain_world_lifecycle_smoke as harness
from tqp_release_common import ROOT, git_output, load_json, run_python, sha256


ARTIFACT_ROOT = ROOT / "artifacts" / "tqp57_large_terrain_acceptance"
FIXTURE_ROOT = ARTIFACT_ROOT / "project"
SCRIPT = "res://tests/tqp57_large_terrain_acceptance.gd"
MARKER = "WT_TERRAIN_TQP57_LARGE_ACCEPTANCE_GODOT_PASS"
REPORT_PATH = ARTIFACT_ROOT / "tqp57_large_terrain_acceptance_report.json"


def prepare_fixture() -> None:
    harness.ARTIFACT_ROOT = ARTIFACT_ROOT
    harness.FIXTURE_ROOT = FIXTURE_ROOT
    harness.SCRIPT = SCRIPT
    harness.MARKER = MARKER
    harness.prepare_fixture()
    target = FIXTURE_ROOT / "tests" / "tqp57_large_terrain_acceptance.gd"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "tests" / target.name, target)
    shutil.copy2(ROOT / "TQP57_LARGE_TERRAIN_ACCEPTANCE_CONTRACT.json", FIXTURE_ROOT)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", type=Path, action="append", default=[])
    parser.add_argument("--headless", action="store_true")
    arguments = parser.parse_args()
    run_python("tools/validate_tqp57_large_terrain_acceptance.py")
    prepare_fixture()
    engines = harness.discover_engines(arguments.godot)
    if [version for version, _engine in engines] != ["4.7"]:
        raise RuntimeError("TQP-57 large-terrain acceptance requires the sole Godot 4.7 target")
    version, engine = engines[0]
    harness.run_import(version, engine)
    command = [str(engine)]
    if arguments.headless:
        command.append("--headless")
    command.extend(
        ["--path", str(FIXTURE_ROOT), "--resolution", "1280x720", "--script", SCRIPT]
    )
    environment = os.environ.copy()
    environment["GODOT_AUDIO_DRIVER"] = "Dummy"
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    log_path = ARTIFACT_ROOT / f"godot-{version}-large-acceptance.log"
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command,
            cwd=FIXTURE_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            errors="replace",
            env=environment,
        )
        lines: list[str] = []
        assert process.stdout is not None
        try:
            for line in process.stdout:
                lines.append(line)
                log.write(line)
                log.flush()
                print(line, end="", flush=True)
            return_code = process.wait(timeout=30)
        except Exception:
            process.kill()
            process.wait(timeout=30)
            raise
    output = "".join(lines)
    if return_code != 0 or MARKER not in output or harness.has_godot_error(output):
        raise RuntimeError("TQP-57 Godot large-terrain acceptance workload failed")
    result_path = FIXTURE_ROOT / "tqp57_large_terrain_acceptance_result.json"
    if not result_path.is_file():
        raise RuntimeError("TQP-57 Godot large-terrain result is missing")
    report = load_json(result_path)
    report["base_revision"] = git_output(ROOT, "rev-parse", "HEAD")
    report["execution_mode"] = "headless" if arguments.headless else "windowed_forward_plus"
    report["marker"] = next(line for line in output.splitlines() if line.startswith(MARKER))
    captures_root = ARTIFACT_ROOT / "captures"
    captures_root.mkdir(parents=True, exist_ok=True)
    source_captures = FIXTURE_ROOT / "tqp57_large_terrain_acceptance_captures"
    for capture in report.get("captures", []):
        name = f"{capture['id']}.png"
        source = source_captures / name
        target = captures_root / name
        if not source.is_file():
            raise RuntimeError(f"TQP-57 capture is missing: {name}")
        shutil.copy2(source, target)
        capture["path"] = target.relative_to(ROOT).as_posix()
        capture["sha256"] = sha256(target)
        capture["bytes"] = target.stat().st_size
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    run_python("tools/validate_tqp57_large_terrain_acceptance.py", "--require-report")
    frame = report.get("aggregate", {}).get("frame_envelope", {})
    print(
        "WT_TERRAIN_TQP57_LARGE_ACCEPTANCE_PASS "
        f"scenarios={len(report['scenarios'])} lods=3 "
        f"frame_p99_usec={frame.get('p99_usec', 0):.3f} "
        f"captures={len(report.get('captures', []))}"
    )


if __name__ == "__main__":
    main()
