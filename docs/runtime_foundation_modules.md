# Foundation Runtime Modules

Date: 2026-06-25

This document describes the first foundation-layer runtime modules added after
the view export work. It distinguishes verified helpers from started wrappers
that still require dedicated SolidWorks sample validation.

## Validation Levels

| Level | Meaning |
|---|---|
| Verified | A minimum SolidWorks sample has run successfully on this workstation. |
| Partly verified | Some functions in the module have run successfully; others still need samples. |
| Started | Module and wrapper API exist, but a SolidWorks sample still needs to verify it. |
| Placeholder | Location reserved; function intentionally raises `NotImplementedError`. |

## Modules

### `sketch_entities.py`

Purpose: native sketch entity creation.

Current helpers:

- `draw_line`
- `draw_centerline`
- `draw_corner_rectangle`
- `draw_center_rectangle`
- `draw_circle`
- `draw_circle_by_diameter`
- `draw_3point_arc`
- `draw_ellipse`
- `draw_polygon`
- `draw_spline`
- `draw_text`
- `draw_centerpoint_straight_slot`

Verified so far:

- `draw_center_rectangle` through `debug_foundation_features.py`.
- `draw_line`
- `draw_centerline`
- `draw_3point_arc`
- `draw_ellipse`
- `draw_polygon`

Current SW2025 Python COM limitations found:

- `draw_spline`: `SketchManager.CreateSpline` is exposed as a non-callable property
  on this workstation.
- `draw_text`: `SketchManager.CreateText` is exposed as a non-callable property
  on this workstation.
- `draw_centerpoint_straight_slot`: `CreateSketchSlot` exists, but the exact
  optional-parameter signature is not stable yet.

### `sketch_relations.py`

Purpose: native sketch geometric constraints.

Current helpers:

- `add_relation`
- `add_coincident`
- `add_horizontal`
- `add_vertical`
- `add_tangent`
- `add_concentric`
- `add_equal`
- `add_parallel`
- `add_perpendicular`

Verified so far:

- `add_horizontal` with an existing sketch line.

Needs validation:

- coincident, vertical, tangent, concentric, equal, parallel, perpendicular.

### `sketch_dimensions.py`

Purpose: native sketch dimensions.

Current helpers:

- `add_dimension`
- `add_smart_dimension`

Verified so far:

- `add_smart_dimension` can create a native sketch dimension.

Current SW2025 Python COM limitation found:

- Setting the created dimension value through `SystemValue` was not exposed
  consistently by this dynamic binding. Current safe path is create-and-name
  first, then add a dedicated dimension-value setter after signature validation.

### `edge_features.py`

Purpose: reusable native fillet and chamfer operations.

Current helpers:

- `select_edge_by_ray`
- `fillet_selected_edges`
- `chamfer_selected_edges`
- `fillet_edges_by_rays`
- `chamfer_edges_by_rays`
- `fillet_all_current_body_edges`
- `chamfer_all_current_body_edges`

Verified so far:

- `fillet_all_current_body_edges` through `debug_foundation_features.py`.
- `chamfer_all_current_body_edges` through `debug_unverified_features.py`.

Needs validation:

- `fillet_edges_by_rays`
- `chamfer_edges_by_rays`
- `chamfer_selected_edges` as a reusable workflow.

### `holes.py`

Purpose: hole-related modeling helpers.

Current helpers:

- `cut_simple_through_hole`
- `cut_blind_hole`
- `cut_counterbore_hole`
- `create_hole_wizard_placeholder`

Verified so far:

- `cut_simple_through_hole`
- `cut_counterbore_hole`
- `cut_blind_hole`

Needs validation:

- countersink helper.
- tapped/threaded hole.
- SolidWorks Hole Wizard wrapper.

### `references.py`

Purpose: stable reference geometry.

Current helpers:

- `create_offset_plane`
- `create_axis_from_two_planes`
- `create_axis_from_cylindrical_face_by_ray`
- `create_coordinate_system_from_selection`

Verified so far:

- `create_offset_plane`
- `create_axis_from_two_planes`
- `create_axis_from_cylindrical_face_by_ray`

Needs validation:

- coordinate system creation and naming.

### `interfaces.py`

Purpose: CAD assembly interface semantics outside fragile topology IDs.

Current helpers:

- `ReferenceGeometry`
- `MateRelation`
- `MateInterface`
- `pin_interface`
- `flange_interface`
- `write_interfaces_json`

Verified so far:

- Python data model and JSON export path.

Needs validation:

- integration with actual named reference geometry in generated parts.

### `transform_features.py`

Purpose: transform-like native features.

Current helpers:

- `mirror_feature`

Status: started, not verified.

Validation result:

- `debug_unverified_features.py --only mirror` created the seed boss, but native
  mirror returned no feature through the tried `InsertMirrorFeature` selection
  path. Keep this wrapper out of production generation until a macro-recorded
  signature is added.

### `thin_wall_features.py`

Purpose: shell and thin-wall operations.

Current helpers:

- `shell_selected_faces`

Status: started, not verified.

Validation result:

- `debug_unverified_features.py --only shell` selected an open face, but
  `InsertFeatureShell` rejected the current Python COM parameters with
  `非选择性的参数`. Keep this wrapper out of production generation until the
  exact signature is validated.

### `structural_features.py`

Purpose: structure/manufacturing features.

Current helpers:

- `rib_from_selected_sketch`
- `draft_selected_faces`

Status:

- rib wrapper started, not verified. `InsertRib` and `InsertRib2` are exposed,
  but the tested argument combinations either returned `None` or raised
  `非选择性的参数`.
- draft placeholder needs COM signature validation.

### `curves.py`

Purpose: native curves used by sweeps, threads, springs, cable paths.

Current helpers:

- `insert_helix_from_selected_circle`
- `projected_curve`
- `composite_curve`

Status:

- helix wrapper started, not verified. `InsertHelix` is exposed, but the tested
  argument combinations failed in the current binding.
- projected/composite curve placeholders remain.

### `boundary_features.py`

Purpose: boundary boss/base and boundary cut.

Current helpers:

- `boundary_boss`
- `boundary_cut`

Status: placeholder.

## Regression Script

Run:

```powershell
cd D:\text2solidworks
python workspace_scripts\debug_foundation_features.py
```

Extended validation:

```powershell
cd D:\text2solidworks
python workspace_scripts\debug_unverified_features.py
python workspace_scripts\debug_unverified_features.py --only mirror shell rib helix
```

Verified output:

```text
D:\text2solidworks_workspace\debug\foundation_features
```

The script currently verifies:

- center rectangle sketch entity;
- boss extrusion;
- native all-body-edge fillet;
- simple through hole;
- counterbore hole composition;
- offset plane;
- 9-view PNG export.

`debug_unverified_features.py` currently verifies:

- additional sketch primitives: line, centerline, 3-point arc, ellipse, polygon;
- sketch horizontal relation;
- smart-dimension creation without value override;
- all-body-edge chamfer;
- blind hole;
- datum axes from two planes and cylindrical face.

It also records known failures for mirror, shell, rib, and helix instead of
silently accepting non-created features.

## Documentation Gaps Still Open

The following docs are still needed as the wrappers mature:

- `docs/sketch_runtime.md`
- `docs/edge_features_runtime.md`
- `docs/hole_runtime.md`
- `docs/reference_geometry_runtime.md`
- `docs/interface_runtime.md`
- `docs/structural_features_runtime.md`

For now, this foundation document is the index for those modules.
