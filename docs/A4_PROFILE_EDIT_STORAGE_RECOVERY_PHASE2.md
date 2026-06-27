# A4 Profile, Edit, Storage, and Recovery Phase 2

Status: complete.

Markers:

```text
WT_TERRAIN_A4_PHASE2_CONTRACT_PASS next=a4_phase3_public_terrain_world_lifecycle implementation=bridge_storage_fixture
WT_TERRAIN_A4_PHASE2_GODOT_PASS operations=5 backend_commands=8 commit=1 journal=replayed implementation=bridge_storage_fixture
WT_TERRAIN_A4_PHASE2_SMOKE_PASS engines=2 report=artifacts/a4_phase2_bridge_storage/a4_phase2_bridge_storage_report.json
```

## What this phase proves

A4 phase 2 connects the A4 phase 1 terrain edit resources to the official
MIT-backed `world-transvoxel` edit API:

- `WtTerrainEditBridge` converts a validated `WtTerrainEditBatch` into a real
  `WorldTransvoxelEditTransaction`;
- carve, construct, fill, paint, and restore-to-base operations are submitted
  through backend transaction methods;
- construct, fill, and restore-to-base emit density and material commands when
  material is part of the operation;
- the smoke fixture starts the official backend production lifecycle world,
  commits the batch, verifies a native `world.wtedit` journal exists, restarts
  the world, and verifies the committed sample replays from the journal.

Restore-to-base in this phase is explicit snapshot replay: the caller supplies
the exact density and material to restore. Automatic base sampling, timed
regeneration, smoothing, stability, and fluid equilibrium remain out of scope.

## Boundary

This phase is `bridge_storage_fixture`.

A4 is not complete. This phase does not:

- make `WtTerrainWorld` own the backend world lifecycle;
- expose a final public game-facing terrain scene;
- implement chunk streaming policy above `world-transvoxel`;
- prove collision readiness or debug UI;
- prove the 2048 x 2048 x 64 terrain profile running as a full terrain scene;
- prove game-ready performance.

## Exit criteria

A4 phase 2 is complete when:

- `python tools/validate_a4_phase2.py` passes;
- `python tools/a4_phase2_bridge_storage_smoke.py` passes on discovered Godot
  engines;
- the smoke uses an ignored temporary fixture and does not vendor
  `world-transvoxel`, sandbox implementation, MIT Transvoxel source, or MIT
  topology data into this repository.

Next valid action is A4 phase 3: public `WtTerrainWorld` lifecycle ownership
above the bridge, still using the official backend and still avoiding broad GPU,
game repository, water/lava, planets, stability, and 0BSD backend work.
