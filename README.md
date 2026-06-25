# text2solidworks

Text-to-SolidWorks planning and automation project.

The project separates agent design reasoning from deterministic SolidWorks COM execution:

```text
Prompt -> Skills -> Plans -> Python runtime -> SolidWorks
```

## Current Layout

- `.agents/skills/part-design/`: single-part design, parameters, interfaces, manufacturability, and simulation planning.
- `.agents/skills/solidworks-modeling/`: current end-to-end SolidWorks planning and execution guidance.
- `cad_runtime/solidworks/`: verified Python wrappers around the SolidWorks COM API.
- `cad_runtime/dsl/`: initial executor for agent-produced CAD operations.
- `examples/`: runnable SolidWorks examples and debugging scripts.
- `docs/architecture.md`: accepted target architecture and migration rules.
- `check_environment.py`: local Python and pywin32 environment check.

Generated prompts, plans, logs, CAD files, and exports belong in:

```text
D:\text2solidworks_workspace
```

## Environment Check

From `D:\text2solidworks`:

```powershell
python check_environment.py
```

If Python or `pywin32` is missing, follow `INSTALL.md`.

## Smoke Test

```powershell
python examples\debug_circle_extrude.py
```

## Robot Arm Example

Generate parts and assembly:

```powershell
python examples\create_6dof_robot_arm.py --visible
```

Rebuild only the assembly from existing parts:

```powershell
python examples\create_6dof_robot_arm.py --visible --assembly-only
```

## Migration Status

The existing `cad_runtime` import path is intentionally preserved while verified COM functions are gradually reorganized. Do not move it into `src/` until compatibility imports and SolidWorks smoke tests are in place.
