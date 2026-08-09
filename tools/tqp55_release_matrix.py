#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path

from tqp_release_common import ROOT, git_output, load_json, run_python, write_deterministic_addon_zip


ARTIFACT_ROOT = ROOT / "artifacts" / "tqp55_release_matrix"
REPORT_PATH = ARTIFACT_ROOT / "tqp55_release_matrix_report.json"
ZIP_PATH = ARTIFACT_ROOT / "world-transvoxel-terrain-cpu-1.0.0-candidate.zip"


def main() -> None:
    for validator in (
        "tools/validate_tqp51_boundary.py",
        "tools/validate_tqp52_runtime_contract.py",
        "tools/validate_tqp53_authoring_workflow.py",
    ):
        run_python(validator)
    run_python("tools/tqp52_runtime_contract_smoke.py")
    run_python("tools/tqp53_authoring_workflow_smoke.py")
    run_python("tools/validate_tqp55_release_matrix.py")

    package = write_deterministic_addon_zip(ZIP_PATH)
    tqp52 = load_json(ROOT / "artifacts/tqp52_runtime_contract/tqp52_runtime_contract_report.json")
    tqp53 = load_json(ROOT / "artifacts/tqp53_authoring_workflow/tqp53_authoring_workflow_report.json")
    contract = load_json(ROOT / "TQP55_RELEASE_MATRIX.json")
    report = {
        "schema": "world_transvoxel_terrain.tqp55_release_matrix_evidence.v1",
        "milestone": "TQP-55",
        "status": "PASS",
        "release_id": contract["release_id"],
        "version": contract["version"],
        "base_revision": git_output(ROOT, "rev-parse", "HEAD"),
        "engine_versions": ["4.7"],
        "platforms": contract["supported_matrix"]["platforms"],
        "renderers": contract["supported_matrix"]["renderers"],
        "profiles": contract["supported_matrix"]["profiles"],
        "runtime_markers": {
            "TQP-52": [item["marker"] for item in tqp52["engines"]],
            "TQP-53": [item["marker"] for item in tqp53["engines"]],
        },
        "authority_revision": contract["authority"]["revision"],
        "package": package,
        "retained_evidence_count": len(contract["required_retained_evidence"]),
        "power_target_status": "retained_measured_target_miss",
        "explicitly_unqualified_scope": contract["explicitly_unqualified_scope"],
    }
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    run_python("tools/validate_tqp55_release_matrix.py", "--require-report")
    print(
        "WT_TERRAIN_TQP55_QUALIFICATION_PASS "
        f"engines=1 profiles=4 package={package['package_digest_sha256']}"
    )


if __name__ == "__main__":
    main()
