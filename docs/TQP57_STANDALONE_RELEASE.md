# TQP-57 Standalone CPU Terrain Release

Version `1.0.0` is the first limited Windows CPU reference release. The release
archive contains only `addons/world_transvoxel_terrain` and is reproducible from
tracked source. `world-transvoxel` remains a separate exact dependency.

## Installation

1. Use Godot 4.7 on Windows x86-64 with Forward+.
2. Install `world-transvoxel` revision
   `f4abd7ab4f921f98aba4ee45b4453af0bae53cd8` as
   `res://addons/world_transvoxel`.
3. Extract `world-transvoxel-terrain-1.0.0.zip` so the addon is at
   `res://addons/world_transvoxel_terrain`.
4. Enable both plugins and use `WtTerrainWorld` API version 2.

The release does not silently substitute missing native authority. Dependency,
artifact, profile, storage, and queue failures remain explicit.

## Migration

Consumers migrating from the pre-release candidate keep native `.wtworld`,
`.wtchunk`, and `world.wtedit` formats unchanged. Game-specific shaders,
materials, controls, topology probes, and presentation remain outside this
addon. Use the native object-root journal path, keep durable edits append-only,
and replace direct native/game glue with `WtTerrainWorld` lifecycle, viewer,
collision-viewer, edit, query, readiness, and telemetry APIs.

Godot 4.6 results are historical only. Godot 4.7 is the minimum and sole current
qualification target; newer versions require an explicit qualification pass.

## Reproduce

Run:

```console
python -B tools/tqp55_release_matrix.py
python -B tools/tqp56_cpu_long_haul.py
python -B tools/build_tqp57_release.py
```

The final command writes the archive, per-file manifest, package digest, ZIP
digest, supported matrix, dependency pin, and release evidence under ignored
`artifacts/tqp57_release`. The authoritative scope and exclusions are in
`CPU_TERRAIN_STANDARD_1_0.md` and `TQP55_RELEASE_MATRIX.json`.
