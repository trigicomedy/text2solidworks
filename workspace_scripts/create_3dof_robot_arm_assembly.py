from __future__ import annotations

import json
import math
import sys
import time
import argparse
from pathlib import Path

PROJECT_ROOT = Path(r"D:\text2solidworks")
PROJECT_DIR = Path(r"D:\text2solidworks_workspace\projects\robot_arm_3dof_assembly")
PART_DIR = PROJECT_DIR / "parts"
VIEW_DIR = PROJECT_DIR / "views"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cad_runtime.solidworks import (
    AssemblyRef,
    add_component,
    connect_solidworks,
    create_revolute_joint,
    fix_component_in_assembly,
    mate_angle,
    new_assembly,
    save_assembly,
    summarize_assembly,
)
from cad_runtime.solidworks.document import new_part, save_as
from cad_runtime.solidworks.features import extrude_boss, extrude_cut_through_all, rebuild_model
from cad_runtime.solidworks.holes import cut_simple_through_hole
from cad_runtime.solidworks.references import create_axis_from_two_planes, create_offset_plane
from cad_runtime.solidworks.selection import clear_selection
from cad_runtime.solidworks.sketch_entities import draw_polygon
from cad_runtime.solidworks.sketches import begin_sketch_on_plane, draw_circle, end_sketch
from cad_runtime.solidworks.units import mm
from cad_runtime.solidworks.views import export_model_nine_view_images


def log(message: str) -> None:
    print(f"[3DOF-ASM] {time.strftime('%H:%M:%S')} {message}", flush=True)


def part_template(sw) -> str:
    for candidate in [
        Path(r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\templates\gb_part.prtdot"),
        Path(r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\templates\Part.prtdot"),
    ]:
        if candidate.exists():
            return str(candidate)
    pref = sw.GetUserPreferenceStringValue(1)
    if pref and Path(pref).exists():
        return pref
    raise RuntimeError("No SolidWorks part template found.")


def close_doc(sw, model) -> None:
    try:
        title_attr = getattr(model, "GetTitle", None)
        title = title_attr() if callable(title_attr) else title_attr
        if title:
            sw.CloseDoc(title)
    except Exception:
        pass


def view(model, pause_s: float = 0.15) -> None:
    rebuild_model(model)
    try:
        model.ViewZoomtofit2()
    except Exception:
        pass
    time.sleep(pause_s)


def save_part(sw, model, name: str) -> Path:
    PART_DIR.mkdir(parents=True, exist_ok=True)
    path = PART_DIR / f"{name}.SLDPRT"
    save_as(model, str(path))
    view(model)
    close_doc(sw, model)
    return path


def add_ref_planes_and_axes_for_pitch_part(model, length_mm: float | None = None):
    create_offset_plane(model, "MID_PLANE_Y0", "Front Plane", 0.01)
    create_offset_plane(model, "PIN_A_X0_PLANE", "Right Plane", 0.01)
    create_axis_from_two_planes(model, "PIN_A_AXIS_Y", "PIN_A_X0_PLANE", "Top Plane")
    if length_mm is not None:
        create_offset_plane(model, "PIN_B_X_PLANE", "Right Plane", length_mm)
        create_axis_from_two_planes(model, "PIN_B_AXIS_Y", "PIN_B_X_PLANE", "Top Plane")


def create_base(sw) -> Path:
    log("Creating Base")
    model = new_part(sw, part_template(sw))
    begin_sketch_on_plane(model, "Top Plane")
    draw_circle(model, 0, 0, 95)
    end_sketch(model, "SK_BASE_FLANGE")
    extrude_boss(model, "BASE_FLANGE_D190_H22", 22)

    begin_sketch_on_plane(model, "Top Plane")
    draw_circle(model, 0, 0, 54)
    end_sketch(model, "SK_BASE_BEARING_OUTER")
    extrude_boss(model, "BASE_BEARING_HOUSING_D108_H44", 44)

    begin_sketch_on_plane(model, "Top Plane")
    draw_circle(model, 0, 0, 18)
    end_sketch(model, "SK_BASE_CABLE_BORE")
    try:
        extrude_cut_through_all(model, "BASE_CENTER_CABLE_BORE_D36", fallback_depth_mm=80, preferred_reverse_direction=False)
    except Exception as exc:
        log(f"Center cable bore skipped: {exc}")

    begin_sketch_on_plane(model, "Top Plane")
    for x, y in [(70, 0), (0, 70), (-70, 0), (0, -70)]:
        draw_circle(model, x, y, 3.4)
    end_sketch(model, "SK_BASE_4X_M6")
    extrude_cut_through_all(model, "BASE_4X_M6_CLEARANCE", fallback_depth_mm=30, preferred_reverse_direction=True)

    create_offset_plane(model, "TOP_MOUNT_PLANE", "Top Plane", 44)
    create_axis_from_two_planes(model, "YAW_AXIS_Z", "Front Plane", "Right Plane")
    create_offset_plane(model, "BASE_FRONT_REF", "Front Plane", 0.01)
    return save_part(sw, model, "Base")


def create_joint1(sw) -> Path:
    log("Creating Joint1 rotary base joint")
    model = new_part(sw, part_template(sw))
    begin_sketch_on_plane(model, "Top Plane")
    draw_circle(model, 0, 0, 42)
    end_sketch(model, "SK_J1_ROTARY_STAGE")
    extrude_boss(model, "J1_ROTARY_STAGE_D84_H58", 58)

    begin_sketch_on_plane(model, "Front Plane")
    draw_circle(model, 0, 62, 43)
    end_sketch(model, "SK_J1_SHOULDER_DISC")
    extrude_boss(model, "J1_SHOULDER_DISC_D86_T40", 40)

    begin_sketch_on_plane(model, "Front Plane")
    draw_circle(model, 0, 62, 15)
    end_sketch(model, "SK_J1_HOLLOW_SHAFT")
    try:
        extrude_cut_through_all(model, "J1_HOLLOW_SHAFT_D30", fallback_depth_mm=60, preferred_reverse_direction=True)
    except Exception as exc:
        log(f"J1 hollow shaft skipped: {exc}")

    create_offset_plane(model, "BOTTOM_MOUNT_PLANE", "Top Plane", 0.01)
    create_axis_from_two_planes(model, "YAW_AXIS_Z", "Front Plane", "Right Plane")
    create_offset_plane(model, "PITCH_Z62_PLANE", "Top Plane", 62)
    create_axis_from_two_planes(model, "PITCH_AXIS_Y", "Right Plane", "PITCH_Z62_PLANE")
    create_offset_plane(model, "MID_PLANE_Y0", "Front Plane", 0.01)
    return save_part(sw, model, "Joint1")


def link_body(model, name: str, length: float, height: float, thickness: float, end_radius: float):
    begin_sketch_on_plane(model, "Front Plane")
    model.SketchManager.CreateCenterRectangle(mm(length / 2), 0, 0, mm(length), mm(height / 2), 0)
    end_sketch(model, f"SK_{name}_WEB")
    extrude_boss(model, f"{name}_MAIN_WEB_L{length:g}", thickness)

    for x, label in [(0, "A"), (length, "B")]:
        begin_sketch_on_plane(model, "Front Plane")
        draw_circle(model, x, 0, end_radius)
        end_sketch(model, f"SK_{name}_END_{label}")
        extrude_boss(model, f"{name}_HINGE_EYE_{label}", thickness)

    # Honeycomb-style hexagonal lightening windows. The top and bottom material
    # bands remain continuous for bending stiffness.
    begin_sketch_on_plane(model, "Front Plane")
    pitch = 42
    centers = []
    x = 55
    while x < length - 45:
        centers.append((x, 0))
        if x + pitch / 2 < length - 45:
            centers.append((x + pitch / 2, 13))
            centers.append((x + pitch / 2, -13))
        x += pitch
    for cx, cz in centers:
        draw_polygon(model, (cx, cz), (cx + 10, cz), 6)
    end_sketch(model, f"SK_{name}_HEX_LIGHTENING")
    try:
        extrude_cut_through_all(model, f"{name}_HEX_LIGHTENING_CUTS", fallback_depth_mm=thickness * 3, preferred_reverse_direction=True)
    except Exception as exc:
        log(f"{name} hex lightening cut skipped: {exc}")

    # Pin holes at the hinge eyes.
    for x, label in [(0, "A"), (length, "B")]:
        try:
            cut_simple_through_hole(model, f"{name}_PIN_HOLE_{label}_D16", "Front Plane", (x, 0), 16)
        except Exception as exc:
            log(f"{name} pin hole {label} skipped: {exc}")


def create_link(sw, part_name: str, length: float, height: float, thickness: float, end_radius: float) -> Path:
    log(f"Creating {part_name}")
    model = new_part(sw, part_template(sw))
    link_body(model, part_name.upper(), length, height, thickness, end_radius)
    add_ref_planes_and_axes_for_pitch_part(model, length)
    return save_part(sw, model, part_name)


def create_joint2(sw) -> Path:
    log("Creating Joint2 elbow joint")
    model = new_part(sw, part_template(sw))
    begin_sketch_on_plane(model, "Front Plane")
    draw_circle(model, 0, 0, 36)
    end_sketch(model, "SK_J2_ELBOW_DISC")
    extrude_boss(model, "J2_ELBOW_DISC_D72_T34", 34)

    begin_sketch_on_plane(model, "Front Plane")
    draw_circle(model, 0, 0, 13)
    end_sketch(model, "SK_J2_PIN_BORE")
    try:
        extrude_cut_through_all(model, "J2_PIN_BORE_D26", fallback_depth_mm=60, preferred_reverse_direction=True)
    except Exception as exc:
        log(f"J2 pin bore skipped: {exc}")

    add_ref_planes_and_axes_for_pitch_part(model, None)
    return save_part(sw, model, "Joint2")


def create_end_effector_mount(sw) -> Path:
    log("Creating End Effector Mount")
    model = new_part(sw, part_template(sw))
    begin_sketch_on_plane(model, "Front Plane")
    model.SketchManager.CreateCenterRectangle(0, 0, 0, mm(26), mm(24), 0)
    end_sketch(model, "SK_TOOL_PALM")
    extrude_boss(model, "TOOL_PALM_BLOCK", 28)

    begin_sketch_on_plane(model, "Front Plane")
    draw_circle(model, 0, 0, 24)
    end_sketch(model, "SK_TOOL_FLANGE")
    extrude_boss(model, "TOOL_FLANGE_ISO_STYLE_D48", 10)

    for index, angle in enumerate((45, 135, 225, 315), start=1):
        a = math.radians(angle)
        try:
            cut_simple_through_hole(
                model,
                f"TOOL_M4_CLEARANCE_{index}",
                "Front Plane",
                (17 * math.cos(a), 17 * math.sin(a)),
                4.4,
            )
        except Exception as exc:
            log(f"Tool flange M4 hole {index} skipped: {exc}")

    add_ref_planes_and_axes_for_pitch_part(model, None)
    return save_part(sw, model, "End_Effector_Mount")


def component_ref(component, entity_type: str, ref_name: str) -> AssemblyRef:
    return AssemblyRef(str(getattr(component, "Name2", "")), entity_type, ref_name)


def add_nominal_angle(asm, name: str, comp_a, plane_a: str, comp_b, plane_b: str, angle: float, mates: list[dict]):
    try:
        mate = mate_angle(
            asm,
            name,
            component_ref(comp_a, "plane", plane_a),
            component_ref(comp_b, "plane", plane_b),
            angle,
        )
        mates.append({"name": name, "type": "angle", "status": "ok", "api": mate.api, "angle_deg": angle})
    except Exception as exc:
        mates.append({"name": name, "type": "angle", "status": "failed", "error": str(exc), "angle_deg": angle})


def create_assembly(sw, parts: dict[str, Path]) -> Path:
    log("Creating assembly")
    asm = new_assembly(sw)
    comps = {
        "Base": add_component(sw, asm, parts["Base"], name="Base", xyz_mm=(0, 0, 0)),
        "Joint1": add_component(sw, asm, parts["Joint1"], name="Joint1", xyz_mm=(0, 0, 44)),
        "Link1": add_component(sw, asm, parts["Link1"], name="Link1", xyz_mm=(0, 0, 106)),
        "Joint2": add_component(sw, asm, parts["Joint2"], name="Joint2", xyz_mm=(220, 0, 106)),
        "Link2": add_component(sw, asm, parts["Link2"], name="Link2", xyz_mm=(220, 0, 106)),
        "End_Effector_Mount": add_component(sw, asm, parts["End_Effector_Mount"], name="End_Effector_Mount", xyz_mm=(380, 0, 106)),
    }

    mates: list[dict] = []
    try:
        fix_component_in_assembly(asm, comps["Base"])
        mates.append({"name": "FIX_Base", "type": "fix", "status": "ok"})
    except Exception as exc:
        mates.append({"name": "FIX_Base", "type": "fix", "status": "failed", "error": str(exc)})

    joint_specs = [
        (
            "J1_YAW",
            comps["Base"], "YAW_AXIS_Z", "TOP_MOUNT_PLANE",
            comps["Joint1"], "YAW_AXIS_Z", "BOTTOM_MOUNT_PLANE",
            (-180, 180),
        ),
        (
            "J2_SHOULDER_PITCH",
            comps["Joint1"], "PITCH_AXIS_Y", "MID_PLANE_Y0",
            comps["Link1"], "PIN_A_AXIS_Y", "MID_PLANE_Y0",
            (-135, 135),
        ),
        (
            "J3_ELBOW_PITCH",
            comps["Link1"], "PIN_B_AXIS_Y", "MID_PLANE_Y0",
            comps["Joint2"], "PIN_A_AXIS_Y", "MID_PLANE_Y0",
            (-135, 135),
        ),
        (
            "J4_FOREARM_PITCH_INTERFACE",
            comps["Joint2"], "PIN_A_AXIS_Y", "MID_PLANE_Y0",
            comps["Link2"], "PIN_A_AXIS_Y", "MID_PLANE_Y0",
            (-120, 120),
        ),
        (
            "J5_END_MOUNT_INTERFACE",
            comps["Link2"], "PIN_B_AXIS_Y", "MID_PLANE_Y0",
            comps["End_Effector_Mount"], "PIN_A_AXIS_Y", "MID_PLANE_Y0",
            (-90, 90),
        ),
    ]
    for name, ca, aa, pa, cb, ab, pb, limits in joint_specs:
        try:
            joint = create_revolute_joint(
                asm,
                name,
                component_ref(ca, "axis", aa),
                component_ref(cb, "axis", ab),
                plane_a=component_ref(ca, "plane", pa),
                plane_b=component_ref(cb, "plane", pb),
                limit_deg=limits,
            )
            mates.append({
                "name": name,
                "type": "revolute",
                "status": "ok",
                "limit_deg": list(limits),
                "axis_mate_api": joint.axis_mate.api,
                "plane_mate_api": joint.plane_mate.api if joint.plane_mate else None,
            })
        except Exception as exc:
            mates.append({"name": name, "type": "revolute", "status": "failed", "limit_deg": list(limits), "error": str(exc)})

    add_nominal_angle(asm, "J2_NOMINAL_35DEG", comps["Joint1"], "PITCH_Z62_PLANE", comps["Link1"], "PIN_A_X0_PLANE", 35, mates)
    add_nominal_angle(asm, "J3_NOMINAL_MINUS45DEG", comps["Link1"], "PIN_B_X_PLANE", comps["Link2"], "PIN_A_X0_PLANE", 45, mates)

    rebuild_model(asm)
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    asm_path = PROJECT_DIR / "robot_arm_3dof_constrained.SLDASM"
    save_assembly(asm, asm_path)

    summary = summarize_assembly(asm)
    connection_plan = {
        "source_prompt": "3-DOF serial robot arm, independent modeled parts, assembly mates, revolute joints, lightweight links",
        "assembly": str(asm_path),
        "components": {name: str(path) for name, path in parts.items()},
        "summary": {
            "component_count": summary.component_count,
            "mate_count": summary.mate_count,
            "component_names": summary.component_names,
        },
        "mates": mates,
        "note": "Limit ranges are recorded in this plan. Current runtime uses concentric/coincident/angle mates; native SolidWorks Limit Angle mate is not yet fully validated.",
    }
    (PROJECT_DIR / "connection_plan.json").write_text(json.dumps(connection_plan, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        export_model_nine_view_images(sw, asm_path, VIEW_DIR, visible=True, pause_s=0.1)
    except Exception as exc:
        log(f"9-view export skipped: {exc}")
    log(f"Saved assembly: {asm_path}")
    return asm_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reuse-parts", action="store_true", help="Reuse existing SLDPRT files and only create missing parts.")
    args = parser.parse_args()

    sw = connect_solidworks(visible=True)
    sw.Visible = True
    try:
        sw.FrameState = 1
    except Exception:
        pass
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    (PROJECT_DIR / "original_prompt.md").write_text(
        "# 3-DOF constrained robot arm assembly\n\n"
        "Independent parts: Base, Joint1, Link1, Joint2, Link2, End Effector Mount. "
        "Assembly constraints: concentric/coincident revolute joints and recorded angle limits.\n",
        encoding="utf-8",
    )
    builders = {
        "Base": create_base,
        "Joint1": create_joint1,
        "Link1": lambda app: create_link(app, "Link1", 220, 42, 24, 28),
        "Joint2": create_joint2,
        "Link2": lambda app: create_link(app, "Link2", 160, 36, 20, 24),
        "End_Effector_Mount": create_end_effector_mount,
    }
    parts = {}
    for name, builder in builders.items():
        path = PART_DIR / f"{name}.SLDPRT"
        if args.reuse_parts and path.exists():
            log(f"Reusing existing part: {path}")
            parts[name] = path
        else:
            parts[name] = builder(sw)
    create_assembly(sw, parts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
