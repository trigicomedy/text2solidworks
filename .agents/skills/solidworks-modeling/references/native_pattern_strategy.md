# Native Pattern Strategy

Use this reference whenever a model contains repeated geometry.

## When To Pattern

Prefer native pattern features for:

- bolt circles on flanges;
- repeated mounting screws;
- radial holes around a cylinder;
- repeated ribs or spokes around an axis;
- linear rows of holes, slots, fins, ribs, or fasteners;
- rectangular grids that can be represented as two linear pattern directions.

Do not manually loop over repeated features when the repeat has a clear axis,
direction, spacing, angle, or count.

## Circular Feature Pattern

Use for radial repeats around an axis.

Required inputs:

- seed feature name;
- pattern axis name;
- instance count;
- total angle or angular spacing;
- whether spacing is equal;
- feature name for the pattern.

Typical flange-hole strategy:

1. Create one native seed hole at the first PCD point.
2. Name it, for example `BOLT_HOLE_SEED_D8_THROUGH_FLANGE`.
3. Use the center bore axis or flange datum axis as the pattern axis.
4. Create `BOLT_HOLE_CIRCULAR_PATTERN_4X_D8_PCD62`.

## Linear Feature Pattern

Use for repeats along a named direction reference.

Required inputs:

- seed feature name;
- direction reference name;
- spacing;
- count;
- optional second direction reference, spacing, and count;
- feature name for the pattern.

## Failure Policy

If a native pattern fails:

1. Check seed feature selection.
2. Check axis or direction reference selection.
3. Check spacing, angle, and count.
4. Check the current SolidWorks COM signature.
5. Stop and fix the native pattern call.

Manual copies are not an allowed automatic fallback because they lose the
design intent and make later parameter edits brittle.
