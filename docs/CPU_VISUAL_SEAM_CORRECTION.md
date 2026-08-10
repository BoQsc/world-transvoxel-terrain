# CPU Visual Seam Correction

Status: **PASS** on 2026-08-10.

## Qualified revisions

- Terrain: `df936025086ee4e1141d4f4a3d4c9927db5db346`.
- Authority: `269871299974c250379028d88b9a9c3086507f52`.
- Godot: 4.7.1, Forward+, Windows x86-64.
- Execution: three-logical-CPU affinity.

## Defects found

The reported black sawtooth at the LOD3 positive-X boundary was an open geometry
gap. A mesh generated for one transition mask had been reused with another mask
after source-mask finalization had already discarded triangles. The original
probe found 58 open boundary edges after streaming settled.

Exact-mask remeshing removed that defect, but repeated large-world startup then
exposed a second problem. Two LOD3 chunks stopped permanently at 517 of 519
ready records with empty queues. A normal render publication had overtaken
same-key remove/re-expect control state under priority fairness and was rejected
as stale. The authority now permits unrelated-key fairness while preserving
per-key control-before-render ordering.

Neither defect is a flaw in the Transvoxel transition-cell tables. Both were
runtime integration and publication errors downstream of the table authority.

## Final evidence

The strict visual investigation captured 33 shadow-on, shadow-off, and unshaded
frames during streaming and after settlement. It reported:

- classification `reported_artifact_not_reproduced`;
- 0 geometry-gap samples, 0 directional-shadow samples, and 0 unexplained-dark
  samples;
- 0 visible ancestor overlaps in every sampled frame;
- 3,042 exact seam edges, all 3,042 matched;
- 0 boundary, nonmanifold, orientation-inconsistent, or zero-area results;
- 2,640 triangles across 13 mesh instances in the exact seam region.

Representative retained captures:

- `artifacts/cpu_visual_defect_investigation/captures/reported_area_settled_shadow_on.png`
  (`caf5bcf14e814888d5e0bef995ef869ab54f9e5a87e43552d32daafd2c3370a8`);
- `artifacts/cpu_visual_defect_investigation/captures/cross_lod_return_settled_shadow_on.png`
  (`3737fe023dcd7b189aaa6ac51a66a6ee11f87ddad33144629756360402eeb37b`);
- `artifacts/cpu_visual_defect_investigation/captures/cross_lod_return_settled_unshaded.png`
  (`59c5f72d4c545ecb7b8c77f87561ee0feab4cc87cb5a71f57e5e51a66cafc39b`);
- `artifacts/cpu_visual_defect_investigation/captures/cross_lod_return_top_down_settled_unshaded.png`
  (`60177b19de39b19f16e0a94764de0abffbb5f4fb0047ac2bd0a92195607dccd3`).

Manual review found no black slit or diagnostic background through terrain.
Stepped color contours remain visible at coarse resolution; those are material
and voxel-resolution boundaries, not open geometry.

## Reproduce

```console
python ../world-transvoxel-cell-lab/labs/terrain_lab/tools/run_with_cpu_limit.py --logical-cpus 3 -- python tools/cpu_visual_defect_investigation.py
```

The runner fails for any classified artifact, failed exact seam probe, nonzero
topology defect, failed capture, or visible ancestor overlap. This fixture is a
targeted regression, not proof for every field, camera, renderer, or hardware.
