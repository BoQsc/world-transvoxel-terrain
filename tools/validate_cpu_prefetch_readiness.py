#!/usr/bin/env python3

from __future__ import annotations

import argparse

from tqp_release_common import ROOT, git_output, load_json, sha256


CONTRACT_PATH = ROOT / "CPU_PREFETCH_READINESS_CONTRACT.json"
REPORT_PATH = ROOT / "artifacts/cpu_prefetch_readiness/cpu_prefetch_readiness_report.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_contract() -> dict[str, object]:
    contract = load_json(CONTRACT_PATH)
    require(
        contract.get("schema") == "world_transvoxel_terrain.cpu_prefetch_readiness_contract.v1",
        "prefetch readiness contract schema mismatch",
    )
    require(contract.get("engine") == "4.7", "prefetch readiness requires Godot 4.7")
    world = contract.get("world", {})
    require(world.get("maximum_lod") == 3, "prefetch maximum LOD drifted")
    require(world.get("global_coarse_lod_coverage") is True, "global coarse coverage is required")
    require(world.get("visual_radius_chunks") == 2, "prefetch visual radius drifted")
    require(world.get("collision_radius_chunks") == 1, "targeted collision radius drifted")
    authority = ROOT.parent / "world-transvoxel"
    require(authority.is_dir(), "world-transvoxel authority is unavailable")
    require(
        git_output(authority, "rev-parse", "HEAD") == contract.get("authority_revision"),
        "prefetch authority revision drifted",
    )
    runner = (ROOT / "tests/cpu_prefetch_readiness_runner.gd").read_text(encoding="utf-8")
    for marker in (
        '"update_viewer"',
        '"remove_viewer"',
        "visual_already_resident",
        "collision_required_lod0",
        "storage_accepted_requests",
        "mesh_jobs",
    ):
        require(marker in runner, f"prefetch runner missing marker: {marker}")
    profile = (ROOT / "addons/world_transvoxel_terrain/api/wt_terrain_runtime_profile.gd").read_text(
        encoding="utf-8"
    )
    require(
        "collision_from_visual_viewers: bool = false" in profile,
        "terrain profile does not default to explicit collision viewers",
    )
    return contract


def validate_report(contract: dict[str, object]) -> None:
    require(REPORT_PATH.is_file(), "prefetch readiness report is missing")
    report = load_json(REPORT_PATH)
    require(
        report.get("schema") == "world_transvoxel_terrain.cpu_prefetch_readiness_evidence.v1",
        "prefetch readiness report schema mismatch",
    )
    require(report.get("status") == "PASS", "prefetch readiness workload failed")
    version = report.get("engine", {})
    require(int(version.get("major", 0)) == 4 and int(version.get("minor", 0)) == 7, "report did not run on Godot 4.7")
    require(
        report.get("authority_revision") == contract.get("authority_revision"),
        "prefetch report authority revision drifted",
    )
    budget = contract.get("budgets", {})
    prefetch = report.get("prefetch", {})
    arrival = report.get("arrival", {})
    require(prefetch.get("settlement", {}).get("status") == "PASS", "prefetch did not settle")
    require(
        int(prefetch.get("work_delta", {}).get("collision_viewer_updates", -1))
        <= int(budget.get("maximum_prefetch_collision_viewer_updates", 0)),
        "visual prefetch performed collision work",
    )
    before = prefetch.get("target_state_before_arrival", {})
    require(
        int(before.get("visual_ready_lod0", 0))
        >= int(budget.get("minimum_prefetched_lod0_visual_chunks", 1)),
        "target LOD0 visuals were not prefetched",
    )
    require(int(before.get("collision_required_lod0", -1)) == 0, "prefetch activated target collision")
    settlement = arrival.get("settlement", {})
    require(settlement.get("status") == "PASS", "prefetched arrival failed")
    require(settlement.get("visual_already_resident") is True, "arrival visual was not already resident")
    work = arrival.get("work_delta", {})
    require(
        int(work.get("storage_accepted_requests", -1))
        <= int(budget.get("maximum_arrival_storage_requests", 0)),
        "arrival requested storage after prefetch",
    )
    require(
        int(work.get("mesh_jobs", -1)) <= int(budget.get("maximum_arrival_mesh_jobs", 0)),
        "arrival requested meshing after prefetch",
    )
    require(
        int(work.get("application_applied_render", -1))
        <= int(budget.get("maximum_arrival_render_publications", 0)),
        "arrival republished visual terrain after prefetch",
    )
    require(
        int(arrival.get("target_state", {}).get("collision_ready_lod0", 0))
        >= int(budget.get("minimum_arrival_lod0_collision_chunks", 1)),
        "arrival collision was not ready",
    )
    require(report.get("visual_handoff", {}).get("status") == "PASS", "visual handoff failed")
    require(not report.get("failures"), "prefetch report retained failures")
    capture_ids: set[str] = set()
    for capture in report.get("captures", []):
        capture_id = capture.get("id", "")
        path = ROOT / "artifacts/cpu_prefetch_readiness/captures" / f"{capture_id}.png"
        require(capture.get("status") == "PASS", f"capture failed: {capture_id}")
        require(path.is_file() and path.stat().st_size > 4096, f"capture is missing: {capture_id}")
        require(capture.get("sha256") == sha256(path), f"capture digest drifted: {capture_id}")
        capture_ids.add(capture_id)
    require(capture_ids == set(contract.get("required_capture_ids", [])), "prefetch capture matrix drifted")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-report", action="store_true")
    arguments = parser.parse_args()
    contract = validate_contract()
    if arguments.require_report:
        validate_report(contract)
    print("WT_TERRAIN_CPU_PREFETCH_READINESS_CONTRACT_PASS engine=4.7 visual_only=1")


if __name__ == "__main__":
    main()
