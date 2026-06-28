# A5 Local Reference Scene and Debug UI Phase 2

Status: complete.

Markers:

```text
WT_TERRAIN_A5_PHASE2_CONTRACT_PASS next=a5_phase3_backend_reference_scene_runtime_smoke implementation=local_reference_scene_scaffold
WT_TERRAIN_A5_PHASE2_GODOT_PASS scene=instanced overlay=ready profile=2048x64 implementation=local_reference_scene_scaffold
WT_TERRAIN_A5_PHASE2_SMOKE_PASS engines=2 report=artifacts/a5_phase2_reference_scene_scaffold/a5_phase2_reference_scene_scaffold_report.json
```

## What this phase proves

A5 phase 2 creates the addon-local reference scene scaffold:

- `wt_terrain_reference_scene.tscn` is an installable addon scene, not a game
  repository scene;
- the scene owns a `WtTerrainWorld` child and a minimal debug overlay label;
- `WtTerrainReferenceScene` assigns default terrain, generation, storage, and
  recovery resources when the scene is inspected;
- the scene refreshes through `WtTerrainDebugSnapshot`;
- default scene inspection does not start backend work.

## Boundary

A5 is not complete. This phase does not prove backend-backed streaming inside
the reference scene, visual terrain inspection, material preview, or interactive
debug controls.

Next valid action is A5 phase 3: backend reference-scene runtime smoke.
