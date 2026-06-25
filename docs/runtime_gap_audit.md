# Runtime Gap Audit

Date: 2026-06-25

This audit compares the current `cad_runtime.solidworks` wrappers with common SolidWorks Feature and Sketch toolbar operations. It is based on the current runtime files and small SolidWorks COM probes on this workstation.

## Current Verified Coverage

### Feature Operations

| Area | Runtime status | Notes |
|---|---|---|
| Extruded Boss/Base | Verified | `features.extrude_boss` |
| Extruded Cut | Verified | `features.extrude_cut_through_all` |
| Revolved Boss/Base | Verified | `advanced_features.revolve_boss` |
| Revolved Cut | Verified | `advanced_features.revolve_cut`; `Merge=True` is required |
| Swept Boss/Base | Verified | `advanced_features.sweep_boss` |
| Swept Cut | Verified | `advanced_features.sweep_cut` |
| Lofted Boss/Base | Verified | `advanced_features.loft_boss` |
| Lofted Cut | Verified | `advanced_features.loft_cut` |
| Circular Feature Pattern | Verified | `patterns.circular_feature_pattern` |
| Linear Feature Pattern | Verified | `patterns.linear_feature_pattern` |
| Native Fillet | Partly verified | `edge_features.fillet_all_current_body_edges` verified |
| Native Chamfer | Started | `edge_features.chamfer_*` wrappers exist; reusable sample still needed |
| Offset Plane | Verified | `references.create_offset_plane` |

### Sketch Operations

| Area | Runtime status | Notes |
|---|---|---|
| Begin/end sketch | Verified | Handles Chinese/English sketch names through `end_sketch` |
| Circle | Verified | `sketches.draw_circle` |
| Center rectangle | Verified | `sketches.draw_center_rectangle` |
| Center arc | Verified | `sketches.draw_center_arc` |
| Lines | Started | `sketch_entities.draw_line` exists; sample still needed |
| 3-point arcs | Started | `sketch_entities.draw_3point_arc` exists; sample still needed |
| Center rectangle | Verified | `sketch_entities.draw_center_rectangle` verified through foundation sample |
| Polygon / ellipse / spline / text / slot | Started | Helpers exist; samples still needed |

## Important Missing Feature Wrappers

### High Priority

1. `edge_features.py`
   - Native constant-radius fillet.
   - Native chamfer.
   - Edge selection by planned geometry signatures.
   - Edge treatment registry integration.
   - Required because many generated parts need reliable R/C edge operations.

2. `holes.py`
   - Hole Wizard / countersink / tapped hole.
   - Simple through holes and counterbore composition now have reusable helpers.
   - Needed for M-series bolts, clearance holes, threaded holes, ISO/GB hole descriptions.

3. `references.py` expansion
   - Datum axis from cylinder face or two planes.
   - Datum plane from face/offset/angle.
   - Coordinate system creation.
   - Named mate interfaces.
   - Needed for stable assembly and mate planning.

4. `drawings.py` family
   - `views.py` now exports named model views as PNG.
   - Create drawing document and insert standard views.
   - Save drawing as `SLDDRW`, `PDF`, or image.
   - Needed for automated visual inspection and dataset generation.

### Medium Priority

5. Mirror feature
   - Mirror bodies/features about a plane.
   - Common for symmetric grippers, brackets, arms.

6. Shell
   - Native shell feature for housings and hollow parts.
   - Important for cast/CNC enclosures and lightweight parts.

7. Rib
   - Native rib feature.
   - Useful for brackets, covers, mounting plates, housings.

8. Draft
   - Native draft feature.
   - Useful for molded or cast parts.

9. Boundary Boss/Base and Boundary Cut
   - Similar design use case to loft, but better for some controlled surfaces.
   - Appears in the Feature toolbar and should be validated separately.

10. Mirror / Curve / Reference Geometry helpers
   - Curves: helix/spiral, projected curve, composite curve.
   - Needed for springs, threads, pipes, cable paths, sweep paths.

### Lower Priority Or Specialized

11. Wrap
   - Useful for embossing/engraving text or curves on cylinders.

12. Intersect
   - Useful for complex volume operations and mold-like workflows.

13. Flex
   - Powerful but less deterministic; should be added only after core features are stable.

14. Dome / Freeform / Deform
   - Useful for industrial design surfaces, lower priority for mechanical primitives.

## Important Missing Sketch Wrappers

### High Priority

1. Basic entities
   - Line.
   - Construction line / centerline.
   - Rectangle variants: corner rectangle, center rectangle, 3-point rectangle.
   - Arc variants: 3-point arc, tangent arc, centerpoint arc.
   - Slot variants: straight slot, centerpoint slot, arc slot.

2. Sketch constraints and dimensions
   - Smart dimension wrapper.
   - Horizontal/vertical/coincident/tangent/concentric/equal relations.
   - Fully define sketch helpers.
   - Current scripts rely heavily on absolute coordinates; constraints are needed for true parametric CAD.

3. Sketch naming and selection helpers
   - Named sketch entities where possible.
   - Selection by generated sketch names is working; entity-level naming is still weak.

### Medium Priority

4. Polygon.
5. Ellipse / partial ellipse.
6. Spline.
7. Text.
8. Point.
9. Sketch fillet / sketch chamfer.
10. Trim / extend.
11. Offset entities.
12. Convert entities / intersection curve.

## 9-View Extraction Feasibility

It is feasible. There are two useful modes.

### Mode A: Drawing 9 Views

Create a SolidWorks drawing document and insert model views.

Verified COM availability on this workstation after opening a drawing template:

- `CreateDrawViewFromModelView3`
- `CreateDrawViewFromModelView2`
- `Create3rdAngleViews2`
- `Create3rdAngleViews`
- `InsertModelInPredefinedView`
- `SaveAs3`

Recommended wrapper:

```text
cad_runtime.solidworks.drawings.create_standard_views_drawing(
    model_path,
    drawing_template,
    output_slddrw,
    output_pdf=None,
)
```

Suggested 9-view set:

- Front
- Back
- Left
- Right
- Top
- Bottom
- Isometric
- Dimetric
- Trimetric

This should output `SLDDRW` and optionally `PDF`.

### Mode B: Model View Image Export

Open the part/assembly, switch named orientations, zoom to fit, and save PNG images.

Verified COM availability on active model documents:

- `ShowNamedView2`
- `ViewZoomtofit2`
- `SaveAs3`
- `Extension.SaveAs`

Recommended wrapper:

```text
cad_runtime.solidworks.views.export_named_view_images(
    model_path,
    output_dir,
    views=("Front", "Back", "Left", "Right", "Top", "Bottom", "Isometric", "Dimetric", "Trimetric"),
)
```

This is better for quick visual QA and dataset generation. Drawing views are better for formal engineering deliverables.

## Recommended Next Implementation Order

1. Validate reusable chamfer and ray-based edge selection helpers.
2. Validate sketch entity helpers: line, centerline, 3-point arc, slot, polygon, ellipse, spline, text.
3. Validate sketch relations and dimensions.
4. Validate stable datum axis and coordinate system helpers.
5. Add formal drawing modules:
   - `drawings.py`
   - `drawing_views.py`
   - `drawing_export.py`
   - `drawing_annotations.py`
6. Add Hole Wizard / tapped-hole wrappers.
7. Validate Shell, Rib, Draft, Mirror.
8. Validate Boundary Boss/Cut and curve helpers.

## Current Risk

The runtime can now generate many solid models, but it is still more geometry-driven than constraint-driven. For complex prompt-to-CAD work, the largest quality jump will come from:

- richer sketch constraints/dimensions;
- stable reference geometry;
- reusable fillet/chamfer/hole wrappers;
- drawing/view extraction for automated checking.
