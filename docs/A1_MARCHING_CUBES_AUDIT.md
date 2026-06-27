# A1 Marching-Cubes Maintainability Audit

Status: complete for A1 contract input.

Inspected local project:

```text
C:\Users\Windows10_new\Documents\gpu-marching-cubes\world_marching_cubes
```

This audit exists to prevent `world-transvoxel-terrain` from repeating the old
terrain architecture failure mode.

## Measured structure

Largest inspected source/doc files:

| File | Lines | Bytes | Classification |
| --- | ---: | ---: | --- |
| `chunk_manager.gd` | 9,116 | 401,086 | mixed-purpose runtime monolith |
| `terrain.gdshader` | 482 | 20,400 | large material/debug shader |
| `technical_documents/03_optional_migration_roadmap.md` | 441 | 11,897 | migration notes |
| `technical_documents/04_alternative_architectures.md` | 409 | 12,053 | alternative design notes |
| `gen_density.glsl` | 363 | 13,953 | terrain density compute shader |
| `marching_cubes.glsl` | 292 | 11,309 | meshing compute shader |
| `roads/road_manager.gd` | 249 | 7,817 | road subsystem split-out |

`chunk_manager.gd` contains:

- 9,116 lines;
- 356 `func` declarations;
- 109 exported properties;
- direct `RenderingDevice` orchestration;
- GPU and CPU worker queues;
- water, roads, biome/world-map handling;
- terrain modification storage;
- collision policy;
- visual batching;
- spawn-zone loading;
- telemetry and debug state;
- save/load readiness hooks.

## Failure patterns to avoid

1. One node owns too many subsystems.

   Terrain generation, streaming, rendering, collision, water, roads, material
   setup, save/load, edits, and telemetry all converge into one manager. This
   makes correctness and performance changes hard to isolate.

2. Hot terrain policy lives in GDScript.

   GDScript directly owns task queues, dispatch timing, chunk lifecycle,
   RenderingDevice resources, and large dictionaries. `world-transvoxel-terrain`
   must keep hot generation, streaming, storage, and recovery paths in native
   code, low-level addon APIs, binary formats, shaders when justified, or Python
   offline tooling.

3. Optional systems are fused into core terrain.

   Water, roads, world-map LOD, building visuals, spawn zones, and render
   prewarm are coupled to the terrain manager. In `world-transvoxel-terrain`,
   water/lava, roads, vegetation, building blocks, structural stability, and
   game systems remain separate optional contracts.

4. Too many exported knobs replace stable profiles.

   The old manager exposes many direct tunables. The terrain addon must use a
   small set of typed profiles: terrain profile, generation profile, streaming
   policy, material profile, collision policy, storage profile, and budget
   profile.

5. Additive density creates unpredictable edit behavior.

   The old technical documents identify additive edits (`density +=
   modification`) as creating density memory. The new terrain contract must use
   explicit edit operation semantics and authoritative sample ownership, not
   unbounded additive cancellation.

6. Physical overlap is used as a seam fix.

   The old standard uses `CHUNK_STRIDE = CHUNK_SIZE - 1` to physically overlap
   chunks, and its architecture notes classify overlap-related water
   z-fighting. `world-transvoxel-terrain` must rely on `world-transvoxel`
   topology, seam ownership, and explicit boundary policy rather than hiding
   cracks with overlapping chunks.

7. Material policy is hardcoded near runtime ownership.

   Texture loading and shader parameter synchronization are mixed into the chunk
   manager. `world-transvoxel-terrain` needs a material/texture profile boundary
   and debug-view policy.

8. Hidden background work is difficult to reason about.

   The old project has many queues, adaptive throttles, idle polish paths, and
   background loaders. The new terrain addon must make work triggers explicit:
   viewer demand, edit submission, profile change, preload request, save/load,
   or a separately enabled optional system.

9. Documentation describes a desired migration, but the runtime structure still
   remains monolithic.

   A contract alone is not enough. `world-transvoxel-terrain` must enforce the
   package layout with validators before implementation grows.

## A1 consequences

`world-transvoxel-terrain` must:

- keep source ownership split by subsystem from the start;
- reject large mixed-purpose source files before they become normal;
- keep GDScript out of terrain hot paths;
- model terrain features as typed profiles and operations;
- keep optional systems behind explicit contracts;
- validate its source layout in Python;
- avoid copying old marching-cubes source or shader implementation code.
