---
name: solidworks-modeling
description: 将自然语言机械建模需求拆解为结构化 CAD 计划，并指导 Agent 通过现有 Python runtime 调用 SolidWorks。适用于零件分解、参数规划、稳定装配接口规划、SolidWorks 可见执行以及 API 兼容调试。
---

# SolidWorks Modeling

Use this skill to turn natural-language mechanical modeling requests into a structured CAD plan before calling the Python runtime.

## Workflow

1. Read [SW2025 Python COM compatibility](references/sw2025_python_com_compatibility.md) before editing or generating execution code.
2. Run `python examples/debug_circle_extrude.py` when entering a new machine, Python environment, SolidWorks version, or Codex thread that has not yet verified the runtime.
3. Decompose the request into parts, standard components, and assembly relationships.
4. For each custom part, produce a parameter table in millimeters.
5. Identify the base feature first: box, cylinder, plate, revolved body, sweep, loft, or imported body.
6. Create stable reference geometry early: planes, axes, coordinate systems, and sketch points.
7. Prefer references such as `part.refs.top_plane` over volatile body faces.
8. Output CAD operations using the runtime DSL or call functions from `cad_runtime.solidworks`.
9. Do not duplicate raw COM calls inside generated task scripts when a runtime wrapper exists.

## Execution Contract

- Treat `cad_runtime.solidworks` as the supported API boundary.
- Treat functions copied inside `examples/create_6dof_robot_arm.py` as legacy compatibility evidence, not the preferred import surface.
- Never use `FirstFeature()`, `IFirstFeature()`, or `GetActiveSketch2()` as the only way to locate a sketch.
- After leaving a sketch, preserve or restore sketch selection before calling an extrusion or cut.
- Start with the verified one-direction blind extrusion. Use mid-plane extrusion only after a dedicated smoke test succeeds in the current binding.
- Use native SolidWorks circles, arcs, holes, and fillets.
- Use native SolidWorks chamfers for all chamfers; never replace chamfers with cuts, revolved cuts, or approximated geometry.
- Use native SolidWorks pattern features for rule-based repeats. Bolt circles, repeated screws, radial holes, hole rows, repeated ribs, slots, fins, and similar repeated geometry must be modeled as one seed feature plus a circular or linear pattern whenever practical.
- For manually assembled arc profiles, specify direction explicitly and verify that the profile is closed and non-self-intersecting before extrusion.
- A returned `None` from a feature call is an execution failure even when no COM exception was raised.
- Do not describe a failure as “geometry failure” until sketch selection and profile validity have both been checked.
- Do not replace a failed native pattern with manual copied features unless the user explicitly approves a non-parametric fallback.

## Minimal DSL Operations

- `create_box`
- `draw_circle_on_plane`
- `cut_hole_on_plane`
- `circular_feature_pattern`
- `linear_feature_pattern`

Example:

```json
{
  "operations": [
    {
      "op": "create_box",
      "name": "base_block",
      "length_mm": 50,
      "width_mm": 50,
      "height_mm": 50
    },
    {
      "op": "cut_hole_on_plane",
      "plane_name": "base_block_top_ref_plane",
      "name": "center_top_hole",
      "center_mm": [0, 0],
      "diameter_mm": 12
    }
  ]
}
```

## Assembly Interface Rule

For any multi-part model, plan assembly interfaces before detailed geometry. Use [assembly interface strategy](references/assembly_interface_strategy.md).

Every named part that participates in assembly must define:

- stable reference planes
- stable reference axes
- joint centers or insertion points
- mate interfaces
- parent/child assembly relationships

Generated CAD plans should assemble parts through these interfaces rather than raw coordinates whenever possible.

## Category Parameter Rules

When assigning a part `category`, use [category parameter rules](references/category_parameter_rules.md) to determine required parameters, recommended features, and required assembly interfaces. If the prompt lacks required values, ask for them or infer conservative defaults and mark them as inferred.

Use [robot arm notes](references/robot_arm_skill_notes.md) for the current robot-arm examples and known runtime constraints.

## Native Pattern Rule

Read [native pattern strategy](references/native_pattern_strategy.md) before creating repeated geometry.

When a repeated structure has a count plus an axis, angle, pitch, row spacing, or direction reference:

1. Create exactly one seed feature.
2. Give the seed feature a stable name.
3. Create or select a stable pattern axis or direction reference.
4. Call the runtime native pattern wrapper.
5. Validate that a SolidWorks pattern feature exists in the feature tree.

Use `circular_feature_pattern` for bolt circles and other radial repeats. Use `linear_feature_pattern` for rows or grids. If native pattern creation fails, stop and repair the selection/API call.
