#!/usr/bin/env python3

from __future__ import annotations

import argparse
import zipfile

from build_cpu_release_bundle import MANIFEST_PATH, REPORT_PATH, ZIP_PATH, bundle_files, package_digest, write_bundle
from tqp_release_common import ROOT, git_output, load_json, sha256


CONTRACT_PATH = ROOT / "CPU_RELEASE_BUNDLE_CONTRACT.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_contract() -> dict[str, object]:
    contract = load_json(CONTRACT_PATH)
    require(contract.get("schema") == "world_transvoxel_terrain.cpu_release_bundle_contract.v1", "CPU release bundle contract schema mismatch")
    require(contract.get("engine") == "4.7", "CPU release bundle requires Godot 4.7")
    require(contract.get("platform") == "windows" and contract.get("architecture") == "x86_64", "CPU release bundle target drifted")
    require(contract.get("authority", {}).get("fallback") is False, "CPU release bundle permits a fallback")
    authority = ROOT.parent / contract["authority"]["repository"]
    require(git_output(authority, "rev-parse", "HEAD") == contract["authority"]["revision"], "CPU release authority revision drifted")
    for relative in contract.get("required_evidence", []):
        path = ROOT / relative
        require(path.is_file() and load_json(path).get("status") == "PASS", f"CPU release evidence failed: {relative}")
    return contract


def validate_report(contract: dict[str, object]) -> None:
    report = load_json(REPORT_PATH)
    require(report.get("schema") == "world_transvoxel_terrain.cpu_release_bundle_evidence.v1", "CPU release bundle evidence schema mismatch")
    require(report.get("status") == "PASS" and not report.get("failures"), "CPU release bundle failed")
    require(report.get("authority_revision") == contract["authority"]["revision"], "CPU release bundle authority drifted")
    package = report["package"]
    require(ZIP_PATH.is_file() and sha256(ZIP_PATH) == package["zip_sha256"], "CPU release zip digest drifted")
    files = bundle_files(contract)
    require(package["package_digest_sha256"] == package_digest(files), "CPU release package digest drifted")
    with zipfile.ZipFile(ZIP_PATH) as archive:
        entries = set(archive.namelist())
    require(entries == {path.as_posix() for path in files}, "CPU release zip contents drifted")
    require(any(path.startswith("addons/world_transvoxel/") for path in entries), "CPU release zip omitted authority addon")
    require(any(path.startswith("addons/world_transvoxel_terrain/") for path in entries), "CPU release zip omitted terrain addon")
    require(not any("terrain_lab" in path or "gameworld" in path for path in entries), "CPU release zip contains lab/game runtime")
    for binary in (
        "addons/world_transvoxel/bin/world_transvoxel.windows.template_debug.x86_64.dll",
        "addons/world_transvoxel/bin/world_transvoxel.windows.template_release.x86_64.dll",
    ):
        require(binary in entries, f"CPU release zip omitted binary: {binary}")
    manifest = load_json(MANIFEST_PATH)
    require(manifest.get("schema") == "world_transvoxel_terrain.cpu_release_bundle_manifest.v1", "CPU release manifest schema mismatch")
    require(manifest.get("package", {}).get("zip_sha256") == package["zip_sha256"], "CPU release manifest drifted")
    require(len(manifest.get("files", [])) == package["files"], "CPU release manifest file count drifted")
    smoke = report.get("clean_install_smoke", {})
    require(smoke.get("status") == "PASS", "CPU release clean-install smoke failed")
    require(smoke.get("sibling_repository_dependency") is False, "CPU release smoke used a sibling repository")
    reproduction = ZIP_PATH.with_name(".cpu-release-reproduction.zip")
    reproduced = write_bundle(reproduction, contract)
    try:
        require(reproduced["zip_sha256"] == package["zip_sha256"], "CPU release zip is not deterministic")
    finally:
        reproduction.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-report", action="store_true")
    arguments = parser.parse_args()
    contract = validate_contract()
    if arguments.require_report:
        validate_report(contract)
    print("WT_TERRAIN_CPU_RELEASE_BUNDLE_CONTRACT_PASS engine=4.7 platform=windows-x86_64")


if __name__ == "__main__":
    main()
