from __future__ import annotations

import math

from .assembly_components import component_name
from .selection import clear_selection, null_dispatch
from .units import mm


def set_component_transform(
    sw_app,
    component,
    xyz_mm: tuple[float, float, float],
    rpy_deg: tuple[float, float, float] = (0.0, 0.0, 0.0),
):
    """Set component transform from translation and XYZ roll/pitch/yaw degrees."""
    transform = make_component_transform(component, xyz_mm, rpy_deg)
    for method_name in ("SetTransformAndSolve3", "SetTransformAndSolve2", "SetTransformAndSolve"):
        method = getattr(component, method_name, None)
        if not callable(method):
            continue
        try:
            if method_name == "SetTransformAndSolve3":
                result = method(transform, True)
            else:
                result = method(transform)
            if result is not False:
                return result
        except Exception:
            continue
    try:
        component.Transform2 = transform
        return True
    except Exception as exc:
        raise RuntimeError(f"Failed to set component transform: {component_name(component)}") from exc


def move_component(sw_app, component, xyz_mm: tuple[float, float, float]):
    return set_component_transform(sw_app, component, xyz_mm, (0.0, 0.0, 0.0))


def rotate_component(sw_app, component, axis: tuple[float, float, float], angle_deg: float):
    ax = tuple(round(float(v), 6) for v in axis)
    if ax == (1.0, 0.0, 0.0):
        rpy = (angle_deg, 0.0, 0.0)
    elif ax == (0.0, 1.0, 0.0):
        rpy = (0.0, angle_deg, 0.0)
    elif ax == (0.0, 0.0, 1.0):
        rpy = (0.0, 0.0, angle_deg)
    else:
        raise NotImplementedError("rotate_component currently validates principal X/Y/Z axes only.")
    return set_component_transform(sw_app, component, _current_translation_mm(component), rpy)


def _current_translation_mm(component) -> tuple[float, float, float]:
    transform = getattr(component, "Transform2", None) or getattr(component, "Transform", None)
    try:
        data = tuple(transform.ArrayData)
        return (data[9] * 1000.0, data[10] * 1000.0, data[11] * 1000.0)
    except Exception:
        return (0.0, 0.0, 0.0)


def make_transform(sw_app, xyz_mm: tuple[float, float, float], rpy_deg: tuple[float, float, float]):
    data = transform_array(xyz_mm, rpy_deg)
    return _math_utility(sw_app).CreateTransform(data)


def make_component_transform(component, xyz_mm: tuple[float, float, float], rpy_deg: tuple[float, float, float]):
    transform = getattr(component, "Transform2", None) or getattr(component, "Transform", None)
    if transform is None:
        raise RuntimeError(f"Component has no transform object: {component_name(component)}")
    data = transform_array(xyz_mm, rpy_deg)
    set_data = getattr(transform, "SetData", None)
    if callable(set_data):
        result = set_data(data)
        if result is False:
            raise RuntimeError(f"MathTransform.SetData failed for component: {component_name(component)}")
        return transform
    try:
        transform.ArrayData = data
        return transform
    except Exception as exc:
        raise RuntimeError(f"Failed to update component transform data: {component_name(component)}") from exc


def transform_array(xyz_mm: tuple[float, float, float], rpy_deg: tuple[float, float, float]):
    rx, ry, rz = (math.radians(v) for v in rpy_deg)
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)

    # R = Rz * Ry * Rx
    r00 = cz * cy
    r01 = cz * sy * sx - sz * cx
    r02 = cz * sy * cx + sz * sx
    r10 = sz * cy
    r11 = sz * sy * sx + cz * cx
    r12 = sz * sy * cx - cz * sx
    r20 = -sy
    r21 = cy * sx
    r22 = cy * cx

    tx, ty, tz = (mm(v) for v in xyz_mm)
    return [
        r00, r01, r02,
        r10, r11, r12,
        r20, r21, r22,
        tx, ty, tz,
        1.0, 0.0, 0.0, 0.0,
    ]


def select_component(component, *, append: bool = False) -> bool:
    for mark in (null_dispatch(), None):
        try:
            if component.Select4(append, mark, False):
                return True
        except Exception:
            pass
    try:
        return bool(component.Select2(append, 0))
    except Exception:
        return False


def fix_component_in_assembly(assembly, component):
    clear_selection(assembly)
    if not select_component(component, append=False):
        raise RuntimeError(f"Failed to select component for fix: {component_name(component)}")
    method = getattr(assembly, "FixComponent", None)
    if callable(method):
        return method()
    raise RuntimeError("Assembly does not expose FixComponent.")


def float_component_in_assembly(assembly, component):
    clear_selection(assembly)
    if not select_component(component, append=False):
        raise RuntimeError(f"Failed to select component for float: {component_name(component)}")
    method = getattr(assembly, "UnfixComponent", None)
    if callable(method):
        return method()
    raise RuntimeError("Assembly does not expose UnfixComponent.")


def _math_utility(sw_app):
    math_util = getattr(sw_app, "GetMathUtility", None)
    if callable(math_util):
        try:
            return math_util()
        except Exception:
            return math_util
    return math_util
