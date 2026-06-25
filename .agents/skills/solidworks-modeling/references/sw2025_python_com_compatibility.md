# SW2025 Python COM Compatibility

This reference records behavior verified in the current Windows, SolidWorks 2025, and pywin32 environment. Execution agents must use these rules before inventing new COM call sequences.

## Supported Path

Use:

```python
from cad_runtime.solidworks import ...
```

Prefer the functions in:

- `cad_runtime.solidworks.selection`
- `cad_runtime.solidworks.sketches`
- `cad_runtime.solidworks.features`
- `cad_runtime.solidworks.document`
- `cad_runtime.solidworks.references`
- `cad_runtime.solidworks.patterns`

Do not copy large helper blocks from an example into a new task script. If a missing helper is generally useful, add it to the runtime first.

## Required Smoke Test

Before a complex part is generated in an unverified environment or new thread:

```powershell
cd D:\text2solidworks
python examples\debug_circle_extrude.py
```

The smoke test verifies:

- SolidWorks connection.
- Part template discovery.
- Chinese or English top-plane selection.
- Native circle creation.
- Sketch exit and reselection.
- Blind boss extrusion.
- Model save.

Do not continue to a complex profile when this test fails.

## Typed Null COM Argument

Some SolidWorks calls reject Python `None` for dispatch arguments. Use:

```python
win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)
```

The runtime exposes this as `null_dispatch()`.

## Plane Names

Default feature names depend on template language. Probe aliases:

| Canonical | Aliases |
|---|---|
| `Top Plane` | `Top Plane`, `上视基准面`, `上基准面` |
| `Front Plane` | `Front Plane`, `前视基准面`, `前基准面` |
| `Right Plane` | `Right Plane`, `右视基准面`, `右基准面` |

Do not hard-code only the English name.

## Sketch Exit And Selection

Known issue: this pywin32 binding may not expose `GetActiveSketch2()`, `FirstFeature()`, or `IFirstFeature()` consistently.

Required sequence:

1. Enter sketch with `SketchManager.InsertSketch(True)`.
2. Create native sketch entities.
3. Exit with `SketchManager.InsertSketch(True)`.
4. Rebuild through the runtime compatibility wrapper.
5. Select the newest generated sketch by probing `草图N` and `SketchN`.
6. Call the feature API while that sketch remains selected.

Feature-tree traversal is a fallback diagnostic tool, not the primary sketch-selection path.

## Rebuild

Try callable methods in this order:

1. `ForceRebuild3(False)`
2. `EditRebuild3()`

Some dynamic COM properties appear as booleans instead of callable methods. Always test `callable()` before invoking.

## Boss Extrusion

Verified baseline:

- One-direction blind extrusion.
- End condition value `0`.
- Depth converted from millimeters to meters.
- One closed selected sketch.

Runtime fallback order:

1. `FeatureExtrusion2`
2. `FeatureExtrusion3`

Do not switch to mid-plane extrusion merely to center a part. Create the baseline blind extrusion first, then create stable midpoint reference geometry. Add mid-plane support only after a dedicated current-environment test.

If the API returns `None`:

1. Confirm the intended sketch is selected.
2. Confirm exactly one intended closed contour exists.
3. Check for self-intersections, duplicate segments, gaps, and long-way arcs.
4. Retry the verified baseline call.

## Through Cut

Runtime fallback order:

1. `FeatureCut4`
2. `FeatureCut3`

The cut sketch must remain selected. A `None` return is a failure even without an exception.

Verified on the current part template:

- a boss extruded from `Top Plane` occupies the positive normal side;
- a cut profile created again on that base plane requires `reverse_direction=True`
  to cut into the body;
- `FeatureCut4` with through-all and `reverse_direction=True` is the first
  successful path for the upper-arm link.

Pass `preferred_reverse_direction=True` when this geometric relationship is
known. The runtime still tries the opposite direction and a deep blind fallback
if the preferred call fails.

When several circles overlap an area already removed by earlier cuts, do not
put all circles into one feature if SolidWorks rejects the resulting contour
set. Create one native-circle cut per corner. This is the verified strategy for
the R12 rounded lightening window.

## Native Patterns

Repeated geometry must use native SolidWorks pattern features when the design
intent is a regular repeat.

Supported runtime entry points:

- `cad_runtime.solidworks.patterns.circular_feature_pattern`
- `cad_runtime.solidworks.patterns.linear_feature_pattern`

Verified API availability in the current SW2025 pywin32 binding:

- `FeatureCircularPattern`
- `FeatureCircularPattern2`
- `FeatureCircularPattern3`
- `FeatureCircularPattern4`
- `FeatureCircularPattern5`
- `FeatureLinearPattern`
- `FeatureLinearPattern2`
- `FeatureLinearPattern3`
- `FeatureLinearPattern4`
- `FeatureLinearPattern5`

Known missing names:

- `InsertFeatureCircularPattern`
- `InsertFeatureLinearPattern`

Rule:

1. Create one seed feature.
2. Select the seed feature.
3. Select the pattern axis or direction reference.
4. Call the native pattern wrapper.
5. Treat `None` returns as failures.

Do not replace a failed native pattern with manually copied features unless the
user explicitly approves a non-parametric fallback.

For flanges and bolt circles, the expected modeling strategy is one native seed
hole plus a native circular feature pattern around the flange center axis.

Verified circular feature pattern call:

- create one seed cut feature;
- create a named datum axis, for example `AXIS_CENTER_BORE`;
- select the seed feature with selection mark `4`;
- select the pattern axis with selection mark `1`;
- call `FeatureCircularPattern5(Number, Spacing, FlipDirection, DName, GeometryPattern, EqualSpacing, VaryInstance, SyncSubAssemblies, BDir2, BSymmetric, Number2, Spacing2, DName2, EqualSpacing2)`;
- for the current binding, `DName` can be an empty string when the axis is selected with mark `1`.

The verified flange example uses:

```text
FeatureCircularPattern5(4, 2*pi, False, "", True, True, False, False, False, False, 1, 0.0, "", False)
```

If all pattern calls return `None` without raising, check the selection marks
before changing geometry.

Important: with `EqualSpacing=True`, SolidWorks interprets `Spacing` as the
total angular span. For a full four-hole bolt circle, pass `2*pi` radians
or `360` degrees converted to radians. Do not pass `pi/2`, because that places
all four instances within a 90-degree span.

## Advanced Features

Use `cad_runtime.solidworks.advanced_features` for native revolve, sweep, and
loft operations. Do not call the newer COM methods directly from task scripts
until they have a dedicated workstation test.

Verified runtime entry points:

- `revolve_boss`
- `revolve_cut`
- `sweep_boss`
- `sweep_cut`
- `loft_boss`
- `loft_cut`

Verified native API calls in the current SW2025 pywin32 binding:

| Runtime function | Native API | Verified behavior |
|---|---|---|
| `revolve_boss` | `FeatureRevolve2` | selected closed profile sketch with centerline or axis |
| `revolve_cut` | `FeatureRevolve2` | selected closed cut sketch; `Merge=True` is required |
| `sweep_boss` | `InsertProtrusionSwept` | 14-argument legacy call; profile sketch + path sketch |
| `sweep_cut` | `InsertCutSwept` | 13-argument legacy call; profile/path must intersect the target body |
| `loft_boss` | `InsertProtrusionBlend` | 17-argument legacy call; ordered section sketches |
| `loft_cut` | `InsertCutBlend` | 12-argument legacy call; ordered section sketches through the target body |

Compatibility finding: the COM binding exposes newer names such as
`InsertProtrusionSwept4`, `InsertCutSwept4`, and `InsertProtrusionBlend2`, but
minimal examples were more reliable with the older legacy methods above.

Selection requirements:

1. Create all required sketches with native sketch entities.
2. Exit sketches through the runtime `end_sketch` flow.
3. Select named sketches through `SelectByID2`.
4. For sweeps, select the profile and path sketches; the wrapper tries profile
   mark `1` plus path mark `4`, then mark `0`.
5. For lofts, select section sketches in order; the wrapper tries mark `1`,
   then mark `0`.
6. Treat `None` returns as feature creation failures.

Validation script:

```powershell
cd D:\text2solidworks
python workspace_scripts\debug_advanced_features.py
```

The current workstation has verified and saved:

- `revolve_boss_test.SLDPRT`
- `revolve_cut_test.SLDPRT`
- `sweep_boss_test.SLDPRT`
- `sweep_cut_test.SLDPRT`
- `loft_boss_test.SLDPRT`
- `loft_cut_test.SLDPRT`

## Arc Direction And Rounded Profiles

Use SolidWorks native arcs. Do not approximate arcs with line segments.

For the current SW2025 pywin32 binding:

- `direction=1` creates the clockwise path.
- `direction=-1` creates the counterclockwise path.

Never pass a direction value without naming the intended direction in code. Before extrusion:

- verify start and end radii match;
- verify the intended short or long arc was created;
- verify adjacent endpoints are coincident;
- verify the complete contour is closed;
- verify no segment crosses another segment.

For critical rounded rectangles, prefer a tested high-level helper or native sketch fillet workflow over hand-assembling four ambiguous arcs.

## Diagnosing Feature Failure

Use this order:

1. Document exists and is the active document.
2. Correct plane or sketch is selected.
3. Sketch mode has been exited.
4. Profile is closed and non-self-intersecting.
5. Units were converted to meters.
6. Baseline feature call is used.
7. Fallback API is attempted.
8. Returned feature object is non-`None`.
9. Model rebuild succeeds.

Do not repeatedly change extrusion enums while profile selection and profile validity remain unknown.

## Visibility

For interactive debugging:

- connect with `visible=True`;
- set `sw.Visible = True`;
- rebuild after major features;
- update or fit the view;
- optionally pause between major steps.

Keep pauses out of normal batch execution.
