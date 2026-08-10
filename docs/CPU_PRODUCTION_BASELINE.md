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

- Frame samples: 2700 across nine scenarios; p50 16.308 ms, p99 70.161 ms, worst 98.044 ms.
- Process: 314.219 CPU-seconds over 191.405 s, 1.642 average occupied cores, 54.7% of the three-CPU affinity capacity.
- Peak RSS: 1118.3 MiB; peak Godot video memory: 137.7 MiB.
- Queue peaks: scheduler 236, storage 505, render 0, collision 3.
- Coarse world became ready in 3.474 s with all 262,144 LOD0-equivalent cells covered.
- Prefetched arrival: storage jobs 0, mesh jobs 0, first collision 23.588 ms.
- Dig: visual 90.189 ms, collision 109.456 ms.
- Construct: visual 75.786 ms, collision 96.567 ms; existing solid samples repainted: 0.
- Temporal continuity: 2270 monitored frames, 78 topology samples, 0 visible ancestor overlaps, 0 topology failures.

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
