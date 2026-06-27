# A4 Profile, Edit, Storage, and Recovery Phase 1

Status: complete.

Markers:

```text
WT_TERRAIN_A4_PHASE1_CONTRACT_PASS next=a4_phase2_bridge_edit_submission implementation=resource_semantics_only
WT_TERRAIN_A4_PHASE1_GODOT_PASS profile=2048x64 operations=5 storage=valid recovery=cold_idle implementation=resource_semantics_only
WT_TERRAIN_A4_PHASE1_SMOKE_PASS engines=2 report=artifacts/a4_phase1_resources/a4_phase1_resources_report.json
```

## What this phase proves

A4 phase 1 defines and validates the resource-level contract for the first
real terrain layer above `world-transvoxel`:

- the reference `WtTerrainProfile` is 2048 x 2048 x 64, finite, and `+Y` up;
- `WtTerrainEditOperation` represents carve, construct, fill, paint, and
  restore-to-base as explicit commands;
- each edit operation validates input, estimates an affected `AABB`, and emits
  a schema-versioned bridge command;
- `WtTerrainEditBatch` validates grouped edit commands;
- `WtTerrainStorageProfile` names deterministic write targets for manifest,
  edit journal, and snapshots without using `res://`;
- `WtTerrainRecoveryPolicy` defaults to manual recovery targets with automatic
  timed regeneration, smoothing, structural collapse, and fluid equilibrium
  disabled;
- `WtTerrainWorld` exposes terrain, generation, storage, and recovery summaries
  without starting a backend world.

## Boundary

This phase is intentionally `resource_semantics_only`.

A4 is not complete. This phase does not:

- submit edit batches into the `world-transvoxel` backend;
- generate or stream real terrain pages;
- persist a real edit journal through save/restart;
- prove collision readiness;
- prove seamless dynamic LOD;
- prove game-ready performance.

## Exit criteria

A4 phase 1 is complete when:

- `python tools/validate_a4_phase1.py` passes;
- `python tools/a4_phase1_resources_smoke.py` passes on discovered Godot
  engines;
- no `world-transvoxel`, sandbox implementation, MIT Transvoxel source, or MIT
  topology data is committed into this repository.

Next valid action is A4 phase 2: bridge edit submission and a storage fixture
that writes, reloads, and verifies an edit journal.
