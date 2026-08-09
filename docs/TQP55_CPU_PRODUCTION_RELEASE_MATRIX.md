# TQP-55 CPU Production Release Qualification Matrix

Status: qualified when `WT_TERRAIN_TQP55_QUALIFICATION_PASS` is reproduced.

The first CPU release matrix is intentionally narrow: Windows 10 x86-64,
Godot 4.7, Forward+, the pinned `world-transvoxel` authority, and the reference
hardware class. Low-power, balanced, quality, and reference profiles are
declared configuration envelopes, not claims that every target is achieved on
every machine.

The qualification combines current production-addon API and editor smokes with
retained Terrain Lab evidence for visual review, far-arrival response, targeted
collision residency, large-world rendering, power measurement, long-run drift,
and exact downstream migration. The production package contains only
`addons/world_transvoxel_terrain`; the required native authority remains a
separately installed, exactly pinned dependency. No fallback is provided.

The release candidate is deterministic: tracked addon files are sorted,
UTF-8 text is normalized to LF, ZIP timestamps are fixed, and both canonical
package and ZIP SHA-256 digests are recorded. TQP-55 does not qualify GPU
terrain execution, non-Windows platforms, arbitrary hardware, or complete
system power. The retained TQP-48 result remains an honest measured target
miss, not a concealed pass.
