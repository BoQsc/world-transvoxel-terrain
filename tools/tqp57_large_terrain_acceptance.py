#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time

import psutil

import a4_phase3_terrain_world_lifecycle_smoke as harness
from tqp_release_common import ROOT, git_output, load_json, run_python, sha256


ARTIFACT_ROOT = ROOT / "artifacts" / "tqp57_large_terrain_acceptance"
FIXTURE_ROOT = ARTIFACT_ROOT / "project"
SCRIPT = "res://tests/tqp57_large_terrain_acceptance.gd"
MARKER = "WT_TERRAIN_TQP57_LARGE_ACCEPTANCE_GODOT_PASS"
REPORT_PATH = ARTIFACT_ROOT / "tqp57_large_terrain_acceptance_report.json"


class ProcessTelemetrySampler:
    def __init__(self, process: subprocess.Popen[str]) -> None:
        self._process = psutil.Process(process.pid)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._sample, daemon=True)
        self._started = time.perf_counter()
        self._samples = 0
        self._peak_rss_bytes = 0
        self._peak_thread_count = 0
        self._process_cpu_seconds = 0.0
        self._read_bytes = 0
        self._write_bytes = 0
        self._affinity = self._process.cpu_affinity()

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> dict[str, object]:
        self._stop.set()
        self._thread.join(timeout=5)
        wall_seconds = max(time.perf_counter() - self._started, 1e-9)
        average_cpu_cores = self._process_cpu_seconds / wall_seconds
        affinity_capacity = max(len(self._affinity), 1)
        return {
            "sampling_interval_seconds": 0.1,
            "sample_count": self._samples,
            "logical_cpu_affinity": self._affinity,
            "logical_cpu_count": len(self._affinity),
            "wall_seconds": wall_seconds,
            "process_cpu_seconds": self._process_cpu_seconds,
            "average_cpu_cores": average_cpu_cores,
            "average_affinity_utilization_percent":
                average_cpu_cores * 100.0 / affinity_capacity,
            "peak_rss_bytes": self._peak_rss_bytes,
            "peak_thread_count": self._peak_thread_count,
            "read_bytes": self._read_bytes,
            "write_bytes": self._write_bytes,
        }

    def _sample(self) -> None:
        while not self._stop.is_set():
            try:
                cpu = self._process.cpu_times()
                memory = self._process.memory_info()
                io = self._process.io_counters()
                self._process_cpu_seconds = float(cpu.user + cpu.system)
                self._peak_rss_bytes = max(self._peak_rss_bytes, int(memory.rss))
                self._peak_thread_count = max(
                    self._peak_thread_count, self._process.num_threads()
                )
                self._read_bytes = max(self._read_bytes, int(io.read_bytes))
                self._write_bytes = max(self._write_bytes, int(io.write_bytes))
                self._samples += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
            self._stop.wait(0.1)


def prepare_fixture() -> None:
    harness.ARTIFACT_ROOT = ARTIFACT_ROOT
    harness.FIXTURE_ROOT = FIXTURE_ROOT
    harness.SCRIPT = SCRIPT
    harness.MARKER = MARKER
    harness.prepare_fixture()
    tests_root = FIXTURE_ROOT / "tests"
    tests_root.mkdir(parents=True, exist_ok=True)
    for name in (
        "tqp57_large_terrain_acceptance.gd",
        "tqp57_large_terrain_acceptance_runner.gd",
        "cpu_finalization_export_main.gd",
        "cpu_finalization_export_main.tscn",
    ):
        shutil.copy2(ROOT / "tests" / name, tests_root / name)
    shutil.copy2(ROOT / "TQP57_LARGE_TERRAIN_ACCEPTANCE_CONTRACT.json", FIXTURE_ROOT)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", type=Path, action="append", default=[])
    parser.add_argument("--headless", action="store_true")
    arguments = parser.parse_args()
    run_python("tools/validate_tqp57_large_terrain_acceptance.py")
    prepare_fixture()
    engines = harness.discover_engines(arguments.godot)
    if len(engines) != 1:
        raise RuntimeError("TQP-57 large-terrain acceptance requires the sole Godot 4.7 target")
    version, engine = engines[0]
    if version != "4.7":
        version_output = subprocess.run(
            [str(engine), "--version"],
            check=False,
            text=True,
            capture_output=True,
            errors="replace",
            timeout=30,
        )
        if version_output.returncode != 0 or not version_output.stdout.strip().startswith("4.7"):
            raise RuntimeError("TQP-57 large-terrain acceptance requires Godot 4.7")
        version = "4.7"
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
        telemetry = ProcessTelemetrySampler(process)
        telemetry.start()
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
        finally:
            process_telemetry = telemetry.stop()
    output = "".join(lines)
    if return_code != 0 or MARKER not in output or harness.has_godot_error(output):
        raise RuntimeError("TQP-57 Godot large-terrain acceptance workload failed")
    result_path = FIXTURE_ROOT / "tqp57_large_terrain_acceptance_result.json"
    if not result_path.is_file():
        raise RuntimeError("TQP-57 Godot large-terrain result is missing")
    report = load_json(result_path)
    report["base_revision"] = git_output(ROOT, "rev-parse", "HEAD")
    report["authority_revision"] = git_output(
        ROOT.parent / "world-transvoxel", "rev-parse", "HEAD"
    )
    report["execution_mode"] = "headless" if arguments.headless else "windowed_forward_plus"
    report["execution"] = {
        "logical_cpu_affinity": process_telemetry["logical_cpu_affinity"],
        "logical_cpu_count": process_telemetry["logical_cpu_count"],
        "cpu_power_measurement": "unavailable_no_trusted_package_energy_provider",
    }
    report["process_telemetry"] = process_telemetry
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
        f"scenarios={len(report['scenarios'])} lods=4 global_coarse=1 "
        f"frame_p99_usec={frame.get('p99_usec', 0):.3f} "
        f"captures={len(report.get('captures', []))}"
    )


if __name__ == "__main__":
    main()
