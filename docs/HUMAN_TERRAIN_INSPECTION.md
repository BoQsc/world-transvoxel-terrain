# Human Terrain Inspection

This is the direct human defect-reproduction surface for the CPU terrain
standard. It subclasses the `2,048 x 256 x 2,048` TQP-57 acceptance scene
without changing that automated qualification scene. It uses the same
`WtTerrainWorld` runtime, `world-transvoxel` native authority, adaptive LOD0-3
residency, global LOD3 coverage, targeted collision, and edit-batch path. It
contains no alternate mesher, terrain implementation, or fallback.

The launcher creates an ignored Godot composition project under
`artifacts/human_terrain_inspection/project`. Godot requires installed add-ons
under `res://`, so the launcher copies the current terrain add-on and the exact
sibling `world-transvoxel` package into that disposable project. The copied
files are packaging inputs, not a fork or a second implementation.

## Launch

```console
python -B tools/launch_human_terrain_inspection.py
```

The launcher accepts `--editor` to open the generated project in the editor and
`--prepare-only` to build and import it without opening a window. It rejects
Godot older than 4.7 and constrains itself and the launched Godot process to at
most three logical CPUs.

The runtime opens fullscreen, moves itself to the foreground, captures mouse
look, and enters collision-controlled walking as soon as the initial terrain
target is ready. Press `Escape` to release the mouse when UI access is needed.

## Runtime Controls

| Control | Action |
| --- | --- |
| Right mouse | Capture or release mouse look |
| Mouse | Look while captured |
| W / A / S / D | Move in fly or walk mode |
| Space | Ascend in fly mode; jump in walk mode |
| C / Ctrl | Descend in fly mode |
| Shift | Fast flight |
| Escape | Release mouse look |
| Carve / Construct or 1 / 2 | Select the authoritative sphere edit mode |
| Apply, Enter, or left mouse | Apply the selected edit at the crosshair target |
| Fly / Walk or F | Select free inspection or collision-controlled movement |
| F8 | Start or stop an issue recording |
| F9 | Save an exact-frame PNG and state mark |
| F10 | Replay the last stopped camera path |

The yellow target appears only when the crosshair hits a currently ready LOD0
collision resource. The human viewer follows the camera horizontally with a
small look-ahead and remains at the reference terrain's surface band while the
free camera flies above it. The human harness requests a two-chunk local
collision radius so the crosshair and player can operate around that focus;
the TQP-57 acceptance profile remains at its authoritative one-chunk default.
An edit is refused while local collision is missing or invalid. A valid prior
collision remains usable while the authority stages its atomic replacement,
matching the runtime's safety-collision contract. A second edit remains blocked
until the current edit's own render and collision replacements finish. Walk
mode can only start from a valid yellow terrain target and uses a
`CharacterBody3D` capsule against the same localized terrain collision
resources. The dock exposes world readiness, viewer and
revision state, active and ready residency, LOD counts, overlap count, pending
generation state, queues, FPS, and frame time.

Each human edit reports authoritative commit, local visual replacement, and
local collision replacement latency in milliseconds. Results are appended to
`user://world_transvoxel_terrain/human_performance/edit_timings.jsonl`; they are
diagnostic evidence and do not replace the automated acceptance baseline.

Issue recordings are capped at 30 seconds and sample camera motion, viewer
position, active LOD counts, readiness, revisions, queues, replacements, and
retirements at 10 Hz. F9 adds a PNG and a full validation snapshot at the exact
frame selected by the human reviewer. Recording and marking do not rerun the
long qualification suite. F10 replays only the captured camera path against the
live terrain to reproduce temporal LOD behavior.

Teleport buttons move the streaming window to deterministic inspection sites.
The harness starts at the near-field surface so collision walking and edits can
be exercised immediately; `Center` is the explicit reference-cave and temporal
LOD stress site.
`Resident chunk bounds` reveals the active render hierarchy. `World envelope`
shows the bounded world, and `Stream with camera` controls whether free flight
publishes visual and collision viewer updates.

Human observations are evidence for investigation, not an automatic pass. Any
suspected crack, sawtooth, stale collision, edit delay, pop, or material defect
must be reproduced by a focused machine-readable test before changing the
authority or the terrain integration.
