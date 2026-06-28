# A6 Game Repository Readiness Decision

Status: complete.

Markers:

```text
WT_TERRAIN_A6_CONTRACT_PASS decision=approve_validation_game_repository implementation=readiness_decision next=separate_validation_game_repository_when_user_approves
WT_TERRAIN_A6_READINESS_DECISION_PASS decision=approve_validation_game_repository validators=2 report=artifacts/a6_readiness_decision/a6_readiness_decision_report.json next=separate_validation_game_repository_when_user_approves
```

## Decision

A6 approves creating a separate validation game repository when the user
explicitly asks for it.

This approval is narrow:

- the future game repository may import `world-transvoxel` and
  `world-transvoxel-terrain` as addons;
- the future game repository may test real gameplay integration, visual quality,
  input, camera, interaction, loading, and user-facing performance;
- the future game repository must not fork or copy `world-transvoxel-sandbox` as
  its implementation base;
- this decision does not claim production-ready terrain, final visuals,
  seamless dynamic LOD, broad 2048 x 2048 x 64 exploration acceptance, GPU
  compute, fluids, planets, vegetation, building blocks, structural stability,
  or 0BSD backend replacement.

The decision is `approve_validation_game_repository` because the addon now has
the three prerequisites that A6 was created to check: package boundary, local
smoke evidence, and stable minimal API.

## Readiness gates

### Gate 1 - Package boundary

Pass. The installable addon boundary is `addons/world_transvoxel_terrain/` with
`plugin.cfg`, addon-local README/license scope, separated API/runtime/edit/
storage/generation/debug/editor folders, and no vendored `world-transvoxel`
dependency.

### Gate 2 - Local smoke evidence

Pass. A5 closed with `WT_TERRAIN_A5_PHASE5_EXIT_REVIEW_PASS`, which reruns the
terrain skeleton validator, A4 phase 5 validator, A5 phase 1 through phase 5
validators, and A5 phase 1 through phase 4 Godot smoke harnesses.

### Gate 3 - Stable minimal API

Pass for validation-game creation. The minimal public surface has stable
class-name entry points for:

- `WtTerrainWorld`;
- `WtTerrainProfile`;
- `WtTerrainGenerationProfile`;
- `WtTerrainStorageProfile`;
- `WtTerrainRecoveryPolicy`;
- `WtTerrainEditOperation`;
- `WtTerrainEditBatch`;
- `WtTerrainReferenceScene`;
- `WtTerrainDebugSnapshot`;
- `WtTerrainDebugOverlayFormatter`.

The validation game can start with this minimal API:

- create or instance `WtTerrainWorld`;
- assign terrain, generation, storage, and recovery resources;
- start and stop the backend world;
- submit edit batches;
- update and remove viewers;
- query ready chunk state;
- read runtime metrics, cold-idle state, dependency status, and debug snapshots.

## Required first scope for the future game repository

The first game-repository milestone must stay small:

1. create an empty Godot project;
2. install `world-transvoxel`;
3. install `world-transvoxel-terrain`;
4. instance the addon-local reference scene or a tiny game scene using
   `WtTerrainWorld`;
5. run one headless smoke and one human-visible playtest scene;
6. record every integration failure back as terrain-addon work, not as hidden
   game-side workaround code.

Any larger gameplay system is out of scope until this install-and-run path is
working.

## Boundary

A6 answers whether the separate validation game repository may be created. It
does not replace the need for that game repository to validate real gameplay.

## Downstream repository

The A6-approved downstream repository now exists as
`world-transvoxel-validation-game`.

Initial validation-game commit:

```text
8923f6e Create validation game G0 install run scaffold
```

G0 completed the install/run validation smoke against `world-transvoxel` commit
`a84256e` and `world-transvoxel-terrain` commit `2219a0f` on Godot 4.6.3 and
Godot 4.7. The next validation-game step is G1 human-visible playtest
confirmation.
