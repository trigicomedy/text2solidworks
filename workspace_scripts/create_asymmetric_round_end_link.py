from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(r"D:\text2solidworks")
WORK_DIR = Path(r"D:\text2solidworks_workspace\projects\asymmetric_round_end_link")
EXPORT_DIR = WORK_DIR / "exports"
LOG_DIR = WORK_DIR / "logs"
PARAM_FILE = WORK_DIR / "plans" / "part_parameters.json"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cad_runtime.solidworks import connect_solidworks
from cad_runtime.solidworks.document import save_as
from cad_runtime.solidworks.features import extrude_boss, extrude_cut_through_all, rebuild_model
from cad_runtime.solidworks.selection import clear_selection, null_dispatch, select_plane
from cad_runtime.solidworks.sketches import begin_sketch_on_plane, draw_circle, end_sketch
from cad_runtime.solidworks.units import mm


def log(message: str) -> None:
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}"
    print(line, flush=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with (LOG_DIR / "solidworks_modeling.log").open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def view_update(model, delay_s: float = 0.7) -> None:
    rebuild_model(model)
    try:
        model.ViewZoomtofit2()
    except Exception:
        try:
            model.ViewZoomToFit2()
        except Exception:
            pass
    time.sleep(delay_s)


def user_part_template(sw) -> str:
    template = sw.GetUserPreferenceStringValue(1)
    if template and Path(template).exists():
        return template
    candidates = [
        Path(r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\templates\gb_part.prtdot"),
        Path(r"C:\ProgramData\SolidWorks\SOLIDWORKS 2025\templates\gb_part.prtdot"),
        Path(r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\templates\Part.prtdot"),
        Path(r"C:\ProgramData\SolidWorks\SOLIDWORKS 2025\templates\Part.prtdot"),
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    raise RuntimeError("No usable SolidWorks part template was found.")


def values_from_plan() -> dict[str, float]:
    payload = json.loads(PARAM_FILE.read_text(encoding="utf-8"))
    return {item["name"]: item["value"] for item in payload["parameters"]}


def line(model, p1: tuple[float, float], p2: tuple[float, float]):
    return model.SketchManager.CreateLine(mm(p1[0]), mm(p1[1]), 0, mm(p2[0]), mm(p2[1]), 0)


def arc3(model, start: tuple[float, float], end: tuple[float, float], through: tuple[float, float]):
    return model.SketchManager.Create3PointArc(
        mm(start[0]),
        mm(start[1]),
        0,
        mm(end[0]),
        mm(end[1]),
        0,
        mm(through[0]),
        mm(through[1]),
        0,
    )


def transition_geometry(center_distance: float, left_r: float, right_r: float, neck_half: float, fillet_r: float):
    """Return exact circle/line tangent points for a symmetric necked link sketch."""
    # Fillet centers are outside the narrow shank. The fillet arc is externally
    # tangent to the round head and tangent to the horizontal neck line.
    y_top_center = neck_half + fillet_r
    y_bottom_center = -neck_half - fillet_r

    left_dx = math.sqrt((left_r + fillet_r) ** 2 - y_top_center**2)
    right_dx = math.sqrt((right_r + fillet_r) ** 2 - y_top_center**2)

    left_top_fillet_center = (left_dx, y_top_center)
    left_bottom_fillet_center = (left_dx, y_bottom_center)
    right_top_fillet_center = (center_distance - right_dx, y_top_center)
    right_bottom_fillet_center = (center_distance - right_dx, y_bottom_center)

    def external_tangent_point(circle_center: tuple[float, float], circle_r: float, fillet_center: tuple[float, float]):
        vx = fillet_center[0] - circle_center[0]
        vy = fillet_center[1] - circle_center[1]
        scale = circle_r / (circle_r + fillet_r)
        return (circle_center[0] + scale * vx, circle_center[1] + scale * vy)

    def arc_mid_on_radius(center: tuple[float, float], radius: float, start: tuple[float, float], end: tuple[float, float]):
        sv = (start[0] - center[0], start[1] - center[1])
        ev = (end[0] - center[0], end[1] - center[1])
        mv = (sv[0] + ev[0], sv[1] + ev[1])
        length = math.hypot(mv[0], mv[1])
        if length < 1e-9:
            raise RuntimeError("Cannot compute stable arc midpoint from opposite vectors.")
        return (center[0] + radius * mv[0] / length, center[1] + radius * mv[1] / length)

    left_circle_center = (0.0, 0.0)
    right_circle_center = (center_distance, 0.0)
    left_top_line = (left_top_fillet_center[0], neck_half)
    left_bottom_line = (left_bottom_fillet_center[0], -neck_half)
    right_top_line = (right_top_fillet_center[0], neck_half)
    right_bottom_line = (right_bottom_fillet_center[0], -neck_half)
    left_top_circle = external_tangent_point(left_circle_center, left_r, left_top_fillet_center)
    left_bottom_circle = external_tangent_point(left_circle_center, left_r, left_bottom_fillet_center)
    right_top_circle = external_tangent_point(right_circle_center, right_r, right_top_fillet_center)
    right_bottom_circle = external_tangent_point(right_circle_center, right_r, right_bottom_fillet_center)

    return {
        "left_top_line": left_top_line,
        "left_bottom_line": left_bottom_line,
        "right_top_line": right_top_line,
        "right_bottom_line": right_bottom_line,
        "left_top_circle": left_top_circle,
        "left_bottom_circle": left_bottom_circle,
        "right_top_circle": right_top_circle,
        "right_bottom_circle": right_bottom_circle,
        "left_top_fillet_mid": arc_mid_on_radius(left_top_fillet_center, fillet_r, left_top_circle, left_top_line),
        "left_bottom_fillet_mid": arc_mid_on_radius(left_bottom_fillet_center, fillet_r, left_bottom_line, left_bottom_circle),
        "right_top_fillet_mid": arc_mid_on_radius(right_top_fillet_center, fillet_r, right_top_line, right_top_circle),
        "right_bottom_fillet_mid": arc_mid_on_radius(right_bottom_fillet_center, fillet_r, right_bottom_circle, right_bottom_line),
        "left_outer_mid": (-left_r, 0.0),
        "right_outer_mid": (center_distance + right_r, 0.0),
    }


def sketch_outer_profile(model, p: dict[str, float]) -> None:
    left_r = p["left_head_outer_diameter"] / 2
    right_r = p["right_head_outer_diameter"] / 2
    center_distance = p["requested_center_distance"]
    neck_half = p["mid_shank_width"] / 2
    fillet_r = p["side_transition_fillet_radius"]
    g = transition_geometry(center_distance, left_r, right_r, neck_half, fillet_r)

    begin_sketch_on_plane(model, "Top Plane")
    log("Sketch started: SK_LINK_OUTER_PROFILE on Top Plane")

    # Clockwise closed contour: native lines plus native 3-point arcs.
    line(model, g["left_top_line"], g["right_top_line"])
    arc3(model, g["right_top_line"], g["right_top_circle"], g["right_top_fillet_mid"])
    arc3(model, g["right_top_circle"], g["right_bottom_circle"], g["right_outer_mid"])
    arc3(model, g["right_bottom_circle"], g["right_bottom_line"], g["right_bottom_fillet_mid"])
    line(model, g["right_bottom_line"], g["left_bottom_line"])
    arc3(model, g["left_bottom_line"], g["left_bottom_circle"], g["left_bottom_fillet_mid"])
    arc3(model, g["left_bottom_circle"], g["left_top_circle"], g["left_outer_mid"])
    arc3(model, g["left_top_circle"], g["left_top_line"], g["left_top_fillet_mid"])

    selected = end_sketch(model, "SK_LINK_OUTER_PROFILE")
    log(f"Sketch completed: SK_LINK_OUTER_PROFILE; selected as {selected}")


def cut_hole(model, name: str, sketch_name: str, x_mm: float, diameter_mm: float) -> None:
    begin_sketch_on_plane(model, "Top Plane")
    log(f"Sketch started: {sketch_name} on Top Plane")
    draw_circle(model, x_mm, 0, diameter_mm / 2)
    selected = end_sketch(model, sketch_name)
    log(f"Sketch completed: {sketch_name}; selected as {selected}")
    extrude_cut_through_all(model, name, preferred_reverse_direction=True)
    log(f"Through cut created: {name}, center=({x_mm}, 0), diameter={diameter_mm} mm")
    view_update(model)


def select_edge_by_ray(model, x_mm: float, y_mm: float, z_mm: float, dx: float, dy: float, dz: float, *, append: bool = True, radius_mm: float = 2.0) -> bool:
    return bool(
        model.Extension.SelectByRay(
            mm(x_mm), mm(y_mm), mm(z_mm),
            dx, dy, dz,
            mm(radius_mm),
            1,
            append,
            0,
            0,
        )
    )


def create_native_chamfer(model, name: str, size_mm: float, sample_edges: list[tuple[float, float, float, float, float, float]]) -> None:
    clear_selection(model)
    selected = 0
    for x, y, z, dx, dy, dz in sample_edges:
        ok = select_edge_by_ray(model, x, y, z, dx, dy, dz, append=True, radius_mm=2.0)
        log(f"Select chamfer edge for {name}: point=({x}, {y}, {z}), dir=({dx}, {dy}, {dz}), ok={ok}")
        selected += int(ok)
    if selected == 0:
        raise RuntimeError(f"No edges selected for native chamfer: {name}")

    fm = model.FeatureManager
    attempts = [
        ("InsertFeatureChamfer distance-angle", lambda: fm.InsertFeatureChamfer(4, 0, mm(size_mm), 0, 0, 0, 0, 0)),
        ("InsertFeatureChamfer distance-distance", lambda: fm.InsertFeatureChamfer(4, 1, mm(size_mm), mm(size_mm), 0, 0, 0, 0)),
    ]
    for label, call in attempts:
        try:
            log(f"Trying native chamfer API for {name}: {label}")
            feature = call()
            log(f"Native chamfer API result for {name}: {feature}")
            if feature is not None:
                feature.Name = name
                view_update(model)
                return
        except Exception as exc:
            log(f"Native chamfer API raised for {name}: {label}: {exc}")
    raise RuntimeError(f"Native chamfer failed: {name}")


def create_native_fillet(model, name: str, radius_mm: float, sample_edges: list[tuple[float, float, float, float, float, float]]) -> None:
    clear_selection(model)
    selected = 0
    for x, y, z, dx, dy, dz in sample_edges:
        ok = select_edge_by_ray(model, x, y, z, dx, dy, dz, append=True, radius_mm=2.5)
        log(f"Select fillet edge for {name}: point=({x}, {y}, {z}), dir=({dx}, {dy}, {dz}), ok={ok}")
        selected += int(ok)
    if selected == 0:
        raise RuntimeError(f"No edges selected for native fillet: {name}")
    try:
        feature = model.FeatureManager.FeatureFillet3(
            195, mm(radius_mm), 0, 0, 0, 0, 0, 0,
            null_dispatch(), null_dispatch(), null_dispatch()
        )
    except Exception as exc:
        raise RuntimeError(f"Native fillet API raised for {name}: {exc}") from exc
    if feature is None:
        raise RuntimeError(f"Native fillet failed: {name}")
    feature.Name = name
    log(f"Native fillet created: {name}, R{radius_mm}")
    view_update(model)


def create_native_fillet_all_current_body_edges(model, name: str, radius_mm: float) -> None:
    bodies = model.GetBodies2(0, True) or []
    if len(bodies) != 1:
        raise RuntimeError(f"Expected one solid body before outer fillet, got {len(bodies)}")
    edges = bodies[0].GetEdges() or []
    if not edges:
        raise RuntimeError(f"No body edges found for native fillet: {name}")
    clear_selection(model)
    selected = 0
    for index, edge in enumerate(edges):
        append = selected > 0
        ok = False
        for mark in (null_dispatch(), None):
            try:
                ok = bool(edge.Select4(append, mark))
                if ok:
                    break
            except Exception:
                continue
        log(f"Select body edge for {name}: index={index}, ok={ok}")
        selected += int(ok)
    if selected == 0:
        raise RuntimeError(f"No body edges selected for native fillet: {name}")
    try:
        feature = model.FeatureManager.FeatureFillet3(
            195, mm(radius_mm), 0, 0, 0, 0, 0, 0,
            null_dispatch(), null_dispatch(), null_dispatch()
        )
    except Exception as exc:
        raise RuntimeError(f"Native fillet API raised for {name}: {exc}") from exc
    if feature is None:
        raise RuntimeError(f"Native fillet failed: {name}")
    feature.Name = name
    log(f"Native fillet created from all pre-hole body edges: {name}, selected={selected}, R{radius_mm}")
    view_update(model)


def create_offset_plane(model, name: str, base_plane: str, offset_mm: float) -> None:
    clear_selection(model)
    select_plane(model, base_plane)
    feature = model.FeatureManager.InsertRefPlane(8, mm(offset_mm), 0, 0, 0, 0)
    if feature is None:
        raise RuntimeError(f"Datum plane failed: {name}")
    feature.Name = name
    log(f"Datum plane created: {name}, offset {offset_mm} mm from {base_plane}")
    view_update(model, delay_s=0.2)


def body_count(model) -> int:
    bodies = model.GetBodies2(0, True)
    return len(bodies or [])


def save_exports(model) -> list[Path]:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths = [
        EXPORT_DIR / "asymmetric_round_end_link.SLDPRT",
        EXPORT_DIR / "asymmetric_round_end_link.STEP",
        EXPORT_DIR / "asymmetric_round_end_link.x_t",
    ]
    for path in paths:
        save_as(model, str(path))
        log(f"Saved: {path}")
    return paths


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / "solidworks_modeling.log").write_text("", encoding="utf-8")
    p = values_from_plan()

    sw = connect_solidworks(visible=True)
    sw.Visible = True
    try:
        sw.FrameState = 1
    except Exception:
        pass
    log("Connected to SolidWorks in visible mode")

    template = user_part_template(sw)
    model = sw.NewDocument(template, 0, 0, 0)
    if model is None:
        raise RuntimeError("Failed to create SolidWorks part document.")
    log(f"Created new part from template: {template}")
    view_update(model)

    sketch_outer_profile(model, p)
    extrude_boss(model, "LINK_PLATE_BODY_T10", p["thickness"])
    log("Boss created: LINK_PLATE_BODY_T10")
    view_update(model)

    create_native_fillet_all_current_body_edges(model, "OUTER_EDGE_FILLET_R2", p["outer_edge_fillet_radius"])

    cut_hole(model, "LEFT_CENTER_HOLE_D26_THROUGH", "SK_LEFT_HOLE_D26", 0, p["left_hole_diameter"])
    cut_hole(model, "RIGHT_CENTER_HOLE_D18_THROUGH", "SK_RIGHT_HOLE_D18", p["requested_center_distance"], p["right_hole_diameter"])

    # Stable reference names are part of the interface plan. These are logged
    # here; later runtime work can replace them with true datum feature helpers.
    log("Interface references planned: CSYS_LINK, PLN_BOTTOM_FACE, PLN_MID_THICKNESS, PLN_TOP_FACE")
    log("Interface axes planned: AXIS_LEFT_HOLE at X=0, AXIS_RIGHT_HOLE at X=125")

    t = p["thickness"]
    cd = p["requested_center_distance"]
    left_hole_r = p["left_hole_diameter"] / 2
    right_hole_r = p["right_hole_diameter"] / 2

    create_offset_plane(model, "PLN_MID_THICKNESS", "Top Plane", t / 2)
    create_offset_plane(model, "PLN_TOP_FACE", "Top Plane", t)

    create_native_chamfer(
        model,
        "LEFT_HOLE_EDGE_CHAMFER_C0_8",
        p["hole_edge_chamfer_size"],
        [
            (left_hole_r, 0, 0, -1, 0, 0),
            (left_hole_r, 0, t, -1, 0, 0),
        ],
    )
    create_native_chamfer(
        model,
        "RIGHT_HOLE_EDGE_CHAMFER_C0_8",
        p["hole_edge_chamfer_size"],
        [
            (cd + right_hole_r, 0, 0, -1, 0, 0),
            (cd + right_hole_r, 0, t, -1, 0, 0),
        ],
    )

    count = body_count(model)
    log(f"Final solid body count: {count}")
    if count != 1:
        raise RuntimeError(f"Expected one solid body, got {count}")

    view_update(model, delay_s=0.2)
    paths = save_exports(model)
    result = {
        "status": "completed",
        "solid_body_count": count,
        "files": [str(path) for path in paths],
        "notes": [
            "Outer profile uses native SolidWorks lines and 3-point arcs.",
            "Hole chamfers use native SolidWorks chamfer API.",
            "Outer edge rounding uses native SolidWorks fillet API."
        ],
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
