from __future__ import annotations

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(r"D:\text2solidworks")
WORK_DIR = Path(r"D:\text2solidworks_workspace\debug\assembly_core_features")
PART_DIR = WORK_DIR / "parts"
EXPORT_DIR = WORK_DIR / "exports"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cad_runtime.solidworks import (
    AssemblyRef,
    add_component,
    check_interference,
    connect_solidworks,
    create_revolute_joint,
    create_subassembly,
    fix_component_in_assembly,
    float_component_in_assembly,
    insert_subassembly,
    mate_angle,
    mate_coincident,
    mate_distance,
    mate_parallel,
    move_component,
    new_assembly,
    save_assembly,
    set_component_transform,
    summarize_assembly,
)
from cad_runtime.solidworks.document import new_part, save_as
from cad_runtime.solidworks.features import extrude_boss, rebuild_model
from cad_runtime.solidworks.references import create_axis_from_cylindrical_face_by_ray, create_offset_plane
from cad_runtime.solidworks.sketches import begin_sketch_on_plane, draw_circle, end_sketch


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def close_doc(sw, model) -> None:
    try:
        title_attr = getattr(model, "GetTitle", None)
        title = title_attr() if callable(title_attr) else title_attr
        if title:
            sw.CloseDoc(title)
    except Exception:
        pass


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
        if root.exists():
            for name in ("gb_part.prtdot", "Part.prtdot"):
                matches = list(root.rglob(name))
                if matches:
                    return str(matches[0])
    raise RuntimeError("No SolidWorks part template found.")


def create_part(sw, name: str, radius_mm: float, height_mm: float) -> Path:
    PART_DIR.mkdir(parents=True, exist_ok=True)
    model = new_part(sw, part_template(sw))
    begin_sketch_on_plane(model, "Top Plane")
    draw_circle(model, 0, 0, radius_mm)
    end_sketch(model, f"SK_{name}_CYL")
    extrude_boss(model, f"{name}_CYL", height_mm)
    create_offset_plane(model, "MATE_PLANE", "Top Plane", 0.01)
    create_offset_plane(model, "MATE_FRONT", "Front Plane", 0.01)
    create_offset_plane(model, "MATE_RIGHT", "Right Plane", 0.01)
    create_axis_from_cylindrical_face_by_ray(
        model,
        "MATE_AXIS",
        (radius_mm, 0, height_mm / 2, -1, 0, 0),
        selection_radius_mm=3,
    )
    rebuild_model(model)
    path = PART_DIR / f"{name}.SLDPRT"
    save_as(model, str(path))
    close_doc(sw, model)
    return path


def save_case_assembly(asm, name: str) -> str:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / f"{name}.SLDASM"
    save_assembly(asm, path)
    return str(path)


def run_case(results: dict, name: str, func):
    try:
        log(f"CASE start: {name}")
        results[name] = {"status": "ok", **func()}
        log(f"CASE ok: {name}")
    except Exception as exc:
        results[name] = {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
        log(f"CASE failed: {name}: {exc}")


def component_ref(component, entity_type: str, ref_name: str) -> AssemblyRef:
    return AssemblyRef(str(getattr(component, "Name2", "")), entity_type, ref_name)


def main() -> int:
    sw = connect_solidworks(visible=True)
    sw.Visible = True
    try:
        sw.FrameState = 1
    except Exception:
        pass

    part_a = create_part(sw, "core_part_a", 20, 20)
    part_b = create_part(sw, "core_part_b", 16, 30)
    results: dict = {"parts": [str(part_a), str(part_b)]}

    def case_initial_placement_fix_float():
        asm = new_assembly(sw)
        comp = add_component(sw, asm, part_a, name="tf_part", xyz_mm=(30, 20, 10))
        fix_result = fix_component_in_assembly(asm, comp)
        float_result = float_component_in_assembly(asm, comp)
        return {
            "assembly": save_case_assembly(asm, "initial_placement_fix_float"),
            "fix_result": str(fix_result),
            "float_result": str(float_result),
        }

    def case_dynamic_transform_probe():
        asm = new_assembly(sw)
        comp = add_component(sw, asm, part_a, name="dynamic_tf_part", xyz_mm=(0, 0, 0))
        errors = []
        for label, call in [
            ("set_component_transform", lambda: set_component_transform(sw, comp, (30, 20, 10), (0, 0, 20))),
            ("move_component", lambda: move_component(sw, comp, (40, 10, 0))),
        ]:
            try:
                errors.append(f"{label}: ok {call()}")
            except Exception as exc:
                errors.append(f"{label}: {type(exc).__name__}: {exc}")
        return {
            "assembly": save_case_assembly(asm, "dynamic_transform_probe"),
            "status_note": "needs_macro_if_errors_show_type_mismatch",
            "attempts": errors,
        }

    def case_distance_parallel_angle():
        output = {}
        asm = new_assembly(sw)
        a = add_component(sw, asm, part_a, name="dist_a", xyz_mm=(0, 0, 0))
        b = add_component(sw, asm, part_b, name="dist_b", xyz_mm=(60, 0, 0))
        output["distance"] = str(mate_distance(
            asm,
            "MATE_DISTANCE_40",
            component_ref(a, "plane", "MATE_PLANE"),
            component_ref(b, "plane", "MATE_PLANE"),
            40,
        ))
        output["assembly_distance"] = save_case_assembly(asm, "distance_mate")

        asm = new_assembly(sw)
        a = add_component(sw, asm, part_a, name="parallel_a", xyz_mm=(0, 0, 0))
        b = add_component(sw, asm, part_b, name="parallel_b", xyz_mm=(60, 0, 0))
        output["parallel"] = str(mate_parallel(
            asm,
            "MATE_PARALLEL_FRONT",
            component_ref(a, "plane", "MATE_FRONT"),
            component_ref(b, "plane", "MATE_FRONT"),
        ))
        output["assembly_parallel"] = save_case_assembly(asm, "parallel_mate")

        asm = new_assembly(sw)
        a = add_component(sw, asm, part_a, name="angle_a", xyz_mm=(0, 0, 0))
        b = add_component(sw, asm, part_b, name="angle_b", xyz_mm=(60, 0, 0))
        output["angle"] = str(mate_angle(
            asm,
            "MATE_ANGLE_20",
            component_ref(a, "plane", "MATE_FRONT"),
            component_ref(b, "plane", "MATE_FRONT"),
            20,
        ))
        output["assembly_angle"] = save_case_assembly(asm, "angle_mate")
        return output

    def case_revolute_joint():
        asm = new_assembly(sw)
        a = add_component(sw, asm, part_a, name="rev_a", xyz_mm=(0, 0, 0))
        b = add_component(sw, asm, part_b, name="rev_b", xyz_mm=(60, 0, 0))
        joint = create_revolute_joint(
            asm,
            "J_TEST",
            component_ref(a, "axis", "MATE_AXIS"),
            component_ref(b, "axis", "MATE_AXIS"),
            plane_a=component_ref(a, "plane", "MATE_PLANE"),
            plane_b=component_ref(b, "plane", "MATE_PLANE"),
            limit_deg=(-90, 90),
        )
        return {"assembly": save_case_assembly(asm, "revolute_joint"), "joint": str(joint)}

    def case_subassembly():
        sub_path = EXPORT_DIR / "validated_subassembly.SLDASM"
        create_subassembly(sw, sub_path, [{"path": str(part_a), "name": "sub_part_a", "xyz_mm": (0, 0, 0)}])
        asm = new_assembly(sw)
        comp = insert_subassembly(sw, asm, sub_path, name="subasm_component", xyz_mm=(20, 0, 0))
        return {"subassembly": str(sub_path), "top_assembly": save_case_assembly(asm, "subassembly_insert"), "component": str(getattr(comp, "Name2", ""))}

    def case_mate_status():
        asm = new_assembly(sw)
        a = add_component(sw, asm, part_a, name="status_a", xyz_mm=(0, 0, 0))
        b = add_component(sw, asm, part_b, name="status_b", xyz_mm=(60, 0, 0))
        mate_coincident(asm, "MATE_STATUS_PLANE", component_ref(a, "plane", "MATE_PLANE"), component_ref(b, "plane", "MATE_PLANE"))
        summary = summarize_assembly(asm)
        return {
            "assembly": save_case_assembly(asm, "mate_status"),
            "component_count": summary.component_count,
            "mate_count": summary.mate_count,
            "component_names": summary.component_names,
        }

    def case_interference():
        asm = new_assembly(sw)
        add_component(sw, asm, part_a, name="interfere_a", xyz_mm=(0, 0, 0))
        add_component(sw, asm, part_b, name="interfere_b", xyz_mm=(0, 0, 0))
        result = check_interference(asm)
        return {"assembly": save_case_assembly(asm, "interference_check"), "interference": str(result)}

    for name, func in [
        ("initial_placement_fix_float", case_initial_placement_fix_float),
        ("dynamic_transform_probe", case_dynamic_transform_probe),
        ("distance_parallel_angle_mates", case_distance_parallel_angle),
        ("revolute_joint", case_revolute_joint),
        ("subassembly", case_subassembly),
        ("mate_status", case_mate_status),
        ("interference", case_interference),
    ]:
        run_case(results, name, func)

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    result_path = WORK_DIR / "assembly_core_features_result.json"
    result_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(v.get("status") == "ok" for k, v in results.items() if k != "parts") else 1


if __name__ == "__main__":
    raise SystemExit(main())
