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

Needs validation:

- line, centerline, 3-point arc, ellipse, polygon, spline, text, slot.

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

Status: started. Needs a dedicated constrained-sketch sample.

### `sketch_dimensions.py`

Purpose: native sketch dimensions.

Current helpers:

- `add_dimension`
- `add_smart_dimension`

Status: started. Needs validation with line length, circle diameter, radius,
and angle dimensions.

### `edge_features.py`

Purpose: reusable native fillet and chamfer operations.

Current helpers:

- `select_edge_by_ray`
- `fillet_selected_edges`
- `chamfer_selected_edges`
- `fillet_edges_by_rays`
- `chamfer_edges_by_rays`
- `fillet_all_current_body_edges`

Verified so far:

- `fillet_all_current_body_edges` through `debug_foundation_features.py`.

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

Needs validation:

- `cut_blind_hole` as an isolated sample.
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

Needs validation:

- datum axis from two planes.
- datum axis from cylindrical face.
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

Status: started. Needs a dedicated mirror-feature sample.

### `thin_wall_features.py`

Purpose: shell and thin-wall operations.

Current helpers:

- `shell_selected_faces`

Status: started. Needs a dedicated shell sample.

### `structural_features.py`

Purpose: structure/manufacturing features.

Current helpers:

- `rib_from_selected_sketch`
- `draft_selected_faces`

Status:

- rib wrapper started, needs sample.
- draft placeholder needs COM signature validation.

### `curves.py`

Purpose: native curves used by sweeps, threads, springs, cable paths.

Current helpers:

- `insert_helix_from_selected_circle`
- `projected_curve`
- `composite_curve`

Status:

- helix wrapper started, needs sample.
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

## Documentation Gaps Still Open

The following docs are still needed as the wrappers mature:

- `docs/sketch_runtime.md`
- `docs/edge_features_runtime.md`
- `docs/hole_runtime.md`
- `docs/reference_geometry_runtime.md`
- `docs/interface_runtime.md`
- `docs/structural_features_runtime.md`

For now, this foundation document is the index for those modules.
