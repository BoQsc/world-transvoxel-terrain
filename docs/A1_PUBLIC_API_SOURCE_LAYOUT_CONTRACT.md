# A1 Public API and Source-Layout Contract

Status: complete.

Validation marker:

```text
WT_TERRAIN_A1_CONTRACT_PASS next=a2_addon_local_smoke_harness implementation=contract_only
```

A1 defines the public terrain-addon boundary before implementation. It does not
implement terrain generation, meshing, streaming, storage, or edit recovery.

## Public API shape

The first API should be small and typed. Games should normally touch one terrain
world node and a few resources, not a pile of low-level knobs.

Reserved contract names:

| Concept | Contract name | Godot shape | Ownership |
| --- | --- | --- | --- |
| Terrain root | `WtTerrainWorld` | `Node3D` | scene entry point, profile binding, viewer binding |
| Terrain profile | `WtTerrainProfile` | `Resource` | dimensions, finite bounds, vertical range, default policies |
| Generation profile | `WtTerrainGenerationProfile` | `Resource` | flat/noise/baked source selection, seed, material defaults |
| Streaming policy | `WtTerrainStreamingPolicy` | `Resource` | viewer radius, LOD range, active capacity, fast-travel rule |
| Edit controller | `WtTerrainEditController` | node/helper | edit submission and edit-settle status |
| Edit operation | `WtTerrainEditOperation` | `Resource` or value object | carve, construct, fill, paint, restore-to-base command |
| Storage profile | `WtTerrainStorageProfile` | `Resource` | world manifest, edit journal, save/restart policy |
| Material profile | `WtTerrainMaterialProfile` | `Resource` | material IDs, textures, triplanar/debug view policy |
| Collision policy | `WtTerrainCollisionPolicy` | `Resource` | collision radius, readiness, prewarm, game queries |
| Runtime budget profile | `WtTerrainRuntimeBudgetProfile` | `Resource` | CPU, memory, queue, render, collision, edit limits |
| Debug overlay | `WtTerrainDebugOverlay` | `Control` or helper node | visible status UI and diagnostics |

The exact implementation language may change. The concept names may not silently
disappear.

## Normal game-facing flow

```text
World scene
  WtTerrainWorld
    terrain_profile = WtTerrainProfile
    generation_profile = WtTerrainGenerationProfile
    streaming_policy = WtTerrainStreamingPolicy
    storage_profile = WtTerrainStorageProfile
    material_profile = WtTerrainMaterialProfile
    collision_policy = WtTerrainCollisionPolicy
    budget_profile = WtTerrainRuntimeBudgetProfile
```

Expected game calls:

- configure or assign the terrain profiles;
- bind one or more viewers by node path or explicit transform;
- request preload/fast-travel with loading-screen semantics;
- submit edit operations through the edit controller;
- query collision/readiness/status;
- save or close through the storage boundary;
- enable debug overlay during development.

Games must not manage raw chunk queues, raw density arrays, Transvoxel lookup
data, or mesh/collision publication directly.

## Edit operation contract

Edits are commands, not unbounded additive density deltas.

Required modes:

- `carve`;
- `construct`;
- `fill`;
- `paint`;
- `restore_to_base`.

Required brush descriptors:

- sphere;
- box;
- capsule or segment;
- plane/flatten region.

Each edit operation must declare:

- mode;
- world-space transform or region;
- brush shape and radius/extent;
- material target when relevant;
- strength/falloff only if the mode semantics define bounded behavior;
- author/source tag for debugging and persistence;
- deterministic command ID;
- affected region estimate before execution.

Restore-to-base remains explicit. Automatic timed regeneration, smoothing,
erosion, collapse, and fluid equilibrium are optional future systems.

## Work-trigger contract

Settled terrain must be cold.

Allowed work triggers:

- viewer movement crossing the streaming threshold;
- explicit profile change;
- explicit preload/fast-travel request;
- edit submission;
- save/load/reopen;
- debug capture request;
- separately enabled optional system.

Idle polish, hidden continuous rebuilds, and unbounded background cleanup are
not accepted default behavior.

## Source layout contract

Required addon directories:

```text
addons/world_transvoxel_terrain/
  api/
  runtime/
  generation/
  streaming/
  edit/
  storage/
  material/
  collision/
  debug/
  editor/
  tests/
```

Ownership:

- `api/`: public adapters, resource registration, stable names;
- `runtime/`: terrain root, profile binding, viewer binding;
- `generation/`: generation profile definitions and offline hooks;
- `streaming/`: terrain-layer policy above `world-transvoxel`;
- `edit/`: edit operation definitions, validation, settle tracking;
- `storage/`: manifest/journal integration and save/restart boundary;
- `material/`: material IDs, textures, triplanar policy, debug views;
- `collision/`: readiness state, query policy, collision budget hooks;
- `debug/`: overlay, counters, inspection surfaces;
- `editor/`: Godot editor plugin glue only;
- `tests/`: addon-local smoke and contract harnesses.

No file in these directories may become a mixed-purpose terrain manager. A
future validator should reject large source files or cross-subsystem ownership
when implementation starts.

## Dependency contract

`world-transvoxel-terrain` depends on `world-transvoxel` but does not vendor it.

A2 must detect the dependency and fail clearly when it is absent. A2 may expose
placeholder terrain resources, but it must not implement terrain hot paths in
GDScript.

## Reference contract

A1 is allowed to keep a reference manifest and ignored local downloads. It must
not copy third-party implementation code into the addon.

Required reference inputs:

- Transvoxel primary reference;
- Godot addon/plugin documentation;
- Godot GDExtension/native-extension documentation;
- Godot RenderingDevice/compute documentation as deferred context only;
- local `world-transvoxel` implementation charter;
- local old marching-cubes audit.

## A1 exit criteria

A1 is complete when:

- `docs/A1_PUBLIC_API_SOURCE_LAYOUT_CONTRACT.md` exists;
- `docs/A1_MARCHING_CUBES_AUDIT.md` exists;
- `references/MANIFEST.md` records pinned/downloaded references;
- required source-layout directories exist with ownership placeholders;
- `python tools/validate_a1_contract.py` passes;
- next work is A2 addon-local smoke harness, not terrain implementation, compute,
  fluids, planets, or a game repository.
