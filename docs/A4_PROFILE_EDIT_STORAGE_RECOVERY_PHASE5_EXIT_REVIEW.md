# A4 Profile, Edit, Storage, and Recovery Phase 5 Exit Review

Status: complete.

Markers:

```text
WT_TERRAIN_A4_PHASE5_CONTRACT_PASS next=a5_local_reference_scene_debug_ui implementation=a4_exit_review
WT_TERRAIN_A4_PHASE5_EXIT_REVIEW_PASS validators=9 smokes=6 report=artifacts/a4_phase5_exit_review/a4_phase5_exit_review_report.json next=a5_local_reference_scene_debug_ui
```

## Exit decision

A4 closes at the terrain-addon API, profile, edit, storage, recovery, and
runtime-control level.

The next valid milestone is A5 local reference scene and debug UI.

## Evidence reviewed

A4 is closed by the combined evidence from phases 1 through 4:

- the default `WtTerrainProfile` is the 2048 x 2048 x 128 reference profile with
  `+Y` up and finite closed boundaries;
- `WtTerrainEditOperation` and `WtTerrainEditBatch` represent carve, construct,
  fill, paint, and restore-to-base operations;
- `WtTerrainEditBridge` submits those operations into real
  `WorldTransvoxelEditTransaction` objects through the official backend API;
- `WtTerrainWorld` owns backend terrain/config lifecycle, starts and stops the
  official backend fixture, and submits edit batches through the terrain-addon
  public API;
- edit persistence is verified by writing native `world.wtedit`, restarting,
  and reading the replayed edit;
- `WtTerrainWorld` exposes viewer update/removal, chunk query, runtime metrics,
  and cold-idle summary methods;
- the public runtime smoke streams one viewer, waits for render/collision
  readiness, queries a ready chunk, holds selected runtime counters stable while
  cold idle, removes the viewer, and stops cleanly.

## Closure boundary

A4 closure does not make broad gameplay or visual claims. These are not A4
claims and remain later work:

- full generated 2048 x 2048 x 64 exploration scene;
- broad movement, dynamic LOD, seam, and visual smoothness acceptance;
- addon-local inspection scene and debug UI;
- native terrain generation policy above baked fixtures;
- water/lava, planets, stability, vegetation, building blocks, GPU compute, or
  a separate game repository.

A5 owns the local reference scene and debug UI. A6 owns the game-repository
readiness decision.

## One-run evidence command

Run:

```console
python tools/a4_phase5_exit_review.py
```

The runner executes the terrain skeleton validator, A1 through A4 phase 5
contract validators, and the A2/A3/A4 phase 1/A4 phase 2/A4 phase 3/A4 phase 4
Godot smoke harnesses in one documented sequence.
