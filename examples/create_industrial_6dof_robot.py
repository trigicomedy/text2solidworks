from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import examples.create_6dof_robot_arm as rt
from cad_runtime.solidworks import connect_solidworks

WORKSPACE = Path(r"D:\text2solidworks_workspace")
OUT_DIR = WORKSPACE / "exports" / "industrial_6dof_robot"
PART_DIR = OUT_DIR / "parts"
PLAN_DIR = WORKSPACE / "plans"

PART_NAMES = [
    "base", "axis1_column", "shoulder_housing", "upper_arm", "elbow_housing", "forearm",
    "wrist_axis4_housing", "wrist_axis5_housing", "wrist_axis6_housing",
    "tool_flange", "gripper_palm", "finger_a", "finger_b", "finger_c",
]

PARAMS = {
    "total_height_mm": 1350,
    "max_reach_mm": 950,
    "payload_kg": 5,
    "base_diameter_mm": 280,
    "base_height_mm": 180,
    "mount_hole_count": 16,
    "mount_hole_diameter_mm": 11,
    "mount_pcd_mm": 240,
    "center_hole_mm": 80,
    "axis2_diameter_mm": 140,
    "axis2_thickness_mm": 55,
    "upper_arm_length_mm": 420,
    "upper_arm_section_mm": [90, 40],
    "axis3_diameter_mm": 120,
    "axis3_thickness_mm": 50,
    "forearm_length_mm": 350,
    "forearm_section_mm": [80, 35],
    "wrist_length_mm": 180,
    "wrist_diameter_mm": 95,
    "tool_flange_diameter_mm": 50,
    "tool_flange_thickness_mm": 16,
    "gripper_palm_mm": [70, 55, 38],
    "finger_length_mm": 80,
    "finger_width_mm": 14,
    "finger_thickness_mm": 8,
}


def configure_runtime_globals():
    rt.OUT_DIR = OUT_DIR
    rt.PART_DIR = PART_DIR
    rt.PLAN_DIR = PLAN_DIR
    rt.PARAMS = PARAMS
    rt.PART_NAMES = PART_NAMES


def create_base(sw) -> Path:
    p = PARAMS
    model = rt.new_doc(sw, rt.user_template(sw, "part"))
    rt.circle_profile(model, "Top Plane", p["base_diameter_mm"] / 2, "base_flange_sketch")
    rt.extrude_boss(model, "base_flange", 35)
    rt.circle_profile(model, "Top Plane", 95, "axis1_column_sketch")
    rt.extrude_boss(model, "axis1_column_body", p["base_height_mm"])

    rt.begin_sketch(model, "Top Plane")
    radius = p["mount_pcd_mm"] / 2
    for i in range(p["mount_hole_count"]):
        a = 2 * math.pi * i / p["mount_hole_count"]
        x = rt.mm(radius * math.cos(a))
        y = rt.mm(radius * math.sin(a))
        rr = rt.mm(p["mount_hole_diameter_mm"] / 2)
        model.SketchManager.CreateCircle(x, y, 0, x + rr, y, 0)
    rr = rt.mm(p["center_hole_mm"] / 2)
    model.SketchManager.CreateCircle(0, 0, 0, rr, 0, 0)
    rt.end_sketch(model, "base_mounting_holes_interface_sketch")

    rt.add_simple_fillet(model, 6)
    rt.create_offset_ref_plane(model, "base_flange_top_plane", "Top Plane", 35)
    rt.create_offset_ref_plane(model, "base_top_mount_plane", "Top Plane", p["base_height_mm"])
    rt.create_axis_sketch(model, "base_axis1_axis_sketch", "Front Plane", p["base_height_mm"] / 2)
    rt.create_center_point_sketch(model, "base_axis1_center_point_sketch", "Top Plane")
    return rt.save_part_and_close(sw, model, PART_DIR / "base.SLDPRT")


def create_tool_flange(sw) -> Path:
    p = PARAMS
    model = rt.new_doc(sw, rt.user_template(sw, "part"))
    rt.circle_profile(model, "Right Plane", p["tool_flange_diameter_mm"] / 2, "iso_9409_flange_sketch")
    rt.extrude_boss(model, "iso_9409_1_50_4_m6_flange", p["tool_flange_thickness_mm"])
    rt.add_linear_part_datums(model, "tool_flange", "Right Plane", p["tool_flange_thickness_mm"], "Top Plane", 40)
    rt.add_simple_fillet(model, 3)
    return rt.save_part_and_close(sw, model, PART_DIR / "tool_flange.SLDPRT")


def create_finger(sw, name: str) -> Path:
    p = PARAMS
    model = rt.new_doc(sw, rt.user_template(sw, "part"))
    rt.rect_profile(model, "Right Plane", p["finger_width_mm"], p["finger_thickness_mm"], f"{name}_finger_section")
    rt.extrude_boss(model, f"{name}_finger_body", p["finger_length_mm"])
    rt.add_linear_part_datums(model, name, "Right Plane", p["finger_length_mm"], "Top Plane", p["finger_length_mm"] / 2)
    rt.create_offset_ref_plane(model, f"{name}_mount_plane", "Right Plane", 0.01)
    rt.add_simple_fillet(model, 3)
    return rt.save_part_and_close(sw, model, PART_DIR / f"{name}.SLDPRT")


def create_parts(sw) -> dict[str, Path]:
    p = PARAMS
    PART_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "base": create_base(sw),
        "axis1_column": rt.create_cylinder(sw, "axis1_column", 160, 110, "Z"),
        "shoulder_housing": rt.create_cylinder(sw, "shoulder_housing", p["axis2_diameter_mm"], p["axis2_thickness_mm"], "X"),
        "upper_arm": rt.create_link(sw, "upper_arm", p["upper_arm_length_mm"], tuple(p["upper_arm_section_mm"])),
        "elbow_housing": rt.create_cylinder(sw, "elbow_housing", p["axis3_diameter_mm"], p["axis3_thickness_mm"], "X"),
        "forearm": rt.create_link(sw, "forearm", p["forearm_length_mm"], tuple(p["forearm_section_mm"])),
        "wrist_axis4_housing": rt.create_cylinder(sw, "wrist_axis4_housing", p["wrist_diameter_mm"], 60, "X"),
        "wrist_axis5_housing": rt.create_cylinder(sw, "wrist_axis5_housing", p["wrist_diameter_mm"], 60, "Y"),
        "wrist_axis6_housing": rt.create_cylinder(sw, "wrist_axis6_housing", p["wrist_diameter_mm"], 60, "X"),
        "tool_flange": create_tool_flange(sw),
        "gripper_palm": rt.create_box(sw, "gripper_palm", tuple(p["gripper_palm_mm"]), "X", 4),
        "finger_a": create_finger(sw, "finger_a"),
        "finger_b": create_finger(sw, "finger_b"),
        "finger_c": create_finger(sw, "finger_c"),
    }


def load_existing_parts() -> dict[str, Path]:
    parts = {name: PART_DIR / f"{name}.SLDPRT" for name in PART_NAMES}
    missing = [str(v) for v in parts.values() if not v.exists()]
    if missing:
        raise RuntimeError("--assembly-only missing parts:\n" + "\n".join(missing))
    return parts


def create_assembly(sw, parts: dict[str, Path]) -> Path:
    p = PARAMS
    asm = rt.new_doc(sw, rt.user_template(sw, "assembly"))

    z_axis1 = p["base_height_mm"]
    z_shoulder = z_axis1 + 110
    x_upper = 70
    x_elbow = x_upper + p["upper_arm_length_mm"]
    x_forearm = x_elbow + 45
    x_wrist = x_forearm + p["forearm_length_mm"]
    x_tool = x_wrist + p["wrist_length_mm"]

    placements = {
        "base": (0, 0, 0),
        "axis1_column": (0, 0, z_axis1),
        "shoulder_housing": (0, 0, z_shoulder),
        "upper_arm": (x_upper, 0, z_shoulder),
        "elbow_housing": (x_elbow, 0, z_shoulder),
        "forearm": (x_forearm, 0, z_shoulder),
        "wrist_axis4_housing": (x_wrist, 0, z_shoulder),
        "wrist_axis5_housing": (x_wrist + 60, 0, z_shoulder),
        "wrist_axis6_housing": (x_wrist + 120, 0, z_shoulder),
        "tool_flange": (x_tool, 0, z_shoulder),
        "gripper_palm": (x_tool + 25, 0, z_shoulder),
        "finger_a": (x_tool + 70, 0, z_shoulder + 35),
        "finger_b": (x_tool + 70, 30, z_shoulder - 20),
        "finger_c": (x_tool + 70, -30, z_shoulder - 20),
    }

    comps = {name: rt.add_component(sw, asm, name, parts[name], xyz) for name, xyz in placements.items()}

    specs = [
        ("base", "base_top_mount_plane", "axis1_column", "axis1_column_start_plane", "mate_base_to_axis1"),
        ("axis1_column", "axis1_column_end_plane", "shoulder_housing", "shoulder_housing_start_plane", "mate_axis1_to_shoulder"),
        ("shoulder_housing", "shoulder_housing_end_plane", "upper_arm", "upper_arm_proximal_mount_plane", "mate_shoulder_to_upper_arm"),
        ("upper_arm", "upper_arm_distal_mount_plane", "elbow_housing", "elbow_housing_start_plane", "mate_upper_arm_to_elbow"),
        ("elbow_housing", "elbow_housing_end_plane", "forearm", "forearm_proximal_mount_plane", "mate_elbow_to_forearm"),
        ("forearm", "forearm_distal_mount_plane", "wrist_axis4_housing", "wrist_axis4_housing_start_plane", "mate_forearm_to_wrist4"),
        ("wrist_axis4_housing", "wrist_axis4_housing_end_plane", "wrist_axis5_housing", "wrist_axis5_housing_start_plane", "mate_wrist4_to_wrist5"),
        ("wrist_axis5_housing", "wrist_axis5_housing_end_plane", "wrist_axis6_housing", "wrist_axis6_housing_start_plane", "mate_wrist5_to_wrist6"),
        ("wrist_axis6_housing", "wrist_axis6_housing_end_plane", "tool_flange", "tool_flange_start_plane", "mate_wrist6_to_tool_flange"),
        ("tool_flange", "tool_flange_end_plane", "gripper_palm", "gripper_palm_start_plane", "mate_tool_flange_to_palm"),
        ("gripper_palm", "gripper_palm_end_plane", "finger_a", "finger_a_mount_plane", "mate_palm_to_finger_a"),
        ("gripper_palm", "gripper_palm_end_plane", "finger_b", "finger_b_mount_plane", "mate_palm_to_finger_b"),
        ("gripper_palm", "gripper_palm_end_plane", "finger_c", "finger_c_mount_plane", "mate_palm_to_finger_c"),
    ]

    made = []
    for a_part, a_ref, b_part, b_ref, label in specs:
        mate = rt.mate_planes_coincident(asm, comps, a_part, a_ref, b_part, b_ref, label)
        if mate is not None:
            made.append(label)
    print(f"[DEBUG] industrial first-pass mates created: {made}")

    try:
        asm.ViewZoomtofit2()
    except Exception:
        pass

    path = OUT_DIR / "industrial_6dof_robot.SLDASM"
    rt.save_as(asm, str(path))
    return path


def write_plan(parts: dict[str, Path], assembly: Path | None):
    PLAN_DIR.mkdir(parents=True, exist_ok=True)
    plan = {
        "model": "industrial_6dof_robot",
        "units": "MMGS",
        "parameters": PARAMS,
        "subassemblies_requested": [
            "Base Assembly", "Shoulder Assembly", "Upper Arm Assembly",
            "Forearm Assembly", "Wrist Assembly", "Gripper Assembly",
        ],
        "runtime_status": {
            "parts": "implemented",
            "datum_planes": "implemented",
            "plane_mates": "first_pass",
            "axis_mates": "planned_next",
            "exploded_view": "planned",
            "drawings": "planned",
        },
        "parts": {k: str(v) for k, v in parts.items()},
        "assembly": str(assembly) if assembly else None,
    }
    (PLAN_DIR / "industrial_6dof_robot_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")


def build(sw, parts_only: bool = False, assembly_only: bool = False):
    configure_runtime_globals()
    PART_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    parts = load_existing_parts() if assembly_only else create_parts(sw)
    assembly = None if parts_only else create_assembly(sw, parts)
    write_plan(parts, assembly)
    return assembly or PART_DIR


def main():
    parser = argparse.ArgumentParser(description="Create an industrial 6-DOF articulated robot arm in SolidWorks.")
    parser.add_argument("--visible", action="store_true")
    parser.add_argument("--parts-only", action="store_true")
    parser.add_argument("--assembly-only", action="store_true")
    args = parser.parse_args()
    if args.parts_only and args.assembly_only:
        raise SystemExit("Use either --parts-only or --assembly-only, not both.")
    sw = connect_solidworks(visible=args.visible)
    result = build(sw, parts_only=args.parts_only, assembly_only=args.assembly_only)
    print(f"Created: {result}")


if __name__ == "__main__":
    main()
