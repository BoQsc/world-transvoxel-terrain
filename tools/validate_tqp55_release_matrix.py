#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

from tqp_release_common import (
    ADDON_ROOT,
    ROOT,
    git_output,
    load_json,
    package_digest,
    sha256,
)


CONTRACT_PATH = ROOT / "TQP55_RELEASE_MATRIX.json"
REPORT_PATH = ROOT / "artifacts" / "tqp55_release_matrix" / "tqp55_release_matrix_report.json"
REPOSITORY_ROOT = ROOT.parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def engine_names(report: dict) -> list[str]:
    return [str(item.get("engine", "")) for item in report.get("engines", [])]


def validate_static_contract() -> None:
    contract = load_json(CONTRACT_PATH)
    require(
        contract.get("schema") == "world_transvoxel_terrain.tqp55_release_matrix.v1",
        "TQP-55 schema mismatch",
    )
    require(contract.get("version") == "1.0.0", "TQP-55 version mismatch")
    matrix = contract.get("supported_matrix", {})
    require(matrix.get("engine_versions") == ["4.7"], "Godot matrix must be 4.7 only")
    require(matrix.get("platforms") == ["windows-10-x86_64"], "platform matrix drifted")
    require(matrix.get("renderers") == ["forward_plus"], "renderer matrix drifted")
    require(len(matrix.get("profiles", [])) == 4, "runtime profile matrix is incomplete")
    authority = contract.get("authority", {})
    require(authority.get("fallback_mesher") is False, "fallback mesher is forbidden")
    require(authority.get("fallback_field") is False, "fallback field is forbidden")

    plugin = (ADDON_ROOT / "plugin.cfg").read_text(encoding="utf-8")
    require('version="1.0.0"' in plugin, "addon version is not 1.0.0")
    project = (ROOT / "project.godot").read_text(encoding="utf-8")
    require('PackedStringArray("4.7", "Forward Plus")' in project, "project does not require Godot 4.7")
    fixture_builders = [
        ROOT / "tools" / name
        for name in (
            "a3_bridge_smoke.py",
            "a4_phase2_bridge_storage_smoke.py",
            "a4_phase3_terrain_world_lifecycle_smoke.py",
            "a4_phase4_reference_runtime_cold_idle_smoke.py",
            "a5_phase3_reference_scene_runtime_smoke.py",
            "a5_phase4_debug_overlay_categories_smoke.py",
        )
    ]
    for path in fixture_builders:
        source = path.read_text(encoding="utf-8")
        require('PackedStringArray("4.6"' not in source, f"legacy fixture feature in {path.name}")
        require('PackedStringArray("4.7"' in source, f"Godot 4.7 fixture feature missing in {path.name}")

    forbidden = ("marching_cubes_fallback", "fallback_mesher", "fallback_density_field")
    for path in ADDON_ROOT.rglob("*"):
        if path.is_file() and path.suffix in {".gd", ".gdshader", ".glsl"}:
            source = path.read_text(encoding="utf-8", errors="replace").lower()
            require(not any(item in source for item in forbidden), f"terrain fallback marker in {path}")

    authority_repo = REPOSITORY_ROOT / authority["repository"]
    require(authority_repo.is_dir(), "world-transvoxel authority repository is missing")
    require(
        git_output(authority_repo, "rev-parse", "HEAD") == authority["revision"],
        "world-transvoxel authority revision drifted",
    )
    for artifact in authority.get("native_artifacts", []):
        path = authority_repo / artifact["path"]
        require(path.is_file(), f"native artifact missing: {path}")
        require(path.stat().st_size == artifact["bytes"], f"native artifact size drifted: {path.name}")
        require(sha256(path) == artifact["sha256"], f"native artifact digest drifted: {path.name}")

    for relative, schema in (
        ("artifacts/tqp52_runtime_contract/tqp52_runtime_contract_report.json", "world_transvoxel_terrain.tqp52_runtime_evidence.v1"),
        ("artifacts/tqp53_authoring_workflow/tqp53_authoring_workflow_report.json", "world_transvoxel_terrain.tqp53_authoring_evidence.v1"),
    ):
        path = ROOT / relative
        require(path.is_file(), f"required local evidence missing: {relative}")
        report = load_json(path)
        require(report.get("schema") == schema, f"local evidence schema drifted: {relative}")
        require(report.get("status") == "PASS", f"local evidence failed: {relative}")
        require(engine_names(report) == ["4.7"], f"local evidence engine matrix drifted: {relative}")

    for evidence in contract.get("required_retained_evidence", []):
        repository = REPOSITORY_ROOT / evidence["repository"]
        path = repository / evidence["path"]
        require(path.is_file(), f"retained evidence missing: {path}")
        require(sha256(path) == evidence["sha256"], f"retained evidence digest drifted: {path.name}")
        payload = load_json(path)
        require(payload.get("status") in evidence["accepted_status"], f"retained evidence status rejected: {path.name}")
        if evidence.get("requires_retained_complete"):
            require(payload.get("retained_complete") is True, f"retained evidence is incomplete: {path.name}")


def validate_report() -> None:
    require(REPORT_PATH.is_file(), "TQP-55 report is missing")
    report = load_json(REPORT_PATH)
    require(report.get("schema") == "world_transvoxel_terrain.tqp55_release_matrix_evidence.v1", "TQP-55 report schema mismatch")
    require(report.get("status") == "PASS", "TQP-55 report failed")
    require(report.get("engine_versions") == ["4.7"], "TQP-55 report engine matrix drifted")
    package = report.get("package", {})
    require(package.get("package_digest_sha256") == package_digest(), "TQP-55 package digest drifted")
    zip_path = ROOT / str(package.get("path", ""))
    require(zip_path.is_file(), "TQP-55 candidate zip is missing")
    require(package.get("zip_sha256") == sha256(zip_path), "TQP-55 candidate zip digest drifted")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-report", action="store_true")
    arguments = parser.parse_args()
    validate_static_contract()
    if arguments.require_report:
        validate_report()
    print(
        "WT_TERRAIN_TQP55_RELEASE_MATRIX_PASS "
        f"engines=1 profiles=4 package_digest={package_digest()}"
    )


if __name__ == "__main__":
    main()
