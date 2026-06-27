# License Scope

Project-owned code and documentation in `world-transvoxel-terrain` are 0BSD
unless a file explicitly states otherwise.

This repository currently does not vendor:

- Eric Lengyel's MIT Transvoxel implementation or lookup data;
- the `world-transvoxel` addon;
- `world-transvoxel-sandbox`;
- Voxel Tools or other terrain implementation code.

`world-transvoxel-terrain` depends on `world-transvoxel` as a separate addon.
When a Godot project distributes both addons together, it must retain
`world-transvoxel`'s own license notices, including the MIT Transvoxel notices
inside that addon.

Rules:

- do not copy MIT Transvoxel tables into this repository;
- do not convert MIT tables into generated 0BSD arrays;
- do not copy sandbox implementation files as terrain architecture;
- do not copy Voxel Tools implementation code;
- keep downloaded papers and repository checkouts under
  `references/downloaded/`, which is ignored by Git;
- retain only non-reconstructive aggregate comparison reports if future backend
  comparisons are performed.
