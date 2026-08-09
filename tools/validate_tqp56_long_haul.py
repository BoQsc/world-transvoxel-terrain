#!/usr/bin/env python3

from __future__ import annotations

from tqp_release_common import ROOT, load_json, sha256


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    contract = load_json(ROOT / "TQP56_LONG_HAUL_CONTRACT.json")
    report = load_json(ROOT / "artifacts/tqp56_long_haul/tqp56_long_haul_report.json")
    require(contract.get("schema") == "world_transvoxel_terrain.tqp56_long_haul_contract.v1", "TQP-56 contract schema mismatch")
    require(contract.get("engine") == "4.7", "TQP-56 engine policy drifted")
    require(report.get("schema") == "world_transvoxel_terrain.tqp56_long_haul_evidence.v1", "TQP-56 report schema mismatch")
    require(report.get("status") == "PASS" and report.get("engine") == "4.7", "TQP-56 report failed")
    workload = report.get("workload", {})
    require(workload.get("status") == "PASS", "TQP-56 workload failed")
    require(float(workload.get("duration_seconds", 0)) >= contract["minimum_wrapper_duration_seconds"], "TQP-56 duration is too short")
    for key in ("cycles", "edits", "queries", "restarts"):
        required = contract[f"minimum_{key}"]
        require(int(workload.get(key, 0)) >= required, f"TQP-56 {key} coverage is incomplete")
    budgets = contract["budgets"]
    require(int(workload.get("queue_rejections", -1)) <= budgets["maximum_queue_rejections"], "TQP-56 queue rejection budget failed")
    require(int(workload.get("memory_growth_bytes", -1)) <= budgets["maximum_memory_growth_bytes"], "TQP-56 memory growth budget failed")
    require(workload.get("clean_shutdown") is True, "TQP-56 clean shutdown missing")
    require(workload.get("origin_shift_authority_coordinates_unchanged") is True, "TQP-56 origin-shift boundary missing")
    retained = contract["retained_long_run"]
    path = ROOT.parent / retained["repository"] / retained["path"]
    require(path.is_file() and sha256(path) == retained["sha256"], "TQP-56 retained long-run evidence drifted")
    payload = load_json(path)
    require(payload.get("status") == "PASS" and payload.get("retained_complete") is True, "TQP-56 retained long run failed")
    drift = payload.get("temporal_drift", {})
    require(float(drift.get("complex_rendered_seconds", 0)) >= retained["minimum_rendered_seconds"], "retained rendered duration is too short")
    require(int(drift.get("frame_samples", 0)) >= retained["minimum_frame_samples"], "retained frame sample count is too low")
    print(
        "WT_TERRAIN_TQP56_LONG_HAUL_PASS "
        f"duration={workload['duration_seconds']:.3f} retained_seconds={drift['complex_rendered_seconds']} "
        f"memory_growth={workload['memory_growth_bytes']} queue_rejections={workload['queue_rejections']}"
    )


if __name__ == "__main__":
    main()
