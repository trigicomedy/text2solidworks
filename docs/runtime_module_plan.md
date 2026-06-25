# SolidWorks Runtime Module Plan

Date: 2026-06-25

This document records the file-level split for the next runtime expansion.

## Implemented Or Started

| Module | Purpose | Current status |
|---|---|---|
| `features.py` | Basic extrude/cut | Verified existing |
| `advanced_features.py` | Revolve/sweep/loft boss and cut | Verified existing |
| `edge_features.py` | Native fillet/chamfer helpers | Partly verified: all-current-body-edge fillet verified |
| `holes.py` | Simple, blind, counterbore holes | Partly verified: simple through and counterbore verified; Hole Wizard placeholder remains |
| `references.py` | Planes, axes, coordinate systems | Partly verified: offset plane verified; axis/CSYS need more validation |
| `interfaces.py` | Mate interface data structures | Started; JSON export supported |
| `sketch_entities.py` | Lines, centerlines, arcs, polygons, ellipses, splines, text, slots | Partly verified: center rectangle verified through foundation sample |
| `sketch_relations.py` | Sketch geometric relations | Started |
| `sketch_dimensions.py` | Sketch dimensions | Started |
| `transform_features.py` | Mirror and transform-like features | Started; mirror needs validation |
| `thin_wall_features.py` | Shell/thin-wall features | Started; needs validation |
| `structural_features.py` | Rib/draft/manufacturing structure features | Started; rib/draft need validation |
| `boundary_features.py` | Boundary boss/cut | Placeholder |
| `curves.py` | Helix/projected/composite curves | Started; helix needs validation |
| `views.py` | Model orientation image export | Verified |

## Validation Policy

Functions fall into three levels:

1. `verified`: minimum SolidWorks sample has been run and saved.
2. `started`: wrapper exists but needs a dedicated minimum sample.
3. `placeholder`: module/API location is reserved and raises `NotImplementedError`.

Task scripts should prefer verified functions. Started functions may be used only
when the calling task explicitly includes validation and fallback diagnostics.

## Next Validation Order

1. `edge_features.py`: chamfer from rays and selected-edge fillet/chamfer.
2. `holes.py`: blind hole, countersink, Hole Wizard/tapped holes.
3. `sketch_entities.py`: line, centerline, 3-point arc, polygon, ellipse, spline, text, slots.
4. `sketch_relations.py` and `sketch_dimensions.py`.
5. `references.py`: axis from planes, axis from cylindrical face, coordinate system.
6. `transform_features.py`: mirror feature.
7. `thin_wall_features.py`: shell.
8. `structural_features.py`: rib and draft.
9. `curves.py`: helix.
10. `boundary_features.py`: boundary boss/cut.

## Current Regression Scripts

Run these after changes that touch core modeling helpers:

```powershell
cd D:\text2solidworks
python workspace_scripts\debug_advanced_features.py
python workspace_scripts\debug_views.py
python workspace_scripts\debug_foundation_features.py
```

`debug_foundation_features.py` verifies the first foundation stack:

- `sketch_entities.draw_center_rectangle`
- `features.extrude_boss`
- `edge_features.fillet_all_current_body_edges`
- `holes.cut_simple_through_hole`
- `holes.cut_counterbore_hole`
- `references.create_offset_plane`
- `views.export_named_view_images`
