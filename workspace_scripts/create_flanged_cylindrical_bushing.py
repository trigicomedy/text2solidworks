from __future__ import annotations

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(r"D:\text2solidworks")
WORK_DIR = Path(r"D:\text2solidworks_workspace\projects\flanged_cylindrical_bushing")
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
from cad_runtime.solidworks.edge_treatments import (
    EdgeSignature,
    EdgeTreatmentRegistry,
    circular_edge_signature,
)
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


def begin_sketch(model, plane_name: str, label: str) -> None:
    begin_sketch_on_plane(model, plane_name)
    log(f"Sketch started: {label} on {plane_name}")


def finish_sketch(model, sketch_name: str) -> str:
    selected = end_sketch(model, sketch_name)
    log(f"Sketch completed: {sketch_name}; selected as {selected}")
    return selected


def circle_boss(model, plane_name: str, sketch_name: str, feature_name: str, diameter_mm: float, depth_mm: float) -> None:
    begin_sketch(model, plane_name, sketch_name)
    draw_circle(model, 0, 0, diameter_mm / 2)
    finish_sketch(model, sketch_name)
    extrude_boss(model, feature_name, depth_mm)
    log(f"Boss created: {feature_name}, diameter {diameter_mm} mm, depth {depth_mm} mm")
    view_update(model)


def circle_cut(model, plane_name: str, sketch_name: str, feature_name: str, x_mm: float, y_mm: float, diameter_mm: float) -> None:
    begin_sketch(model, plane_name, sketch_name)
    draw_circle(model, x_mm, y_mm, diameter_mm / 2)
    finish_sketch(model, sketch_name)
    extrude_cut_through_all(model, feature_name, preferred_reverse_direction=True)
    log(f"Cut created: {feature_name}, diameter {diameter_mm} mm")
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


def select_circular_edge(
    model,
    radius_mm: float,
    z_mm: float,
    *,
    outer: bool,
    append: bool = True,
    mode: str = "radial",
) -> bool:
    if mode == "from_above":
        return select_edge_by_ray(model, radius_mm, 0, z_mm + 2.0, 0, 0, -1, append=append)
    if outer:
        return select_edge_by_ray(model, radius_mm + 1.0, 0, z_mm, -1, 0, 0, append=append)
    return select_edge_by_ray(model, 0, 0, z_mm, 1, 0, 0, append=append)


def edge_tuple_to_signature(edge: tuple[float, float, bool] | tuple[float, float, bool, str]) -> EdgeSignature:
    edge_radius, z, outer = edge[:3]
    mode = edge[3] if len(edge) > 3 else "radial"
    return circular_edge_signature(edge_radius, z, outer=outer, mode=mode)


def create_fillet(
    model,
    registry: EdgeTreatmentRegistry,
    name: str,
    radius_mm: float,
    edges: list[tuple[float, float, bool] | tuple[float, float, bool, str]],
    *,
    required: bool = False,
) -> bool:
    planned = [edge_tuple_to_signature(edge) for edge in edges]
    allowed = registry.filter_untreated(
        planned,
        operation="fillet",
        feature_name=name,
        required=required,
        log=log,
    )
    if not allowed:
        if required:
            raise RuntimeError(f"No untreated planned edges remain for fillet: {name}")
        return False

    clear_selection(model)
    selected = 0
    selected_signatures = []
    for signature in allowed:
        outer = signature.kind == "outer_circular_edge"
        if select_circular_edge(model, signature.radius_mm, signature.z_mm, outer=outer, append=True, mode=signature.mode):
            selected += 1
            selected_signatures.append(signature)
            log(f"Selected fillet edge for {name}: {signature.label()}")
        else:
            log(f"Failed to select fillet edge for {name}: {signature.label()}")
    log(f"Fillet edge selection count for {name}: {selected}")
    if selected == 0:
        if required:
            raise RuntimeError(f"No edges selected for fillet: {name}")
        return False
    try:
        feature = model.FeatureManager.FeatureFillet3(
            195, mm(radius_mm), 0, 0, 0, 0, 0, 0,
            null_dispatch(), null_dispatch(), null_dispatch()
        )
    except Exception as exc:
        log(f"Fillet API raised for {name}: {exc}")
        return False
    if feature is None:
        return False
    feature.Name = name
    registry.mark_treated(selected_signatures, operation="fillet", feature_name=name)
    registry.blacklist_generated_edges(name)
    log(f"Fillet created: {name}, R{radius_mm}")
    view_update(model)
    return True


def try_chamfer_call(model, size_mm: float):
    fm = model.FeatureManager
    attempts = [
        ("InsertFeatureChamfer distance-angle verified", lambda: fm.InsertFeatureChamfer(4, 0, mm(size_mm), 0, 0, 0, 0, 0)),
        ("InsertFeatureChamfer distance-distance fallback", lambda: fm.InsertFeatureChamfer(4, 1, mm(size_mm), mm(size_mm), 0, 0, 0, 0)),
    ]
    last_error = None
    for api_name, call in attempts:
        try:
            log(f"Trying chamfer API: {api_name}")
            feature = call()
            log(f"Chamfer API {api_name} result: {feature}")
            if feature is not None:
                return feature
        except Exception as exc:
            last_error = exc
            log(f"Chamfer API {api_name} raised: {exc}")
    if last_error:
        log(f"Last chamfer error: {last_error}")
    return None


def create_chamfer(
    model,
    registry: EdgeTreatmentRegistry,
    name: str,
    size_mm: float,
    edges: list[tuple[float, float, bool] | tuple[float, float, bool, str]],
    *,
    required: bool,
) -> bool:
    planned = [edge_tuple_to_signature(edge) for edge in edges]
    allowed = registry.filter_untreated(
        planned,
        operation="chamfer",
        feature_name=name,
        required=required,
        log=log,
    )
    if not allowed:
        if required:
            raise RuntimeError(f"No untreated planned edges remain for chamfer: {name}")
        return False

    clear_selection(model)
    selected = 0
    selected_signatures = []
    for signature in allowed:
        outer = signature.kind == "outer_circular_edge"
        if select_circular_edge(model, signature.radius_mm, signature.z_mm, outer=outer, append=True, mode=signature.mode):
            selected += 1
            selected_signatures.append(signature)
            log(f"Selected chamfer edge for {name}: {signature.label()}")
        else:
            log(f"Failed to select chamfer edge for {name}: {signature.label()}")
    log(f"Chamfer edge selection count for {name}: {selected}")
    if selected == 0:
        if required:
            raise RuntimeError(f"No edges selected for chamfer: {name}")
        return False
    feature = try_chamfer_call(model, size_mm)
    if feature is None:
        if required:
            raise RuntimeError(f"Native chamfer feature failed: {name}")
        return False
    feature.Name = name
    registry.mark_treated(selected_signatures, operation="chamfer", feature_name=name)
    registry.blacklist_generated_edges(name)
    log(f"Chamfer created: {name}, C{size_mm}")
    view_update(model)
    return True


def body_count(model) -> int:
    bodies = model.GetBodies2(0, True)
    return len(bodies or [])


def save_exports(model) -> list[Path]:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths = [
        EXPORT_DIR / "flanged_cylindrical_bushing_v1.SLDPRT",
        EXPORT_DIR / "flanged_cylindrical_bushing_v1.STEP",
        EXPORT_DIR / "flanged_cylindrical_bushing_v1.x_t",
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

    flange_od = values["flange_outer_diameter"]
    flange_thickness = values["flange_thickness"]
    body_od = values["body_outer_diameter"]
    body_length = values["body_length"]
    total_length = values["total_length"]
    bore_diameter = values["center_bore_diameter"]
    bolt_count = values["bolt_hole_count"]
    bolt_diameter = values["bolt_hole_diameter"]
    bolt_pcd = values["bolt_pitch_circle_diameter"]
    right_chamfer = values["right_outer_chamfer_size"]
    bore_chamfer = values["center_bore_end_chamfer_size"]
    flange_fillet = values["flange_outer_edge_fillet_radius"]
    planned_edge_treatments = [
        circular_edge_signature(flange_od / 2, 0, outer=True),
        circular_edge_signature(flange_od / 2, flange_thickness, outer=True),
        circular_edge_signature(body_od / 2, total_length, outer=True, mode="from_above"),
        circular_edge_signature(bore_diameter / 2, 0, outer=False, mode="radial"),
        circular_edge_signature(bore_diameter / 2, total_length, outer=False, mode="from_above"),
    ]
    edge_registry = EdgeTreatmentRegistry(planned_edge_treatments)

    log("Connecting to SolidWorks in visible mode")
    sw = connect_solidworks(visible=True)
    try:
        sw.Visible = True
        sw.FrameState = 1
    except Exception:
        pass

    template = user_part_template(sw)
    model = sw.NewDocument(template, 0, 0, 0)
    if model is None:
        raise RuntimeError("Failed to create part document.")
    log(f"Created part from template: {template}")
    view_update(model)

    circle_boss(model, "Top Plane", "SK_FLANGE_OD80", "FLANGE_CYLINDER_OD80_T10", flange_od, flange_thickness)

    select_plane(model, "Top Plane")
    plane = model.FeatureManager.InsertRefPlane(8, mm(flange_thickness), 0, 0, 0, 0)
    if plane is not None:
        plane.Name = "PLN_FLANGE_BACK"
        log("Datum created: PLN_FLANGE_BACK")
        view_update(model)

    circle_boss(model, "PLN_FLANGE_BACK", "SK_BODY_OD45", "BUSHING_BODY_OD45_L60", body_od, body_length)

    circle_cut(model, "Top Plane", "SK_CENTER_BORE_D24", "CENTER_BORE_D24_THROUGH", 0, 0, bore_diameter)

    bolt_radius = bolt_pcd / 2
    for i in range(int(bolt_count)):
        angle = 360 / bolt_count * i
        if i == 0:
            x, y = bolt_radius, 0
        elif i == 1:
            x, y = 0, bolt_radius
        elif i == 2:
            x, y = -bolt_radius, 0
        else:
            x, y = 0, -bolt_radius
        circle_cut(
            model,
            "Top Plane",
            f"SK_BOLT_HOLE_{int(angle)}_D8",
            f"BOLT_HOLE_{int(angle)}_D8_THROUGH_FLANGE",
            x,
            y,
            bolt_diameter,
        )

    create_fillet(
        model,
        edge_registry,
        "FLANGE_OUTER_EDGE_FILLET_R1_5",
        flange_fillet,
        [(flange_od / 2, 0, True), (flange_od / 2, flange_thickness, True)],
    )

    create_chamfer(
        model,
        edge_registry,
        "RIGHT_OUTER_CHAMFER_C2",
        right_chamfer,
        [(body_od / 2, total_length, True, "from_above")],
        required=True,
    )
    create_chamfer(
        model,
        edge_registry,
        "CENTER_BORE_LEFT_RIGHT_CHAMFER_C1",
        bore_chamfer,
        [(bore_diameter / 2, 0, False, "radial"), (bore_diameter / 2, total_length, False, "from_above")],
        required=True,
    )

    count = body_count(model)
    log(f"Final solid body count: {count}")
    log(f"Edge treatment registry: {json.dumps(edge_registry.records(), ensure_ascii=False)}")
    if count != 1:
        raise RuntimeError(f"Expected one solid body, got {count}")

    try:
        material = getattr(model, "SetMaterialPropertyName2", None)
        if callable(material):
            material("", "", "Plain Carbon Steel")
            log("Material assignment attempted: Plain Carbon Steel")
    except Exception as exc:
        log(f"Material assignment skipped: {exc}")

    view_update(model, delay_s=0.2)
    paths = save_exports(model)
    result = {
        "status": "completed",
        "solid_body_count": count,
        "files": [str(path) for path in paths],
        "notes": [
            "Chamfer features are attempted with native SolidWorks chamfer APIs.",
            "If a chamfer API is unavailable in this COM binding, the model remains generated and the log records the failure."
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
