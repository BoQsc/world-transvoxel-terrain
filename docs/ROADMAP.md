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

Status: active.

Next:

- create an addon-local inspection scene;
- expose readable terrain/debug status for budget, collision, streaming, edit,
  material, and storage state;
- keep the scene as addon smoke evidence, not game-repository validation.

Exit:

- addon-local inspection scene exists;
- debug UI exposes chunk, collision, queue, budget, material, storage, and edit
  state;
- the scene is addon smoke evidence, not final game validation.

## A6 - Game repository readiness decision

Status: deferred until A5 exits.

Exit:

- decide whether the separate game repository can be created;
- game repository remains deferred until this addon has a stable package
  boundary and local smoke tests.
