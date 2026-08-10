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


ARTIFACT_ROOT = ROOT / "artifacts" / "cpu_prefetch_readiness"
FIXTURE_ROOT = ARTIFACT_ROOT / "project"
SCRIPT = "res://tests/cpu_prefetch_readiness.gd"
MARKER = "WT_TERRAIN_CPU_PREFETCH_READINESS_GODOT_PASS"
REPORT_PATH = ARTIFACT_ROOT / "cpu_prefetch_readiness_report.json"


def prepare_fixture() -> None:
    harness.ARTIFACT_ROOT = ARTIFACT_ROOT
    harness.FIXTURE_ROOT = FIXTURE_ROOT
    harness.SCRIPT = SCRIPT
    harness.MARKER = MARKER
    harness.prepare_fixture()
    tests_root = FIXTURE_ROOT / "tests"
    tests_root.mkdir(parents=True, exist_ok=True)
    for name in ("cpu_prefetch_readiness.gd", "cpu_prefetch_readiness_runner.gd"):
        shutil.copy2(ROOT / "tests" / name, tests_root / name)
    shutil.copy2(ROOT / "CPU_PREFETCH_READINESS_CONTRACT.json", FIXTURE_ROOT)


def verify_engine(version: str, engine: Path) -> tuple[str, Path]:
    if version == "4.7":
        return version, engine
    result = subprocess.run(
        [str(engine), "--version"],
        check=False,
        text=True,
        capture_output=True,
        errors="replace",
        timeout=30,
    )
    if result.returncode != 0 or not result.stdout.strip().startswith("4.7"):
        raise RuntimeError("CPU prefetch readiness requires Godot 4.7")
    return "4.7", engine


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", type=Path, action="append", default=[])
    arguments = parser.parse_args()
    run_python("tools/validate_cpu_prefetch_readiness.py")
    prepare_fixture()
    engines = harness.discover_engines(arguments.godot)
    if len(engines) != 1:
        raise RuntimeError("CPU prefetch readiness requires one Godot 4.7 executable")
    version, engine = verify_engine(*engines[0])
    harness.run_import(version, engine)
    environment = os.environ.copy()
    environment["GODOT_AUDIO_DRIVER"] = "Dummy"
    command = [
        str(engine),
        "--path",
        str(FIXTURE_ROOT),
        "--resolution",
        "960x540",
        "--script",
        SCRIPT,
    ]
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    log_path = ARTIFACT_ROOT / f"godot-{version}-prefetch-readiness.log"
    try:
        result = subprocess.run(
            command,
            cwd=FIXTURE_ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            errors="replace",
            env=environment,
            timeout=180,
        )
        output = result.stdout
    except subprocess.TimeoutExpired as error:
        partial = error.stdout or ""
        if isinstance(partial, bytes):
            partial = partial.decode("utf-8", errors="replace")
        log_path.write_text(partial, encoding="utf-8")
        print(partial, end="", flush=True)
        raise RuntimeError("Godot CPU prefetch readiness exceeded 180 seconds") from error
    log_path.write_text(output, encoding="utf-8")
    print(output, end="", flush=True)
    result_path = FIXTURE_ROOT / "cpu_prefetch_readiness_result.json"
    if result.returncode != 0 or MARKER not in output or harness.has_godot_error(output):
        (ARTIFACT_ROOT / f"godot-{version}-prefetch-readiness-last-failure.log").write_text(
            output, encoding="utf-8"
        )
        if result_path.is_file():
            shutil.copy2(
                result_path,
                ARTIFACT_ROOT / "cpu_prefetch_readiness_last_failure_report.json",
            )
        raise RuntimeError("Godot CPU prefetch readiness workload failed")
    if not result_path.is_file():
        raise RuntimeError("CPU prefetch readiness result is missing")
    report = load_json(result_path)
    report["terrain_revision"] = git_output(ROOT, "rev-parse", "HEAD")
    report["authority_revision"] = git_output(ROOT.parent / "world-transvoxel", "rev-parse", "HEAD")
    report["execution_mode"] = "windowed_forward_plus"
    source_captures = FIXTURE_ROOT / "cpu_prefetch_readiness_captures"
    captures_root = ARTIFACT_ROOT / "captures"
    captures_root.mkdir(parents=True, exist_ok=True)
    for capture in report.get("captures", []):
        name = f"{capture['id']}.png"
        source = source_captures / name
        target = captures_root / name
        if not source.is_file():
            raise RuntimeError(f"prefetch capture is missing: {name}")
        shutil.copy2(source, target)
        capture["path"] = target.relative_to(ROOT).as_posix()
        capture["sha256"] = sha256(target)
        capture["bytes"] = target.stat().st_size
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    run_python("tools/validate_cpu_prefetch_readiness.py", "--require-report")
    arrival = report["arrival"]
    print(
        "WT_TERRAIN_CPU_PREFETCH_READINESS_PASS "
        f"storage={arrival['work_delta']['storage_accepted_requests']} "
        f"mesh={arrival['work_delta']['mesh_jobs']} "
        f"collision_usec={arrival['settlement']['first_collision_latency_usec']}"
    )


if __name__ == "__main__":
    main()
