# World Transvoxel Terrain Roadmap

Milestones are sequential. Do not jump to a later milestone while the current
one is incomplete. If a task is required for the current milestone, move it into
that milestone with explicit exit criteria.

## A0 - Repository skeleton and contract

Status: complete.

Exit:

- separate `world-transvoxel-terrain` repo exists;
- canonical implementation charter exists;
- Godot addon manifest exists;
- license scope is explicit;
- skeleton validator passes;
- no sandbox implementation or MIT Transvoxel topology data is copied.

## A1 - Public API and source-layout contract

Status: complete by `WT_TERRAIN_A1_CONTRACT_PASS`.

Exit:

- terrain root node/resource concepts are named;
- generation, streaming, edit, storage, material, collision, debug, and budget
  APIs are defined at contract level;
- old marching-cubes maintainability failures are inspected before substantial
  implementation;
- required references are downloaded or pinned under ignored reference storage.

## A2 - Addon-local smoke harness

Status: complete by `WT_TERRAIN_A2_SMOKE_PASS`.

Exit:

- Godot plugin loads;
- `world-transvoxel` dependency is detected without vendoring;
- placeholder terrain resources are visible;
- no terrain hot path is implemented in GDScript.

## A3 - world-transvoxel bridge

Status: complete by `WT_TERRAIN_A3_BRIDGE_PASS`.

Exit:

- the terrain addon talks to the official MIT-backed `world-transvoxel` API;
- dependency boundaries remain explicit;
- deterministic CPU/native fallback remains accepted.

## A4 - Terrain profile, edit, storage, and recovery

Status: complete. Phase 1 complete by `WT_TERRAIN_A4_PHASE1_SMOKE_PASS`; phase
2 complete by `WT_TERRAIN_A4_PHASE2_SMOKE_PASS`; phase 3 complete by
`WT_TERRAIN_A4_PHASE3_SMOKE_PASS`; phase 4 complete by
`WT_TERRAIN_A4_PHASE4_SMOKE_PASS`; phase 5 complete by
`WT_TERRAIN_A4_PHASE5_EXIT_REVIEW_PASS`.

Phase 1 exit:

- reference terrain profile, edit operation, edit batch, storage profile, and
  recovery policy resources exist;
- carve, construct, fill, paint, and restore-to-base are represented as
  validated commands;
- storage and recovery defaults preserve deterministic write targets and cold
  idle behavior;
- the implementation boundary is `resource_semantics_only`.

Phase 2 next:

- submit edit batches through the `world-transvoxel` bridge;
- add a deterministic storage fixture that writes, reloads, and verifies an edit
  journal.

Phase 2 exit:

- `WtTerrainEditBridge` submits edit batches into real
  `WorldTransvoxelEditTransaction` objects;
- a temporary fixture starts the official backend production lifecycle world,
  commits edits, verifies `world.wtedit`, restarts, and verifies journal replay;
- the implementation boundary is `bridge_storage_fixture`.

Phase 3 next:

- make public `WtTerrainWorld` own backend lifecycle configuration/start/stop;
- keep the next step focused on terrain-world ownership, not game repository or
  optional systems.

Phase 3 exit:

- `WtTerrainWorld` owns backend terrain/config lifecycle through the bridge;
- public `WtTerrainWorld` start/stop and edit submission are smoke-tested;
- journal replay is verified through terrain-world-owned backend restart;
- the implementation boundary is `terrain_world_lifecycle`.

Phase 4 next:

- validate reference-profile runtime/cold-idle behavior through public
  `WtTerrainWorld`;
- keep the step focused on A4 exit evidence, not optional systems.

Phase 4 exit:

- `WtTerrainWorld` exposes viewer update/removal, chunk query, runtime metrics,
  and cold-idle summary APIs;
- the reference profile defaults are verified as 2048 x 2048 x 64 with `+Y` up
  and finite closed boundaries;
- one public terrain-world viewer streams to ready render/collision state,
  remains cold-idle with selected counters stable, removes cleanly, and stops;
- the implementation boundary is `reference_profile_runtime_cold_idle`.

Phase 5 next:

- perform the A4 exit review;
- either close A4 with evidence or record the exact remaining A4 slice before
  A5 can begin.

Phase 5 exit:

- A4 closes at the terrain-addon API, profile, edit, storage, recovery, and
  runtime-control level;
- one documented run executes A4 phase 1 through phase 4 validators and smokes;
- the implementation boundary is `a4_exit_review`;
- next milestone is A5 local reference scene and debug UI.

Exit:

- 2048 x 2048 x 64 reference profile works through the terrain addon;
- carve, construct, fill, paint, and restore-to-base work through addon APIs;
- edits persist through save/restart;
- settled terrain remains cold.

## A5 - Local reference scene and debug UI

Status: complete. Phase 1 complete by `WT_TERRAIN_A5_PHASE1_SMOKE_PASS`; phase 2
complete by `WT_TERRAIN_A5_PHASE2_SMOKE_PASS`; phase 3 complete by
`WT_TERRAIN_A5_PHASE3_SMOKE_PASS`; phase 4 complete by
`WT_TERRAIN_A5_PHASE4_SMOKE_PASS`; phase 5 complete by
`WT_TERRAIN_A5_PHASE5_EXIT_REVIEW_PASS`.

Phase 1 exit:

- `WtTerrainDebugSnapshot` exposes world, terrain profile, generation profile,
  storage profile, recovery policy, budget, collision, streaming, edit, and
  material categories;
- default snapshot capture does not start backend work;
- the implementation boundary is `debug_snapshot_contract`.

Phase 2 exit:

- addon-local inspection scene scaffold exists;
- the scene owns a `WtTerrainWorld` child and minimal debug overlay label;
- the scene refreshes through `WtTerrainDebugSnapshot`;
- default scene inspection does not start backend work;
- the implementation boundary is `local_reference_scene_scaffold`.

Phase 3 exit:

- run the local reference scene against the official backend fixture;
- scene-level backend start/stop and viewer update/removal are smoke-tested;
- debug status text reports backend state, cold-idle, render resources, and
  collision resources while live;
- the implementation boundary is `backend_reference_scene_runtime_smoke`.

Phase 4 exit:

- render the debug snapshot categories into explicit overlay sections;
- debug overlay text exposes world/profile/storage/budget/collision/streaming/
  edit/material state;
- the implementation boundary is `debug_overlay_category_rendering`.

Phase 5 exit:

- perform the A5 exit review;
- close A5 or name the exact remaining A5 implementation slice;
- next milestone is A6 game repository readiness decision;
- keep the scene as addon smoke evidence, not game-repository validation.

Exit:

- addon-local inspection scene exists;
- debug UI exposes chunk, collision, queue, budget, material, storage, and edit
  state;
- the scene is addon smoke evidence, not final game validation.

## A6 - Game repository readiness decision

Status: complete by `WT_TERRAIN_A6_READINESS_DECISION_PASS`.

Exit:

- decision: `approve_validation_game_repository`;
- package boundary, local smoke evidence, and stable minimal API are accepted as
  sufficient for creating a separate validation game repository when the user
  explicitly asks;
- this does not claim production-ready terrain or final gameplay validation;
- `world-transvoxel-validation-game` exists with G0 install/run validation
  complete;
- `world-transvoxel-validation-game` commit `5a47a8d` adds the root-safe notice
  project plus G1 visual capture after the first gray-rectangle-only human run;
- next validation-game action is human rerun confirmation.
