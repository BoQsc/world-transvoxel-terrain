# World Transvoxel Terrain

Reusable Godot terrain addon built above `world-transvoxel`.

Status: A0 skeleton. This repository defines the addon boundary and validation
rules before implementation. It is not a game repository and does not yet claim
game-ready terrain.

## Role

`world-transvoxel-terrain` packages proven terrain patterns into game-facing
APIs, resources, presets, debug tools, save/load hooks, and edit/recovery
conventions.

It depends on `world-transvoxel`. It does not vendor or copy
`world-transvoxel-sandbox`, and it does not contain Eric Lengyel's MIT
Transvoxel source or lookup data.

Intended consumer path:

```text
install world-transvoxel
install world-transvoxel-terrain
add terrain scene/resource
choose config preset
connect player/camera
run
```

## Current non-goals

- no separate game repository yet;
- no GPU compute rewrite;
- no water/lava, planets, structural collapse, vegetation, building blocks, or
  inventory systems;
- no independent 0BSD Transvoxel backend replacement;
- no large GDScript terrain hot paths.

## Implementation rule

Performance-sensitive terrain work belongs in native code, low-level addon
interfaces, binary formats, shaders when justified, or Python offline tooling.
GDScript is limited to Godot scaffolding, editor glue, input routing, debug UI,
and small smoke-test harnesses.

Read [IMPLEMENTATION_CHARTER.md](IMPLEMENTATION_CHARTER.md) before changing the
project. It is the single source of truth for scope, package boundaries,
implementation order, and definition of done.

## Validate

```console
python tools/validate_terrain_skeleton.py
```

Expected marker:

```text
WT_TERRAIN_SKELETON_PASS addon=world-transvoxel-terrain implementation=deferred game_repository=deferred
```

## License

Project-owned code and documentation in this repository are 0BSD unless a file
explicitly says otherwise. See [LICENSE_SCOPE.md](LICENSE_SCOPE.md) and
[addons/world_transvoxel_terrain/LICENSE_SCOPE.md](addons/world_transvoxel_terrain/LICENSE_SCOPE.md).
