#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

from tqp_release_common import ROOT, git_output, load_json, sha256


CONTRACT_PATH = ROOT / "TQP57_LARGE_TERRAIN_ACCEPTANCE_CONTRACT.json"
REPORT_PATH = ROOT / "artifacts/tqp57_large_terrain_acceptance/tqp57_large_terrain_acceptance_report.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_contract() -> None:
    contract = load_json(CONTRACT_PATH)
    require(
        contract.get("schema")
        == "world_transvoxel_terrain.tqp57_large_terrain_acceptance_contract.v1",
        "TQP-57 large-terrain contract schema mismatch",
    )
    require(contract.get("engine") == "4.7", "large-terrain gate must use Godot 4.7")
    require(contract.get("renderer") == "forward_plus", "large-terrain renderer drifted")
    authority = contract.get("authority", {})
    require(authority.get("fallback_mesher") is False, "fallback mesher is forbidden")
    require(authority.get("fallback_field") is False, "fallback field is forbidden")
    profile = contract.get("runtime_profile", {})
    require(profile.get("volume_cells") == [2048, 256, 2048], "large terrain volume drifted")
    require(profile.get("maximum_lod") == 2, "large terrain maximum LOD drifted")
    require(contract.get("required_lod_levels") == [0, 1, 2], "required LOD matrix drifted")
    require(len(contract.get("scenarios", [])) == 9, "large terrain scenario matrix is incomplete")

    required_sources = {
        "addons/world_transvoxel_terrain/debug/wt_terrain_large_acceptance_scene.gd": (
            "class_name WtTerrainLargeAcceptanceScene",
        ),
        "addons/world_transvoxel_terrain/debug/wt_terrain_large_acceptance_runtime.gd": (
            'procedural_preset_id = &"rolling_hills_cave"',
        ),
        "addons/world_transvoxel_terrain/debug/wt_terrain_large_acceptance_qualification.gd": (
            "collect_lod_audit",
            "restart_preserving_storage",
        ),
        "addons/world_transvoxel_terrain/debug/wt_terrain_lod_audit.gd": (
            "class_name WtTerrainLodAudit",
            "coverage_overlap_count",
            "visual_generation_mismatches",
            "wt_terrain_watertightness_probe.gd",
        ),
        "addons/world_transvoxel_terrain/runtime/wt_terrain_world.gd": (
            "func query_active_chunk_states()",
        ),
        "tests/tqp57_large_terrain_acceptance.gd": (
            "WT_TERRAIN_TQP57_LARGE_ACCEPTANCE_GODOT_PASS",
            "lod_churn",
            "far_return",
            "targeted_residency",
        ),
    }
    for relative, markers in required_sources.items():
        source = (ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            require(marker in source, f"{relative} missing marker: {marker}")
        lowered = source.lower()
        require("world_transvoxel_terrain_lab" not in lowered, f"{relative} depends on Terrain Lab")
        require("world_transvoxel_gameworld" not in lowered, f"{relative} depends on game runtime")
        require("fallback_mesher" not in lowered, f"{relative} contains fallback meshing")

    repository = ROOT.parent / authority["repository"]
    require(repository.is_dir(), "world-transvoxel authority repository is unavailable")
    require(
        git_output(repository, "rev-parse", "HEAD") == authority["revision"],
        "world-transvoxel authority revision drifted",
    )


def validate_report() -> None:
    require(REPORT_PATH.is_file(), "TQP-57 large-terrain report is missing")
    report = load_json(REPORT_PATH)
    require(
        report.get("schema")
        == "world_transvoxel_terrain.tqp57_large_terrain_acceptance_evidence.v1",
        "TQP-57 large-terrain report schema mismatch",
    )
    require(report.get("status") == "PASS", "TQP-57 large-terrain acceptance failed")
    require(report.get("retained_complete") is True, "large-terrain evidence is incomplete")
    version = report.get("engine", {})
    require(int(version.get("major", 0)) == 4 and int(version.get("minor", 0)) == 7, "report did not run on Godot 4.7")
    require(len(report.get("scenarios", [])) == 9, "report scenario coverage is incomplete")
    require(all(item.get("status") == "PASS" for item in report["scenarios"]), "a report scenario failed")
    for lod in ("0", "1", "2"):
        require(int(report.get("observed_lod_counts", {}).get(lod, 0)) > 0, f"LOD{lod} was not observed")
    audit = report.get("final_lod_audit", {})
    require(audit.get("status") == "PASS", "final LOD audit failed")
    require(audit.get("coverage_overlap_count") == 0, "adaptive coverage overlaps were retained")
    require(not audit.get("visual_generation_mismatches"), "visual generation mismatch retained")
    require(not audit.get("collision_generation_mismatches"), "collision generation mismatch retained")
    topology = audit.get("topology", {})
    require(topology.get("orientation_inconsistent_edges") == 0, "shared-edge orientation inconsistency retained")
    require(report.get("collision", {}).get("status") == "PASS", "targeted collision evidence failed")
    require(report.get("persistence", {}).get("status") == "PASS", "far-return persistence failed")
    seam_audit = report.get("lod_seam_audit", {})
    require(seam_audit.get("status") == "PASS", "mixed-LOD seam audit failed")
    require(seam_audit.get("lod_seam", {}).get("found") is True, "mixed-LOD seam was not retained")
    require(
        seam_audit.get("topology", {}).get("orientation_inconsistent_edges") == 0,
        "mixed-LOD seam orientation inconsistency retained",
    )
    require(report.get("shutdown", {}).get("status") == "PASS", "clean shutdown failed")
    require(not report.get("failures"), "large-terrain report retained failures")
    capture_ids = set()
    for capture in report.get("captures", []):
        require(capture.get("status") == "PASS", f"capture failed: {capture.get('id')}")
        path = ROOT / "artifacts/tqp57_large_terrain_acceptance/captures" / f"{capture['id']}.png"
        require(path.is_file() and path.stat().st_size > 4096, f"capture is missing or blank: {path.name}")
        require(capture.get("sha256") == sha256(path), f"capture digest drifted: {path.name}")
        capture_ids.add(capture["id"])
    require(capture_ids == {"initial_lod", "edited_site", "far_return", "lod_seam"}, "capture matrix drifted")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-report", action="store_true")
    arguments = parser.parse_args()
    validate_contract()
    if arguments.require_report:
        validate_report()
    print("WT_TERRAIN_TQP57_LARGE_ACCEPTANCE_CONTRACT_PASS engine=4.7 lods=3 scenarios=9 fallback=0")


if __name__ == "__main__":
    main()
