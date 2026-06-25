# Robot Arm Skill Notes

Use this reference when converting a broad robot-arm prompt into a CAD plan.

## Decomposition Pattern

For serial robots, first decompose by kinematic chain rather than by visible shape:

1. Fixed base and mounting flange
2. J1 yaw module
3. Shoulder pitch module
4. Upper-arm link
5. Elbow pitch module
6. Forearm link
7. Wrist roll module
8. Wrist pitch module
9. Wrist yaw module
10. End effector palm
11. Left finger
12. Right finger

Each item should become a named part unless the user asks for a single multibody part.

## Planning Rules

- Extract nominal dimensions into a parameter table before geometry generation.
- Create joint axes as stable references, even if the first geometry pass only creates visual cylinders.
- Prefer simple external envelopes for first-pass STEP export: cylinders, rounded boxes, covers, holes, and visible plates.
- Keep motor covers and cable covers as separate named features or parts when they may become selectable later.
- Keep all joint centers in a kinematic layout table: `joint_id`, `axis`, `origin_mm`, `parent`, `child`.
- Avoid relying on volatile selected faces for downstream assembly. Use reference axes and planes for mates.
- The first generated model should be mechanically plausible and non-intersecting; fine internal detail is a later refinement pass.

## Operation Strategy

For a complex prompt, produce three artifacts:

1. `part_breakdown`: named parts and their roles.
2. `parameter_table`: all inferred and user-provided dimensions.
3. `feature_plan`: base feature, added features, reference geometry, and assembly placement.

## First-Pass Geometry Simplification

- Rounded rectangular hollow links may be approximated as rounded rectangular solid links first.
- Shallow side grooves can be represented as narrow cable-cover strips or later cut features.
- Wrist modules can be compact cylinders with alternating axes.
- Gripper fingers can be simple rounded-tip rectangular prismatic parts.

## Missing Data Policy

If the prompt does not specify exact offsets, choose conservative defaults and record them in the parameter table. Do not silently invent hidden internal mechanisms.
