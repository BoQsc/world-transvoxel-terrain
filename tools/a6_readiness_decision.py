#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "a6_readiness_decision"

VALIDATORS = (
    (
        "a5_phase5_exit_review",
        "tools/a5_phase5_exit_review.py",
        "WT_TERRAIN_A5_PHASE5_EXIT_REVIEW_PASS",
    ),
    (
        "a6_readiness_contract",
        "tools/validate_a6_readiness_decision.py",
        "WT_TERRAIN_A6_CONTRACT_PASS",
    ),
)


def run_step(name: str, script: str, marker: str) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, script],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        errors="replace",
        timeout=420,
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

    report_path = ARTIFACT_ROOT / "a6_readiness_decision_report.json"
    report_path.write_text(
        json.dumps(
            {
                "validators": len(VALIDATORS),
                "steps": results,
                "decision": "approve_validation_game_repository",
                "next": "separate_validation_game_repository_when_user_approves",
                "implementation": "readiness_decision",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        "WT_TERRAIN_A6_READINESS_DECISION_PASS "
        "decision=approve_validation_game_repository "
        f"validators={len(VALIDATORS)} "
        f"report={report_path.relative_to(ROOT).as_posix()} "
        "next=separate_validation_game_repository_when_user_approves"
    )


if __name__ == "__main__":
    main()
