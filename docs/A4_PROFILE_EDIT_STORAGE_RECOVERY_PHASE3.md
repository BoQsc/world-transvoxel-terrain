# A4 Profile, Edit, Storage, and Recovery Phase 3

Status: complete.

Markers:

```text
WT_TERRAIN_A4_PHASE3_CONTRACT_PASS next=a4_phase4_reference_profile_runtime_cold_idle implementation=terrain_world_lifecycle
WT_TERRAIN_A4_PHASE3_GODOT_PASS lifecycle=start_stop_restart edit_commit=1 journal=replayed implementation=terrain_world_lifecycle
WT_TERRAIN_A4_PHASE3_SMOKE_PASS engines=2 report=artifacts/a4_phase3_terrain_world_lifecycle/a4_phase3_terrain_world_lifecycle_report.json
```

## What this phase proves

A4 phase 3 moves lifecycle ownership from a standalone bridge fixture into the
public `WtTerrainWorld` node:

- `WtTerrainWorld.start_backend_world()` instantiates the official backend
  terrain and config through `WtWorldTransvoxelBridge`;
- `WtTerrainGenerationBackend` chooses manifest-backed startup or
  `start_procedural_world()` for `DETERMINISTIC_REFERENCE` generation profiles;
- the backend node is owned as a child named `WT_BackendTerrain`;
- `WtTerrainStorageProfile` supplies the world manifest and object-root paths;
- `WtTerrainWorld.stop_backend_world()` controls backend shutdown;
- `WtTerrainWorld.submit_edit_batch()` submits validated terrain edit batches
  through `WtTerrainEditBridge`;
- the smoke starts, edits, verifies native `world.wtedit`, stops, restarts, and
  verifies journal replay through the owned backend.

The `allow_res_paths_for_test_fixtures` storage flag exists only to run ignored
temporary Godot fixtures from copied `res://build/...` data. Normal write paths
remain `user://`.

## Boundary

This phase is `terrain_world_lifecycle`.

A4 is not complete. This phase does not:

- prove the 2048 x 2048 x 64 profile as a full terrain scene;
- add viewer binding or terrain streaming policy above `world-transvoxel`;
- prove collision readiness through the terrain-world API;
- add debug UI;
- prove cold-idle budgets;
- prove game-ready terrain.

## Exit criteria

A4 phase 3 is complete when:

- `python tools/validate_a4_phase3.py` passes;
- `python tools/a4_phase3_terrain_world_lifecycle_smoke.py` passes on
  discovered Godot engines;
- no `world-transvoxel`, sandbox implementation, MIT Transvoxel source, or MIT
  topology data is committed into this repository.

Next valid action is A4 phase 4: reference-profile runtime/cold-idle validation
through public `WtTerrainWorld`, still using the official backend and still
avoiding broad GPU, game repository, water/lava, planets, stability, and 0BSD
backend work.
