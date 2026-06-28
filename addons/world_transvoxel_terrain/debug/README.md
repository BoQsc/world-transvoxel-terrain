# Debug Ownership

Debug overlays, status surfaces, counters, captures, and inspector helpers
belong here.

Debug features must not create hidden terrain work in normal runtime mode.

A5 phase 1 adds `WtTerrainDebugSnapshot`, a read-only status aggregation helper
for the later local reference scene and debug UI.

A5 phase 2 adds `wt_terrain_reference_scene.tscn` and
`WtTerrainReferenceScene`, a minimal addon-local scene scaffold with a
`WtTerrainWorld` child and debug status label.
