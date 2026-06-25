# Advanced Feature Runtime Notes

This note records SolidWorks 2025 + pywin32 calls verified on the current workstation.

## Runtime Module

Use:

```python
from cad_runtime.solidworks.advanced_features import (
    revolve_boss,
    revolve_cut,
    sweep_boss,
    sweep_cut,
    loft_boss,
    loft_cut,
)
```

All functions create native SolidWorks features. They do not approximate circles, arcs, sweeps, lofts, or cuts with mesh/polyline substitutes.

## Verified Functions

| Function | Native API verified | Selection requirement |
|---|---|---|
| `revolve_boss` | `FeatureRevolve2` | selected closed profile sketch with construction centerline or selected axis |
| `revolve_cut` | `FeatureRevolve2` | selected closed cut profile sketch with centerline/axis; `Merge=True` is required |
| `sweep_boss` | `InsertProtrusionSwept` 14-argument legacy call | profile sketch + path sketch |
| `sweep_cut` | `InsertCutSwept` 13-argument legacy call | profile sketch + path sketch intersecting a solid body |
| `loft_boss` | `InsertProtrusionBlend` 17-argument legacy call | ordered section sketches |
| `loft_cut` | `InsertCutBlend` 12-argument legacy call | ordered section sketches intersecting a solid body |

## Selection Rules

- Sketches must be exited before feature creation.
- The wrapper selects named sketches with `SelectByID2(..., "SKETCH", ..., mark, null_dispatch(), 0)`.
- Sweep wrappers try profile mark `1` and path mark `4` first, then mark `0`.
- Loft wrappers try section mark `1` first, then mark `0`.
- If SolidWorks returns `None`, treat it as failure even when no exception is raised.

## Compatibility Findings

- The newer methods `InsertProtrusionSwept4`, `InsertCutSwept4`, and `InsertProtrusionBlend2` are exposed by COM but were less reliable in this environment for minimal examples.
- The legacy calls were more stable:
  - `InsertProtrusionSwept` with 14 Boolean arguments.
  - `InsertCutSwept` with 13 Boolean arguments.
  - `InsertProtrusionBlend` with 17 Boolean arguments.
  - `InsertCutBlend` with 12 Boolean arguments.
- `revolve_cut` uses the same `FeatureRevolve2` signature as `revolve_boss`, but the merge argument must be `True`; otherwise SolidWorks may return `None`.

## Validation Script

Run:

```powershell
cd D:\text2solidworks
python workspace_scripts\debug_advanced_features.py
```

Expected output files:

- `D:\text2solidworks_workspace\debug\advanced_features\exports\revolve_boss_test.SLDPRT`
- `D:\text2solidworks_workspace\debug\advanced_features\exports\revolve_cut_test.SLDPRT`
- `D:\text2solidworks_workspace\debug\advanced_features\exports\sweep_boss_test.SLDPRT`
- `D:\text2solidworks_workspace\debug\advanced_features\exports\sweep_cut_test.SLDPRT`
- `D:\text2solidworks_workspace\debug\advanced_features\exports\loft_boss_test.SLDPRT`
- `D:\text2solidworks_workspace\debug\advanced_features\exports\loft_cut_test.SLDPRT`

The current workstation verification completed successfully for all six features.
