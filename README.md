# World Transvoxel Terrain

Reusable Godot terrain addon built above `world-transvoxel`.

Status: A4 phase 3 terrain-world lifecycle complete. This repository defines the
addon boundary, public API shape, source layout, dependency detection, local
smoke validation, official `world-transvoxel` bridge, and the first
terrain/edit/storage/recovery resource contract plus backend edit transaction
and journal replay evidence through public `WtTerrainWorld` lifecycle ownership.
It is not a game repository and does not yet claim game-ready terrain.

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
python tools/validate_a1_contract.py
python tools/validate_a2_smoke.py
python tools/validate_a3_bridge.py
python tools/validate_a4_phase1.py
python tools/validate_a4_phase2.py
python tools/validate_a4_phase3.py
python tools/a2_addon_smoke.py
python tools/a3_bridge_smoke.py
python tools/a4_phase1_resources_smoke.py
python tools/a4_phase2_bridge_storage_smoke.py
python tools/a4_phase3_terrain_world_lifecycle_smoke.py
```

Expected marker:

```text
WT_TERRAIN_SKELETON_PASS addon=world-transvoxel-terrain implementation=deferred game_repository=deferred
WT_TERRAIN_A1_CONTRACT_PASS next=a2_addon_local_smoke_harness implementation=contract_only
WT_TERRAIN_A2_CONTRACT_PASS next=a3_world_transvoxel_bridge implementation=smoke_only
WT_TERRAIN_A2_SMOKE_PASS engines=2 report=artifacts/a2_addon_smoke/a2_addon_smoke_report.json
WT_TERRAIN_A3_CONTRACT_PASS next=a4_terrain_profile_edit_storage_recovery implementation=bridge_only
WT_TERRAIN_A3_BRIDGE_PASS engines=2 report=artifacts/a3_bridge_smoke/a3_bridge_smoke_report.json
WT_TERRAIN_A4_PHASE1_CONTRACT_PASS next=a4_phase2_bridge_edit_submission implementation=resource_semantics_only
WT_TERRAIN_A4_PHASE1_SMOKE_PASS engines=2 report=artifacts/a4_phase1_resources/a4_phase1_resources_report.json
WT_TERRAIN_A4_PHASE2_CONTRACT_PASS next=a4_phase3_public_terrain_world_lifecycle implementation=bridge_storage_fixture
WT_TERRAIN_A4_PHASE2_SMOKE_PASS engines=2 report=artifacts/a4_phase2_bridge_storage/a4_phase2_bridge_storage_report.json
WT_TERRAIN_A4_PHASE3_CONTRACT_PASS next=a4_phase4_reference_profile_runtime_cold_idle implementation=terrain_world_lifecycle
WT_TERRAIN_A4_PHASE3_SMOKE_PASS engines=2 report=artifacts/a4_phase3_terrain_world_lifecycle/a4_phase3_terrain_world_lifecycle_report.json
```

## License

Project-owned code and documentation in this repository are 0BSD unless a file
explicitly says otherwise. See [LICENSE_SCOPE.md](LICENSE_SCOPE.md) and
[addons/world_transvoxel_terrain/LICENSE_SCOPE.md](addons/world_transvoxel_terrain/LICENSE_SCOPE.md).
