# CPU Release Bundle 1.1.0-rc1

This release candidate is the self-contained Windows x86-64 package for the
bounded CPU Terrain Standard 1.0 reference matrix. It contains both
`addons/world_transvoxel` and `addons/world_transvoxel_terrain`, including the
Godot 4.7 debug and release native libraries. No fallback mesher or density
field is included.

## Install

Extract the archive at the root of a Godot 4.7 project. The resulting project
must contain both addon directories. Enable **World Transvoxel Terrain** in
Project Settings > Plugins. The native authority GDExtension is discovered from
its bundled `.gdextension` file.

The release gate performs this operation in a newly created project, imports
the project with Godot 4.7, verifies the authority classes and backend identity,
loads the terrain API, and confirms that no sibling repository is needed.

## Build

Build both authority binaries under the three-logical-CPU limit, then build and
validate the deterministic archive:

```console
python ../world-transvoxel-cell-lab/labs/terrain_lab/tools/run_with_cpu_limit.py --logical-cpus 3 -- scons -j3 target=template_debug
python ../world-transvoxel-cell-lab/labs/terrain_lab/tools/run_with_cpu_limit.py --logical-cpus 3 -- scons -j3 target=template_release
python ../world-transvoxel-cell-lab/labs/terrain_lab/tools/run_with_cpu_limit.py --logical-cpus 3 -- python tools/build_cpu_release_bundle.py
```

The generated archive, manifest, smoke logs, and report are under
`artifacts/cpu_release_bundle/`.

## Boundary

This is release-candidate evidence for Godot 4.7, Windows, x86-64, and Forward+.
It does not claim public Asset Library acceptance, other platforms, GPU terrain,
universal frame rate, or CPU/whole-system watts.
