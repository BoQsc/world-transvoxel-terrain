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

Status: active. Phase 1 complete by `WT_TERRAIN_A4_PHASE1_SMOKE_PASS`.

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

Exit:

- 2048 x 2048 x 64 reference profile works through the terrain addon;
- carve, construct, fill, paint, and restore-to-base work through addon APIs;
- edits persist through save/restart;
- settled terrain remains cold.

## A5 - Local reference scene and debug UI

Status: deferred until A4 exits.

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
