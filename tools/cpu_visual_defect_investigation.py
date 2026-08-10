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
from tqp_release_common import ROOT, git_output, load_json, sha256


ARTIFACT_ROOT = ROOT / "artifacts" / "cpu_visual_defect_investigation"
FIXTURE_ROOT = ARTIFACT_ROOT / "project"
SCRIPT = "res://tests/cpu_visual_defect_investigation.gd"
MARKER = "WT_TERRAIN_CPU_VISUAL_DEFECT_INVESTIGATION_PASS"
REPORT_PATH = ARTIFACT_ROOT / "cpu_visual_defect_investigation_report.json"


def prepare_fixture() -> None:
    harness.ARTIFACT_ROOT = ARTIFACT_ROOT
    harness.FIXTURE_ROOT = FIXTURE_ROOT
    harness.SCRIPT = SCRIPT
    harness.MARKER = MARKER
    harness.prepare_fixture()
    tests_root = FIXTURE_ROOT / "tests"
    tests_root.mkdir(parents=True, exist_ok=True)
    for name in (
        "cpu_visual_defect_investigation.gd",
        "cpu_visual_defect_investigation_runner.gd",
    ):
        shutil.copy2(ROOT / "tests" / name, tests_root / name)


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
        raise RuntimeError("visual defect investigation requires Godot 4.7+")
    return "4.7", engine


def _crop(image: np.ndarray) -> np.ndarray:
    height, width, _channels = image.shape
    return image[int(height * 0.30) : int(height * 0.88), int(width * 0.08) : int(width * 0.92)]


def _image_metrics(image: np.ndarray) -> dict[str, int]:
    crop = _crop(image)
    magenta = (crop[:, :, 0] >= 220) & (crop[:, :, 1] <= 40) & (crop[:, :, 2] >= 220)
    dark = crop.astype(np.uint16).sum(axis=2) <= 54
    return {
        "crop_pixels": int(magenta.size),
        "diagnostic_background_pixels": int(np.count_nonzero(magenta)),
        "dark_pixels": int(np.count_nonzero(dark)),
        "magenta_rows": int(np.count_nonzero(np.any(magenta, axis=1))),
        "magenta_columns": int(np.count_nonzero(np.any(magenta, axis=0))),
    }


def analyze_triplets(report: dict[str, object], captures_root: Path) -> dict[str, object]:
    images: dict[str, np.ndarray] = {}
    for capture in report.get("captures", []):
        capture_id = str(capture["id"])
        images[capture_id] = np.asarray(
            Image.open(captures_root / f"{capture_id}.png").convert("RGB")
        )
    triplets: list[dict[str, object]] = []
    geometry_gap_samples = 0
    lighting_samples = 0
    unexplained_dark_samples = 0
    for station in report.get("stations", []):
        for sample in station.get("samples", []):
            prefix = str(sample["id"])
            shadow_on = images[f"{prefix}_shadow_on"]
            shadow_off = images[f"{prefix}_shadow_off"]
            unshaded = images[f"{prefix}_unshaded"]
            on_metrics = _image_metrics(shadow_on)
            off_metrics = _image_metrics(shadow_off)
            diagnostic_metrics = _image_metrics(unshaded)
            pair_changed = int(np.count_nonzero(np.any(shadow_on != shadow_off, axis=2)))
            extra_shadow_dark = max(0, on_metrics["dark_pixels"] - off_metrics["dark_pixels"])
            background_pixels = diagnostic_metrics["diagnostic_background_pixels"]
            if background_pixels > 16:
                classification = "geometry_or_publication_gap"
                geometry_gap_samples += 1
            elif extra_shadow_dark > 64 and pair_changed > 256:
                classification = "directional_shadow_artifact"
                lighting_samples += 1
            elif on_metrics["dark_pixels"] > 64 or off_metrics["dark_pixels"] > 64:
                classification = "material_or_depth_artifact"
                unexplained_dark_samples += 1
            else:
                classification = "no_artifact_detected"
            triplets.append(
                {
                    "id": prefix,
                    "settled": sample.get("settled", False),
                    "snapshot_status": sample.get("snapshot_status", "UNKNOWN"),
                    "metrics": sample.get("metrics", {}),
                    "visible_coverage": sample.get("visible_coverage", {}),
                    "shadow_on": on_metrics,
                    "shadow_off": off_metrics,
                    "unshaded": diagnostic_metrics,
                    "shadow_pair_changed_pixels": pair_changed,
                    "extra_shadow_dark_pixels": extra_shadow_dark,
                    "classification": classification,
                }
            )
    if geometry_gap_samples:
        overall = "geometry_or_publication_gap_confirmed"
    elif lighting_samples and not unexplained_dark_samples:
        overall = "directional_shadow_artifact_confirmed"
    elif unexplained_dark_samples:
        overall = "material_or_depth_artifact_requires_followup"
    else:
        overall = "reported_artifact_not_reproduced"
    return {
        "overall_classification": overall,
        "geometry_gap_samples": geometry_gap_samples,
        "directional_shadow_samples": lighting_samples,
        "unexplained_dark_samples": unexplained_dark_samples,
        "triplets": triplets,
    }


def strict_failures(report: dict[str, object]) -> list[str]:
    failures: list[str] = []
    if report.get("status") != "PASS":
        failures.append("Godot investigation report did not pass")
    captures = report.get("captures", [])
    if not captures or any(capture.get("status") != "PASS" for capture in captures):
        failures.append("one or more required captures failed")
    analysis = report.get("image_analysis", {})
    if analysis.get("overall_classification") != "reported_artifact_not_reproduced":
        failures.append(
            "visual classifier reported "
            f"{analysis.get('overall_classification', 'missing_classification')}"
        )
    stations = {
        str(station.get("id", "")): station for station in report.get("stations", [])
    }
    seam_probe = stations.get("cross_lod_return", {}).get("seam_probe", {})
    if not seam_probe or not seam_probe.get("ok", False):
        failures.append("the exact x=1408 seam probe did not pass")
    for field in (
        "boundary_edges",
        "nonmanifold_edges",
        "orientation_inconsistent_edges",
        "zero_area_triangles",
    ):
        if int(seam_probe.get(field, -1)) != 0:
            failures.append(f"the exact seam probe reported {field}")
    for station in report.get("stations", []):
        for sample in station.get("samples", []):
            overlap = sample.get("visible_coverage", {})
            if int(overlap.get("count", -1)) != 0:
                failures.append(
                    f"visible ancestor overlap at {sample.get('id', 'unknown_sample')}"
                )
    return failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", type=Path, action="append", default=[])
    arguments = parser.parse_args()
    prepare_fixture()
    engines = harness.discover_engines(arguments.godot)
    if len(engines) != 1:
        raise RuntimeError("visual defect investigation requires one Godot executable")
    version, engine = verify_engine(*engines[0])
    harness.run_import(version, engine)
    environment = os.environ.copy()
    environment["GODOT_AUDIO_DRIVER"] = "Dummy"
    command = [
        str(engine),
        "--path",
        str(FIXTURE_ROOT),
        "--resolution",
        "1280x720",
        "--script",
        SCRIPT,
    ]
    result = subprocess.run(
        command,
        cwd=FIXTURE_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        errors="replace",
        env=environment,
        timeout=900,
    )
    output = result.stdout
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    (ARTIFACT_ROOT / f"godot-{version}-visual-defect.log").write_text(
        output, encoding="utf-8"
    )
    print(output, end="" if output.endswith("\n") else "\n")
    if result.returncode != 0 or MARKER not in output or harness.has_godot_error(output):
        raise RuntimeError("Godot visual defect investigation failed")
    source_report = FIXTURE_ROOT / "cpu_visual_defect_investigation_result.json"
    report = load_json(source_report)
    captures_root = ARTIFACT_ROOT / "captures"
    captures_root.mkdir(parents=True, exist_ok=True)
    source_captures = FIXTURE_ROOT / "cpu_visual_defect_investigation_captures"
    for capture in report.get("captures", []):
        name = f"{capture['id']}.png"
        source = source_captures / name
        target = captures_root / name
        if not source.is_file():
            raise RuntimeError(f"visual defect capture is missing: {name}")
        shutil.copy2(source, target)
        capture["path"] = target.relative_to(ROOT).as_posix()
        capture["sha256"] = sha256(target)
        capture["bytes"] = target.stat().st_size
    report["terrain_revision"] = git_output(ROOT, "rev-parse", "HEAD")
    report["authority_revision"] = git_output(
        ROOT.parent / "world-transvoxel", "rev-parse", "HEAD"
    )
    report["execution"] = {
        "mode": "windowed_forward_plus",
        "logical_cpu_affinity": list(range(3)),
        "logical_cpu_count": 3,
    }
    report["image_analysis"] = analyze_triplets(report, captures_root)
    report["strict_failures"] = strict_failures(report)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if report["strict_failures"]:
        raise RuntimeError("; ".join(report["strict_failures"]))
    print(
        "WT_TERRAIN_CPU_VISUAL_DEFECT_INVESTIGATION_COMPLETE "
        f"classification={report['image_analysis']['overall_classification']} "
        f"captures={len(report['captures'])}"
    )


if __name__ == "__main__":
    main()
