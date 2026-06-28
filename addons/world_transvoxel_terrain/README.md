# World Transvoxel Terrain Addon

This directory is the installable Godot addon boundary for
`world-transvoxel-terrain`.

Current status: A5 phase 4. The addon has public terrain/profile/edit/storage
resources, a bridge to the official `world-transvoxel` backend, terrain-world
lifecycle/edit submission, and a bounded reference runtime/cold-idle smoke
through `WtTerrainWorld`. It now also has the debug snapshot data contract for
the local reference scene plus an addon-local reference scene scaffold that can
run against the official backend fixture and render explicit debug overlay
sections. A5 phase 5 exit review is next. It is not yet a game-ready terrain
package.

Allowed GDScript here is limited to editor glue, scene scaffolding, input
routing, debug UI, and small smoke-test harnesses. Terrain generation, meshing,
streaming policy, storage, edit recovery, and other hot paths must be native,
low-level addon code, binary tooling, shaders when justified, or Python offline
tooling.

The addon depends on `world-transvoxel` but does not vendor it.
