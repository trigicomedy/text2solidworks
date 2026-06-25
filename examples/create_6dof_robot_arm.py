from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import os
import json
import pythoncom
import win32com.client
import math
from pathlib import Path
from typing import Iterable

from cad_runtime.solidworks import connect_solidworks
from cad_runtime.solidworks.document import save_as
from cad_runtime.solidworks.units import mm

WORKSPACE = Path(r"D:\text2solidworks_workspace")
OUT_DIR = WORKSPACE / "exports" / "robot_arm_6dof"
PART_DIR = OUT_DIR / "parts"
PLAN_DIR = WORKSPACE / "plans"
SKETCH_COUNTERS = {}

PLANE_ALIASES = {
    "Top Plane": ["Top Plane", "\u4e0a\u89c6\u57fa\u51c6\u9762", "\u4e0a\u57fa\u51c6\u9762"],
    "Front Plane": ["Front Plane", "\u524d\u89c6\u57fa\u51c6\u9762", "\u524d\u57fa\u51c6\u9762"],
    "Right Plane": ["Right Plane", "\u53f3\u89c6\u57fa\u51c6\u9762", "\u53f3\u57fa\u51c6\u9762"],
}


PART_NAMES = [
    "base",
    "J1_housing",
    "shoulder_housing",
    "upper_arm",
    "elbow_housing",
    "forearm",
    "wrist_roll_housing",
    "wrist_pitch_housing",
    "wrist_yaw_housing",
    "gripper_palm",
    "left_finger",
    "right_finger",
]

PARAMS = {
    "total_height_mm": 600,
    "max_reach_mm": 500,
    "base_flange_diameter_mm": 160,
    "base_height_mm": 60,
    "j1_diameter_mm": 90,
    "j1_height_mm": 70,
    "shoulder_diameter_mm": 100,
    "shoulder_width_mm": 80,
    "upper_arm_length_mm": 220,
    "upper_arm_section_mm": [60, 45],
    "elbow_diameter_mm": 80,
    "elbow_width_mm": 70,
    "forearm_length_mm": 200,
    "forearm_section_mm": [50, 38],
    "wrist_length_mm": 120,
    "wrist_module_diameter_mm": 55,
    "gripper_palm_mm": [60, 45, 35],
    "finger_length_mm": 100,
    "finger_width_mm": 15,
    "finger_thickness_mm": 12,
    "finger_gap_mm": 40,
}










def null_dispatch():
    """Typed null IDispatch for SolidWorks API arguments that reject Python None."""
    return win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)

def model_key(model):
    try:
        return model.GetPathName() or model.GetTitle() or str(id(model))
    except Exception:
        return str(id(model))


def select_latest_generated_sketch(model, max_index: int = 50):
    # Search newest likely generated sketch name first. This avoids maintaining
    # fragile counters across many newly created, unsaved part documents.
    for index in range(max_index, 0, -1):
        for sketch_name in (f"\u8349\u56fe{index}", f"Sketch{index}"):
            try:
                ok = model.Extension.SelectByID2(sketch_name, "SKETCH", 0.0, 0.0, 0.0, False, 0, null_dispatch(), 0)
                if ok:
                    print(f"[DEBUG] select sketch {sketch_name!r}: {ok}")
                    return sketch_name
            except Exception as exc:
                print(f"[WARN] select sketch {sketch_name!r} failed: {exc}")
    print("[DEBUG] select latest sketch: no generated sketch name matched")
    return None


def iter_features(model):
    """Iterate features using whichever entry point SW exposes through COM."""
    first = None
    for method_name in ("FirstFeature", "IFirstFeature"):
        try:
            method = getattr(model, method_name, None)
            if callable(method):
                first = method()
                if first is not None:
                    break
        except Exception:
            first = None

    if first is not None:
        feat = first
        seen = set()
        while feat is not None:
            ident = id(feat)
            if ident in seen:
                break
            seen.add(ident)
            yield feat
            next_feat = None
            for method_name in ("GetNextFeature", "IGetNextFeature"):
                try:
                    method = getattr(feat, method_name, None)
                    if callable(method):
                        next_feat = method()
                        break
                except Exception:
                    next_feat = None
            feat = next_feat
        return

    try:
        feats = model.FeatureManager.GetFeatures(False)
    except Exception:
        feats = None
    for feat in feats or []:
        yield feat


def feature_type(feature):
    try:
        return feature.GetTypeName2()
    except Exception:
        try:
            return feature.GetTypeName()
        except Exception:
            return ""


def last_sketch_feature(model):
    last = None
    for feat in iter_features(model):
        if feature_type(feat) in {"ProfileFeature", "3DProfileFeature"}:
            last = feat
    return last


def rename_and_select_last_sketch(model, sketch_name: str):
    sketch_feat = last_sketch_feature(model)
    if sketch_feat is None:
        return None
    try:
        sketch_feat.Name = sketch_name
    except Exception:
        pass
    try:
        model.ClearSelection2(True)
        sketch_feat.Select2(False, 0)
    except Exception:
        pass
    return sketch_feat

def rebuild_model(model):
    """Rebuild model with compatibility across SolidWorks COM bindings."""
    try:
        rebuild = getattr(model, "ForceRebuild3", None)
        if callable(rebuild):
            return rebuild(False)
    except Exception:
        pass
    try:
        rebuild = getattr(model, "EditRebuild3", None)
        if callable(rebuild):
            return rebuild()
    except Exception:
        pass
    return None

def user_template(sw, kind: str) -> str:
    """Return a SolidWorks template path for a part or assembly."""
    env_name = {
        "part": "TEXT2SW_PART_TEMPLATE",
        "assembly": "TEXT2SW_ASSEMBLY_TEMPLATE",
    }[kind]
    env_path = os.environ.get(env_name)
    if env_path and Path(env_path).exists():
        return env_path

    pref = {"part": 1, "assembly": 2}[kind]
    template = sw.GetUserPreferenceStringValue(pref)
    if template and Path(template).exists():
        return template

    filenames = {
        "part": ["gb_part.prtdot", "Part.prtdot"],
        "assembly": ["gb_assembly.asmdot", "Assembly.asmdot"],
    }[kind]
    roots = [
        Path(r"C:\ProgramData\SOLIDWORKS"),
        Path(r"C:\ProgramData\SolidWorks"),
    ]
    candidates = []
    for root in roots:
        if root.exists():
            for filename in filenames:
                candidates.extend(root.glob(f"**/{filename}"))

    if candidates:
        candidates = sorted(candidates, key=lambda p: ("2025" not in str(p), str(p)))
        return str(candidates[0])

    example = r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\templates\gb_part.prtdot"
    raise RuntimeError(
        f"No SolidWorks {kind} template found. Set {env_name} to your template path. "
        f"Example: {example}"
    )

def new_doc(sw, template: str):
    model = sw.NewDocument(template, 0, 0, 0)
    if model is None:
        raise RuntimeError(f"Failed to create SolidWorks document from template: {template}")
    return model


def clear(model):
    model.ClearSelection2(True)


def select_plane(model, canonical_name: str):
    clear(model)
    for name in PLANE_ALIASES.get(canonical_name, [canonical_name]):
        ok = model.Extension.SelectByID2(name, "PLANE", 0.0, 0.0, 0.0, False, 0, null_dispatch(), 0)
        print(f"[DEBUG] select plane {name!r}: {ok}")
        if ok:
            return name
    raise RuntimeError(f"Cannot select plane: {canonical_name}. Tried {PLANE_ALIASES.get(canonical_name)}")


def begin_sketch(model, plane: str):
    select_plane(model, plane)
    model.SketchManager.InsertSketch(True)


def end_sketch(model, name: str):
    # Exit the active sketch, then select the newest generated sketch in this
    # document. Chinese SW templates commonly use ??1, ??2, etc.
    model.SketchManager.InsertSketch(True)
    rebuild_model(model)
    selected = select_latest_generated_sketch(model)
    if selected is None:
        rename_and_select_last_sketch(model, name)


def extrude_boss(model, name: str, depth_mm: float):
    # end_sketch() leaves the newly created sketch selected. Do not reselect
    # through feature-tree traversal here; SW2025 pywin32 may expose feature
    # traversal inconsistently and can disturb the valid selection state.
    print(f"[DEBUG] extrude_boss {name}: trying FeatureExtrusion2")
    feat = model.FeatureManager.FeatureExtrusion2(
        True, False, False,
        0, 0,
        mm(depth_mm), 0,
        False, False, False, False,
        0, 0,
        False, False, False, False,
        True, True, True,
        0, 0,
        False,
    )
    print(f"[DEBUG] extrude_boss {name}: result={feat}")
    if feat is None:
        raise RuntimeError(f"Failed to extrude feature: {name}")
    feat.Name = name
    rebuild_model(model)
    return feat


def cut_through_all(model, name: str, required: bool = False):
    # end_sketch() leaves the newly created cut profile selected. Try several
    # cut APIs because signatures vary across SolidWorks versions/bindings.
    attempts = []

    def cut4():
        return model.FeatureManager.FeatureCut4(
            True, False, False,
            1, 0,
            0, 0,
            False, False, False, False,
            0, 0,
            False, False, False, False,
            False, True, True, True, True,
            False,
            0, 0,
            False, False,
        )

    attempts.append(("FeatureCut4", cut4))

    def cut3():
        return model.FeatureManager.FeatureCut3(
            True, False, False,
            1, 0,
            0, 0,
            False, False, False, False,
            0, 0,
            False, False, False, False,
            False, True, True, True, True,
            False,
            0, 0,
            False,
        )

    attempts.append(("FeatureCut3", cut3))

    last_error = None
    for api_name, fn in attempts:
        try:
            print(f"[DEBUG] cut_through_all {name}: trying {api_name}")
            feat = fn()
            print(f"[DEBUG] cut_through_all {name}: {api_name} result={feat}")
            if feat is not None:
                feat.Name = name
                rebuild_model(model)
                return feat
        except Exception as exc:
            last_error = exc
            print(f"[WARN] cut_through_all {name}: {api_name} raised {exc}")

    message = f"Failed to cut feature: {name}"
    if last_error:
        message += f"; last error: {last_error}"
    if required:
        raise RuntimeError(message)
    print(f"[WARN] {message}; continuing without this cut")
    return None


def add_simple_fillet(model, radius_mm: float):
    # Fillet API signatures vary by version. This best-effort call is deliberately optional.
    try:
        model.FeatureManager.FeatureFillet3(195, mm(radius_mm), 0, 0, 0, 0, 0, 0, None, None, None)
        rebuild_model(model)
    except Exception:
        pass


def circle_profile(model, plane: str, radius_mm: float, sketch_name: str):
    begin_sketch(model, plane)
    r = mm(radius_mm)
    model.SketchManager.CreateCircle(0, 0, 0, r, 0, 0)
    end_sketch(model, sketch_name)


def rect_profile(model, plane: str, width_mm: float, height_mm: float, sketch_name: str):
    begin_sketch(model, plane)
    model.SketchManager.CreateCenterRectangle(0, 0, 0, mm(width_mm) / 2, mm(height_mm) / 2, 0)
    end_sketch(model, sketch_name)




def save_part_and_close(sw, model, path: Path) -> Path:
    save_as(model, str(path))
    try:
        title = model.GetTitle()
        sw.CloseDoc(title)
    except Exception:
        pass
    return path


def set_component_translation(sw, comp, xyz_mm: tuple[float, float, float]):
    try:
        math_util = sw.GetMathUtility()
        x, y, z = (mm(v) for v in xyz_mm)
        # 4x4 identity transform in row-major order. Translation occupies
        # elements 9..11 in SolidWorks MathTransform array data.
        data = [
            1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 1.0,
            x, y, z,
            1.0, 0.0, 0.0, 0.0,
        ]
        transform = math_util.CreateTransform(data)
        try:
            comp.Transform2 = transform
        except Exception:
            comp.SetTransformAndSolve2(transform)
    except Exception as exc:
        print(f"[WARN] set component transform failed for {comp}: {exc}")



def create_offset_ref_plane(model, name: str, base_plane: str, offset_mm: float):
    try:
        select_plane(model, base_plane)
        feat = model.FeatureManager.InsertRefPlane(8, mm(offset_mm), 0, 0, 0, 0)
        if feat is not None:
            feat.Name = name
            rebuild_model(model)
            print(f"[DEBUG] datum plane {name}: offset {offset_mm} mm from {base_plane}")
            return feat
    except Exception as exc:
        print(f"[WARN] datum plane {name} failed: {exc}")
    return None


def create_axis_sketch(model, name: str, plane: str, half_length_mm: float = 50):
    try:
        begin_sketch(model, plane)
        h = mm(half_length_mm)
        try:
            line = model.SketchManager.CreateCenterLine(-h, 0.0, 0.0, h, 0.0, 0.0)
        except Exception:
            line = model.SketchManager.CreateLine(-h, 0.0, 0.0, h, 0.0, 0.0)
        end_sketch(model, name)
        print(f"[DEBUG] datum axis sketch {name}: {line}")
        return line
    except Exception as exc:
        print(f"[WARN] datum axis sketch {name} failed: {exc}")
    return None


def create_center_point_sketch(model, name: str, plane: str):
    try:
        begin_sketch(model, plane)
        point = model.SketchManager.CreatePoint(0.0, 0.0, 0.0)
        end_sketch(model, name)
        print(f"[DEBUG] datum center point sketch {name}: {point}")
        return point
    except Exception as exc:
        print(f"[WARN] datum center point sketch {name} failed: {exc}")
    return None


def add_linear_part_datums(model, part_name: str, base_plane: str, length_mm: float, axis_sketch_plane: str, axis_half_length_mm: float):
    # These are first-pass assembly interfaces. They are intentionally simple
    # and visible in the feature tree; later runtime work can promote them to
    # true reference axes/coordinate systems and mate references.
    create_offset_ref_plane(model, f"{part_name}_start_plane", base_plane, 0.01)
    create_offset_ref_plane(model, f"{part_name}_mid_plane", base_plane, length_mm / 2)
    create_offset_ref_plane(model, f"{part_name}_end_plane", base_plane, length_mm)
    create_axis_sketch(model, f"{part_name}_center_axis_sketch", axis_sketch_plane, axis_half_length_mm)
    create_center_point_sketch(model, f"{part_name}_origin_point_sketch", base_plane)


def create_cylinder(sw, name: str, diameter_mm: float, length_mm: float, axis: str = "Z") -> Path:
    model = new_doc(sw, user_template(sw, "part"))
    plane = {"Z": "Top Plane", "X": "Right Plane", "Y": "Front Plane"}[axis]
    circle_profile(model, plane, diameter_mm / 2, f"{name}_circle_sketch")
    extrude_boss(model, f"{name}_cylindrical_body", length_mm)
    add_simple_fillet(model, 3)
    axis_plane = {"Z": "Top Plane", "X": "Right Plane", "Y": "Front Plane"}[axis]
    sketch_plane = {"Z": "Front Plane", "X": "Top Plane", "Y": "Right Plane"}[axis]
    add_linear_part_datums(model, name, axis_plane, length_mm, sketch_plane, max(diameter_mm, length_mm) / 2)
    path = PART_DIR / f"{name}.SLDPRT"
    return save_part_and_close(sw, model, path)


def create_box(sw, name: str, size_mm: tuple[float, float, float], axis: str = "Z", fillet_mm: float = 3) -> Path:
    model = new_doc(sw, user_template(sw, "part"))
    x, y, z = size_mm
    if axis == "X":
        rect_profile(model, "Right Plane", y, z, f"{name}_section_sketch")
        extrude_boss(model, f"{name}_body", x)
    elif axis == "Y":
        rect_profile(model, "Front Plane", x, z, f"{name}_section_sketch")
        extrude_boss(model, f"{name}_body", y)
    else:
        rect_profile(model, "Top Plane", x, y, f"{name}_section_sketch")
        extrude_boss(model, f"{name}_body", z)
    add_simple_fillet(model, fillet_mm)
    base_plane = {"X": "Right Plane", "Y": "Front Plane", "Z": "Top Plane"}[axis]
    sketch_plane = {"X": "Top Plane", "Y": "Right Plane", "Z": "Front Plane"}[axis]
    length = {"X": x, "Y": y, "Z": z}[axis]
    add_linear_part_datums(model, name, base_plane, length, sketch_plane, max(x, y, z) / 2)
    path = PART_DIR / f"{name}.SLDPRT"
    return save_part_and_close(sw, model, path)


def create_base(sw) -> Path:
    p = PARAMS
    model = new_doc(sw, user_template(sw, "part"))
    circle_profile(model, "Top Plane", p["base_flange_diameter_mm"] / 2, "base_flange_sketch")
    extrude_boss(model, "base_flange", 18)

    circle_profile(model, "Top Plane", 48, "base_column_sketch")
    extrude_boss(model, "base_column", p["base_height_mm"])

    begin_sketch(model, "Top Plane")
    bolt_radius = 65
    for i in range(6):
        a = 2 * math.pi * i / 6
        x = mm(bolt_radius * math.cos(a))
        y = mm(bolt_radius * math.sin(a))
        r = mm(3.4)
        model.SketchManager.CreateCircle(x, y, 0, x + r, y, 0)
    end_sketch(model, "base_m6_clearance_hole_sketch")
    cut_through_all(model, "base_m6_clearance_holes")

    add_simple_fillet(model, 4)
    create_offset_ref_plane(model, "base_flange_top_plane", "Top Plane", 18)
    create_offset_ref_plane(model, "base_top_mount_plane", "Top Plane", p["base_height_mm"])
    create_axis_sketch(model, "base_J1_axis_sketch", "Front Plane", p["base_height_mm"] / 2)
    create_center_point_sketch(model, "base_J1_center_point_sketch", "Top Plane")
    path = PART_DIR / "base.SLDPRT"
    return save_part_and_close(sw, model, path)


def create_link(sw, name: str, length_mm: float, section_mm: tuple[float, float], cable_cover: bool = True) -> Path:
    model = new_doc(sw, user_template(sw, "part"))
    width, height = section_mm
    rect_profile(model, "Right Plane", width, height, f"{name}_rounded_rect_section")
    extrude_boss(model, f"{name}_main_link", length_mm)
    add_simple_fillet(model, 6)

    if cable_cover:
        # A narrow external routing cover as a simple raised strip on the link side.
        rect_profile(model, "Right Plane", 8, height * 0.65, f"{name}_cable_cover_section")
        extrude_boss(model, f"{name}_cable_routing_cover", length_mm * 0.78)
        add_simple_fillet(model, 2)

    add_linear_part_datums(model, name, "Right Plane", length_mm, "Top Plane", length_mm / 2)
    create_offset_ref_plane(model, f"{name}_proximal_mount_plane", "Right Plane", 0.01)
    create_offset_ref_plane(model, f"{name}_distal_mount_plane", "Right Plane", length_mm)
    path = PART_DIR / f"{name}.SLDPRT"
    return save_part_and_close(sw, model, path)


def create_gripper_finger(sw, name: str) -> Path:
    p = PARAMS
    model = new_doc(sw, user_template(sw, "part"))
    rect_profile(model, "Right Plane", p["finger_width_mm"], p["finger_thickness_mm"], f"{name}_finger_section")
    extrude_boss(model, f"{name}_finger_body", p["finger_length_mm"])
    circle_profile(model, "Right Plane", p["finger_width_mm"] / 2, f"{name}_rounded_tip_sketch")
    extrude_boss(model, f"{name}_rounded_tip", p["finger_thickness_mm"])
    add_simple_fillet(model, 3)
    add_linear_part_datums(model, name, "Right Plane", p["finger_length_mm"], "Top Plane", p["finger_length_mm"] / 2)
    create_offset_ref_plane(model, f"{name}_mount_plane", "Right Plane", 0.01)
    path = PART_DIR / f"{name}.SLDPRT"
    return save_part_and_close(sw, model, path)




def select_component_ref(asm, comp, part_name: str, ref_name: str, ref_type: str = "PLANE", append: bool = False):
    try:
        comp_name = comp.Name2
    except Exception:
        comp_name = f"{part_name}-1"

    try:
        asm_title = asm.GetTitle()
        asm_stem = Path(str(asm_title)).stem
    except Exception:
        asm_title = ""
        asm_stem = ""

    # In this SW2025 setup, references inside components select successfully as:
    #   ref_name@ComponentInstance@AssemblyTitle
    # Try the known-good forms first to avoid pages of expected False probes.
    patterns = []
    if asm_title:
        patterns.append(f"{ref_name}@{comp_name}@{asm_title}")
    if asm_stem and asm_stem != asm_title:
        patterns.append(f"{ref_name}@{comp_name}@{asm_stem}")
    patterns.extend([
        f"{ref_name}@{comp_name}",
        f"{ref_name}@{part_name}@{comp_name}",
        f"{ref_name}@{part_name}-1@{comp_name}",
    ])

    ref_types = [ref_type]
    for typ in ("PLANE", "DATUMPLANE", ""):
        if typ not in ref_types:
            ref_types.append(typ)

    probes = 0
    for full_name in dict.fromkeys(patterns):
        for typ in ref_types:
            probes += 1
            try:
                ok = asm.Extension.SelectByID2(full_name, typ, 0.0, 0.0, 0.0, append, 0, null_dispatch(), 0)
                if ok:
                    print(f"[DEBUG] select ref OK {full_name!r} type={typ!r} probes={probes}")
                    return full_name
            except Exception as exc:
                print(f"[WARN] select ref {full_name!r} type={typ!r} failed: {exc}")
    print(f"[WARN] select ref failed {part_name}.{ref_name}; tried {probes} probes")
    return None


def add_coincident_mate(asm, label: str):
    attempts = []

    def mate5():
        status = byref_i4(0)
        mate = asm.AddMate5(
            0, 0, False,
            0.0, 0.0, 0.0,
            0.0, 0.0,
            0.0, 0.0, 0.0,
            False, False,
            0,
            status,
        )
        return mate, status.value

    attempts.append(("AddMate5", mate5))

    def mate3():
        status = byref_i4(0)
        mate = asm.AddMate3(
            0, 0, False,
            0.0, 0.0, 0.0,
            0.0, 0.0,
            0.0, 0.0, 0.0,
            False,
            status,
        )
        return mate, status.value

    attempts.append(("AddMate3", mate3))

    def mate2():
        status = byref_i4(0)
        mate = asm.AddMate2(
            0, 0, False,
            0.0, 0.0, 0.0,
            0.0, 0.0,
            0.0, 0.0, 0.0,
            False,
            status,
        )
        return mate, status.value

    attempts.append(("AddMate2", mate2))

    for api_name, fn in attempts:
        try:
            mate, status = fn()
            print(f"[DEBUG] mate {label}: {api_name} result={mate}, status={status}")
            if mate is not None:
                try:
                    mate.Name = label
                except Exception:
                    pass
                return mate
        except Exception as exc:
            print(f"[WARN] mate {label}: {api_name} failed: {exc}")
    return None


def mate_planes_coincident(asm, comps: dict, a_part: str, a_ref: str, b_part: str, b_ref: str, label: str):
    asm.ClearSelection2(True)
    a = select_component_ref(asm, comps[a_part], a_part, a_ref, "PLANE", False)
    b = select_component_ref(asm, comps[b_part], b_part, b_ref, "PLANE", True)
    if not a or not b:
        print(f"[WARN] mate {label}: could not select both refs ({a_part}.{a_ref}, {b_part}.{b_ref})")
        asm.ClearSelection2(True)
        return None
    mate = add_coincident_mate(asm, label)
    asm.ClearSelection2(True)
    return mate


def apply_first_pass_plane_mates(asm, comps: dict):
    # First pass: plane mates only. This validates reference selection and mate
    # creation before we add true axes/coordinate-system mates.
    specs = [
        ("base", "base_top_mount_plane", "J1_housing", "J1_housing_start_plane", "mate_base_to_J1"),
        ("J1_housing", "J1_housing_end_plane", "shoulder_housing", "shoulder_housing_start_plane", "mate_J1_to_shoulder"),
        ("shoulder_housing", "shoulder_housing_end_plane", "upper_arm", "upper_arm_proximal_mount_plane", "mate_shoulder_to_upper_arm"),
        ("upper_arm", "upper_arm_distal_mount_plane", "elbow_housing", "elbow_housing_start_plane", "mate_upper_arm_to_elbow"),
        ("elbow_housing", "elbow_housing_end_plane", "forearm", "forearm_proximal_mount_plane", "mate_elbow_to_forearm"),
        ("forearm", "forearm_distal_mount_plane", "wrist_roll_housing", "wrist_roll_housing_start_plane", "mate_forearm_to_wrist_roll"),
        ("wrist_roll_housing", "wrist_roll_housing_end_plane", "wrist_pitch_housing", "wrist_pitch_housing_start_plane", "mate_wrist_roll_to_pitch"),
        ("wrist_pitch_housing", "wrist_pitch_housing_end_plane", "wrist_yaw_housing", "wrist_yaw_housing_start_plane", "mate_wrist_pitch_to_yaw"),
        ("wrist_yaw_housing", "wrist_yaw_housing_end_plane", "gripper_palm", "gripper_palm_start_plane", "mate_wrist_yaw_to_palm"),
        ("gripper_palm", "gripper_palm_end_plane", "left_finger", "left_finger_mount_plane", "mate_palm_to_left_finger"),
        ("gripper_palm", "gripper_palm_end_plane", "right_finger", "right_finger_mount_plane", "mate_palm_to_right_finger"),
    ]
    made = []
    for a_part, a_ref, b_part, b_ref, label in specs:
        mate = mate_planes_coincident(asm, comps, a_part, a_ref, b_part, b_ref, label)
        if mate is not None:
            made.append(label)
    print(f"[DEBUG] first-pass mates created: {made}")
    return made




def byref_i4(value: int = 0):
    return win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, value)


def open_part_silent(sw, path: Path):
    errors = byref_i4(0)
    warnings = byref_i4(0)
    attempts = []

    def open_silent():
        return sw.OpenDoc6(str(path), 1, 1, "", errors, warnings)

    attempts.append(("OpenDoc6 silent", open_silent))

    def open_normal():
        return sw.OpenDoc6(str(path), 1, 0, "", errors, warnings)

    attempts.append(("OpenDoc6 normal", open_normal))

    for label, fn in attempts:
        try:
            doc = fn()
            print(f"[DEBUG] {label} {path}: doc={doc}, errors={errors.value}, warnings={warnings.value}")
            if doc is not None:
                return doc
        except Exception as exc:
            print(f"[WARN] {label} failed for {path}: {exc}")
    return None


def activate_doc(sw, title: str):
    try:
        errors = byref_i4(0)
        doc = sw.ActivateDoc3(title, False, 0, errors)
        print(f"[DEBUG] activate doc {title!r}: doc={doc}, errors={errors.value}")
        return doc
    except Exception as exc:
        print(f"[WARN] ActivateDoc3 failed for {title!r}: {exc}")
        try:
            doc = sw.ActivateDoc2(title, False, 0)
            print(f"[DEBUG] activate doc2 {title!r}: doc={doc}")
            return doc
        except Exception as exc2:
            print(f"[WARN] ActivateDoc2 failed for {title!r}: {exc2}")
    return None


def add_component(sw, asm, name: str, path: Path, xyz_mm: tuple[float, float, float]):
    x, y, z = (mm(v) for v in xyz_mm)
    comp = None

    try:
        asm_title = asm.GetTitle()
    except Exception:
        asm_title = None

    attempts = []

    def add5_path():
        return asm.AddComponent5(str(path), 0, "", False, "", x, y, z)

    attempts.append(("AddComponent5(path)", add5_path))

    def add_path():
        return asm.AddComponent(str(path), x, y, z)

    attempts.append(("AddComponent(path)", add_path))

    open_part_silent(sw, path)
    if asm_title:
        activate_doc(sw, asm_title)

    def add5_opened():
        return asm.AddComponent5(str(path), 0, "", False, "", x, y, z)

    attempts.append(("AddComponent5(opened path)", add5_opened))

    def add_opened():
        return asm.AddComponent(str(path), x, y, z)

    attempts.append(("AddComponent(opened path)", add_opened))

    for label, fn in attempts:
        try:
            result = fn()
            print(f"[DEBUG] insert {name}: {label} result={result}")
            # pywin32 may return False for failure; only COM objects count.
            if result not in (None, False):
                comp = result
                break
        except Exception as exc:
            print(f"[WARN] insert {name}: {label} failed: {exc}")

    if comp is None:
        raise RuntimeError(f"Failed to insert component {path}")

    try:
        comp.Name2 = name
    except Exception:
        pass
    set_component_translation(sw, comp, xyz_mm)
    print(f"[DEBUG] inserted component {name} at {xyz_mm} mm")
    return comp


def create_assembly(sw, parts: dict[str, Path]) -> Path:
    p = PARAMS
    asm = new_doc(sw, user_template(sw, "assembly"))

    z_base = 0
    z_j1 = p["base_height_mm"]
    z_shoulder = z_j1 + p["j1_height_mm"]
    x_upper = 35
    x_elbow = x_upper + p["upper_arm_length_mm"]
    x_forearm = x_elbow + 25
    x_wrist = x_forearm + p["forearm_length_mm"]
    x_gripper = x_wrist + p["wrist_length_mm"]

    placements = {
        "base": (0, 0, z_base),
        "J1_housing": (0, 0, z_j1),
        "shoulder_housing": (0, 0, z_shoulder),
        "upper_arm": (x_upper, 0, z_shoulder),
        "elbow_housing": (x_elbow, 0, z_shoulder),
        "forearm": (x_forearm, 0, z_shoulder),
        "wrist_roll_housing": (x_wrist, 0, z_shoulder),
        "wrist_pitch_housing": (x_wrist + 40, 0, z_shoulder),
        "wrist_yaw_housing": (x_wrist + 80, 0, z_shoulder),
        "gripper_palm": (x_gripper, 0, z_shoulder),
        "left_finger": (x_gripper + 35, p["finger_gap_mm"] / 2, z_shoulder),
        "right_finger": (x_gripper + 35, -p["finger_gap_mm"] / 2, z_shoulder),
    }

    comps = {}
    for name, xyz in placements.items():
        comps[name] = add_component(sw, asm, name, parts[name], xyz)

    for name, comp in comps.items():
        try:
            select_id = getattr(comp, "GetSelectByIDString", "")
            if callable(select_id):
                select_id = select_id()
            print(f"[DEBUG] comp instance {name}: Name2={comp.Name2}, SelectByIDString={select_id}")
        except Exception as exc:
            try:
                print(f"[DEBUG] comp instance {name}: Name2={comp.Name2}, select string unavailable: {exc}")
            except Exception:
                print(f"[WARN] comp instance {name}: cannot inspect component: {exc}")

    made = apply_first_pass_plane_mates(asm, comps)
    if not made:
        print("[WARN] No first-pass mates were created. Run output above shows whether ref selection or AddMate failed.")

    try:
        asm.ViewZoomtofit2()
    except Exception:
        pass

    path = OUT_DIR / "compact_6dof_robot_arm.SLDASM"
    save_as(asm, str(path))
    return path




def load_existing_parts() -> dict[str, Path]:
    parts = {name: PART_DIR / f"{name}.SLDPRT" for name in PART_NAMES}
    missing = [str(path) for path in parts.values() if not path.exists()]
    if missing:
        raise RuntimeError(
            "--assembly-only requires existing part files. Missing:\n" + "\n".join(missing)
        )
    return parts


def build(sw, parts_only: bool = False, assembly_only: bool = False):
    PART_DIR.mkdir(parents=True, exist_ok=True)
    PLAN_DIR.mkdir(parents=True, exist_ok=True)

    p = PARAMS
    if assembly_only:
        print(f"[DEBUG] assembly-only mode: loading existing parts from {PART_DIR}")
        parts = load_existing_parts()
    else:
        parts = {
            "base": create_base(sw),
            "J1_housing": create_cylinder(sw, "J1_housing", p["j1_diameter_mm"], p["j1_height_mm"], "Z"),
            "shoulder_housing": create_cylinder(sw, "shoulder_housing", p["shoulder_diameter_mm"], p["shoulder_width_mm"], "X"),
            "upper_arm": create_link(sw, "upper_arm", p["upper_arm_length_mm"], tuple(p["upper_arm_section_mm"])),
            "elbow_housing": create_cylinder(sw, "elbow_housing", p["elbow_diameter_mm"], p["elbow_width_mm"], "X"),
            "forearm": create_link(sw, "forearm", p["forearm_length_mm"], tuple(p["forearm_section_mm"])),
            "wrist_roll_housing": create_cylinder(sw, "wrist_roll_housing", p["wrist_module_diameter_mm"], 40, "X"),
            "wrist_pitch_housing": create_cylinder(sw, "wrist_pitch_housing", p["wrist_module_diameter_mm"], 40, "Y"),
            "wrist_yaw_housing": create_cylinder(sw, "wrist_yaw_housing", p["wrist_module_diameter_mm"], 40, "X"),
            "gripper_palm": create_box(sw, "gripper_palm", tuple(p["gripper_palm_mm"]), "X", 3),
            "left_finger": create_gripper_finger(sw, "left_finger"),
            "right_finger": create_gripper_finger(sw, "right_finger"),
        }

    assembly = None if parts_only else create_assembly(sw, parts)
    (PLAN_DIR / "compact_6dof_robot_arm_parameters.json").write_text(
        json.dumps({"parameters": PARAMS, "parts": {k: str(v) for k, v in parts.items()}, "assembly": str(assembly) if assembly else None}, indent=2),
        encoding="utf-8",
    )
    return assembly or PART_DIR


def main():
    parser = argparse.ArgumentParser(description="Create a compact 6-DOF serial robot arm assembly in SolidWorks.")
    parser.add_argument("--visible", action="store_true", help="Show SolidWorks while generating the model.")
    parser.add_argument("--parts-only", action="store_true", help="Generate named parts with datum interfaces but skip assembly insertion.")
    parser.add_argument("--assembly-only", action="store_true", help="Reuse existing part files and regenerate only the assembly and mates.")
    args = parser.parse_args()

    if args.parts_only and args.assembly_only:
        raise SystemExit("Use either --parts-only or --assembly-only, not both.")

    sw = connect_solidworks(visible=args.visible)
    result = build(sw, parts_only=args.parts_only, assembly_only=args.assembly_only)
    print(f"Created: {result}")


if __name__ == "__main__":
    main()







