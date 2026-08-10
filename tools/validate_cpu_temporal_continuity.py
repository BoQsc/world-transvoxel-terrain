#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

from tqp_release_common import ROOT, git_output, load_json, sha256


CONTRACT_PATH = ROOT / "CPU_TEMPORAL_CONTINUITY_CONTRACT.json"
REPORT_PATH = ROOT / "artifacts/cpu_temporal_continuity/cpu_temporal_continuity_report.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_contract() -> dict[str, object]:
    contract = load_json(CONTRACT_PATH)
    require(
        contract.get("schema")
        == "world_transvoxel_terrain.cpu_temporal_continuity_contract.v1",
        "temporal continuity contract schema mismatch",
    )
    require(contract.get("engine") == "4.7", "temporal continuity requires Godot 4.7")
    world = contract.get("world", {})
    require(world.get("maximum_lod") == 3, "temporal continuity maximum LOD drifted")
    require(world.get("global_coarse_lod_coverage") is True, "global coarse coverage is required")
    require(world.get("global_coarse_root_count") == 512, "global coarse root count drifted")
    require(len(contract.get("cases", [])) == 4, "temporal continuity case matrix is incomplete")
    authority = ROOT.parent / "world-transvoxel"
    require(authority.is_dir(), "world-transvoxel authority is unavailable")
    require(
        git_output(authority, "rev-parse", "HEAD") == contract.get("authority_revision"),
        "temporal continuity authority revision drifted",
    )
    sources = {
        "tests/cpu_temporal_continuity_runner.gd": (
            "_visible_ancestor_overlap_audit",
            "WatertightnessProbe",
            "shadow_on",
            "shadow_off",
        ),
        "addons/world_transvoxel_terrain/debug/wt_terrain_watertightness_probe.gd": (
            "is_visible_in_tree",
        ),
    }
    for relative, markers in sources.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            require(marker in text, f"{relative} missing marker: {marker}")
    return contract


def validate_report(contract: dict[str, object]) -> None:
    require(REPORT_PATH.is_file(), "temporal continuity report is missing")
    report = load_json(REPORT_PATH)
    require(
        report.get("schema")
        == "world_transvoxel_terrain.cpu_temporal_continuity_evidence.v1",
        "temporal continuity report schema mismatch",
    )
    require(report.get("status") == "PASS", "temporal continuity workload failed")
    version = report.get("engine", {})
    require(int(version.get("major", 0)) == 4 and int(version.get("minor", 0)) == 7, "report did not run on Godot 4.7")
    require(
        report.get("authority_revision") == contract.get("authority_revision"),
        "temporal report authority revision drifted",
    )
    expected_cases = [item["id"] for item in contract.get("cases", [])]
    cases = report.get("cases", [])
    require([item.get("id") for item in cases] == expected_cases, "temporal case order drifted")
    require(all(item.get("status") == "PASS" for item in cases), "a temporal case failed")
    budgets = contract.get("budgets", {})
    maximum_case_usec = int(float(budgets.get("maximum_settlement_seconds_per_case", 0)) * 1_000_000)
    require(
        all(int(item.get("latency_usec", maximum_case_usec + 1)) <= maximum_case_usec for item in cases),
        "a temporal case exceeded its settlement budget",
    )
    cases_by_id = {item["id"]: item for item in cases}
    cold_work = cases_by_id["edit_site_arrival"].get("work_delta", {})
    warm_work = cases_by_id["local_refinement_return"].get("work_delta", {})
    cold_storage = int(cold_work.get("storage_accepted_requests", 0))
    warm_storage = int(warm_work.get("storage_accepted_requests", cold_storage + 1))
    require(cold_storage > 0, "cold-arrival storage evidence is missing")
    require(
        warm_storage <= cold_storage * float(budgets.get("maximum_warm_revisit_storage_request_fraction", 0)),
        "bounded source-page cache did not reduce warm-revisit storage work",
    )
    require(
        int(warm_work.get("page_cache_decoded_hits", 0))
        >= int(budgets.get("minimum_warm_revisit_decoded_cache_hits", 0)),
        "warm revisit recorded no decoded-page cache hits",
    )
    require(
        int(report.get("monitored_frames", 0)) >= int(budgets.get("minimum_monitored_frames", 0)),
        "temporal frame evidence is incomplete",
    )
    require(
        int(report.get("maximum_visible_ancestor_overlaps", -1))
        <= int(budgets.get("maximum_visible_ancestor_overlaps", 0)),
        "visible parent-child overlap retained",
    )
    require(
        int(report.get("topology_failures", -1)) <= int(budgets.get("maximum_topology_failures", 0)),
        "temporal topology failure retained",
    )
    require(not report.get("failures"), "temporal report retained failures")
    capture_ids = set()
    for capture in report.get("captures", []):
        capture_id = capture.get("id", "")
        path = ROOT / "artifacts/cpu_temporal_continuity/captures" / f"{capture_id}.png"
        require(capture.get("status") == "PASS", f"capture failed: {capture_id}")
        require(path.is_file() and path.stat().st_size > 4096, f"capture is missing or blank: {capture_id}")
        require(capture.get("sha256") == sha256(path), f"capture digest drifted: {capture_id}")
        capture_ids.add(capture_id)
    require(capture_ids == set(contract.get("required_capture_ids", [])), "temporal capture matrix drifted")
    maximum_background = int(budgets.get("maximum_center_background_pixels", 0))
    for analysis in report.get("image_analysis", {}).get("diagnostic_captures", []):
        require(
            int(analysis.get("center_background_pixels", -1)) <= maximum_background,
            f"diagnostic capture exposed background in terrain center: {analysis.get('id')}",
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-report", action="store_true")
    arguments = parser.parse_args()
    contract = validate_contract()
    if arguments.require_report:
        validate_report(contract)
    print("WT_TERRAIN_CPU_TEMPORAL_CONTINUITY_CONTRACT_PASS engine=4.7 lods=4 shadows=paired")


if __name__ == "__main__":
    main()
