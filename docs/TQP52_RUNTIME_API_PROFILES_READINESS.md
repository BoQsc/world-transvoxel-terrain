# TQP-52 Runtime API, Profiles, And Readiness

Status: qualified by `WT_TERRAIN_TQP52_QUALIFICATION_PASS` on Godot 4.6.3 and
4.7.

`WtTerrainWorld` API version 2 is the production orchestration boundary above
the pinned `world-transvoxel` native authority. It does not implement terrain
field evaluation or meshing in GDScript.

## Runtime contract

- World start and stop publish a monotonic `api_generation`.
- Wrapper-owned asynchronous requests are bounded and tagged with that
  generation. Stopping or replacing a world cancels outstanding wrapper
  requests, and late native completions are not republished as current data.
- Viewer and collision-viewer revisions are positive and monotonic per ID.
- Render, collision, edit, and query readiness are separate states. Chunk
  readiness reports native generation, staged generation, and exact visual and
  collision readiness.
- Queue rejection, capacity, pending work, and native rejection counters remain
  visible in readiness and runtime metrics.

## Profiles

`WtTerrainRuntimeProfile` provides low-power, balanced, quality, and
authoritative-reference presets. Each profile declares resolution/distance,
queue, memory, collision, application-budget, and power intent. Power intent is
not a measured power claim. Correctness rules, native authority, stale-result
rejection, and seam behavior do not change between profiles.

The profile is applied before native world startup. Existing nonzero
`WtTerrainWorld` runtime override properties remain compatible and take
precedence over the profile. Runtime profile mutation after startup is outside
the version-1 contract; stop, change the profile, and restart instead.

## Evidence

`tools/validate_tqp52_runtime_contract.py` validates the package contract.
`tools/tqp52_runtime_contract_smoke.py` runs the real native fixture on the
supported Godot versions and retains the report under
`artifacts/tqp52_runtime_contract/`.
