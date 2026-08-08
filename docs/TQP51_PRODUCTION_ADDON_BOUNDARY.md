# TQP-51 Production Addon Boundary

Status: candidate boundary frozen.

Machine contract:
`addons/world_transvoxel_terrain/BOUNDARY_CONTRACT.json`.

Validation marker:

```text
WT_TERRAIN_TQP51_BOUNDARY_PASS candidate=world-transvoxel-terrain-cpu-tqp51-1 next=tqp52_runtime_api_profiles_readiness
```

## Purpose

TQP-51 identifies the standalone CPU terrain-addon candidate and freezes its
responsibility boundary before production API qualification. It does not declare
the addon production-ready and does not qualify TQP-52 or later work.

The installable runtime is exactly `addons/world_transvoxel_terrain`. Tests,
documents, artifacts, games, and labs are not runtime dependencies.

## Required dependency

The candidate depends on sibling addon `world-transvoxel` at revision
`f4abd7ab4f921f98aba4ee45b4453af0bae53cd8`. The dependency is not vendored.
Startup must fail with an explicit error when the required classes or valid
configuration are unavailable. There is no addon-local fallback mesher,
synthetic full-map surface, backdrop terrain, or copied Transvoxel topology.

## Ownership

`world-transvoxel` remains authoritative for density and material volume state,
regular and transition-cell meshing, native workers, streaming and storage
primitives, collision payloads, page publication, and authoritative sample
queries.

`world-transvoxel-terrain` owns game-facing lifecycle and profile orchestration,
bounded request adapters, edit validation and forwarding, terrain presentation
policy, and bounded diagnostic formatting. It may coordinate upstream work; it
may not reproduce upstream terrain hot paths in GDScript.

Games own player, camera, input, gameplay rules, and game-specific systems. Labs
own qualification, evidence, standards, and acceptance decisions. Neither may be
a runtime dependency of the addon.

## Threading And Lifetimes

Native `world-transvoxel` owns worker scheduling. Terrain-addon GDScript is
restricted to bounded main-thread coordination and must not create terrain
worker threads or run density, meshing, page generation, streaming, storage, or
collision build loops.

`WtTerrainWorld` owns its backend and configuration instances while running.
Assigned profile Resources persist for that terrain-world lifetime. Published
render and collision payloads remain upstream-owned. Caller-owned edit batches
are validated and converted into one upstream transaction. Shutdown requests an
upstream stop before backend references are released.

## Extension And Failure Policy

Supported extension points are profile Resources, material and presentation
policy, bounded request adapters, and diagnostic snapshot consumers. Replacing
the mesher, terrain authority, worker scheduler, or storage engine inside this
addon is not an extension point.

Missing dependencies, invalid profiles, invalid edits, and backend failures are
explicit errors. Requests fail closed. Silent fallback is forbidden.

## Unqualified Scope

The generated checker and color-atlas material path is retained only as bounded
diagnostic presentation scaffolding. It does not create geometry or terrain
state and remains unqualified until TQP-53. GPU terrain, game systems, production
texture quality, final runtime API/profile readiness, and a production release
remain outside TQP-51.

## Qualification

Run:

```text
python -B tools/validate_tqp51_boundary.py
```

The validator checks the machine contract, upstream pin, required bridge/API
surface, file-size boundary, absence of vendored authority, absence of lab
runtime dependencies, and absence of addon-local mesh construction or synthetic
terrain surface code.
