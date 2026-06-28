# A5 Local Reference Scene and Debug UI Phase 5 Exit Review

Status: complete.

Markers:

```text
WT_TERRAIN_A5_PHASE5_CONTRACT_PASS next=a6_game_repository_readiness_decision implementation=a5_exit_review
WT_TERRAIN_A5_PHASE5_EXIT_REVIEW_PASS validators=7 smokes=4 report=artifacts/a5_phase5_exit_review/a5_phase5_exit_review_report.json next=a6_game_repository_readiness_decision
```

## Exit decision

A5 closes at the addon-local reference scene and debug UI evidence level.

The next valid milestone is A6 game repository readiness decision.

## Evidence reviewed

A5 is closed by the combined evidence from phases 1 through 4:

- `WtTerrainDebugSnapshot` exposes stable world, terrain profile, generation
  profile, storage profile, recovery policy, budget, collision, streaming, edit,
  and material categories;
- `wt_terrain_reference_scene.tscn` exists inside the addon boundary and owns a
  `WtTerrainWorld` child plus debug overlay label;
- the reference scene assigns default terrain, generation, storage, and
  recovery resources without starting hidden backend work;
- the reference scene can start/stop its owned backend world through scene-level
  methods;
- the reference scene can submit viewer update/removal through scene-level
  methods;
- live debug snapshots and overlay text report backend state, cold-idle state,
  queue state, render resources, collision resources, streaming, edit, and
  configured material profile state;
- all reference-scene backend evidence uses ignored copied fixture data and does
  not vendor `world-transvoxel`.

## Closure boundary

A5 closure does not claim final gameplay validation. These are not A5 claims:

- creating the separate game repository;
- final game feel, player-controller, or gameplay-loop validation;
- broad generated 2048 x 2048 x 64 exploration acceptance;
- polished editor tooling;
- water/lava, planets, structural stability, vegetation, building blocks, GPU
  compute, or 0BSD backend work.

A6 owns the decision on whether the separate game repository can start.

## One-run evidence command

Run:

```console
python tools/a5_phase5_exit_review.py
```

The runner executes the terrain skeleton validator, A4 exit validator, A5 phase
1 through phase 5 contract validators, and the A5 phase 1 through phase 4 Godot
smoke harnesses in one documented sequence.
