# A4 Profile, Edit, Storage, and Recovery Phase 4

Status: complete.

Markers:

```text
WT_TERRAIN_A4_PHASE4_CONTRACT_PASS next=a4_phase5_a4_exit_review implementation=reference_profile_runtime_cold_idle
WT_TERRAIN_A4_PHASE4_GODOT_PASS profile=2048x128 viewer=settled cold_idle=stable remove=settled implementation=reference_profile_runtime_cold_idle
WT_TERRAIN_A4_PHASE4_SMOKE_PASS engines=2 report=artifacts/a4_phase4_reference_runtime_cold_idle/a4_phase4_reference_runtime_cold_idle_report.json
```

## What this phase proves

A4 phase 4 validates the public runtime path above the official
`world-transvoxel` backend:

- `WtTerrainWorld` exposes viewer update/removal methods instead of requiring
  tests or games to call backend viewer APIs directly;
- `WtTerrainWorld` exposes backend runtime metrics as a terrain-layer summary;
- `WtTerrainRuntimeAudit` defines the terrain-layer cold-idle interpretation;
- the default `WtTerrainProfile` remains the 2048 x 2048 x 128 reference profile
  with `+Y` up and finite closed boundaries;
- a public `WtTerrainWorld` starts the official backend fixture, streams one
  viewer, waits for render/collision readiness, queries the ready origin chunk,
  holds cold idle without selected runtime counters changing, removes the
  viewer, and stops cleanly.

## Boundary

This phase is `reference_profile_runtime_cold_idle`.

A4 is not complete. This phase does not:

- generate or stream a full 2048 x 2048 x 64 terrain world;
- prove broad movement, dynamic LOD, seams, or visual smoothness;
- add a reference inspection scene or debug UI;
- add native terrain generation policy above baked fixtures;
- add water/lava, planets, stability, vegetation, building blocks, GPU compute,
  or a game repository;
- prove production game readiness.

The important claim is narrower: the reference profile resource and the public
terrain-world runtime/cold-idle path are wired and smoke-tested through the
official backend fixture.

## Exit criteria

A4 phase 4 is complete when:

- `python tools/validate_a4_phase4.py` passes;
- `python tools/a4_phase4_reference_runtime_cold_idle_smoke.py` passes on
  discovered Godot engines;
- all A4 phase 1 through phase 3 contract and smoke validators still pass;
- no `world-transvoxel`, sandbox implementation, MIT Transvoxel source, or MIT
  topology data is committed into this repository.

Next valid action is A4 phase 5: A4 exit review. Phase 5 must either close A4
with evidence or write the exact remaining A4 slice before A5 can start.
