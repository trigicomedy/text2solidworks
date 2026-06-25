# Assembly Interface Strategy

This rule is mandatory for any model that contains more than one part.

Do not model parts first and decide assembly later. The agent must plan the assembly interfaces before detailed part features are generated.

## Required Planning Order

1. Parse the user prompt into product intent and mechanical function.
2. Decompose the product into named parts and standard components.
3. Build an assembly graph or kinematic chain.
4. Define connection interfaces for every parent-child relationship.
5. Assign stable reference geometry to each part interface.
6. Generate each part feature plan around those interfaces.
7. Generate CAD operations that create both visible geometry and reference geometry.
8. Assemble using the named interfaces, not raw coordinates.

## Interface Types

Each assembly-facing part should expose named interfaces:

- `reference_plane`: mating plane, end face plane, mounting plane, symmetry plane.
- `reference_axis`: revolute axis, cylindrical hole axis, shaft axis, bolt circle axis.
- `reference_point`: joint center, insertion point, tool center point, bolt point.
- `coordinate_system`: local part frame or tool frame.
- `mate_interface`: semantic group of references used for assembly constraints.
- `kinematic_interface`: joint definition such as fixed, revolute, prismatic, or planar.

## Minimum Interface Requirements

For a revolute joint:

- `joint_axis`
- `joint_center`
- `mount_plane`
- `rotation_limit` if known, otherwise record as unknown
- parent and child part names

For a link:

- `proximal_interface`
- `distal_interface`
- `link_centerline_axis`
- `local_coordinate_system`

For a mounting base:

- `world_mount_plane`
- `base_axis`
- `bolt_circle_axis`
- bolt hole center points or a bolt pattern definition

For an end effector:

- `tool_mount_plane`
- `tool_center_point`
- finger reference planes or slide axes

## Mate Planning

Each mate should reference interface names, not faces selected by coordinates.

Preferred mate constraints:

- revolute joint: axis concentric + mount plane coincident, leave rotation free.
- fixed connection: plane coincident + axis concentric or coordinate-system coincidence.
- finger pair: symmetric planes + distance gap or prismatic guide axis.

Example:

```json
{
  "mate": "J2_revolute",
  "type": "revolute",
  "parent_interface": "shoulder_housing.output",
  "child_interface": "upper_arm.proximal",
  "constraints": [
    {"type": "axis_concentric", "a": "shoulder_housing.output.axis", "b": "upper_arm.proximal.axis"},
    {"type": "plane_coincident", "a": "shoulder_housing.output.mount_plane", "b": "upper_arm.proximal.mount_plane"}
  ],
  "free_dof": ["rotation_about_axis"]
}
```

## Runtime Implication

The CAD runtime should create reference geometry as first-class outputs:

- create reference planes for each mount plane
- create reference axes for each joint axis
- create named sketch points for joint centers
- store all names in the registry
- export the registry with the generated CAD files

If a reference cannot yet be created by the runtime, the plan must still include it as an intended interface so implementation can catch up later.
