from __future__ import annotations

from collections.abc import Iterable

from .features import rebuild_model
from .selection import clear_selection, null_dispatch
from .units import mm


RaySpec = tuple[float, float, float, float, float, float]


def select_edge_by_ray(model, ray: RaySpec, *, append: bool = True, radius_mm: float = 2.0) -> bool:
    x, y, z, dx, dy, dz = ray
    return bool(
        model.Extension.SelectByRay(
            mm(x), mm(y), mm(z),
            dx, dy, dz,
            mm(radius_mm),
            1,
            append,
            0,
            0,
        )
    )


def fillet_selected_edges(model, name: str, radius_mm: float):
    feature = model.FeatureManager.FeatureFillet3(
        195, mm(radius_mm), 0, 0, 0, 0, 0, 0,
        null_dispatch(), null_dispatch(), null_dispatch()
    )
    if feature is None:
        raise RuntimeError(f"Native fillet failed: {name}")
    feature.Name = name
    rebuild_model(model)
    return feature


def chamfer_selected_edges(model, name: str, size_mm: float):
    attempts = [
        ("distance-angle", lambda: model.FeatureManager.InsertFeatureChamfer(4, 0, mm(size_mm), 0, 0, 0, 0, 0)),
        ("distance-distance", lambda: model.FeatureManager.InsertFeatureChamfer(4, 1, mm(size_mm), mm(size_mm), 0, 0, 0, 0)),
    ]
    errors = []
    for label, call in attempts:
        try:
            feature = call()
            if feature is not None:
                feature.Name = name
                rebuild_model(model)
                return feature
        except Exception as exc:
            errors.append(f"{label}: {exc}")
    raise RuntimeError(f"Native chamfer failed: {name}. Attempts: {'; '.join(errors)}")


def fillet_edges_by_rays(model, name: str, radius_mm: float, rays: Iterable[RaySpec], *, selection_radius_mm: float = 2.0):
    clear_selection(model)
    selected = 0
    for ray in rays:
        selected += int(select_edge_by_ray(model, ray, append=True, radius_mm=selection_radius_mm))
    if selected == 0:
        raise RuntimeError(f"No edges selected for fillet: {name}")
    return fillet_selected_edges(model, name, radius_mm)


def chamfer_edges_by_rays(model, name: str, size_mm: float, rays: Iterable[RaySpec], *, selection_radius_mm: float = 2.0):
    clear_selection(model)
    selected = 0
    for ray in rays:
        selected += int(select_edge_by_ray(model, ray, append=True, radius_mm=selection_radius_mm))
    if selected == 0:
        raise RuntimeError(f"No edges selected for chamfer: {name}")
    return chamfer_selected_edges(model, name, size_mm)


def fillet_all_current_body_edges(model, name: str, radius_mm: float):
    bodies = model.GetBodies2(0, True) or []
    if len(bodies) != 1:
        raise RuntimeError(f"Expected one solid body for all-edge fillet, got {len(bodies)}")
    edges = bodies[0].GetEdges() or []
    if not edges:
        raise RuntimeError(f"No body edges found for fillet: {name}")
    clear_selection(model)
    selected = 0
    for edge in edges:
        append = selected > 0
        try:
            if edge.Select4(append, null_dispatch()):
                selected += 1
        except Exception:
            try:
                if edge.Select4(append, None):
                    selected += 1
            except Exception:
                continue
    if selected == 0:
        raise RuntimeError(f"No body edges selected for fillet: {name}")
    return fillet_selected_edges(model, name, radius_mm)


def chamfer_all_current_body_edges(model, name: str, size_mm: float):
    bodies = model.GetBodies2(0, True) or []
    if len(bodies) != 1:
        raise RuntimeError(f"Expected one solid body for all-edge chamfer, got {len(bodies)}")
    edges = bodies[0].GetEdges() or []
    if not edges:
        raise RuntimeError(f"No body edges found for chamfer: {name}")
    clear_selection(model)
    selected = 0
    for edge in edges:
        append = selected > 0
        try:
            if edge.Select4(append, null_dispatch()):
                selected += 1
        except Exception:
            try:
                if edge.Select4(append, None):
                    selected += 1
            except Exception:
                continue
    if selected == 0:
        raise RuntimeError(f"No body edges selected for chamfer: {name}")
    return chamfer_selected_edges(model, name, size_mm)
