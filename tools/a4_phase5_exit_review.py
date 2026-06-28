#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "a4_phase5_exit_review"

VALIDATORS = (
    ("terrain_skeleton", "tools/validate_terrain_skeleton.py", "WT_TERRAIN_SKELETON_PASS"),
    ("a1_contract", "tools/validate_a1_contract.py", "WT_TERRAIN_A1_CONTRACT_PASS"),
    ("a2_contract", "tools/validate_a2_smoke.py", "WT_TERRAIN_A2_CONTRACT_PASS"),
    ("a3_contract", "tools/validate_a3_bridge.py", "WT_TERRAIN_A3_CONTRACT_PASS"),
    ("a4_phase1_contract", "tools/validate_a4_phase1.py", "WT_TERRAIN_A4_PHASE1_CONTRACT_PASS"),
    ("a4_phase2_contract", "tools/validate_a4_phase2.py", "WT_TERRAIN_A4_PHASE2_CONTRACT_PASS"),
    ("a4_phase3_contract", "tools/validate_a4_phase3.py", "WT_TERRAIN_A4_PHASE3_CONTRACT_PASS"),
    ("a4_phase4_contract", "tools/validate_a4_phase4.py", "WT_TERRAIN_A4_PHASE4_CONTRACT_PASS"),
    ("a4_phase5_contract", "tools/validate_a4_phase5.py", "WT_TERRAIN_A4_PHASE5_CONTRACT_PASS"),
)

SMOKES = (
    ("a2_smoke", "tools/a2_addon_smoke.py", "WT_TERRAIN_A2_SMOKE_PASS"),
    ("a3_smoke", "tools/a3_bridge_smoke.py", "WT_TERRAIN_A3_BRIDGE_PASS"),
    ("a4_phase1_smoke", "tools/a4_phase1_resources_smoke.py", "WT_TERRAIN_A4_PHASE1_SMOKE_PASS"),
    ("a4_phase2_smoke", "tools/a4_phase2_bridge_storage_smoke.py", "WT_TERRAIN_A4_PHASE2_SMOKE_PASS"),
    ("a4_phase3_smoke", "tools/a4_phase3_terrain_world_lifecycle_smoke.py", "WT_TERRAIN_A4_PHASE3_SMOKE_PASS"),
    ("a4_phase4_smoke", "tools/a4_phase4_reference_runtime_cold_idle_smoke.py", "WT_TERRAIN_A4_PHASE4_SMOKE_PASS"),
)


def run_step(name: str, script: str, marker: str) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, script],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        errors="replace",
        timeout=360,
    )
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    (ARTIFACT_ROOT / f"{name}.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (ARTIFACT_ROOT / f"{name}.stderr.txt").write_text(result.stderr, encoding="utf-8")
    combined = result.stdout + result.stderr
    print(combined, end="" if combined.endswith("\n") else "\n")
    if result.returncode != 0 or marker not in combined:
        raise RuntimeError(f"{name} failed or did not emit {marker}")
    marker_line = next(line for line in combined.splitlines() if line.startswith(marker))
    return {
        "name": name,
        "script": script,
        "marker": marker_line,
    }


def main() -> None:
    results: list[dict[str, object]] = []
    for step in VALIDATORS:
        results.append(run_step(*step))
    for step in SMOKES:
        results.append(run_step(*step))

    report_path = ARTIFACT_ROOT / "a4_phase5_exit_review_report.json"
    report_path.write_text(
        json.dumps(
            {
                "validators": len(VALIDATORS),
                "smokes": len(SMOKES),
                "steps": results,
                "decision": "a4_complete",
                "next": "a5_local_reference_scene_debug_ui",
                "implementation": "a4_exit_review",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        "WT_TERRAIN_A4_PHASE5_EXIT_REVIEW_PASS "
        f"validators={len(VALIDATORS)} smokes={len(SMOKES)} "
        f"report={report_path.relative_to(ROOT).as_posix()} "
        "next=a5_local_reference_scene_debug_ui"
    )


if __name__ == "__main__":
    main()
