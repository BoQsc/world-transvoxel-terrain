# CPU Production Terrain Baseline

Status: **PASS**

This is the reproducible CPU reference baseline for the bounded production terrain standard. It is not a claim that every frame already meets 60 FPS, and it is not a 16 W power qualification.

## Fixed configuration

- Godot 4.7 Forward+ on Windows x86-64.
- World: 2,048 x 256 x 2,048 cells, 299,520 catalog pages.
- LOD0 through LOD3 with 512 globally resident LOD3 coarse roots.
- Two native meshing workers, two procedural/storage workers, and at most three logical CPUs.
- Visual radius 2 chunks; targeted collision radius 1 chunk.

## Measured baseline

- Frame samples: 2700 across nine scenarios; p50 16.263 ms, p99 42.984 ms, worst 134.765 ms.
- Process: 181.812 CPU-seconds over 127.439 s, 1.427 average occupied cores, 47.6% of the three-CPU affinity capacity.
- Peak RSS: 1081.1 MiB; peak Godot video memory: 137.7 MiB.
- Queue peaks: scheduler 169, storage 88, render 0, collision 8.
- Coarse world became ready in 8.128 s with all 262,144 LOD0-equivalent cells covered.
- Prefetched arrival: storage jobs 0, mesh jobs 0, first collision 29.577 ms.
- Dig: visual 75.310 ms, collision 75.311 ms.
- Construct: visual 72.885 ms, collision 89.466 ms; existing solid samples repainted: 0.
- Temporal continuity: 616 monitored frames, 22 topology samples, 0 visible ancestor overlaps, 0 topology failures.

## Interpretation

The authority, terrain wrapper, global coarse coverage, local refinement, temporal publication, warm reuse, prefetch handoff, targeted collision, digging, construction, persistence, and bounded resource envelopes pass together. The measured p99 is a comparison baseline for future CPU or GPU work, not proof of a universal frame rate on other hardware.

CPU-package watts and whole-system watts remain unqualified because this host has no trusted package-energy provider. GPU-board watts are a separate metric and must not be presented as CPU terrain power.

## Reproduce

```console
python ../world-transvoxel-cell-lab/labs/terrain_lab/tools/run_with_cpu_limit.py --logical-cpus 3 -- python tools/tqp57_large_terrain_acceptance.py
python ../world-transvoxel-cell-lab/labs/terrain_lab/tools/run_with_cpu_limit.py --logical-cpus 3 -- python tools/cpu_temporal_continuity.py
python ../world-transvoxel-cell-lab/labs/terrain_lab/tools/run_with_cpu_limit.py --logical-cpus 3 -- python tools/cpu_prefetch_readiness.py
python ../world-transvoxel-cell-lab/labs/terrain_lab/tools/run_with_cpu_limit.py --logical-cpus 3 -- python tools/cpu_production_closure.py
```
