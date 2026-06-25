# Category Parameter Rules

This file maps mechanical part categories to the parameters, features, and interfaces that a planning agent should request or infer.

The table is intentionally incomplete. Extend it whenever new part categories, standards, or recurring design patterns appear.

## How To Use

When creating a `design_plan.json`, every part must have:

- `part_id`: stable programmatic name
- `display_name`: human-readable name
- `category`: one of the controlled categories below
- `role`: function in the product
- `parameters`: category-specific dimensions and engineering values
- `features_required`: visible/modeling features expected for that category
- `interfaces_required`: references needed for assembly and downstream mates

If required values are missing from the user prompt, the agent should either ask for them or infer conservative defaults and mark them as inferred.

## Common Fields For All Parts

Required:

- `part_id`
- `display_name`
- `category`
- `quantity`
- `role`
- `make_or_buy`
- `material`
- `manufacturing.process`
- `parameters.bounding_size_mm` when applicable
- `interfaces_required` if the part participates in assembly

Recommended:

- `mass_target_kg`
- `finish`
- `edge_fillet_mm`
- `tolerance_class`
- `modeling_policy`: `detailed`, `external_envelope`, `placeholder`, or `standard_component`

## Category: mounting_base

Typical meaning: fixed machine base, pedestal, floor/table mounting plate, robot base flange.

Required parameters:

- `diameter_mm` or `length_mm` / `width_mm`
- `height_mm` or `thickness_mm`
- `mounting_pattern.type`: circular, rectangular, custom
- `mounting_pattern.hole_count`
- `mounting_pattern.hole_diameter_mm`
- `mounting_pattern.pcd_mm` for circular patterns
- `center_hole_diameter_mm` if cable/service hole exists

Recommended features:

- base flange
- raised boss or column
- mounting holes
- center through hole
- edge fillets
- counterbore/countersink if specified

Required interfaces:

- `world_mount_plane`
- `base_axis`
- `output_mount_plane`
- `output_axis`
- `bolt_pattern_axis`
- `bolt_hole_centers`

## Category: revolute_joint_housing

Typical meaning: robot joint shell, motor/reducer housing, rotating joint module.

Required parameters:

- `outer_diameter_mm`
- `thickness_mm` or `length_mm`
- `axis_direction`: X, Y, or Z
- `joint_id`
- `rotation_range_deg` if known
- `bearing_type` if specified
- `reducer_type` if specified
- `reducer_ratio` if specified

Recommended features:

- cylindrical housing
- side motor cover plates
- bearing/reducer envelope
- cable pass-through
- hidden screw cover pattern
- edge fillets
- service cover seam

Required interfaces:

- `input_mount_plane`
- `output_mount_plane`
- `joint_axis`
- `joint_center`
- `orientation_plane`
- `motor_mount_interface`
- `bearing_envelope_interface`

## Category: robot_link

Typical meaning: upper arm, forearm, structural link between two joints.

Required parameters:

- `length_mm`
- `width_mm`
- `thickness_mm`
- `cross_section_type`: rectangular, rounded_rect, tube, custom
- `wall_thickness_mm` if hollow
- `material`

Recommended parameters:

- `hollow_enabled`
- `lightening_window.enabled`
- `lightening_window.length_mm`
- `lightening_window.width_mm`
- `lightening_window.corner_radius_mm`
- `taper_enabled`
- `end_boss_diameter_mm`
- `edge_fillet_mm`

Recommended features:

- rounded rectangular main body
- hollow or lightweight shell approximation
- side lightening window
- cable routing cover or internal cable passage
- proximal and distal reinforced ends
- external fillets

Required interfaces:

- `proximal_mount_plane`
- `proximal_joint_axis`
- `proximal_joint_center`
- `distal_mount_plane`
- `distal_joint_axis`
- `distal_joint_center`
- `link_centerline_axis`
- `local_coordinate_system`

## Category: wrist_module

Typical meaning: compact wrist axis module, roll/pitch/yaw module near end effector.

Required parameters:

- `outer_diameter_mm`
- `length_mm`
- `axis_direction`
- `joint_id`
- `rotation_range_deg`

Recommended features:

- compact cylindrical housing
- alternating axis orientation if multi-axis wrist
- cover seams
- tool-side flange transition
- cable passage

Required interfaces:

- `input_mount_plane`
- `output_mount_plane`
- `joint_axis`
- `joint_center`
- `tool_side_axis` if final wrist module

## Category: tool_flange

Typical meaning: robot end flange, ISO tool interface.

Required parameters:

- `standard`: e.g. ISO 9409-1
- `flange_diameter_mm`
- `thickness_mm`
- `bolt_pattern.hole_count`
- `bolt_pattern.thread_or_clearance`
- `bolt_pattern.pcd_mm`
- `center_bore_mm` if specified

Recommended features:

- circular flange
- bolt pattern
- pilot boss or recess
- edge fillets

Required interfaces:

- `robot_side_mount_plane`
- `tool_side_mount_plane`
- `flange_axis`
- `tool_center_point`
- `bolt_pattern_axis`

## Category: gripper_palm

Typical meaning: central body of a gripper or end effector.

Required parameters:

- `length_mm`
- `width_mm`
- `height_mm`
- `finger_count`
- `opening_range_mm` if active gripper
- `mount_standard` if specified

Recommended features:

- palm block
- tool flange mount
- finger mount pads
- actuator placeholder
- cable/pneumatic ports
- edge fillets

Required interfaces:

- `tool_mount_plane`
- `tool_mount_axis`
- `finger_mount_interfaces`
- `tool_center_point`

## Category: gripper_finger

Typical meaning: parallel gripper finger, three-finger jaw, fingertip.

Required parameters:

- `length_mm`
- `width_mm`
- `thickness_mm`
- `finger_role`: left, right, A, B, C, fixed, moving
- `tip_geometry`: rounded, flat, V-groove, pad

Recommended features:

- slender finger body
- rounded or padded fingertip
- mounting holes or mount plane
- grip pads
- edge fillets

Required interfaces:

- `mount_plane`
- `length_axis`
- `grip_surface`
- `tip_point`

## Category: fastener

Typical meaning: screw, bolt, nut, washer, dowel pin.

Required parameters:

- `standard`: ISO, DIN, GB, ANSI, custom
- `size`: e.g. M6, M10
- `length_mm` if bolt/screw
- `quantity`
- `placement_pattern`

Recommended modeling policy:

- Use `standard_component` or `placeholder` unless detailed threads are required.

Required interfaces:

- `axis`
- `head_seat_plane`
- `thread_engagement_depth_mm` if relevant

## Category: bearing

Typical meaning: cross roller bearing, radial bearing, thrust bearing.

Required parameters:

- `bearing_type`
- `outer_diameter_mm`
- `inner_diameter_mm`
- `width_mm`
- `load_rating` if known

Recommended modeling policy:

- Use external envelope for first-pass CAD.

Required interfaces:

- `bearing_axis`
- `inner_ring_interface`
- `outer_ring_interface`
- `mount_planes`

## Category: gearbox

Typical meaning: harmonic reducer, cycloidal reducer, planetary reducer.

Required parameters:

- `gearbox_type`
- `ratio`
- `outer_diameter_mm` if known
- `length_mm` if known
- `input_axis`
- `output_axis`

Recommended modeling policy:

- Use placeholder envelope unless detailed reducer geometry is explicitly requested.

Required interfaces:

- `input_axis`
- `output_axis`
- `mount_plane`
- `housing_envelope`

## Category: motor_placeholder

Typical meaning: servo motor, stepper motor, integrated actuator placeholder.

Required parameters:

- `motor_type`
- `rated_power_w` or `torque_nm` if known
- `body_diameter_mm` or frame size
- `body_length_mm`
- `shaft_diameter_mm` if exposed

Required interfaces:

- `motor_axis`
- `mount_plane`
- `shaft_axis`
- `connector_location` if cable routing is important

## Category: cover_plate

Typical meaning: removable motor cover, access cover, hidden screw cover.

Required parameters:

- `shape`: circular, rectangular, custom
- `diameter_mm` or `length_mm` / `width_mm`
- `thickness_mm`
- `fastener_pattern`

Required interfaces:

- `mount_plane`
- `normal_axis`
- `fastener_points`

## Category: cable_cover

Typical meaning: external routing cover, internal cable path cover.

Required parameters:

- `length_mm`
- `width_mm`
- `thickness_mm`
- `route_start`
- `route_end`

Recommended features:

- raised strip or recessed channel
- rounded ends
- hidden screw details if specified

Required interfaces:

- `mount_plane`
- `route_centerline`
- `start_point`
- `end_point`

## Extension Notes

When adding a new category, include:

- typical meaning
- required parameters
- optional/recommended parameters
- recommended features
- required interfaces
- modeling policy
- common standards or references, if any
