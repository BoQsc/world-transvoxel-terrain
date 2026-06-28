# World Transvoxel Terrain Implementation Charter

Status: canonical project direction for the terrain addon.

Current phase: A4 phase 4 reference-profile runtime/cold-idle validation
complete. Next phase is A4 phase 5 A4 exit review.

This document is the authority for `world-transvoxel-terrain` until a later
commit explicitly revises it. If another README, roadmap, experiment, issue, or
temporary implementation conflicts with this file, this file controls.

## Product goal

Build a reusable Godot terrain addon that lets a game use large, editable,
Transvoxel-backed terrain without copying the reference sandbox or rebuilding
terrain infrastructure from scratch.

The finished addon should make the normal game path boring:

```text
install world-transvoxel
install world-transvoxel-terrain
add terrain scene/resource
choose config preset
connect player/camera
run
```

The addon must support:

- surface and underground volumetric terrain;
- deterministic terrain profiles and generation profiles;
- 2048 x 2048 x 64 reference-scale terrain as an explicit supported profile;
- carve, construct, fill, paint, and restore-to-base operations;
- edit persistence through save/restart;
- collision/readiness status that games can query;
- debug/status UI for chunks, collision, queues, budgets, storage, and edits;
- event-driven streaming and edit work;
- settled cold-idle behavior unless player action, streaming demand, or an
  explicitly enabled system creates work;
- stable public APIs with optional extension points.

## Repository boundary

`world-transvoxel` is the low-level native Transvoxel addon. It owns meshing,
streaming primitives, storage primitives, official MIT backend isolation, native
worker scheduling, collision payloads, and terrain-page authority.

`world-transvoxel-terrain` is the reusable terrain layer above
`world-transvoxel`. It owns game-facing terrain resources, terrain presets,
scene integration, edit/recovery conventions, terrain material policy, runtime
budget profiles, and terrain debug surfaces.

`world-transvoxel-sandbox` is evidence and reference material. It validates
`world-transvoxel` behavior and may demonstrate patterns. It is not a dependency
of this addon and must not be copied as game architecture.

A future game repository validates this addon in actual gameplay. That game
repository is deferred until this addon has a clear package boundary and local
smoke tests.

## Backend and license policy

Use the official MIT-backed `world-transvoxel` backend first.

The independent 0BSD Transvoxel backend is deferred until the official backend
survives this addon and later game validation. Do not mix MIT topology data into
this repository.

Project-owned files in this repository are 0BSD unless a file explicitly states
otherwise. If a future distribution bundles `world-transvoxel`, retain its
separate license notices.

## Implementation model

Performance-sensitive terrain work belongs in:

- native code;
- low-level addon interfaces;
- deterministic binary formats;
- shaders only when already justified by measured evidence;
- Python offline tooling for baking, inspection, validation, and migration.

GDScript is allowed for:

- Godot scene scaffolding;
- editor plugin glue;
- input routing;
- debug UI;
- small smoke-test harnesses.

GDScript is not allowed for:

- terrain generation hot paths;
- Transvoxel meshing;
- large-map streaming policy;
- persistent storage format processing;
- edit recovery algorithms;
- fluid simulation;
- structural stability;
- compute-heavy validation.

GPU compute remains rejected for now by the upstream S4 decision. It can only
return under a later measured bottleneck contract with a deterministic CPU/native
fallback.

## Source organization standard

Avoid the old single-large-source-file failure mode.

Expected package ownership:

```text
addons/world_transvoxel_terrain/
  plugin.cfg
  LICENSE_SCOPE.md
  editor/       Godot editor glue only
  api/          public script/native API adapters
  runtime/      terrain root, profile binding, viewer binding
  generation/   generation profiles and offline hooks
  streaming/    terrain-layer policy above world-transvoxel
  edit/         carve/construct/fill/paint/restore operation policy
  storage/      save/load and journal integration
  material/     material, texture, triplanar, and debug-view policy
  collision/    collision readiness and game query policy
  debug/        debug/status overlay and inspector helpers
  tests/        addon-local smoke and contract tests
```

Do not collapse unrelated runtime, editor, storage, generation, and debug logic
into one source file.

## Required concepts

The first implementation must define names and ownership for:

- terrain world/root node;
- terrain profile/resource;
- generation profile;
- streaming policy;
- edit controller;
- edit operation descriptions;
- save/load and journal boundary;
- material/texture policy;
- collision policy;
- debug/status overlay;
- runtime budget profile;
- local smoke-test entry points.

The exact class names may change, but these concepts may not silently disappear.

## Terrain behavior standard

- `+Y` is up.
- Finite maps need an explicit closed-boundary policy.
- Underground terrain is volumetric, not heightfield-only.
- Flat terrain must be supported as a normal generation profile, not a special
  hack.
- Terrain edits operate on authoritative voxel samples, not visual-only meshes.
- Restore-to-base is explicit and audited before automatic regeneration.
- Timed regeneration, smoothing, erosion, collapse, and fluid equilibrium are
  optional systems, not default behavior.
- Holes, missing backsides, upside-down terrain, diagonal artifacts,
  unexplained popping, and unbounded CPU/GPU use are defects until classified.

## Optional systems deferred by contract

These are not part of A0/A1 unless a later contract moves them in:

- water and lava;
- planets or alternate gravity worlds;
- structural collapse/stability;
- vegetation;
- building blocks;
- inventory/economy systems;
- advanced mining animations/effects;
- automatic timed regeneration or equilibrium simulation;
- broad GPU compute implementation;
- independent 0BSD backend replacement;
- separate game repository.

## Roadmap

A0 - Repository skeleton and contract.

- create the separate addon repository;
- add license scope, addon manifest, canonical charter, roadmap, and skeleton
  validator;
- prove no sandbox implementation or MIT Transvoxel topology data is copied.

A1 - Public API and source-layout contract.

- define the initial Godot-facing terrain node/resource names;
- define terrain profile, generation profile, edit operation, storage, material,
  collision, debug, and budget interfaces;
- inspect the old marching-cubes project for maintainability failures before
  writing substantial implementation;
- download/reference required papers and implementation references under the
  ignored `references/downloaded/` area before using them for design.

A2 - Addon-local smoke harness.

- prove the Godot plugin loads;
- detect the `world-transvoxel` dependency without vendoring it;
- expose placeholder terrain resources without hot-path terrain logic in
  GDScript.

A3 - `world-transvoxel` bridge.

- bind the terrain addon to the official MIT-backed `world-transvoxel` API;
- keep dependency boundaries explicit;
- preserve CPU/native deterministic fallback.

A4 - Terrain profile, edit, storage, and recovery implementation.

- phase 1 defines resource semantics for the reference profile, edit commands,
  storage profile, recovery policy, and terrain-world summary;
- phase 2 submits edit batches through the `world-transvoxel` bridge and proves
  a deterministic storage fixture;
- phase 3 moves from bridge fixture evidence to public `WtTerrainWorld`
  lifecycle ownership;
- phase 4 validates the reference profile runtime/cold-idle path through the
  public terrain-world API;
- phase 5 performs the A4 exit review and either closes A4 or records the exact
  remaining A4 slice;
- support the 2048 x 2048 x 64 reference profile;
- support carve, construct, fill, paint, and restore-to-base;
- persist edits through save/restart;
- keep idle terrain cold.

A5 - Local reference scene and debug UI.

- provide a small addon-local inspection scene;
- show terrain budget, collision, streaming, edit, material, and storage state;
- keep this as addon smoke evidence, not game-repository validation.

A6 - Game repository readiness decision.

- create the separate game repository only after this addon has package
  boundaries, local smoke tests, and a stable minimal API.

## Definition of done for A0

A0 is complete when:

- `python tools/validate_terrain_skeleton.py` passes;
- this repo is initialized as `world-transvoxel-terrain`;
- `addons/world_transvoxel_terrain/plugin.cfg` exists;
- license scope is explicit;
- no `addons/world_transvoxel/` or MIT Transvoxel source is present;
- the next finite task is A1 public API and source-layout contract.

## Definition of done for A1

A1 is complete when:

- `docs/A1_PUBLIC_API_SOURCE_LAYOUT_CONTRACT.md` defines the public API shape;
- `docs/A1_MARCHING_CUBES_AUDIT.md` records the old marching-cubes
  maintainability failures;
- `references/MANIFEST.md` records pinned/downloaded primary references;
- required source-layout directories exist with ownership placeholders;
- `python tools/validate_a1_contract.py` passes;
- the next finite task is A2 addon-local smoke harness.

## Definition of done for A2

A2 is complete when:

- `docs/A2_ADDON_SMOKE_HARNESS.md` records the smoke boundary;
- dependency detection reports whether `world-transvoxel` is installed without
  vendoring it;
- placeholder `WtTerrainWorld`, `WtTerrainProfile`, and
  `WtTerrainGenerationProfile` scripts load in Godot;
- `python tools/validate_a2_smoke.py` passes;
- `python tools/a2_addon_smoke.py` passes on discovered local Godot engines;
- the next finite task is A3 `world-transvoxel` bridge.

## Definition of done for A3

A3 is complete when:

- `docs/A3_WORLD_TRANSVOXEL_BRIDGE.md` records the bridge boundary;
- `WtWorldTransvoxelBridge` detects `WorldTransvoxelTerrain` and
  `WorldTransvoxelConfig` through Godot `ClassDB`;
- the bridge reads backend identity and default config validity without starting
  a world;
- `python tools/validate_a3_bridge.py` passes;
- `python tools/a3_bridge_smoke.py` passes on discovered local Godot engines
  using an ignored temporary fixture;
- no `addons/world_transvoxel/`, sandbox implementation, or MIT Transvoxel
  topology data is committed;
- the next finite task is A4 terrain profile, edit, storage, and recovery.

## Definition of done for A4 phase 1

A4 phase 1 is complete when:

- `docs/A4_PROFILE_EDIT_STORAGE_RECOVERY_PHASE1.md` records the resource
  semantics boundary;
- `WtTerrainEditOperation` defines carve, construct, fill, paint, and
  restore-to-base command resources;
- `WtTerrainEditBatch` validates grouped edit commands;
- `WtTerrainStorageProfile` defines deterministic manifest, journal, and
  snapshot write targets;
- `WtTerrainRecoveryPolicy` defaults to manual recovery and cold idle behavior;
- `WtTerrainWorld` reports terrain, generation, storage, and recovery summaries;
- `python tools/validate_a4_phase1.py` passes;
- `python tools/a4_phase1_resources_smoke.py` passes on discovered local Godot
  engines;
- no backend edit submission or persistence claim is made yet;
- the next finite task is A4 phase 2 bridge edit submission and storage fixture.

## Definition of done for A4 phase 2

A4 phase 2 is complete when:

- `docs/A4_PROFILE_EDIT_STORAGE_RECOVERY_PHASE2.md` records the bridge/storage
  fixture boundary;
- `WtTerrainEditBridge` converts a validated `WtTerrainEditBatch` into a real
  `WorldTransvoxelEditTransaction`;
- the bridge submits carve, construct, fill, paint, and restore-to-base
  operation resources through official backend edit methods;
- the Godot smoke starts the official backend lifecycle fixture, commits the
  terrain edit batch, verifies a native `world.wtedit` journal, restarts, and
  verifies journal replay;
- `python tools/validate_a4_phase2.py` passes;
- `python tools/a4_phase2_bridge_storage_smoke.py` passes on discovered local
  Godot engines;
- no `world-transvoxel`, sandbox implementation, or MIT Transvoxel topology data
  is committed into this repository;
- the next finite task is A4 phase 3 public `WtTerrainWorld` lifecycle ownership.

## Definition of done for A4 phase 3

A4 phase 3 is complete when:

- `docs/A4_PROFILE_EDIT_STORAGE_RECOVERY_PHASE3.md` records the terrain-world
  lifecycle boundary;
- `WtTerrainWorld` instantiates and owns the backend terrain/config through
  `WtWorldTransvoxelBridge`;
- `WtTerrainWorld.start_backend_world()` and `stop_backend_world()` control the
  backend lifecycle from `WtTerrainStorageProfile`;
- `WtTerrainWorld.submit_edit_batch()` submits terrain edit batches through
  `WtTerrainEditBridge`;
- the Godot smoke starts, edits, verifies native `world.wtedit`, stops,
  restarts, and verifies journal replay through the public terrain-world node;
- `python tools/validate_a4_phase3.py` passes;
- `python tools/a4_phase3_terrain_world_lifecycle_smoke.py` passes on
  discovered local Godot engines;
- no `world-transvoxel`, sandbox implementation, or MIT Transvoxel topology data
  is committed into this repository;
- the next finite task is A4 phase 4 reference-profile runtime/cold-idle
  validation.

## Definition of done for A4 phase 4

A4 phase 4 is complete when:

- `docs/A4_PROFILE_EDIT_STORAGE_RECOVERY_PHASE4.md` records the
  runtime/cold-idle boundary;
- `WtTerrainWorld` exposes public viewer update/removal, chunk query, runtime
  metrics, and cold-idle summary methods;
- cold-idle interpretation lives in focused runtime helper code, not a growing
  monolithic terrain-world script;
- the default `WtTerrainProfile` is verified as the 2048 x 2048 x 64 `+Y` up
  finite reference profile;
- the Godot smoke starts the official lifecycle fixture through
  `WtTerrainWorld`, streams one viewer, verifies ready render/collision state,
  queries the ready origin chunk, holds selected runtime counters stable while
  cold idle, removes the viewer, and stops cleanly;
- `python tools/validate_a4_phase4.py` passes;
- `python tools/a4_phase4_reference_runtime_cold_idle_smoke.py` passes on
  discovered local Godot engines;
- no `world-transvoxel`, sandbox implementation, or MIT Transvoxel topology data
  is committed;
- the next finite task is A4 phase 5 A4 exit review.

## Definition of done for A4 phase 5

A4 phase 5 is complete when:

- every A4 phase 1 through phase 4 validator and smoke passes in one
  documented run;
- the A4 exit review states whether A4 closes or names the exact remaining A4
  implementation slice;
- the roadmap is updated to either move to A5 local reference scene/debug UI or
  keep A4 active with a single named next phase;
- no later milestone starts before the A4 status is explicit.
