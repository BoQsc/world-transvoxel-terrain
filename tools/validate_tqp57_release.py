#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import zipfile

from tqp_release_common import ROOT, load_json, package_digest, sha256, tracked_addon_files, write_deterministic_addon_zip


ARTIFACT_ROOT = ROOT / "artifacts" / "tqp57_release"
REPORT_PATH = ARTIFACT_ROOT / "tqp57_release_report.json"
MANIFEST_PATH = ARTIFACT_ROOT / "world-transvoxel-terrain-1.0.0.manifest.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    contract = load_json(ROOT / "TQP57_RELEASE_CONTRACT.json")
    require(contract.get("schema") == "world_transvoxel_terrain.tqp57_release_contract.v1", "TQP-57 contract schema mismatch")
    require(contract.get("version") == "1.0.0", "TQP-57 version mismatch")
    require(contract.get("package_root") == "addons/world_transvoxel_terrain", "TQP-57 package root drifted")
    dependency = contract.get("dependency", {})
    require(dependency.get("bundled") is False and dependency.get("fallback") is False, "TQP-57 dependency boundary drifted")
    require(dependency.get("revision") == "f4abd7ab4f921f98aba4ee45b4453af0bae53cd8", "TQP-57 authority pin drifted")

    for relative in contract.get("required_evidence", []):
        path = ROOT / relative
        require(path.is_file(), f"TQP-57 evidence missing: {relative}")
        require(load_json(path).get("status") == "PASS", f"TQP-57 evidence failed: {relative}")
    for relative, markers in {
        "docs/CPU_TERRAIN_STANDARD_1_0.md": ("Authoritative boundaries", "Targeted collision", "Performance evidence", "Unqualified scope"),
        "docs/TQP57_STANDALONE_RELEASE.md": ("Installation", "Migration", "Reproduce"),
        "CHANGELOG.md": ("1.0.0", "Godot 4.7"),
        "addons/world_transvoxel_terrain/README.md": ("Version: `1.0.0`", "Godot 4.7"),
    }.items():
        source = (ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            require(marker in source, f"{relative} missing marker: {marker}")

    report = load_json(REPORT_PATH)
    require(report.get("schema") == "world_transvoxel_terrain.tqp57_release_evidence.v1", "TQP-57 report schema mismatch")
    require(report.get("status") == "PASS", "TQP-57 report failed")
    require(report.get("release_boundary") == "limited_windows_cpu_reference_release", "TQP-57 release boundary drifted")
    package = report.get("package", {})
    require(package.get("package_digest_sha256") == package_digest(), "TQP-57 package digest drifted")
    zip_path = ROOT / str(package.get("path", ""))
    require(zip_path.is_file() and sha256(zip_path) == package.get("zip_sha256"), "TQP-57 zip digest drifted")
    expected_entries = {
        f"addons/world_transvoxel_terrain/{relative.as_posix()}"
        for relative in tracked_addon_files()
    }
    with zipfile.ZipFile(zip_path) as archive:
        require(set(archive.namelist()) == expected_entries, "TQP-57 zip contents drifted")
        require(not any("world_transvoxel_terrain_lab" in name or "gameworld" in name for name in archive.namelist()), "TQP-57 package contains lab/game runtime")

    manifest = load_json(MANIFEST_PATH)
    require(manifest.get("schema") == "world_transvoxel_terrain.release_manifest.v1", "TQP-57 manifest schema mismatch")
    require(manifest.get("package", {}).get("zip_sha256") == package.get("zip_sha256"), "TQP-57 manifest package drifted")
    require(len(manifest.get("files", [])) == package.get("files"), "TQP-57 manifest file count drifted")
    verification_zip = ARTIFACT_ROOT / ".tqp57-repro-check.zip"
    reproduced = write_deterministic_addon_zip(verification_zip)
    try:
        require(reproduced["zip_sha256"] == package.get("zip_sha256"), "TQP-57 zip is not reproducible")
    finally:
        verification_zip.unlink(missing_ok=True)
    print(
        "WT_TERRAIN_TQP57_RELEASE_CONTRACT_PASS "
        f"version=1.0.0 files={package['files']} package={package['package_digest_sha256']}"
    )


if __name__ == "__main__":
    main()
