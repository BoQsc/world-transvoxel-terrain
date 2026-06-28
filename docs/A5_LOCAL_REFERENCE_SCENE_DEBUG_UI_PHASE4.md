# A5 Local Reference Scene and Debug UI Phase 4

Status: complete.

Markers:

```text
WT_TERRAIN_A5_PHASE4_CONTRACT_PASS next=a5_phase5_a5_exit_review implementation=debug_overlay_category_rendering
WT_TERRAIN_A5_PHASE4_GODOT_PASS sections=10 overlay=live resources=1 implementation=debug_overlay_category_rendering
WT_TERRAIN_A5_PHASE4_SMOKE_PASS engines=2 report=artifacts/a5_phase4_debug_overlay_categories/a5_phase4_debug_overlay_categories_report.json
```

## What this phase proves

A5 phase 4 renders the debug snapshot into explicit overlay sections:

- `WtTerrainDebugOverlayFormatter` renders world, terrain profile, generation
  profile, storage profile, recovery policy, budget, collision, streaming, edit,
  and material sections;
- `WtTerrainReferenceScene` uses the formatter for its debug label;
- live backend state, cold-idle state, render resources, collision resources,
  queue state, and material placeholder state are visible in overlay text;
- the smoke runs the reference scene against the official backend fixture and
  verifies the rendered section names and live values.

## Boundary

A5 phase 4 does not add polished interactive controls or game-repository
validation.

Next valid action is A5 phase 5: A5 exit review.
