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

G1 visible-playtest guard commit:

```text
06e7956 Add G1 visible playtest guard
```

The guard fixes the first gray-rectangle-only human result by aiming the camera
at the generated terrain chunk, adding status text and orientation markers, and
failing if no terrain `MeshInstance3D` is present. Human rerun confirmation is
still pending.

Root-safe visual-capture validation commit:

```text
5a47a8d Add root-safe validation visual capture
```

This commit makes the repository-root `project.godot` a notice-only project,
keeps addon-enabled playtests in generated artifact projects, adds
`WT_VALIDATION_ROOT_PROJECT_SAFE_IMPORT_PASS`, and adds
`WT_VALIDATION_G1_VISUAL_CAPTURE_RUN_PASS` screenshot evidence. Human-visible
rerun confirmation is still pending.

Hardened G1 terrain-geometry evidence commit:

```text
3c521b0 Harden G1 terrain visual evidence
```

This commit makes the G1 guard and visual capture require nonzero terrain
triangle geometry and centered terrain-bright image samples. The accepted run
reported `terrain_triangles=512` on Godot 4.6.3 and Godot 4.7.

Playable-character validation commit:

```text
d9eb31e Add playable G1 validation character
```

This commit adds a small `CharacterBody3D` player, terrain-collision settling,
scripted autonomous movement with human input disabled in tests, and visible
player capture. The accepted run reported `player_motion=2.800` and
`player_cyan_samples=432` on Godot 4.6.3 and Godot 4.7.

First-person playable-world target commit:

```text
d7848dc Add playable world target and first-person baseline
```

This commit adds `docs/PLAYABLE_WORLD_TARGET.md`, first-person camera mode,
crosshair, an overview camera mode for automated capture, and the
`WT_VALIDATION_PLAYABLE_WORLD_TARGET_PASS` contract gate. The accepted run kept
`WT_VALIDATION_G1_SMOKE_PASS` and `WT_VALIDATION_G1_VISUAL_CAPTURE_RUN_PASS`
green on Godot 4.6.3 and Godot 4.7.

G2 first-person flat baseline commit:

```text
1f839f3 Complete first-person flat baseline gate
```

This commit adds `docs/G2_FIRST_PERSON_PLAYABLE_BASELINE.md`,
`WT_VALIDATION_G2_CONTRACT_PASS`, and `WT_VALIDATION_G2_SMOKE_PASS`. The
accepted run proves `generation=FLAT`, `terrain_triangles=512`,
`walk_motion=2.800`, and `jump_height=1.080` on Godot 4.6.3 and Godot 4.7.

G3 flat/mountain generation modes commit:

```text
9aa7018 Add flat and mountain generation mode gate
```

This commit adds `docs/G3_TERRAIN_GENERATION_MODES.md`,
`WT_VALIDATION_G3_CONTRACT_PASS`, and `WT_VALIDATION_G3_SMOKE_PASS`. The
accepted run bakes `flat_large` and `mountain_large` through the standard dense
bake path with 16 pages per profile, then loads both in Godot with
`flat_triangles=4096`, `mountain_triangles=5436`, and `mountain_span=7.862` on
Godot 4.6.3 and Godot 4.7.

G4 terrain edit interaction commit:

```text
3d5df31 Add first-person terrain edit interaction gate
```

This commit adds `docs/G4_TERRAIN_EDIT_INTERACTION.md`,
`ValidationTerrainInteractor`, `WT_VALIDATION_G4_CONTRACT_PASS`, and
`WT_VALIDATION_G4_SMOKE_PASS`. The accepted run verifies left-click carve and
right-click construct/place affordances, submits automated carve/place through
the same interactor with human input disabled, checks authoritative sample
updates and collision resources, and reports edit replacement evidence on Godot
4.6.3 and Godot 4.7.
