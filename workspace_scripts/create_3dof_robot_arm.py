from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(r"D:\text2solidworks")
OUT_DIR = Path(r"D:\text2solidworks_workspace\projects\robot_arm_3dof")

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cad_runtime.solidworks import connect_solidworks
from cad_runtime.solidworks.document import save_as
from cad_runtime.solidworks.features import extrude_boss, extrude_cut_through_all, rebuild_model
from cad_runtime.solidworks.references import create_offset_plane
from cad_runtime.solidworks.selection import clear_selection
from cad_runtime.solidworks.sketches import begin_sketch_on_plane, draw_center_rectangle, draw_circle, end_sketch
from cad_runtime.solidworks.units import mm
from cad_runtime.solidworks.views import export_named_view_images


def log(message: str) -> None:
    print(f"[3DOF] {message}", flush=True)


def template(sw) -> str:
    for candidate in [
        Path(r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\templates\gb_part.prtdot"),
        Path(r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\templates\Part.prtdot"),
    ]:
        if candidate.exists():
            return str(candidate)
    path = sw.GetUserPreferenceStringValue(1)
    if path and Path(path).exists():
        return path
    raise RuntimeError("No SolidWorks part template found.")


def view(model, pause_s: float = 0.25) -> None:
    rebuild_model(model)
    try:
        model.ViewZoomtofit2()
    except Exception:
        pass
    time.sleep(pause_s)


def hide_reference_geometry(model) -> None:
    try:
        model.BlankRefGeom()
    except Exception as exc:
        log(f"Reference geometry hide skipped: {exc}")


def circle_boss(model, plane: str, name: str, cx: float, cy: float, radius: float, depth: float):
    begin_sketch_on_plane(model, plane)
    draw_circle(model, cx, cy, radius)
    end_sketch(model, f"SK_{name}")
    feature = extrude_boss(model, name, depth)
    view(model)
    return feature


def rect_boss(model, plane: str, name: str, length: float, width: float, depth: float, *, cy: float = 0.0, cz: float = 0.0):
    begin_sketch_on_plane(model, plane)
    # For Right/offset-right planes, sketch coordinates are Y/Z. The helper
    # draws around sketch origin, so create the rectangle directly for base
    # blocks and use explicit center rectangles for shifted link/finger blocks.
    model.SketchManager.CreateCenterRectangle(mm(cy), mm(cz), 0, mm(cy + length / 2), mm(cz + width / 2), 0)
    end_sketch(model, f"SK_{name}")
    feature = extrude_boss(model, name, depth)
    view(model)
    return feature


def top_mount_holes(model):
    log("Cutting four visible base mounting holes")
    begin_sketch_on_plane(model, "Top Plane")
    radius = 78
    hole_r = 5.5
    for x, y in [(radius, 0), (0, radius), (-radius, 0), (0, -radius)]:
        draw_circle(model, x, y, hole_r)
    end_sketch(model, "SK_BASE_MOUNTING_HOLES")
    try:
        extrude_cut_through_all(model, "BASE_4X_M10_CLEARANCE_HOLES", fallback_depth_mm=40)
    except Exception as exc:
        log(f"Mounting-hole cut skipped: {exc}")
    view(model)


def build(sw):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    model = sw.NewDocument(template(sw), 0, 0, 0)
    if model is None:
        raise RuntimeError("Failed to create SolidWorks part")

    log("Creating base flange and yaw column")
    circle_boss(model, "Top Plane", "BASE_FLANGE_D200_H20", 0, 0, 100, 20)
    circle_boss(model, "Top Plane", "BASE_YAW_COLUMN_D110_H125", 0, 0, 55, 125)
    top_mount_holes(model)

    log("Creating shoulder joint and upper arm")
    circle_boss(model, "Front Plane", "J1_SHOULDER_DISC_D100_T55", 0, 145, 50, 55)
    rect_boss(model, "Right Plane", "UPPER_ARM_RECT_LINK_L260", 42, 34, 260, cy=0, cz=145)
    circle_boss(model, "Front Plane", "UPPER_ARM_SIDE_COVER_LEFT", 0, 145, 38, 5)
    circle_boss(model, "Front Plane", "J2_ELBOW_DISC_D82_T50", 260, 145, 41, 50)

    log("Creating forearm from elbow to wrist")
    create_offset_plane(model, "PLN_ELBOW_X260", "Right Plane", 260)
    rect_boss(model, "PLN_ELBOW_X260", "FOREARM_RECT_LINK_L220", 34, 28, 220, cy=0, cz=225)
    circle_boss(model, "Front Plane", "J3_WRIST_DISC_D62_T42", 480, 225, 31, 42)

    log("Creating compact end effector")
    create_offset_plane(model, "PLN_WRIST_X500", "Right Plane", 500)
    rect_boss(model, "PLN_WRIST_X500", "GRIPPER_PALM_BLOCK", 52, 38, 32, cy=0, cz=225)
    create_offset_plane(model, "PLN_FINGER_START_X532", "Right Plane", 532)
    rect_boss(model, "PLN_FINGER_START_X532", "LEFT_GRIPPER_FINGER", 12, 18, 82, cy=18, cz=225)
    rect_boss(model, "PLN_FINGER_START_X532", "RIGHT_GRIPPER_FINGER", 12, 18, 82, cy=-18, cz=225)
    circle_boss(model, "Front Plane", "TOOL_FLANGE_DISC_D45_T12", 500, 225, 22.5, 12)

    log("Adding simple visual cable cover strips")
    create_offset_plane(model, "PLN_ARM_COVER_X35", "Right Plane", 35)
    rect_boss(model, "PLN_ARM_COVER_X35", "UPPER_ARM_TOP_CABLE_COVER", 9, 8, 205, cy=24, cz=160)
    create_offset_plane(model, "PLN_FOREARM_COVER_X300", "Right Plane", 300)
    rect_boss(model, "PLN_FOREARM_COVER_X300", "FOREARM_TOP_CABLE_COVER", 8, 7, 155, cy=22, cz=238)

    hide_reference_geometry(model)
    path = OUT_DIR / "robot_arm_3dof_reference.SLDPRT"
    save_as(model, str(path))
    try:
        export_named_view_images(model, OUT_DIR / "views", pause_s=0.08)
    except Exception as exc:
        log(f"9-view export skipped: {exc}")
    view(model, pause_s=0.5)
    log(f"Saved model: {path}")
    return path


def main() -> int:
    sw = connect_solidworks(visible=True)
    sw.Visible = True
    try:
        sw.FrameState = 1
    except Exception:
        pass
    build(sw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
