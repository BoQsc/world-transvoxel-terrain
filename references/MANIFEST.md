# Reference Manifest

Status: A1 pinned/downloaded references.

Downloaded reference files live under `references/downloaded/`, which is ignored
by Git. The repository stores this manifest, not third-party papers, generated
docs, or external source checkouts.

## Downloaded primary references

| ID | Source URL | Ignored local path | SHA-256 |
| --- | --- | --- | --- |
| `transvoxel_home` | https://transvoxel.org/ | `references/downloaded/transvoxel/transvoxel.org.html` | `dea602ce1bae5d73221e6d883c8a8828137e8730d0c624092bd83c52ce95bbf8` |
| `lengyel_dissertation` | https://transvoxel.org/Lengyel-VoxelTerrain.pdf | `references/downloaded/transvoxel/Lengyel-VoxelTerrain.pdf` | `c1c86dc1c441fa86dbe6b4b38a521ffb26a5eec3c4eede0f5782508a6ad41160` |
| `godot_plugins` | https://docs.godotengine.org/en/stable/tutorials/plugins/editor/making_plugins.html | `references/downloaded/godot/making_plugins.html` | `c24d3c12bb3bda86bdc7f61f9eb7f2cbd16f5bb12aa4012b10c84152565f30e6` |
| `godot_gdextension_cpp` | https://docs.godotengine.org/en/stable/tutorials/scripting/cpp/gdextension_cpp_example.html | `references/downloaded/godot/gdextension_cpp_example.html` | `a6f78360da9f4f99772971c87f56302e5cb78ba4c637ef51ba391043c25ab410` |
| `godot_compute` | https://docs.godotengine.org/en/stable/tutorials/shaders/compute_shaders.html | `references/downloaded/godot/compute_shaders.html` | `b736b97a734057a7b54b87cf36d971e34c0c3a1a465d7b530300820ce8fd4ead` |
| `godot_renderingdevice` | https://docs.godotengine.org/en/stable/classes/class_renderingdevice.html | `references/downloaded/godot/class_renderingdevice.html` | `5819af09a8cfa79e11e65101d131e7b617e2ef4dcaa93df0c901394143815033` |

The Godot compute and RenderingDevice pages are context only. Compute remains
deferred by contract until a later measured bottleneck reopens it.

## Local references

| ID | Local path | Use |
| --- | --- | --- |
| `world_transvoxel_charter` | `C:\Users\Windows10_new\Documents\github_repositories\world-transvoxel\IMPLEMENTATION_CHARTER.md` | backend/license/API boundary |
| `sandbox_terrain_contract` | `C:\Users\Windows10_new\Documents\github_repositories\world-transvoxel-sandbox\docs\WORLD_TRANSVOXEL_TERRAIN_ARCHITECTURE_CONTRACT.md` | post-S5 handoff contract |
| `old_marching_cubes_project` | `C:\Users\Windows10_new\Documents\gpu-marching-cubes\world_marching_cubes` | maintainability audit input |

## Rules

- Keep downloaded papers, generated documentation, and external checkouts under
  `references/downloaded/`.
- Do not commit third-party implementation code.
- Do not copy MIT Transvoxel lookup data into this repository.
- Do not use Godot docs snapshots as vendored project docs; they are local
  references only.
