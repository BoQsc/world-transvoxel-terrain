# World Transvoxel Terrain Roadmap

Milestones are sequential. Do not jump to a later milestone while the current
one is incomplete. If a task is required for the current milestone, move it into
that milestone with explicit exit criteria.

## A0 - Repository skeleton and contract

Status: active.

Exit:

- separate `world-transvoxel-terrain` repo exists;
- canonical implementation charter exists;
- Godot addon manifest exists;
- license scope is explicit;
- skeleton validator passes;
- no sandbox implementation or MIT Transvoxel topology data is copied.

## A1 - Public API and source-layout contract

Status: next.

Exit:

- terrain root node/resource concepts are named;
- generation, streaming, edit, storage, material, collision, debug, and budget
  APIs are defined at contract level;
- old marching-cubes maintainability failures are inspected before substantial
  implementation;
- required references are downloaded or pinned under ignored reference storage.

## A2 - Addon-local smoke harness

Status: deferred until A1 exits.

Exit:

- Godot plugin loads;
- `world-transvoxel` dependency is detected without vendoring;
- placeholder terrain resources are visible;
- no terrain hot path is implemented in GDScript.

## A3 - world-transvoxel bridge

Status: deferred until A2 exits.

Exit:

- the terrain addon talks to the official MIT-backed `world-transvoxel` API;
- dependency boundaries remain explicit;
- deterministic CPU/native fallback remains accepted.

## A4 - Terrain profile, edit, storage, and recovery

Status: deferred until A3 exits.

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
