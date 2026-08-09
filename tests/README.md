# Tests

Addon-local tests start in A2.

They must prove local package behavior, dependency detection, API contracts, and
smoke scenes. Final gameplay validation belongs in the later separate game
repository, not in this addon repo and not in `world-transvoxel-sandbox`.

A2 smoke entry point:

```console
python tools/a2_addon_smoke.py
```

A3 bridge smoke entry point:

```console
python tools/a3_bridge_smoke.py
```

A4 terrain profile/edit/storage/recovery smoke entry points:

```console
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
python -B tools/tqp57_large_terrain_acceptance.py
```

The TQP-57 workload requires Godot 4.7 Forward+, runs nine bounded large-world
scenarios, audits an actual mixed-LOD mesh interface, and retains four visual
captures plus performance, edit, collision, and persistence evidence.
