from __future__ import annotations

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(r"D:\text2solidworks")
WORK_DIR = Path(r"D:\text2solidworks_workspace\projects\upper_arm_link")
EXPORT_DIR = WORK_DIR / "exports"
LOG_DIR = WORK_DIR / "logs"
PLAN_FILE = WORK_DIR / "plans" / "part_parameters.json"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cad_runtime.solidworks import connect_solidworks
from cad_runtime.solidworks.document import save_as
from cad_runtime.solidworks.features import (
    extrude_boss,
    extrude_cut_through_all,
    rebuild_model,
)
from cad_runtime.solidworks.selection import clear_selection, null_dispatch, select_plane
from cad_runtime.solidworks.sketches import begin_sketch_on_plane, end_sketch
from cad_runtime.solidworks.units import mm


def log(message: str) -> None:
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}"
    print(line, flush=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with (LOG_DIR / "solidworks_modeling.log").open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def rebuild(model) -> None:
    result = rebuild_model(model)
    log(f"Rebuild result: {result}")


def clear(model) -> None:
    clear_selection(model)


def begin_sketch(model, plane: str) -> None:
    begin_sketch_on_plane(model, plane)
    log(f"Sketch started on {plane}")


def finish_sketch(model, name: str):
    selected = end_sketch(model, name)
    log(f"Sketch completed: {name}; selected as {selected}")
    return selected


def extrude_blind(model, name: str, depth: float):
    feature = extrude_boss(model, name, depth)
    log(f"Boss created: {name}, blind depth {depth} mm")
    return feature


def cut_through_all(model, name: str):
    # These profiles are drawn on the base plane while the solid extends in
    # positive Z. This SW2025 binding cuts into that solid with reverse=True.
    feature = extrude_cut_through_all(
        model,
        name,
        preferred_reverse_direction=True,
    )
    log(f"Cut created: {name}")
    return feature


def create_offset_plane(model, name: str, base: str, offset: float):
    select_plane(model, base)
    feature = model.FeatureManager.InsertRefPlane(8, mm(offset), 0, 0, 0, 0)
    if feature is None:
        raise RuntimeError(f"Datum plane failed: {name}")
    feature.Name = name
    rebuild(model)
    log(f"Datum created: {name}")


def body_count(model) -> int:
    bodies = model.GetBodies2(0, True)
    return len(bodies or [])


def select_edge_by_ray(model, x, y, z, dx, dy, dz, radius=1.5) -> bool:
    return bool(
        model.Extension.SelectByRay(
            mm(x), mm(y), mm(z),
            dx, dy, dz,
            mm(radius),
            1,
            True,
            0,
            0,
        )
    )


def create_r5_edge_fillet(model, overall_length, width, thickness):
    clear(model)
    x0 = -overall_length / 2
    x1 = overall_length / 2
    y0 = -width / 2
    y1 = width / 2
    z0 = 0
    z1 = thickness
    probes = [
        (0, y0, z1, 0, 1, 0),
        (0, y1, z1, 0, -1, 0),
        (0, y0, z0, 0, 1, 0),
        (0, y1, z0, 0, -1, 0),
        (x0, 0, z1, 1, 0, 0),
        (x1, 0, z1, -1, 0, 0),
        (x0, 0, z0, 1, 0, 0),
        (x1, 0, z0, -1, 0, 0),
    ]
    selected = 0
    for probe in probes:
        if select_edge_by_ray(model, *probe):
            selected += 1
    log(f"R5 edge selection count: {selected}")
    if selected < 4:
        raise RuntimeError("Could not select enough exposed edges for required R5 fillet")
    feature = model.FeatureManager.FeatureFillet3(
        195, mm(5), 0, 0, 0, 0, 0, 0,
        null_dispatch(), null_dispatch(), null_dispatch()
    )
    if feature is None:
        raise RuntimeError("Required R5 fillet feature failed")
    feature.Name = "EXPOSED_EDGE_FILLETS_R5"
    rebuild(model)
    log("Required R5 fillet created")


def save_exports(model):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths = [
        EXPORT_DIR / "upper_arm_link_v2.SLDPRT",
        EXPORT_DIR / "upper_arm_link_v2.STEP",
        EXPORT_DIR / "upper_arm_link_v2.x_t",
    ]
    for path in paths:
        save_as(model, str(path))
        if not path.exists():
            raise RuntimeError(f"Export missing after save: {path}")
        log(f"Saved: {path}")
    return paths


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / "solidworks_modeling.log").write_text("", encoding="utf-8")
    params_doc = json.loads(PLAN_FILE.read_text(encoding="utf-8"))
    values = {item["name"]: item["value"] for item in params_doc["parameters"]}

    center_distance = values["joint_center_distance"]
    width = values["section_width"]
    thickness = values["section_thickness"]
    end_diameter = values["joint_end_outer_diameter"]
    overall_length = values["overall_length"]
    hole_diameter = values["joint_hole_diameter"]
    window_length = values["lightening_window_length"]
    window_width = values["lightening_window_width"]
    window_radius = values["window_corner_radius"]
    rib_length = values["corner_rib_axial_length"]
    rib_width = values["corner_rib_base_width"]
    rib_total_height = values["corner_rib_total_height"]

    log("Connecting to SolidWorks in visible mode")
    sw = connect_solidworks(visible=True)
    template = sw.GetUserPreferenceStringValue(1)
    if not template or not Path(template).exists():
        candidates = [
            Path(r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\templates\gb_part.prtdot"),
            Path(r"C:\ProgramData\SolidWorks\SOLIDWORKS 2025\templates\gb_part.prtdot"),
        ]
        template = next((str(path) for path in candidates if path.exists()), "")
    if not template:
        raise RuntimeError("No usable SolidWorks part template was found")
    model = sw.NewDocument(template, 0, 0, 0)
    if model is None:
        raise RuntimeError("Failed to create part document")
    log(f"Created part from template: {template}")

    # Put the link midpoint at the origin. Joint centers are +/-210 mm on X.
    begin_sketch(model, "Top Plane")
    model.SketchManager.CreateCenterRectangle(
        0, 0, 0, mm(center_distance / 2), mm(width / 2), 0
    )
    finish_sketch(model, "SK_MAIN_WEB_420X90")
    extrude_blind(model, "BASE_LINK_BODY_40MM", thickness)

    begin_sketch(model, "Top Plane")
    for x in (-center_distance / 2, center_distance / 2):
        model.SketchManager.CreateCircle(
            mm(x), 0, 0, mm(x + end_diameter / 2), 0, 0
        )
    finish_sketch(model, "SK_END_BOSSES_D90")
    extrude_blind(model, "END_BOSSES_D90", thickness)

    begin_sketch(model, "Top Plane")
    for x in (-center_distance / 2, center_distance / 2):
        model.SketchManager.CreateCircle(mm(x), 0, 0, mm(x + hole_diameter / 2), 0, 0)
    finish_sketch(model, "SK_JOINT_HOLES_D40")
    cut_through_all(model, "JOINT_HOLES_D40_THROUGH")

    # Exact rounded rectangle as the union of two rectangles and four R12 circles.
    begin_sketch(model, "Top Plane")
    model.SketchManager.CreateCenterRectangle(
        0, 0, 0,
        mm((window_length - 2 * window_radius) / 2),
        mm(window_width / 2),
        0,
    )
    finish_sketch(model, "SK_WINDOW_VERTICAL_CORE")
    cut_through_all(model, "WINDOW_VERTICAL_CORE_THROUGH")

    begin_sketch(model, "Top Plane")
    model.SketchManager.CreateCenterRectangle(
        0, 0, 0,
        mm(window_length / 2),
        mm((window_width - 2 * window_radius) / 2),
        0,
    )
    finish_sketch(model, "SK_WINDOW_HORIZONTAL_CORE")
    cut_through_all(model, "WINDOW_HORIZONTAL_CORE_THROUGH")

    corner_x = window_length / 2 - window_radius
    corner_y = window_width / 2 - window_radius
    for sx in (-1, 1):
        for sy in (-1, 1):
            begin_sketch(model, "Top Plane")
            cx = sx * corner_x
            cy = sy * corner_y
            model.SketchManager.CreateCircle(
                mm(cx), mm(cy), 0, mm(cx + window_radius), mm(cy), 0
            )
            suffix = f"{'P' if sx > 0 else 'N'}X_{'P' if sy > 0 else 'N'}Y"
            finish_sketch(model, f"SK_WINDOW_CORNER_R12_{suffix}")
            cut_through_all(model, f"WINDOW_CORNER_R12_{suffix}_THROUGH")

    # Four rectangular rib pads centered around the window end-radius zones.
    begin_sketch(model, "Top Plane")
    rib_x = window_length / 2 - window_radius
    rib_y = window_width / 2 + rib_width / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx = sx * rib_x
            cy = sy * rib_y
            model.SketchManager.CreateCenterRectangle(
                mm(cx), mm(cy), 0,
                mm(cx + rib_length / 2), mm(cy + rib_width / 2), 0,
            )
    finish_sketch(model, "SK_WINDOW_CORNER_RIBS")
    extrude_blind(model, "WINDOW_CORNER_RIBS", thickness + rib_total_height)

    create_r5_edge_fillet(model, overall_length, width, thickness)

    create_offset_plane(model, "PLN_LINK_MID", "Top Plane", thickness / 2)
    create_offset_plane(model, "PLN_MOUNT_TOP", "Top Plane", thickness)
    create_offset_plane(model, "PLN_RIB_TOP", "Top Plane", thickness + rib_total_height)

    rebuild(model)
    count = body_count(model)
    log(f"Final solid body count: {count}")
    if count != 1:
        raise RuntimeError(f"Expected one solid body, got {count}")

    try:
        model.ViewZoomtofit2()
    except Exception:
        model.ViewZoomToFit2()
    paths = save_exports(model)
    result = {
        "status": "completed",
        "revision": 2,
        "solid_body_count": count,
        "files": [str(path) for path in paths],
        "simulation_executed": False,
    }
    (LOG_DIR / "solidworks_modeling_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log("SolidWorks modeling completed; document left open and visible")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        log(f"FAILED: {type(exc).__name__}: {exc}")
        raise
