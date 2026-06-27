# Tests

Addon-local tests start in A2.

They must prove local package behavior, dependency detection, API contracts, and
smoke scenes. Final gameplay validation belongs in the later separate game
repository, not in this addon repo and not in `world-transvoxel-sandbox`.

A2 smoke entry point:

```console
python tools/a2_addon_smoke.py
```
