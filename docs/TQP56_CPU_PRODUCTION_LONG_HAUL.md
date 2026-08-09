# TQP-56 CPU Production Long-Haul Certification

Status: qualified when `WT_TERRAIN_TQP56_QUALIFICATION_PASS` is reproduced.

TQP-56 combines two evidence layers. A bounded 60-second Godot 4.7 workload
exercises the real `WtTerrainWorld` production wrapper through traversal,
flight-like vertical movement, targeted render/collision residency, carve and
construction, authoritative queries, journal restart/replay, presentation
origin shifts, rejected invalid input, queue accounting, memory accounting, and
clean shutdown. The retained TQP-49 evidence supplies the deeper 1800-second
native/rendered frame, queue, memory, thermal, power, persistence, recovery, and
shutdown drift run.

This split keeps ordinary development qualification near one minute while
preserving the long-run baseline. It does not turn one reference machine into a
cross-hardware claim, and it does not qualify multi-day operation or GPU terrain
execution.
