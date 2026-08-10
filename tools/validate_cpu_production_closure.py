#!/usr/bin/env python3

from __future__ import annotations

import argparse

from tqp_release_common import ROOT, git_output, load_json, sha256


CONTRACT_PATH = ROOT / "CPU_PRODUCTION_CLOSURE_CONTRACT.json"
REPORT_PATH = ROOT / "artifacts/cpu_production_closure/cpu_production_closure_report.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_contract() -> dict[str, object]:
    contract = load_json(CONTRACT_PATH)
    require(
        contract.get("schema") == "world_transvoxel_terrain.cpu_production_closure_contract.v1",
        "CPU production closure contract schema mismatch",
    )
    require(contract.get("engine") == "4.7", "CPU closure requires Godot 4.7")
    require(contract.get("renderer") == "forward_plus", "CPU closure renderer drifted")
    profile = contract.get("runtime_profile", {})
    require(profile.get("volume_cells") == [2048, 256, 2048], "CPU closure world size drifted")
    require(profile.get("maximum_lod") == 3, "CPU closure LOD ceiling drifted")
    require(profile.get("maximum_logical_cpu_count") == 3, "CPU closure CPU ceiling drifted")
    require(profile.get("global_coarse_lod_coverage") is True, "CPU closure requires global coarse coverage")
    authority = ROOT.parent / contract["authority"]["repository"]
    require(authority.is_dir(), "CPU closure authority repository is missing")
    require(
        git_output(authority, "rev-parse", "HEAD") == contract["authority"]["revision"],
        "CPU closure authority revision drifted",
    )
    for evidence_id, relative in contract.get("required_evidence", {}).items():
        path = ROOT / relative
        require(path.is_file(), f"CPU closure evidence missing: {evidence_id}")
        require(load_json(path).get("status") == "PASS", f"CPU closure evidence failed: {evidence_id}")
    return contract


def validate_report(contract: dict[str, object]) -> None:
    require(REPORT_PATH.is_file(), "CPU production closure report is missing")
    report = load_json(REPORT_PATH)
    require(
        report.get("schema") == "world_transvoxel_terrain.cpu_production_closure_evidence.v1",
        "CPU production closure evidence schema mismatch",
    )
    require(report.get("status") == "PASS" and not report.get("failures"), "CPU production closure failed")
    require(report.get("authority_revision") == contract["authority"]["revision"], "CPU closure authority drifted")
    for evidence_id, evidence in report.get("source_evidence", {}).items():
        path = ROOT / evidence["path"]
        require(evidence_id in contract["required_evidence"], f"unknown CPU closure evidence: {evidence_id}")
        require(path.is_file() and sha256(path) == evidence["sha256"], f"CPU closure evidence digest drifted: {evidence_id}")
    budgets = contract["budgets"]
    coverage = report["coverage"]
    require(coverage["catalog_pages"] >= budgets["minimum_catalog_pages"], "CPU closure catalog floor missed")
    require(coverage["lod0_equivalent_coverage_cells"] == budgets["required_full_world_lod0_coverage"], "CPU closure world coverage drifted")
    performance = report["performance"]
    require(performance["frame_samples"] >= 2700, "CPU closure frame evidence is incomplete")
    require(performance["frame_p99_usec"] <= budgets["maximum_frame_p99_usec"], "CPU closure frame p99 failed")
    require(performance["frame_worst_usec"] <= budgets["maximum_frame_worst_usec"], "CPU closure worst frame failed")
    require(performance["maximum_stutter_fraction_over_100ms"] <= budgets["maximum_stutter_fraction_over_100ms"], "CPU closure stutter budget failed")
    telemetry = performance["process_telemetry"]
    require(0 < telemetry["logical_cpu_count"] <= 3, "CPU closure process affinity exceeded three CPUs")
    require(telemetry["peak_rss_bytes"] <= budgets["maximum_peak_process_memory_bytes"], "CPU closure peak RSS failed")
    require(performance["memory"]["video_bytes"] <= budgets["maximum_peak_video_memory_bytes"], "CPU closure video memory failed")
    for queue, budget in {
        "scheduler": "maximum_scheduler_queue_depth",
        "storage": "maximum_storage_queue_depth",
        "render": "maximum_render_queue_depth",
        "collision": "maximum_collision_queue_depth",
    }.items():
        require(performance["queue_peaks"][queue] <= budgets[budget], f"CPU closure {queue} queue failed")
    prefetch = report["streaming"]["prefetch_arrival"]
    require(prefetch["storage_requests"] == 0 and prefetch["mesh_jobs"] == 0, "CPU closure prefetched arrival performed cold work")
    require(prefetch["render_publications"] == 0, "CPU closure prefetched arrival republished visuals")
    require(prefetch["collision_ready_lod0_chunks"] > 0, "CPU closure targeted collision was not ready")
    for edit_id in ("digging", "construction"):
        edit = report["edits"][edit_id]
        require(edit["status"] == "PASS", f"CPU closure {edit_id} failed")
        require(edit["first_visual_latency_usec"] <= budgets["maximum_edit_visual_latency_usec"], f"CPU closure {edit_id} visual latency failed")
        require(edit["first_collision_latency_usec"] <= budgets["maximum_edit_collision_latency_usec"], f"CPU closure {edit_id} collision latency failed")
    require(not report["edits"]["construction_material_ownership"]["repainted_existing_solid_samples"], "CPU closure construction repainted existing terrain")
    correctness = report["correctness"]
    require(correctness["coverage_overlaps"] == 0, "CPU closure coverage overlap retained")
    require(correctness["visual_generation_mismatches"] == 0, "CPU closure visual generation mismatch retained")
    require(correctness["collision_generation_mismatches"] == 0, "CPU closure collision generation mismatch retained")
    require(all(value == 0 for value in correctness["topology"].values()), "CPU closure topology failure retained")
    temporal = correctness["temporal_continuity"]
    require(temporal["topology_failures"] == 0 and temporal["visible_ancestor_overlaps"] == 0, "CPU closure temporal continuity failed")
    require(report["power"]["status"] == "UNQUALIFIED_NO_TRUSTED_ENERGY_PROVIDER", "CPU closure invented a power claim")
    document = (ROOT / "docs/CPU_PRODUCTION_BASELINE.md").read_text(encoding="utf-8")
    for marker in ("Measured baseline", "Interpretation", "CPU-package watts", "Reproduce"):
        require(marker in document, f"CPU production baseline document missing: {marker}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-report", action="store_true")
    arguments = parser.parse_args()
    contract = validate_contract()
    if arguments.require_report:
        validate_report(contract)
    print("WT_TERRAIN_CPU_PRODUCTION_CLOSURE_CONTRACT_PASS engine=4.7 cpus=3 lods=4")


if __name__ == "__main__":
    main()
