# CPU Terrain Standard 1.0

This standard defines the first qualified production boundary for
`world-transvoxel-terrain`. It is evidence-scoped, not a claim that every
possible terrain workload or machine is solved.

## Authoritative boundaries

- `world-transvoxel` revision
  `f4abd7ab4f921f98aba4ee45b4453af0bae53cd8` owns density samples, material
  samples, regular and transition topology, adaptive streaming, edit
  application, persistence, native queues, render resources, and collision
  resources.
- `world-transvoxel-terrain` version `1.0.0` owns the stable Godot-facing
  profiles, lifecycle, bounded viewer/edit/query requests, readiness,
  diagnostics, authoring drafts, and deterministic package.
- Terrain Lab owns qualification evidence. Integration games own presentation
  and gameplay. Neither is a runtime dependency of this addon.
- No fallback mesher, fallback density field, synthetic terrain surface, or
  copied Transvoxel table is permitted in the production addon.

The coordinate system is right-handed Godot 3D with +Y up. Density and material
meaning come from the native authority. Terrain is a bounded signed 3D volume,
not a heightmap. LOD transition continuity and edited-state publication must be
accepted only through authority results; consumers must not patch seams with
presentation geometry.

## Runtime behavior

`WtTerrainWorld` API version 2 is the supported entry point. World lifecycle and
request results are generation-aware. Render, collision, edit, and query
readiness are separate. Viewer revisions are positive and monotonic within one
running generation. Queue and request capacities are finite and fail closed.

The built-in `LOW_POWER`, `BALANCED`, `QUALITY`, and `REFERENCE` profiles expose
resolution, distance, queue, memory, collision, and power intent. They are
starting envelopes, not automatic hardware promises. Runtime profile mutation
after world start is unsupported; stop, configure, and restart instead.

## Editing and storage

Carve, construct, fill, paint, restore-to-base, and volume placement are bounded
commands forwarded to the native authority. Smooth SDF behavior is limited to
the supported spherical operations. Durable edits are append-only; the addon
does not claim a mathematically exact undo for committed terrain.

The native object-root `world.wtedit` journal is required. Save/restart replay
must preserve world revision and authoritative sample identity. Custom journal
locations and disabled persistence fail closed. Snapshot compaction and
migration remain bounded by native format and capacity rules.

## Targeted collision

Collision residency is driven by explicit collision viewers and has independent
radius, capacity, apply budget, deadline, activation, and deactivation controls.
Rendering terrain does not imply that every rendered chunk needs collision.
Production consumers should request collision near actors and interactions,
then release it when no longer needed.

## Performance evidence

The release matrix is Windows 10 x86-64, Godot 4.7, Forward+, and the pinned
reference hardware class. TQP-47 retains 2048 x 256 x 2048 rendered traversal,
flight, cave, LOD churn, teleport, digging, and construction evidence. TQP-48
retains measured GPU-board power and frame data with its target-miss status
visible. TQP-49 retains 1802.58 seconds and 108,000 frames of drift, persistence,
recovery, and shutdown evidence. TQP-56 adds 60 seconds through the production
wrapper with repeated edits, queries, restarts, origin shifts, and queue/memory
checks.

These values are comparison baselines and regression ceilings on one reference
machine. They are not universal frame-rate, wattage, view-distance, or latency
guarantees.

## Unqualified scope

- non-Windows platforms, non-x86-64 systems, and Godot versions other than 4.7;
- arbitrary CPU, GPU, driver, renderer, thermal, or power equivalence;
- GPU density generation, meshing, streaming, and edit execution;
- multiplayer authority, navigation, gameplay, water, vegetation, structural
  stability, destruction simulation, and other game systems;
- unbounded terrain, queues, collision, memory, view distance, or edit history;
- multi-day operation and a universal 16 W at 60 FPS claim.

Any expansion of this standard requires new pinned evidence and a versioned
qualification decision. A visual workaround or downstream game success does
not change the authority contract.
