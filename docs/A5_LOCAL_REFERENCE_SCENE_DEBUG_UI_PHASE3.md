# A5 Local Reference Scene and Debug UI Phase 3

Status: complete.

Markers:

```text
WT_TERRAIN_A5_PHASE3_CONTRACT_PASS next=a5_phase4_debug_overlay_category_rendering implementation=backend_reference_scene_runtime_smoke
WT_TERRAIN_A5_PHASE3_GODOT_PASS scene=backend_running overlay=live cold_idle=stable implementation=backend_reference_scene_runtime_smoke
WT_TERRAIN_A5_PHASE3_SMOKE_PASS engines=2 report=artifacts/a5_phase3_reference_scene_runtime/a5_phase3_reference_scene_runtime_report.json
```

## What this phase proves

A5 phase 3 runs the addon-local reference scene against the official backend
fixture:

- `WtTerrainReferenceScene` can start and stop its owned `WtTerrainWorld`
  backend through scene-level methods;
- the scene can submit viewer update/removal through scene-level methods;
- the scene refreshes `WtTerrainDebugSnapshot` while backend resources are live;
- the debug status text reports running backend state, cold-idle state, render
  resources, and collision resources;
- viewer removal returns the scene to zero render/collision resources;
- the smoke uses copied ignored fixture data and does not vendor
  `world-transvoxel`.

## Boundary

A5 is not complete. This phase does not add a polished visual inspector,
interactive controls, material preview, or final game validation.

Next valid action is A5 phase 4: debug overlay category rendering.
