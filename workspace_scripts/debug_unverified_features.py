from __future__ import annotations

import json
import sys
import time
import argparse
from pathlib import Path

PROJECT_ROOT = Path(r"D:\text2solidworks")
WORK_DIR = Path(r"D:\text2solidworks_workspace\debug\unverified_features")
EXPORT_DIR = WORK_DIR / "exports"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cad_runtime.solidworks import connect_solidworks
from cad_runtime.solidworks.document import save_as
from cad_runtime.solidworks.edge_features import chamfer_all_current_body_edges
from cad_runtime.solidworks.features import extrude_boss, rebuild_model
from cad_runtime.solidworks.holes import cut_blind_hole
from cad_runtime.solidworks.references import (
    create_axis_from_cylindrical_face_by_ray,
    create_axis_from_two_planes,
    create_coordinate_system_from_selection,
    create_offset_plane,
)
from cad_runtime.solidworks.selection import clear_selection, null_dispatch, select_plane
from cad_runtime.solidworks.sketch_dimensions import add_smart_dimension
from cad_runtime.solidworks.sketch_entities import (
    draw_3point_arc,
    draw_centerline,
    draw_centerpoint_straight_slot,
    draw_circle,
    draw_ellipse,
    draw_line,
    draw_polygon,
    draw_spline,
    draw_text,
)
from cad_runtime.solidworks.sketch_relations import add_horizontal
from cad_runtime.solidworks.sketches import begin_sketch_on_plane, end_sketch
from cad_runtime.solidworks.structural_features import rib_from_selected_sketch
from cad_runtime.solidworks.thin_wall_features import shell_selected_faces
from cad_runtime.solidworks.transform_features import mirror_feature
from cad_runtime.solidworks.curves import insert_helix_from_selected_circle
from cad_runtime.solidworks.units import mm
from cad_runtime.solidworks.views import export_named_view_images


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def template(sw) -> str:
    path = sw.GetUserPreferenceStringValue(1)
    if path and Path(path).exists():
        return path
    for candidate in [
        Path(r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\templates\gb_part.prtdot"),
        Path(r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\templates\Part.prtdot"),
    ]:
        if candidate.exists():
            return str(candidate)
    raise RuntimeError("No SolidWorks part template found.")


def new_part(sw, label: str):
    model = sw.NewDocument(template(sw), 0, 0, 0)
    if model is None:
        raise RuntimeError(f"Failed to create part: {label}")
    log(f"New part: {label}")
    return model


def view(model):
    rebuild_model(model)
    try:
        model.ViewZoomtofit2()
    except Exception:
        pass
    time.sleep(0.4)


def save(model, label: str):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / f"{label}.SLDPRT"
    save_as(model, str(path))
    view_dir = WORK_DIR / "views" / label
    try:
        export_named_view_images(model, view_dir, pause_s=0.05)
    except Exception as exc:
        log(f"view export skipped for {label}: {exc}")
    log(f"Saved: {path}")
    return str(path)


def close_active_doc(sw) -> None:
    try:
        model = sw.ActiveDoc
        if model is None:
            return
        title_attr = getattr(model, "GetTitle", None)
        title = title_attr() if callable(title_attr) else title_attr
        if not title:
            path_attr = getattr(model, "GetPathName", None)
            path = path_attr() if callable(path_attr) else path_attr
            title = Path(path).name if path else None
        if title:
            sw.CloseDoc(title)
            log(f"Closed document: {title}")
    except Exception as exc:
        log(f"Close document skipped: {exc}")


def run_case(sw, results: dict, name: str, func):
    try:
        path = func()
        results[name] = {"status": "ok", "file": path}
    except Exception as exc:
        log(f"FAILED {name}: {type(exc).__name__}: {exc}")
        results[name] = {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
    finally:
        close_active_doc(sw)


def select_entity(entity, append=False):
    for mark in (null_dispatch(), None):
        try:
            if entity.Select4(append, mark):
                return True
        except Exception:
            continue
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="Run only selected cases, for example: --only mirror shell rib helix",
    )
    args = parser.parse_args()

    sw = connect_solidworks(visible=True)
    sw.Visible = True
    try:
        sw.FrameState = 1
    except Exception:
        pass
    results = {}

    def sketch_entities_case():
        model = new_part(sw, "sketch_entities")
        begin_sketch_on_plane(model, "Top Plane")
        draw_line(model, (-45, -25), (45, -25))
        draw_centerline(model, (-45, 0), (45, 0))
        draw_3point_arc(model, (-35, 15), (0, 15), (-18, 28))
        draw_polygon(model, (30, 18), (42, 18), 6)
        draw_ellipse(model, (-20, -5), (-5, -5), (-20, 5))
        try:
            draw_spline(model, [(-45, 25), (-30, 32), (-15, 24), (0, 30)])
        except Exception as exc:
            log(f"spline failed but continuing: {exc}")
        try:
            draw_text(model, "SW", (10, -5), 6)
        except Exception as exc:
            log(f"sketch text failed but continuing: {exc}")
        try:
            draw_centerpoint_straight_slot(model, (25, -15), (45, -15), 6)
        except Exception as exc:
            log(f"slot failed but continuing: {exc}")
        end_sketch(model, "SK_SKETCH_ENTITY_TEST")
        view(model)
        return save(model, "sketch_entities_test")

    def sketch_relations_dimensions_case():
        model = new_part(sw, "sketch_relations_dimensions")
        begin_sketch_on_plane(model, "Top Plane")
        line = draw_line(model, (-25, 0), (25, 0))
        clear_selection(model)
        if not select_entity(line, append=False):
            raise RuntimeError("Failed to select line for relation/dimension")
        add_horizontal(model)
        clear_selection(model)
        if not select_entity(line, append=False):
            raise RuntimeError("Failed to reselect line for dimension")
        add_smart_dimension(model, "D_LINE_LENGTH_50", (0, 12), None)
        end_sketch(model, "SK_RELATION_DIMENSION_TEST")
        view(model)
        return save(model, "sketch_relations_dimensions_test")

    def chamfer_case():
        model = new_part(sw, "edge_chamfer")
        begin_sketch_on_plane(model, "Top Plane")
        model.SketchManager.CreateCenterRectangle(0, 0, 0, mm(40), mm(25), 0)
        end_sketch(model, "SK_CHAMFER_BLOCK")
        extrude_boss(model, "CHAMFER_BLOCK", 18)
        chamfer_all_current_body_edges(model, "ALL_EDGE_CHAMFER_C1", 1)
        view(model)
        return save(model, "edge_chamfer_test")

    def blind_hole_case():
        model = new_part(sw, "blind_hole")
        begin_sketch_on_plane(model, "Top Plane")
        model.SketchManager.CreateCenterRectangle(0, 0, 0, mm(35), mm(25), 0)
        end_sketch(model, "SK_BLIND_HOLE_BLOCK")
        extrude_boss(model, "BLIND_HOLE_BLOCK", 25)
        cut_blind_hole(model, "BLIND_HOLE_D10_DEPTH8", "Top Plane", (0, 0), 10, 8, reverse_direction=True)
        view(model)
        return save(model, "blind_hole_test")

    def references_case():
        model = new_part(sw, "references")
        begin_sketch_on_plane(model, "Top Plane")
        draw_circle(model, (0, 0), 15)
        end_sketch(model, "SK_REFERENCE_CYL")
        extrude_boss(model, "REFERENCE_CYL", 30)
        create_offset_plane(model, "PLN_MID", "Top Plane", 15)
        create_axis_from_two_planes(model, "AXIS_FRONT_RIGHT", "Front Plane", "Right Plane")
        create_axis_from_cylindrical_face_by_ray(model, "AXIS_CYLINDER", (15, 0, 10, -1, 0, 0))
        view(model)
        return save(model, "references_test")

    def mirror_case():
        model = new_part(sw, "mirror")
        begin_sketch_on_plane(model, "Top Plane")
        model.SketchManager.CreateCenterRectangle(mm(20), 0, 0, mm(30), mm(10), 0)
        end_sketch(model, "SK_MIRROR_SEED")
        extrude_boss(model, "MIRROR_SEED_BOSS", 10)
        mirror_feature(model, "MIRROR_SEED_ACROSS_RIGHT", "MIRROR_SEED_BOSS", "Right Plane")
        view(model)
        return save(model, "mirror_test")

    def shell_case():
        model = new_part(sw, "shell")
        begin_sketch_on_plane(model, "Top Plane")
        model.SketchManager.CreateCenterRectangle(0, 0, 0, mm(30), mm(20), 0)
        end_sketch(model, "SK_SHELL_BLOCK")
        extrude_boss(model, "SHELL_BLOCK", 25)
        clear_selection(model)
        ok = model.Extension.SelectByRay(0, 0, mm(25), 0, 0, -1, mm(5), 2, False, 0, 0)
        if not ok:
            raise RuntimeError("Failed to select top face for shell")
        shell_selected_faces(model, "SHELL_TEST_T2", 2)
        view(model)
        return save(model, "shell_test")

    def rib_case():
        model = new_part(sw, "rib")
        begin_sketch_on_plane(model, "Top Plane")
        model.SketchManager.CreateCenterRectangle(0, 0, 0, mm(40), mm(25), 0)
        end_sketch(model, "SK_RIB_BASE")
        extrude_boss(model, "RIB_BASE", 8)
        begin_sketch_on_plane(model, "Front Plane")
        draw_line(model, (-25, 8), (25, 8))
        end_sketch(model, "SK_RIB_LINE")
        rib_from_selected_sketch(model, "RIB_TEST_T3", 3)
        view(model)
        return save(model, "rib_test")

    def helix_case():
        model = new_part(sw, "helix")
        begin_sketch_on_plane(model, "Top Plane")
        draw_circle(model, (0, 0), 10)
        end_sketch(model, "SK_HELIX_CIRCLE")
        insert_helix_from_selected_circle(model, "HELIX_TEST", 4, 30)
        view(model)
        return save(model, "helix_test")

    cases = [
        ("sketch_entities", sketch_entities_case),
        ("sketch_relations_dimensions", sketch_relations_dimensions_case),
        ("edge_chamfer", chamfer_case),
        ("blind_hole", blind_hole_case),
        ("references", references_case),
        ("mirror", mirror_case),
        ("shell", shell_case),
        ("rib", rib_case),
        ("helix", helix_case),
    ]
    selected = set(args.only) if args.only else None
    for name, func in cases:
        if selected is not None and name not in selected:
            continue
        run_case(sw, results, name, func)

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    result_path = WORK_DIR / "unverified_features_result.json"
    result_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(item["status"] == "ok" for item in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
