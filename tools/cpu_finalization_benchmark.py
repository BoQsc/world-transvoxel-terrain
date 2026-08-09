#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import time

import psutil

import a4_phase3_terrain_world_lifecycle_smoke as harness
import tqp57_large_terrain_acceptance as tqp57
from tqp_release_common import ROOT, git_output, load_json, sha256


ARTIFACT_ROOT = ROOT / "artifacts" / "cpu_finalization"
FIXTURE_ROOT = ARTIFACT_ROOT / "project"
SOURCE_CONTRACT = ROOT / "CPU_FINALIZATION_BENCHMARK_CONTRACT.json"
ACTIVE_CONTRACT = FIXTURE_ROOT / "CPU_FINALIZATION_ACTIVE_CONTRACT.json"
RESULT_PATH = FIXTURE_ROOT / "cpu_finalization_result.json"
SCRIPT = "res://tests/tqp57_large_terrain_acceptance.gd"
MARKER = "WT_TERRAIN_TQP57_LARGE_ACCEPTANCE_GODOT_PASS"
FINAL_SITE_SCENARIOS = {"cold_teleport", "digging", "construction", "far_return"}
KNOWN_NON_SOURCE_STATUS = {
    "world-transvoxel": {"?? tests/godot/cell_probe_test.gd.uid"},
    "world-transvoxel-terrain": set(),
}


def source_status(repository: Path) -> dict[str, object]:
    lines = [
        line
        for line in git_output(
            repository,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ).splitlines()
        if line
    ]
    allowed = KNOWN_NON_SOURCE_STATUS.get(repository.name, set())
    accepted = [line for line in lines if line in allowed]
    rejected = [line for line in lines if line not in allowed]
    return {
        "repository": repository.name,
        "revision": git_output(repository, "rev-parse", "HEAD"),
        "accepted_non_source_status": accepted,
        "rejected_status": rejected,
        "qualification_clean": not rejected,
    }


def cpu_snapshot(process: psutil.Process) -> dict[str, float | int]:
    cpu = process.cpu_times()
    memory = process.memory_info()
    return {
        "wall_seconds": time.perf_counter(),
        "process_cpu_seconds": float(cpu.user + cpu.system),
        "rss_bytes": int(memory.rss),
    }


def telemetry_delta(start: dict, end: dict) -> dict[str, float | int]:
    wall = max(float(end["wall_seconds"]) - float(start["wall_seconds"]), 0.0)
    cpu = max(
        float(end["process_cpu_seconds"]) - float(start["process_cpu_seconds"]),
        0.0,
    )
    return {
        "wall_seconds": round(wall, 6),
        "process_cpu_seconds": round(cpu, 6),
        "average_active_core_equivalents": round(cpu / wall, 6) if wall else 0.0,
        "rss_bytes_start": int(start["rss_bytes"]),
        "rss_bytes_end": int(end["rss_bytes"]),
        "rss_bytes_maximum_boundary_sample": max(
            int(start["rss_bytes"]), int(end["rss_bytes"])
        ),
    }


def prepare_fixture(contract: dict, native_mode: str) -> None:
    tqp57.ARTIFACT_ROOT = ARTIFACT_ROOT
    tqp57.FIXTURE_ROOT = FIXTURE_ROOT
    tqp57.prepare_fixture()
    shutil.copy2(SOURCE_CONTRACT, FIXTURE_ROOT / SOURCE_CONTRACT.name)
    ACTIVE_CONTRACT.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    if native_mode == "release_native_editor_host":
        extension = (
            FIXTURE_ROOT
            / "addons"
            / "world_transvoxel"
            / "world_transvoxel.gdextension"
        )
        contents = extension.read_text(encoding="utf-8")
        debug_name = "world_transvoxel.windows.template_debug.x86_64.dll"
        release_name = "world_transvoxel.windows.template_release.x86_64.dll"
        release_binary = extension.parent / "bin" / release_name
        if contents.count(debug_name) != 1 or not release_binary.is_file():
            raise RuntimeError("release-native editor-host substitution is invalid")
        contents = contents.replace(debug_name, release_name)
        extension.write_text(contents, encoding="utf-8")


def percentile_tail_count(sample_count: int, percentile: float) -> int:
    index = max(0, min(sample_count - 1, int(sample_count * percentile + 0.999999) - 1))
    return sample_count - index


def distribution(values: list[float]) -> dict[str, float | int]:
    if not values:
        return {
            "sample_count": 0,
            "p50": 0.0,
            "p95": 0.0,
            "p99": 0.0,
            "maximum": 0.0,
        }
    ordered = sorted(values)
    value_at = lambda percentile: ordered[
        max(0, min(len(ordered) - 1, int(len(ordered) * percentile + 0.999999) - 1))
    ]
    return {
        "sample_count": len(ordered),
        "nonzero_sample_count": sum(value > 0 for value in ordered),
        "p50": value_at(0.50),
        "p95": value_at(0.95),
        "p99": value_at(0.99),
        "maximum": ordered[-1],
        "total": sum(ordered),
    }


def add_native_distributions(report: dict) -> None:
    for scenario in report.get("scenarios", []):
        start = scenario.get("metrics_start", {})
        distributions: dict[str, dict] = {}
        for metric_name, cumulative in scenario.get(
            "native_cumulative_samples", {}
        ).items():
            previous = int(start.get(metric_name, 0))
            deltas: list[float] = []
            for value in cumulative:
                current = int(value)
                deltas.append(float(max(current - previous, 0)))
                previous = current
            item = distribution(deltas)
            item["unit"] = "nanoseconds_per_observed_frame"
            item["source"] = metric_name
            distributions[metric_name.removesuffix("_time_ns_total")] = item
        scenario["native_phase_frame_distributions"] = distributions


def validate_report(report: dict, contract: dict, worker_count: int) -> list[str]:
    failures: list[str] = []
    if report.get("status") != "PASS" or report.get("retained_complete") is not True:
        failures.append("Godot correctness workload did not retain PASS")
    profile = report.get("profile", {})
    if profile.get("fallback") is not False:
        failures.append("authority fallback was enabled")
    if int(profile.get("meshing_worker_count", 0)) != worker_count:
        failures.append("meshing worker count differs from the requested profile")
    required_samples = int(contract["budgets"]["minimum_frame_samples_per_scenario"])
    process_by_scenario = report.get("process_telemetry", {}).get("scenarios", {})
    for scenario in report.get("scenarios", []):
        scenario_id = str(scenario.get("id", ""))
        samples = scenario.get("frame_samples_usec", [])
        if len(samples) < required_samples:
            failures.append(f"{scenario_id}: raw frame samples are incomplete")
        if percentile_tail_count(len(samples), 0.99) < 3:
            failures.append(f"{scenario_id}: p99 still depends on fewer than three tail samples")
        if scenario_id not in process_by_scenario:
            failures.append(f"{scenario_id}: process CPU boundary telemetry is missing")
        native = scenario.get("native_cumulative_samples", {})
        if not native or any(len(values) != len(samples) for values in native.values()):
            failures.append(f"{scenario_id}: native phase samples are incomplete")
    final_metrics = report.get("final_lod_audit", {})
    if report.get("queue_peaks", {}).get("scheduler", -1) < 0:
        failures.append("queue telemetry is missing")
    end_metrics = report.get("scenarios", [{}])[-1].get("metrics_end", {})
    if int(end_metrics.get("mesh_worker_queue_rejections", -1)) != 0:
        failures.append("mesh worker queue rejected work")
    if int(end_metrics.get("mesh_worker_completed_jobs", 0)) == 0:
        failures.append("mesh workers completed no jobs")
    if int(end_metrics.get("viewer_planning_calls", 0)) == 0:
        failures.append("native viewer-planning phase telemetry is missing")
    if int(end_metrics.get("mesh_worker_execute_time_ns_total", 0)) == 0:
        failures.append("native mesh execution telemetry is missing")
    if not final_metrics:
        failures.append("final LOD audit is missing")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", type=Path, action="append", default=[])
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--native-mode",
        choices=("debug_editor", "release_native_editor_host"),
        default="debug_editor",
    )
    parser.add_argument(
        "--profile",
        choices=("low_power", "balanced", "quality", "reference"),
        default="balanced",
    )
    parser.add_argument("--meshing-workers", type=int, default=2)
    parser.add_argument("--frames", type=int, default=300)
    parser.add_argument("--scenario", action="append", default=[])
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--require-clean", action="store_true")
    arguments = parser.parse_args()
    if arguments.meshing_workers < 1 or arguments.meshing_workers > 8:
        raise RuntimeError("meshing worker count must be between 1 and 8")
    if arguments.frames < 300:
        raise RuntimeError("CPU-finalization p99 evidence requires at least 300 frames")

    authority = ROOT.parent / "world-transvoxel"
    source_integrity = [source_status(repository) for repository in (ROOT, authority)]
    if arguments.require_clean:
        rejected = [
            item
            for item in source_integrity
            if not bool(item["qualification_clean"])
        ]
        if rejected:
            details = "; ".join(
                f"{item['repository']}: {item['rejected_status']}" for item in rejected
            )
            raise RuntimeError(f"qualification repository is dirty: {details}")

    contract = load_json(SOURCE_CONTRACT)
    contract["runtime_profile"]["frames_per_scenario"] = arguments.frames
    contract["budgets"]["minimum_frame_samples_per_scenario"] = arguments.frames
    if arguments.scenario:
        selected = set(arguments.scenario)
        contract["scenarios"] = [
            item for item in contract["scenarios"] if item["id"] in selected
        ]
        missing = selected - {item["id"] for item in contract["scenarios"]}
        if missing:
            raise RuntimeError(f"unknown scenarios: {sorted(missing)}")
        if selected.isdisjoint(FINAL_SITE_SCENARIOS):
            raise RuntimeError(
                "scenario subsets must include a final-site setup scenario: "
                f"{sorted(FINAL_SITE_SCENARIOS)}"
            )
        contract["required_capture_ids"] = []
    prepare_fixture(contract, arguments.native_mode)
    engines = harness.discover_engines(arguments.godot)
    if [version for version, _engine in engines] != ["4.7"]:
        raise RuntimeError("CPU finalization requires the pinned Godot 4.7 engine")
    version, engine = engines[0]
    harness.ARTIFACT_ROOT = ARTIFACT_ROOT
    harness.FIXTURE_ROOT = FIXTURE_ROOT
    harness.run_import(version, engine)

    command = [str(engine)]
    if arguments.headless:
        command.append("--headless")
    command.extend(
        ["--path", str(FIXTURE_ROOT), "--resolution", "1280x720", "--script", SCRIPT]
    )
    environment = os.environ.copy()
    environment["GODOT_AUDIO_DRIVER"] = "Dummy"
    environment["WT_ACCEPTANCE_CONTRACT"] = (
        "res://CPU_FINALIZATION_ACTIVE_CONTRACT.json"
    )
    environment["WT_ACCEPTANCE_RESULT"] = "res://cpu_finalization_result.json"
    environment["WT_CPU_PROFILE"] = arguments.profile
    environment["WT_MESHING_WORKERS"] = str(arguments.meshing_workers)
    log_path = ARTIFACT_ROOT / f"{arguments.run_id}.log"
    process = subprocess.Popen(
        command,
        cwd=FIXTURE_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        errors="replace",
        env=environment,
    )
    measured = psutil.Process(process.pid)
    run_start = cpu_snapshot(measured)
    last_snapshot = run_start
    boundary_snapshots = [run_start]
    scenario_starts: dict[str, dict] = {}
    scenario_telemetry: dict[str, dict] = {}
    lines: list[str] = []
    assert process.stdout is not None
    with log_path.open("w", encoding="utf-8") as log:
        for line in process.stdout:
            lines.append(line)
            log.write(line)
            log.flush()
            print(line, end="", flush=True)
            if line.startswith("TQP57_LARGE_SCENARIO_START id="):
                scenario_id = line.strip().split("=", 1)[1]
                last_snapshot = cpu_snapshot(measured)
                boundary_snapshots.append(last_snapshot)
                scenario_starts[scenario_id] = last_snapshot
            elif line.startswith("TQP57_LARGE_SCENARIO_END id="):
                scenario_id = line.strip().split(" id=", 1)[1].split(" ", 1)[0]
                last_snapshot = cpu_snapshot(measured)
                boundary_snapshots.append(last_snapshot)
                if scenario_id in scenario_starts:
                    scenario_telemetry[scenario_id] = telemetry_delta(
                        scenario_starts[scenario_id], last_snapshot
                    )
            elif line.startswith(MARKER):
                last_snapshot = cpu_snapshot(measured)
                boundary_snapshots.append(last_snapshot)
    return_code = process.wait(timeout=30)
    output = "".join(lines)
    if return_code != 0 or MARKER not in output or harness.has_godot_error(output):
        raise RuntimeError("CPU-finalization Godot workload failed")
    if not RESULT_PATH.is_file():
        raise RuntimeError("CPU-finalization Godot result is missing")
    report = load_json(RESULT_PATH)
    report["candidate_revision"] = git_output(ROOT, "rev-parse", "HEAD")
    report["authority_revision"] = git_output(authority, "rev-parse", "HEAD")
    report["execution"] = {
        "engine_target": version,
        "native_mode": arguments.native_mode,
        "headless": arguments.headless,
        "profile": arguments.profile,
        "meshing_worker_count": arguments.meshing_workers,
        "frames_per_scenario": arguments.frames,
        "evidence_class": "qualification" if arguments.require_clean else "development",
        "promotable": bool(arguments.require_clean and not arguments.headless),
    }
    report["source_integrity"] = source_integrity
    report["host"] = {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "logical_cpu_count": psutil.cpu_count(logical=True),
        "physical_cpu_count": psutil.cpu_count(logical=False),
        "total_memory_bytes": psutil.virtual_memory().total,
    }
    whole_run = telemetry_delta(run_start, last_snapshot)
    whole_run["rss_bytes_maximum_boundary_sample"] = max(
        int(snapshot["rss_bytes"]) for snapshot in boundary_snapshots
    )
    report["process_telemetry"] = {
        "method": "psutil process CPU and RSS sampled only at scenario boundaries",
        "intrusion": "scenario and terminal boundary samples only; no periodic process or thread polling",
        "whole_run": whole_run,
        "scenarios": scenario_telemetry,
        "cpu_package_power_available": False,
        "whole_system_power_available": False,
        "gpu_board_power_is_cpu_power": False,
    }
    report["p99_sample_policy"] = {
        "method": "nearest rank",
        "minimum_samples_per_scenario": arguments.frames,
        "minimum_tail_samples_at_p99": percentile_tail_count(arguments.frames, 0.99),
    }
    report["contract"] = {
        "path": SOURCE_CONTRACT.name,
        "sha256": sha256(SOURCE_CONTRACT),
        "active_contract_sha256": sha256(ACTIVE_CONTRACT),
    }
    add_native_distributions(report)
    failures = validate_report(report, contract, arguments.meshing_workers)
    report["cpu_finalization_validation_failures"] = failures
    if failures:
        report["cpu_finalization_status"] = "FAIL"
    elif arguments.require_clean:
        report["cpu_finalization_status"] = "PASS"
    else:
        report["cpu_finalization_status"] = "DEVELOPMENT_PASS"
    output_path = ARTIFACT_ROOT / f"{arguments.run_id}.json"
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if failures:
        raise RuntimeError("; ".join(failures))
    print(
        "WT_TERRAIN_CPU_FINALIZATION_BENCHMARK_PASS "
        f"run={arguments.run_id} scenarios={len(report['scenarios'])} "
        f"workers={arguments.meshing_workers} frames={arguments.frames} "
        f"cpu_seconds={report['process_telemetry']['whole_run']['process_cpu_seconds']:.3f}"
    )


if __name__ == "__main__":
    main()
