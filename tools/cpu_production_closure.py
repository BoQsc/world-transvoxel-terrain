#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path

import psutil

from tqp_release_common import ROOT, git_output, load_json, run_python, sha256


CONTRACT_PATH = ROOT / "CPU_PRODUCTION_CLOSURE_CONTRACT.json"
ARTIFACT_ROOT = ROOT / "artifacts" / "cpu_production_closure"
REPORT_PATH = ARTIFACT_ROOT / "cpu_production_closure_report.json"
DOCUMENT_PATH = ROOT / "docs" / "CPU_PRODUCTION_BASELINE.md"


def source_evidence(contract: dict[str, object]) -> tuple[dict[str, dict[str, object]], dict[str, dict]]:
    retained: dict[str, dict[str, object]] = {}
    reports: dict[str, dict] = {}
    for evidence_id, relative in contract["required_evidence"].items():
        path = ROOT / relative
        report = load_json(path)
        if report.get("status") != "PASS":
            raise RuntimeError(f"component evidence failed: {evidence_id}")
        reports[evidence_id] = report
        retained[evidence_id] = {
            "path": relative,
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
            "schema": report.get("schema"),
            "status": report.get("status"),
        }
    return retained, reports


def edit_summary(large: dict, scenario_id: str) -> dict[str, object]:
    scenario = next(item for item in large["scenarios"] if item["id"] == scenario_id)
    edit = scenario["edit"]
    return {
        "status": edit["status"],
        "commit_latency_usec": edit["commit_latency_usec"],
        "first_visual_latency_usec": edit["first_visual_latency_usec"],
        "first_collision_latency_usec": edit["first_collision_latency_usec"],
        "settlement_latency_usec": edit["latency_usec"],
    }


def write_document(report: dict[str, object]) -> None:
    performance = report["performance"]
    telemetry = performance["process_telemetry"]
    prefetch = report["streaming"]["prefetch_arrival"]
    temporal = report["correctness"]["temporal_continuity"]
    digging = report["edits"]["digging"]
    construction = report["edits"]["construction"]
    queues = performance["queue_peaks"]
    lines = [
        "# CPU Production Terrain Baseline",
        "",
        f"Status: **{report['status']}**",
        "",
        "This is the reproducible CPU reference baseline for the bounded production terrain standard. It is not a claim that every frame already meets 60 FPS, and it is not a 16 W power qualification.",
        "",
        "## Fixed configuration",
        "",
        "- Godot 4.7 Forward+ on Windows x86-64.",
        "- World: 2,048 x 256 x 2,048 cells, 299,520 catalog pages.",
        "- LOD0 through LOD3 with 512 globally resident LOD3 coarse roots.",
        "- Two native meshing workers, two procedural/storage workers, and at most three logical CPUs.",
        "- Visual radius 2 chunks; targeted collision radius 1 chunk.",
        "",
        "## Measured baseline",
        "",
        f"- Frame samples: {performance['frame_samples']} across nine scenarios; p50 {performance['frame_p50_usec'] / 1000.0:.3f} ms, p99 {performance['frame_p99_usec'] / 1000.0:.3f} ms, worst {performance['frame_worst_usec'] / 1000.0:.3f} ms.",
        f"- Process: {telemetry['process_cpu_seconds']:.3f} CPU-seconds over {telemetry['wall_seconds']:.3f} s, {telemetry['average_cpu_cores']:.3f} average occupied cores, {telemetry['average_affinity_utilization_percent']:.1f}% of the three-CPU affinity capacity.",
        f"- Peak RSS: {telemetry['peak_rss_bytes'] / (1024 * 1024):.1f} MiB; peak Godot video memory: {performance['memory']['video_bytes'] / (1024 * 1024):.1f} MiB.",
        f"- Queue peaks: scheduler {queues['scheduler']}, storage {queues['storage']}, render {queues['render']}, collision {queues['collision']}.",
        f"- Coarse world became ready in {report['coverage']['coarse_ready_latency_usec'] / 1_000_000.0:.3f} s with all 262,144 LOD0-equivalent cells covered.",
        f"- Prefetched arrival: storage jobs {prefetch['storage_requests']}, mesh jobs {prefetch['mesh_jobs']}, first collision {prefetch['first_collision_latency_usec'] / 1000.0:.3f} ms.",
        f"- Dig: visual {digging['first_visual_latency_usec'] / 1000.0:.3f} ms, collision {digging['first_collision_latency_usec'] / 1000.0:.3f} ms.",
        f"- Construct: visual {construction['first_visual_latency_usec'] / 1000.0:.3f} ms, collision {construction['first_collision_latency_usec'] / 1000.0:.3f} ms; existing solid samples repainted: 0.",
        f"- Temporal continuity: {temporal['monitored_frames']} monitored frames, {temporal['topology_samples']} topology samples, {temporal['visible_ancestor_overlaps']} visible ancestor overlaps, {temporal['topology_failures']} topology failures.",
        "",
        "## Interpretation",
        "",
        "The authority, terrain wrapper, global coarse coverage, local refinement, temporal publication, warm reuse, prefetch handoff, targeted collision, digging, construction, persistence, and bounded resource envelopes pass together. The measured p99 is a comparison baseline for future CPU or GPU work, not proof of a universal frame rate on other hardware.",
        "",
        "CPU-package watts and whole-system watts remain unqualified because this host has no trusted package-energy provider. GPU-board watts are a separate metric and must not be presented as CPU terrain power.",
        "",
        "## Reproduce",
        "",
        "```console",
        "python ../world-transvoxel-cell-lab/labs/terrain_lab/tools/run_with_cpu_limit.py --logical-cpus 3 -- python tools/tqp57_large_terrain_acceptance.py",
        "python ../world-transvoxel-cell-lab/labs/terrain_lab/tools/run_with_cpu_limit.py --logical-cpus 3 -- python tools/cpu_temporal_continuity.py",
        "python ../world-transvoxel-cell-lab/labs/terrain_lab/tools/run_with_cpu_limit.py --logical-cpus 3 -- python tools/cpu_prefetch_readiness.py",
        "python ../world-transvoxel-cell-lab/labs/terrain_lab/tools/run_with_cpu_limit.py --logical-cpus 3 -- python tools/cpu_production_closure.py",
        "```",
        "",
    ]
    DOCUMENT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    run_python("tools/validate_tqp57_large_terrain_acceptance.py", "--require-report")
    run_python("tools/validate_cpu_temporal_continuity.py", "--require-report")
    run_python("tools/validate_cpu_prefetch_readiness.py", "--require-report")
    contract = load_json(CONTRACT_PATH)
    affinity = psutil.Process().cpu_affinity()
    maximum_cpus = int(contract["runtime_profile"]["maximum_logical_cpu_count"])
    if not affinity or len(affinity) > maximum_cpus:
        raise RuntimeError("CPU closure must run inside the three-logical-CPU limiter")
    retained, reports = source_evidence(contract)
    large = reports["large_terrain"]
    temporal = reports["temporal_continuity"]
    prefetch = reports["prefetch_readiness"]
    frames = [item["frame"] for item in large["scenarios"]]
    topology = large["final_lod_audit"]["topology"]
    arrival = prefetch["arrival"]
    report = {
        "schema": "world_transvoxel_terrain.cpu_production_closure_evidence.v1",
        "milestone": "TQP-R05",
        "status": "PASS",
        "release_id": contract["release_id"],
        "terrain_revision": git_output(ROOT, "rev-parse", "HEAD"),
        "authority_revision": git_output(ROOT.parent / "world-transvoxel", "rev-parse", "HEAD"),
        "engine": large["engine"],
        "renderer": large["renderer"],
        "execution": {
            "closure_process_logical_cpu_affinity": affinity,
            "maximum_logical_cpu_count": maximum_cpus,
            "meshing_worker_count": large["profile"]["meshing_worker_count"],
            "procedural_generation_worker_count": large["profile"]["procedural_generation_worker_count"],
        },
        "source_evidence": retained,
        "coverage": {
            "volume_cells": large["profile"]["volume_cells"],
            "catalog_pages": large["initial_snapshot"]["catalog_page_count"],
            "global_coarse_roots": large["profile"]["global_coarse_root_count"],
            "lod0_equivalent_coverage_cells": large["final_lod_audit"]["lod0_coverage_cells"],
            "coarse_ready_latency_usec": large["global_coverage_bootstrap"]["coarse_ready_latency_usec"],
            "observed_lod_counts": large["observed_lod_counts"],
        },
        "performance": {
            "frame_samples": sum(int(item["sample_count"]) for item in frames),
            "frame_p50_usec": max(float(item["p50_usec"]) for item in frames),
            "frame_p99_usec": max(float(item["p99_usec"]) for item in frames),
            "frame_worst_usec": max(float(item["worst_usec"]) for item in frames),
            "maximum_stutter_fraction_over_100ms": max(
                float(item["stutter_fraction_over_100ms"]) for item in large["scenarios"]
            ),
            "queue_peaks": large["queue_peaks"],
            "memory": large["memory"],
            "process_telemetry": large["process_telemetry"],
        },
        "streaming": {
            "warm_revisit_storage_requests": temporal["cases"][-1]["work_delta"]["storage_accepted_requests"],
            "warm_revisit_decoded_cache_hits": temporal["cases"][-1]["work_delta"]["page_cache_decoded_hits"],
            "prefetch_arrival": {
                "prefetched_visual_lod0_chunks": prefetch["prefetch"]["target_state_before_arrival"]["visual_ready_lod0"],
                "storage_requests": arrival["work_delta"]["storage_accepted_requests"],
                "mesh_jobs": arrival["work_delta"]["mesh_jobs"],
                "render_publications": arrival["work_delta"]["application_applied_render"],
                "collision_ready_lod0_chunks": arrival["target_state"]["collision_ready_lod0"],
                "first_collision_latency_usec": arrival["settlement"]["first_collision_latency_usec"],
            },
        },
        "edits": {
            "digging": edit_summary(large, "digging"),
            "construction": edit_summary(large, "construction"),
            "construction_material_ownership": next(
                item for item in large["scenarios"] if item["id"] == "construction"
            )["material_ownership"],
            "persistence": large["persistence"],
        },
        "correctness": {
            "coverage_overlaps": large["final_lod_audit"]["coverage_overlap_count"],
            "visual_generation_mismatches": len(large["final_lod_audit"]["visual_generation_mismatches"]),
            "collision_generation_mismatches": len(large["final_lod_audit"]["collision_generation_mismatches"]),
            "topology": {
                key: topology[key]
                for key in (
                    "boundary_edges",
                    "nonmanifold_edges",
                    "orientation_inconsistent_edges",
                    "zero_area_triangles",
                )
            },
            "temporal_continuity": {
                "monitored_frames": temporal["monitored_frames"],
                "topology_samples": len(temporal["topology_samples"]),
                "topology_failures": temporal["topology_failures"],
                "visible_ancestor_overlaps": temporal["maximum_visible_ancestor_overlaps"],
            },
        },
        "power": {
            "cpu_package_watts": None,
            "whole_system_watts": None,
            "gpu_board_watts": None,
            "status": "UNQUALIFIED_NO_TRUSTED_ENERGY_PROVIDER",
        },
        "qualified_scope": contract["qualified_scope"],
        "explicitly_unqualified_scope": contract["explicitly_unqualified_scope"],
        "failures": [],
    }
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_document(report)
    run_python("tools/validate_cpu_production_closure.py", "--require-report")
    print(
        "WT_TERRAIN_CPU_PRODUCTION_CLOSURE_PASS "
        f"frames={report['performance']['frame_samples']} "
        f"p99_usec={report['performance']['frame_p99_usec']:.3f} "
        f"rss={report['performance']['process_telemetry']['peak_rss_bytes']}"
    )


if __name__ == "__main__":
    main()
