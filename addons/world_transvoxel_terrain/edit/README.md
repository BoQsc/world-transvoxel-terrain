# Edit Ownership

Edit operation descriptions, validation, affected-region estimates, and
edit-settle tracking belong here.

Edits are commands. Do not implement unbounded additive density cancellation as
the public edit model.

Current A4 phase 1 resources:

- `WtTerrainEditOperation` defines carve, construct, fill, paint, and
  restore-to-base command semantics;
- `WtTerrainEditBatch` groups validated edit commands before bridge submission.
