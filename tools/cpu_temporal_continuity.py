#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

import numpy as np
from PIL import Image

import a4_phase3_terrain_world_lifecycle_smoke as harness
from tqp_release_common import ROOT, git_output, load_json, run_python, sha256


ARTIFACT_ROOT = ROOT / "artifacts" / "cpu_temporal_continuity"
FIXTURE_ROOT = ARTIFACT_ROOT / "project"
SCRIPT = "res://tests/cpu_temporal_continuity.gd"
MARKER = "WT_TERRAIN_CPU_TEMPORAL_CONTINUITY_GODOT_PASS"
REPORT_PATH = ARTIFACT_ROOT / "cpu_temporal_continuity_report.json"


def prepare_fixture() -> None:
    harness.ARTIFACT_ROOT = ARTIFACT_ROOT
    harness.FIXTURE_ROOT = FIXTURE_ROOT
    harness.SCRIPT = SCRIPT
    harness.MARKER = MARKER
    harness.prepare_fixture()
    tests_root = FIXTURE_ROOT / "tests"
    tests_root.mkdir(parents=True, exist_ok=True)
    for name in ("cpu_temporal_continuity.gd", "cpu_temporal_continuity_runner.gd"):
        shutil.copy2(ROOT / "tests" / name, tests_root / name)
    shutil.copy2(ROOT / "CPU_TEMPORAL_CONTINUITY_CONTRACT.json", FIXTURE_ROOT)


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
        raise RuntimeError("CPU temporal continuity requires Godot 4.7")
    return "4.7", engine


def analyze_images(report: dict[str, object], captures_root: Path) -> dict[str, object]:
    diagnostic: list[dict[str, object]] = []
    shadow: dict[str, int | str] = {}
    for capture in report.get("captures", []):
        capture_id = capture["id"]
        image = np.asarray(Image.open(captures_root / f"{capture_id}.png").convert("RGB"))
        height, width, _channels = image.shape
        crop = image[int(height * 0.25) : int(height * 0.85), int(width * 0.20) : int(width * 0.80)]
        if capture.get("diagnostic"):
            magenta = (crop[:, :, 0] >= 220) & (crop[:, :, 1] <= 40) & (crop[:, :, 2] >= 220)
            diagnostic.append(
                {
                    "id": capture_id,
                    "center_background_pixels": int(np.count_nonzero(magenta)),
                    "center_crop_pixels": int(magenta.size),
                    "background_rule": "r>=220,g<=40,b>=220",
                }
            )
        if capture_id in {"shadow_on", "shadow_off"}:
            luminance = crop.astype(np.uint16).sum(axis=2)
            shadow[f"{capture_id}_dark_pixels"] = int(np.count_nonzero(luminance <= 36))
    on = int(shadow.get("shadow_on_dark_pixels", 0))
    off = int(shadow.get("shadow_off_dark_pixels", 0))
    shadow["dark_pixel_delta"] = on - off
    shadow["classification"] = "lighting_contributes" if on > off else "no_extra_shadow_darkness_detected"
    return {"diagnostic_captures": diagnostic, "shadow_pair": shadow}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", type=Path, action="append", default=[])
    arguments = parser.parse_args()
    run_python("tools/validate_cpu_temporal_continuity.py")
    prepare_fixture()
    engines = harness.discover_engines(arguments.godot)
    if len(engines) != 1:
        raise RuntimeError("CPU temporal continuity requires one Godot 4.7 executable")
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
    log_path = ARTIFACT_ROOT / f"godot-{version}-temporal-continuity.log"
    result = subprocess.run(
        command,
        cwd=FIXTURE_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        errors="replace",
        env=environment,
        timeout=600,
    )
    output = result.stdout
    log_path.write_text(output, encoding="utf-8")
    print(output, end="", flush=True)
    return_code = result.returncode
    if return_code != 0 or MARKER not in output or harness.has_godot_error(output):
        raise RuntimeError("Godot CPU temporal continuity workload failed")
    result_path = FIXTURE_ROOT / "cpu_temporal_continuity_result.json"
    if not result_path.is_file():
        raise RuntimeError("CPU temporal continuity result is missing")
    report = load_json(result_path)
    report["terrain_revision"] = git_output(ROOT, "rev-parse", "HEAD")
    report["authority_revision"] = git_output(ROOT.parent / "world-transvoxel", "rev-parse", "HEAD")
    report["execution_mode"] = "windowed_forward_plus"
    source_captures = FIXTURE_ROOT / "cpu_temporal_continuity_captures"
    captures_root = ARTIFACT_ROOT / "captures"
    captures_root.mkdir(parents=True, exist_ok=True)
    for capture in report.get("captures", []):
        name = f"{capture['id']}.png"
        source = source_captures / name
        target = captures_root / name
        if not source.is_file():
            raise RuntimeError(f"temporal continuity capture is missing: {name}")
        shutil.copy2(source, target)
        capture["path"] = target.relative_to(ROOT).as_posix()
        capture["sha256"] = sha256(target)
        capture["bytes"] = target.stat().st_size
    report["image_analysis"] = analyze_images(report, captures_root)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    run_python("tools/validate_cpu_temporal_continuity.py", "--require-report")
    print(
        "WT_TERRAIN_CPU_TEMPORAL_CONTINUITY_PASS "
        f"frames={report['monitored_frames']} topology={len(report['topology_samples'])} "
        f"overlaps={report['maximum_visible_ancestor_overlaps']} captures={len(report['captures'])}"
    )


if __name__ == "__main__":
    main()
