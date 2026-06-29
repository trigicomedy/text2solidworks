from __future__ import annotations

from .constants import REF_PLANE_OFFSET
from .features import rebuild_model
from .selection import clear_selection, null_dispatch, select_plane
from .units import mm


def create_offset_plane(model, name: str, reference_plane: str, offset_mm: float):
    clear_selection(model)
    select_plane(model, reference_plane)
    feature = model.FeatureManager.InsertRefPlane(REF_PLANE_OFFSET, mm(offset_mm), 0, 0, 0, 0)
    if feature is None:
        raise RuntimeError(f"Failed to create offset plane: {name}")
    feature.Name = name
    rebuild_model(model)
    return name


def create_axis_from_two_planes(model, name: str, plane_a: str, plane_b: str):
    clear_selection(model)
    select_plane(model, plane_a, append=False)
    select_plane(model, plane_b, append=True)
    result = model.InsertAxis2(True)
    if result is None or result is False:
        raise RuntimeError(f"Failed to create datum axis from planes: {name}")
    # Some COM bindings return bool instead of the feature object. In that case
    # naming must be handled by a later feature-tree helper.
    try:
        result.Name = name
    except Exception:
        _rename_latest_feature_by_type(model, "RefAxis", name)
    rebuild_model(model)
    return name


def create_axis_from_cylindrical_face_by_ray(
    model,
    name: str,
    ray_mm: tuple[float, float, float, float, float, float],
    *,
    selection_radius_mm: float = 2.0,
):
    x, y, z, dx, dy, dz = ray_mm
    clear_selection(model)
    selected = model.Extension.SelectByRay(
        mm(x), mm(y), mm(z),
        dx, dy, dz,
        mm(selection_radius_mm),
        2,
        False,
        0,
        0,
    )
    if not selected:
        raise RuntimeError(f"Failed to select cylindrical face for axis: {name}")
    result = model.InsertAxis2(True)
    if result is None or result is False:
        raise RuntimeError(f"Failed to create datum axis from cylindrical face: {name}")
    try:
        result.Name = name
    except Exception:
        _rename_latest_feature_by_type(model, "RefAxis", name)
    rebuild_model(model)
    return name


def _feature_value(feature, attr: str):
    value = getattr(feature, attr, None)
    try:
        return value() if callable(value) else value
    except Exception:
        return None


def _rename_latest_feature_by_type(model, type_name: str, name: str) -> bool:
    """Best-effort rename for COM calls that return bool instead of IFeature."""
    try:
        features = list(model.FeatureManager.GetFeatures(False) or [])
    except Exception:
        return False
    for feature in reversed(features):
        if _feature_value(feature, "GetTypeName2") == type_name:
            try:
                feature.Name = name
                return True
            except Exception:
                return False
    return False


def create_coordinate_system_from_selection(model, name: str):
    """Create a coordinate system from the current SolidWorks selection.

    Selection requirements depend on SolidWorks: origin point, axis references,
    and optional plane references. This helper exposes the native operation but
    does not try to infer references.
    """
    attempts = [
        ("InsertCoordinateSystem", lambda: model.FeatureManager.InsertCoordinateSystem(False, False, False)),
        ("InsertCoordinateSystem2", lambda: model.FeatureManager.InsertCoordinateSystem2(False, False, False, null_dispatch())),
    ]
    errors = []
    for label, call in attempts:
        try:
            feature = call()
            if feature is not None:
                feature.Name = name
                rebuild_model(model)
                return name
        except Exception as exc:
            errors.append(f"{label}: {exc}")
    raise RuntimeError(f"Coordinate system creation failed: {name}. Attempts: {'; '.join(errors)}")
