from __future__ import annotations

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(r"D:\text2solidworks")
WORK_DIR = Path(r"D:\text2solidworks_workspace\debug\assembly_foundation")
PART_DIR = WORK_DIR / "parts"
EXPORT_DIR = WORK_DIR / "exports"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cad_runtime.solidworks import (
    AssemblyRef,
    add_component,
    connect_solidworks,
    mate_coincident,
    mate_concentric,
    new_assembly,
    save_assembly,
    summarize_assembly,
)
from cad_runtime.solidworks.assembly_mates import add_mate_from_current_selection
from cad_runtime.solidworks.document import new_part, save_as
from cad_runtime.solidworks.features import extrude_boss, rebuild_model
from cad_runtime.solidworks.references import create_axis_from_cylindrical_face_by_ray, create_offset_plane
from cad_runtime.solidworks.selection import rename_selected_feature
from cad_runtime.solidworks.units import mm
from cad_runtime.solidworks.sketches import begin_sketch_on_plane, draw_circle, end_sketch


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def close_doc(sw, model) -> None:
    try:
        title_attr = getattr(model, "GetTitle", None)
        title = title_attr() if callable(title_attr) else title_attr
        if title:
            sw.CloseDoc(title)
    except Exception as exc:
        log(f"Close skipped: {exc}")


def create_test_part(sw, name: str, radius_mm: float, height_mm: float) -> Path:
    PART_DIR.mkdir(parents=True, exist_ok=True)
    model = new_part(sw, part_template(sw))
    log(f"Created part document: {name}")

    begin_sketch_on_plane(model, "Top Plane")
    draw_circle(model, 0, 0, radius_mm)
    end_sketch(model, f"SK_{name}_CYLINDER")
    extrude_boss(model, f"{name}_CYLINDER", height_mm)

    create_offset_plane(model, "MATE_PLANE", "Top Plane", 0.01)
    create_axis_from_cylindrical_face_by_ray(
        model,
        "MATE_AXIS",
        (radius_mm, 0, height_mm / 2, -1, 0, 0),
        selection_radius_mm=3,
    )
    # Some SW2025 COM paths create the axis but return a bool. If the new axis
    # remains selected, this best-effort rename makes the assembly ref stable.
    rename_selected_feature(model, "MATE_AXIS")
    try:
        name_cylindrical_face(model, "MATE_CYL_FACE", radius_mm, height_mm)
    except Exception as exc:
        log(f"Cylindrical face naming skipped: {exc}")
    rebuild_model(model)

    path = PART_DIR / f"{name}.SLDPRT"
    save_as(model, str(path))
    log(f"Saved part: {path}")
    close_doc(sw, model)
    return path


def name_cylindrical_face(model, name: str, radius_mm: float, height_mm: float) -> None:
    model.ClearSelection2(True)
    ok = model.Extension.SelectByRay(
        mm(radius_mm), 0.0, mm(height_mm / 2),
        -1, 0, 0,
        mm(3),
        2,
        False,
        0,
        0,
    )
    if not ok:
        raise RuntimeError(f"Failed to select cylindrical face for naming: {name}")
    face = model.SelectionManager.GetSelectedObject6(1, -1)
    if face is None:
        raise RuntimeError(f"Selected cylindrical face object is empty: {name}")
    set_name = getattr(model.Extension, "SetEntityName", None)
    if not callable(set_name):
        raise RuntimeError("SolidWorks Extension.SetEntityName is not available.")
    result = set_name(face, name)
    if result is False:
        raise RuntimeError(f"Failed to name cylindrical face: {name}")


def part_template(sw) -> str:
    import os

    env_path = os.environ.get("TEXT2SW_PART_TEMPLATE")
    if env_path and Path(env_path).exists():
        return env_path
    try:
        pref = sw.GetUserPreferenceStringValue(1)
        if pref and Path(pref).exists():
            return pref
    except Exception:
        pass
    for root in (Path(r"C:\ProgramData\SOLIDWORKS"), Path(r"C:\ProgramData\SolidWorks")):
        if not root.exists():
            continue
        for name in ("gb_part.prtdot", "Part.prtdot"):
            matches = list(root.rglob(name))
            if matches:
                return str(matches[0])
    raise RuntimeError("No SolidWorks part template found.")


def build_validation_assembly(sw, part_a: Path, part_b: Path) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    asm = new_assembly(sw)
    log("Created assembly document")

    comp_a = add_component(sw, asm, part_a, name="part_a", xyz_mm=(0, 0, 0))
    comp_a_name = str(getattr(comp_a, "Name2", "assembly_part_a-1"))
    log(f"Inserted component A: {comp_a_name}")
    comp_b = add_component(sw, asm, part_b, name="part_b", xyz_mm=(80, 0, 0))
    comp_b_name = str(getattr(comp_b, "Name2", "assembly_part_b-1"))
    log(f"Inserted component B: {comp_b_name}")

    plane_a = AssemblyRef(comp_a_name, "plane", "MATE_PLANE")
    plane_b = AssemblyRef(comp_b_name, "plane", "MATE_PLANE")
    mate1 = mate_coincident(asm, "MATE_PLANE_COINCIDENT", plane_a, plane_b)
    log(f"Created coincident mate via {mate1.api}, status={mate1.status}")
    select_cylindrical_faces_by_ray(asm)
    mate2 = add_mate_from_current_selection(asm, "MATE_AXIS_CONCENTRIC", "concentric")
    log(f"Created concentric mate via {mate2.api}, status={mate2.status}")

    try:
        asm.ViewZoomtofit2()
    except Exception:
        pass

    path = EXPORT_DIR / "assembly_foundation_validation.SLDASM"
    save_assembly(asm, path)
    summary = summarize_assembly(asm)
    result = {
        "assembly": str(path),
        "parts": [str(part_a), str(part_b)],
        "summary": {
            "component_count": summary.component_count,
            "mate_count": summary.mate_count,
            "component_names": summary.component_names,
        },
        "mates": [mate1.name, mate2.name],
    }
    (WORK_DIR / "assembly_foundation_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log(f"Saved assembly: {path}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return path


def select_cylindrical_faces_by_ray(asm) -> None:
    asm.ClearSelection2(True)
    first = asm.Extension.SelectByRay(
        mm(20), 0.0, mm(10),
        -1, 0, 0,
        mm(5),
        2,
        False,
        0,
        0,
    )
    second = asm.Extension.SelectByRay(
        mm(96), 0.0, mm(15),
        -1, 0, 0,
        mm(5),
        2,
        True,
        0,
        0,
    )
    if not first or not second:
        raise RuntimeError(f"Failed to select cylindrical faces by ray: first={first}, second={second}")


def main() -> int:
    sw = connect_solidworks(visible=True)
    sw.Visible = True
    try:
        sw.FrameState = 1
    except Exception:
        pass

    part_a = create_test_part(sw, "assembly_part_a", 20, 20)
    part_b = create_test_part(sw, "assembly_part_b", 16, 30)
    build_validation_assembly(sw, part_a, part_b)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
