#!/usr/bin/env python3

from __future__ import annotations

import json

from tqp_release_common import (
    ROOT,
    canonical_sha256,
    git_output,
    load_json,
    run_python,
    tracked_addon_files,
    write_deterministic_addon_zip,
)


ARTIFACT_ROOT = ROOT / "artifacts" / "tqp57_release"
ZIP_PATH = ARTIFACT_ROOT / "world-transvoxel-terrain-1.0.0.zip"
MANIFEST_PATH = ARTIFACT_ROOT / "world-transvoxel-terrain-1.0.0.manifest.json"
REPORT_PATH = ARTIFACT_ROOT / "tqp57_release_report.json"


def main() -> None:
    run_python("tools/validate_tqp55_release_matrix.py", "--require-report")
    run_python("tools/validate_tqp56_long_haul.py")
    contract = load_json(ROOT / "TQP57_RELEASE_CONTRACT.json")
    package = write_deterministic_addon_zip(ZIP_PATH)
    files = tracked_addon_files()
    manifest = {
        "schema": "world_transvoxel_terrain.release_manifest.v1",
        "release_id": contract["release_id"],
        "version": contract["version"],
        "package": package,
        "dependency": contract["dependency"],
        "files": [
            {
                "path": relative.as_posix(),
                "bytes": path.stat().st_size,
                "canonical_sha256": canonical_sha256(path),
            }
            for relative, path in sorted(files.items())
        ],
    }
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    report = {
        "schema": "world_transvoxel_terrain.tqp57_release_evidence.v1",
        "milestone": "TQP-57",
        "status": "PASS",
        "release_id": contract["release_id"],
        "version": contract["version"],
        "base_revision": git_output(ROOT, "rev-parse", "HEAD"),
        "package": package,
        "manifest": MANIFEST_PATH.relative_to(ROOT).as_posix(),
        "supported_matrix": load_json(ROOT / contract["supported_matrix_contract"])["supported_matrix"],
        "dependency": contract["dependency"],
        "evidence": contract["required_evidence"],
        "release_boundary": contract["release_boundary"],
        "review_status": "machine_review_complete_human_visual_evidence_retained",
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    run_python("tools/validate_tqp57_release.py")
    print(
        "WT_TERRAIN_TQP57_RELEASE_PASS "
        f"version={contract['version']} files={package['files']} "
        f"package={package['package_digest_sha256']} zip={package['zip_sha256']}"
    )


if __name__ == "__main__":
    main()
