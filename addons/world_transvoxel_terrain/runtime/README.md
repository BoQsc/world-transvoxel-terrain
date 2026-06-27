# Runtime Ownership

Terrain root, profile binding, viewer binding, lifecycle, and high-level state
coordination belong here.

Runtime code may coordinate subsystem calls. It must not become a monolithic
chunk manager.

A2 adds `WtTerrainWorld` as a placeholder scene entry point with dependency
status reporting only.

A3 adds `WtWorldTransvoxelBridge`, a narrow `ClassDB` adapter that can read
official `world-transvoxel` identity/config status without starting terrain.
