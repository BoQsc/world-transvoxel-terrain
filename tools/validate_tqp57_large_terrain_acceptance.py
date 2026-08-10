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


def validate_contract() -> dict[str, object]:
    contract = load_json(CONTRACT_PATH)
    require(
        contract.get("schema")
        == "world_transvoxel_terrain.tqp57_large_terrain_acceptance_contract.v2",
        "TQP-57 large-terrain contract schema mismatch",
    )
    require(contract.get("engine") == "4.7", "large-terrain gate must use Godot 4.7")
    require(contract.get("renderer") == "forward_plus", "large-terrain renderer drifted")
    authority = contract.get("authority", {})
    require(authority.get("fallback_mesher") is False, "fallback mesher is forbidden")
    require(authority.get("fallback_field") is False, "fallback field is forbidden")
    profile = contract.get("runtime_profile", {})
    require(profile.get("volume_cells") == [2048, 256, 2048], "large terrain volume drifted")
    require(profile.get("maximum_lod") == 3, "large terrain maximum LOD drifted")
    require(profile.get("global_coarse_lod_coverage") is True, "global coarse coverage is required")
    require(profile.get("global_coarse_root_count") == 512, "global coarse root count drifted")
    require(contract.get("required_lod_levels") == [0, 1, 2, 3], "required LOD matrix drifted")
    require(
        contract.get("budgets", {}).get("required_full_world_lod0_coverage") == 262144,
        "full-world coverage requirement drifted",
    )
    require(len(contract.get("scenarios", [])) == 9, "large terrain scenario matrix is incomplete")
    require(
        profile.get("maximum_logical_cpu_count") == 3,
        "large terrain CPU affinity ceiling drifted",
    )

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
        "tests/tqp57_large_terrain_acceptance_runner.gd": (
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
    return contract


def validate_report(contract: dict[str, object]) -> None:
    require(REPORT_PATH.is_file(), "TQP-57 large-terrain report is missing")
    report = load_json(REPORT_PATH)
    require(
        report.get("schema")
        == "world_transvoxel_terrain.tqp57_large_terrain_acceptance_evidence.v1",
        "TQP-57 large-terrain report schema mismatch",
    )
    require(report.get("status") == "PASS", "TQP-57 large-terrain acceptance failed")
    require(report.get("retained_complete") is True, "large-terrain evidence is incomplete")
    require(
        report.get("authority_revision") == contract.get("authority", {}).get("revision"),
        "large-terrain evidence authority revision drifted",
    )
    version = report.get("engine", {})
    require(int(version.get("major", 0)) == 4 and int(version.get("minor", 0)) == 7, "report did not run on Godot 4.7")
    require(len(report.get("scenarios", [])) == 9, "report scenario coverage is incomplete")
    require(all(item.get("status") == "PASS" for item in report["scenarios"]), "a report scenario failed")
    budgets = contract.get("budgets", {})
    for scenario in report["scenarios"]:
        frame = scenario.get("frame", {})
        require(
            int(frame.get("sample_count", 0))
            >= int(budgets.get("minimum_frame_samples_per_scenario", 0)),
            f"{scenario.get('id')} retained too few frame samples",
        )
        require(
            float(frame.get("p99_usec", float("inf")))
            <= float(budgets.get("maximum_frame_p99_usec", 0)),
            f"{scenario.get('id')} frame p99 exceeded budget",
        )
        require(
            float(frame.get("worst_usec", float("inf")))
            <= float(budgets.get("maximum_frame_worst_usec", 0)),
            f"{scenario.get('id')} worst frame exceeded budget",
        )
        require(
            float(scenario.get("stutter_fraction_over_100ms", float("inf")))
            <= float(budgets.get("maximum_stutter_fraction_over_100ms", 0)),
            f"{scenario.get('id')} stutter fraction exceeded budget",
        )
    profile = report.get("profile", {})
    require(profile.get("maximum_lod") == 3, "report maximum LOD drifted")
    require(profile.get("global_coarse_lod_coverage") is True, "report omitted global coarse coverage")
    require(profile.get("global_coarse_root_count") == 512, "report coarse-root count drifted")
    require(
        int(report.get("initial_snapshot", {}).get("catalog_page_count", 0))
        >= int(budgets.get("minimum_catalog_pages", 0)),
        "catalog page count missed the acceptance floor",
    )
    for lod in ("0", "1", "2", "3"):
        require(int(report.get("observed_lod_counts", {}).get(lod, 0)) > 0, f"LOD{lod} was not observed")
    audit = report.get("final_lod_audit", {})
    require(audit.get("status") == "PASS", "final LOD audit failed")
    require(audit.get("coverage_overlap_count") == 0, "adaptive coverage overlaps were retained")
    require(not audit.get("visual_generation_mismatches"), "visual generation mismatch retained")
    require(not audit.get("collision_generation_mismatches"), "collision generation mismatch retained")
    require(audit.get("lod0_coverage_cells") == 262144, "full-world coverage was not retained")
    bootstrap = report.get("global_coverage_bootstrap", {})
    require(bootstrap.get("coarse_stage_ready") is True, "global coarse bootstrap never became ready")
    require(bootstrap.get("refinement_requested") is True, "local refinement did not follow coarse bootstrap")
    require(int(bootstrap.get("coarse_ready_latency_usec", 0)) > 0, "coarse startup latency is missing")
    require(
        int(bootstrap.get("coarse_ready_latency_usec", 0))
        <= int(float(budgets.get("maximum_coarse_startup_seconds", 0)) * 1_000_000),
        "global coarse bootstrap exceeded its time budget",
    )
    queue_peaks = report.get("queue_peaks", {})
    for queue, budget_name in {
        "scheduler": "maximum_scheduler_queue_depth",
        "storage": "maximum_storage_queue_depth",
        "render": "maximum_render_queue_depth",
        "collision": "maximum_collision_queue_depth",
    }.items():
        require(
            int(queue_peaks.get(queue, -1)) <= int(budgets.get(budget_name, -1)),
            f"{queue} queue exceeded its budget",
        )
    telemetry = report.get("process_telemetry", {})
    affinity = telemetry.get("logical_cpu_affinity", [])
    require(
        0 < len(affinity) <= int(contract.get("runtime_profile", {}).get("maximum_logical_cpu_count", 0)),
        "large-terrain process exceeded the logical CPU ceiling",
    )
    require(int(telemetry.get("sample_count", 0)) > 0, "process telemetry was not sampled")
    require(float(telemetry.get("process_cpu_seconds", 0)) > 0, "process CPU time is missing")
    require(
        int(telemetry.get("peak_rss_bytes", 0))
        <= int(budgets.get("maximum_peak_process_memory_bytes", 0)),
        "peak process RSS exceeded its budget",
    )
    construction = next(item for item in report["scenarios"] if item.get("id") == "construction")
    ownership = construction.get("material_ownership", {})
    require(ownership.get("status") == "PASS", "construction material ownership failed")
    require(not ownership.get("repainted_existing_solid_samples"), "construction repainted existing terrain")
    for scenario_id in ("digging", "construction"):
        edit = next(item for item in report["scenarios"] if item.get("id") == scenario_id).get("edit", {})
        require(edit.get("status") == "PASS", f"{scenario_id} edit failed")
        require(
            int(edit.get("first_visual_latency_usec", 0))
            <= int(budgets.get("maximum_edit_visual_latency_usec", 0)),
            f"{scenario_id} visual latency exceeded budget",
        )
        require(
            int(edit.get("first_collision_latency_usec", 0))
            <= int(budgets.get("maximum_edit_collision_latency_usec", 0)),
            f"{scenario_id} collision latency exceeded budget",
        )
    topology = audit.get("topology", {})
    require(topology.get("orientation_inconsistent_edges") == 0, "shared-edge orientation inconsistency retained")
    for field, budget_name in {
        "boundary_edges": "maximum_topology_boundary_edges",
        "nonmanifold_edges": "maximum_topology_nonmanifold_edges",
        "orientation_inconsistent_edges": "maximum_topology_orientation_inconsistent_edges",
        "zero_area_triangles": "maximum_topology_zero_area_triangles",
    }.items():
        require(
            int(topology.get(field, -1)) <= int(budgets.get(budget_name, -1)),
            f"topology {field} exceeded budget",
        )
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
    require(
        capture_ids == {"global_coarse", "initial_lod", "edited_site", "far_return", "lod_seam"},
        "capture matrix drifted",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-report", action="store_true")
    arguments = parser.parse_args()
    contract = validate_contract()
    if arguments.require_report:
        validate_report(contract)
    print("WT_TERRAIN_TQP57_LARGE_ACCEPTANCE_CONTRACT_PASS engine=4.7 lods=4 global_coarse=1 scenarios=9 fallback=0")


if __name__ == "__main__":
    main()
