# TQP-53 Authoring And Inspection Workflow

Status: qualified by `WT_TERRAIN_TQP53_QUALIFICATION_PASS` on Godot 4.7.

Godot 4.7 is the minimum and sole current qualification target. Older engine
results are historical evidence, not a compatibility requirement.

Enabling the addon adds a `Terrain` editor dock. Selecting a `WtTerrainWorld`
exposes runtime profile selection, lifecycle actions, readiness and native
metrics, sphere/box brush drafts, carve/construction/fill/paint/volume
operations, non-persistent brush previews, material IDs, JSON draft import, and
one-action repro export.

The dock is editor-only. Exported games depend on the production runtime addon,
not the dock, Terrain Lab, or Cell Lab. Preview meshes have no scene owner and
are removed when the selection or plugin changes.

## Undo and durability

Editor undo/redo covers the uncommitted authoring document and resource
assignment. A committed terrain edit is append-only durable runtime state. This
version does not advertise a fake inverse operation: carve/construct reversal
is not generally exact, and the native authority does not expose journal
truncation. Reverting durable terrain therefore requires an explicitly chosen
snapshot/save recovery workflow.

## Materials and imports

The standard material palette is `1,2,3,4,5,7,8,10`. Production shading reads
the native generated and authored material-weight payloads directly. The addon
does not reproduce procedural terrain fields in its shader. Godot's normal
resource importer remains the texture import authority; the dock's JSON import
loads only a bounded authoring draft.

## Repro export

The save action writes `world_transvoxel_terrain.repro.v1` containing the API
contract, profiles, readiness, runtime/debug metrics, last error, and current
authoring draft. This is diagnostic evidence, not a world save.
