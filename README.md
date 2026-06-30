# World Transvoxel Terrain

Reusable Godot terrain addon built above `world-transvoxel`.

Status: A6 complete. This repository defines the addon boundary, public API
shape, source layout, dependency detection, local smoke validation, official
`world-transvoxel` bridge,
terrain/edit/storage/recovery resource contracts, backend edit transactions,
journal replay, public `WtTerrainWorld` lifecycle ownership, viewer streaming,
ready chunk query, runtime metrics, cold-idle stability, and a debug snapshot
data contract plus an addon-local reference scene scaffold that can run against
the official backend fixture. The reference scene now renders explicit debug
overlay sections for world/profile/storage/budget/collision/streaming/edit and
material state. The downstream G46 validation gate locks a minimal public
`WtTerrainWorld` API contract with stable lifecycle aliases, profile summaries,
authoritative sample query methods/signals, storage snapshot request wrappers,
runtime telemetry, and debug snapshot access. A6 approved creating a separate
validation game repository when
explicitly requested; `world-transvoxel-validation-game` now exists with G0
install/run validation complete, first-person playable-world target evidence,
G2 first-person flat baseline evidence, G3 flat/mountain generation evidence,
G4 terrain edit interaction evidence, G5 material/performance baseline evidence,
and G6 profile-selectable playable-world evidence through commit `6417d34`,
including 4 by 4 baked page sets, flat and mountain captures, terrain triangles,
terrain collision, scripted player motion, scripted jump, crosshair, visible
player capture, first-person carve/place affordance, edit commits, replacement
metrics, materialized checker terrain, GPU watt sampling, flat/mountain playable
profile selection, first-person plus overview captures, human mouse-capture fix,
and edit-time material reapply to avoid white blink. Human feedback confirms the
fixture is still small and performance cannot be judged from this scale. This is
not a game repository and does not yet claim production-ready terrain.

## Role

`world-transvoxel-terrain` packages proven terrain patterns into game-facing
APIs, resources, presets, debug tools, save/load hooks, and edit/recovery
conventions.

The current minimal game-facing API is centered on `WtTerrainWorld`:
`start_world`, `stop_world`, `is_world_running`, `get_world_state_name`,
`get_world_revision`, `get_world_source_revision`, `get_world_page_count`,
`get_profile_summaries`, `update_viewer`, `remove_viewer`, `query_chunk_state`,
`submit_edit_batch`, `request_authoritative_sample`,
`request_authoritative_samples`, `request_world_compaction`,
`request_world_migration`, `get_runtime_metrics`, `get_cold_idle_summary`,
`get_debug_snapshot`, and `get_terrain_api_contract_summary`.

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
python tools/validate_a4_phase4.py
python tools/validate_a4_phase5.py
python tools/validate_a5_phase1.py
python tools/validate_a5_phase2.py
python tools/validate_a5_phase3.py
python tools/validate_a5_phase4.py
python tools/validate_a5_phase5.py
python tools/validate_a6_readiness_decision.py
python tools/a2_addon_smoke.py
python tools/a3_bridge_smoke.py
python tools/a4_phase1_resources_smoke.py
python tools/a4_phase2_bridge_storage_smoke.py
python tools/a4_phase3_terrain_world_lifecycle_smoke.py
python tools/a4_phase4_reference_runtime_cold_idle_smoke.py
python tools/a4_phase5_exit_review.py
python tools/a5_phase1_debug_snapshot_smoke.py
python tools/a5_phase2_reference_scene_scaffold_smoke.py
python tools/a5_phase3_reference_scene_runtime_smoke.py
python tools/a5_phase4_debug_overlay_categories_smoke.py
python tools/a5_phase5_exit_review.py
python tools/a6_readiness_decision.py
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
WT_TERRAIN_A4_PHASE4_CONTRACT_PASS next=a4_phase5_a4_exit_review implementation=reference_profile_runtime_cold_idle
WT_TERRAIN_A4_PHASE4_SMOKE_PASS engines=2 report=artifacts/a4_phase4_reference_runtime_cold_idle/a4_phase4_reference_runtime_cold_idle_report.json
WT_TERRAIN_A4_PHASE5_CONTRACT_PASS next=a5_local_reference_scene_debug_ui implementation=a4_exit_review
WT_TERRAIN_A4_PHASE5_EXIT_REVIEW_PASS validators=9 smokes=6 report=artifacts/a4_phase5_exit_review/a4_phase5_exit_review_report.json next=a5_local_reference_scene_debug_ui
WT_TERRAIN_A5_PHASE1_CONTRACT_PASS next=a5_phase2_local_reference_scene_scaffold implementation=debug_snapshot_contract
WT_TERRAIN_A5_PHASE1_SMOKE_PASS engines=2 report=artifacts/a5_phase1_debug_snapshot/a5_phase1_debug_snapshot_report.json
WT_TERRAIN_A5_PHASE2_CONTRACT_PASS next=a5_phase3_backend_reference_scene_runtime_smoke implementation=local_reference_scene_scaffold
WT_TERRAIN_A5_PHASE2_SMOKE_PASS engines=2 report=artifacts/a5_phase2_reference_scene_scaffold/a5_phase2_reference_scene_scaffold_report.json
WT_TERRAIN_A5_PHASE3_CONTRACT_PASS next=a5_phase4_debug_overlay_category_rendering implementation=backend_reference_scene_runtime_smoke
WT_TERRAIN_A5_PHASE3_SMOKE_PASS engines=2 report=artifacts/a5_phase3_reference_scene_runtime/a5_phase3_reference_scene_runtime_report.json
WT_TERRAIN_A5_PHASE4_CONTRACT_PASS next=a5_phase5_a5_exit_review implementation=debug_overlay_category_rendering
WT_TERRAIN_A5_PHASE4_SMOKE_PASS engines=2 report=artifacts/a5_phase4_debug_overlay_categories/a5_phase4_debug_overlay_categories_report.json
WT_TERRAIN_A5_PHASE5_CONTRACT_PASS next=a6_game_repository_readiness_decision implementation=a5_exit_review
WT_TERRAIN_A5_PHASE5_EXIT_REVIEW_PASS validators=7 smokes=4 report=artifacts/a5_phase5_exit_review/a5_phase5_exit_review_report.json next=a6_game_repository_readiness_decision
WT_TERRAIN_A6_CONTRACT_PASS decision=approve_validation_game_repository implementation=readiness_decision next=separate_validation_game_repository_when_user_approves
WT_TERRAIN_A6_READINESS_DECISION_PASS decision=approve_validation_game_repository validators=2 report=artifacts/a6_readiness_decision/a6_readiness_decision_report.json next=separate_validation_game_repository_when_user_approves
```

## License

Project-owned code and documentation in this repository are 0BSD unless a file
explicitly says otherwise. See [LICENSE_SCOPE.md](LICENSE_SCOPE.md) and
[addons/world_transvoxel_terrain/LICENSE_SCOPE.md](addons/world_transvoxel_terrain/LICENSE_SCOPE.md).
