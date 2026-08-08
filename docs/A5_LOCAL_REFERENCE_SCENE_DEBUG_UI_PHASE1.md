# A5 Local Reference Scene and Debug UI Phase 1

Status: complete.

Markers:

```text
WT_TERRAIN_A5_PHASE1_CONTRACT_PASS next=a5_phase2_local_reference_scene_scaffold implementation=debug_snapshot_contract
WT_TERRAIN_A5_PHASE1_GODOT_PASS categories=10 profile=2048x128 implementation=debug_snapshot_contract
WT_TERRAIN_A5_PHASE1_SMOKE_PASS engines=2 report=artifacts/a5_phase1_debug_snapshot/a5_phase1_debug_snapshot_report.json
```

## What this phase proves

A5 phase 1 creates the debug data contract that the local reference scene and
debug UI will consume:

- `WtTerrainDebugSnapshot.capture(terrain_world)` returns one dictionary with
  stable world, terrain profile, generation profile, storage profile, recovery
  policy, budget, collision, streaming, edit, and material categories;
- the snapshot reads public `WtTerrainWorld` state and resource summaries;
- default snapshot capture does not start backend work;
- the material category is explicit about the configured debug material profile
  instead of hiding material policy state.

## Boundary

A5 is not complete. This phase does not add the reference scene, visual overlay,
interactive inspector, visual material preview, or backend-backed debug capture.

Next valid action is A5 phase 2: local reference scene scaffold.
