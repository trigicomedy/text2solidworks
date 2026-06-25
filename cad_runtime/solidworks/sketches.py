from __future__ import annotations

import math

from .selection import (
    clear_selection,
    rename_selected_feature,
    select_latest_generated_sketch,
    select_plane,
)
from .units import mm
from .features import rebuild_model


def begin_sketch_on_plane(model, plane_name: str):
    clear_selection(model)
    select_plane(model, plane_name)
    model.SketchManager.InsertSketch(True)


def end_sketch(model, sketch_name: str | None = None):
    # SW2025 pywin32 may not expose GetActiveSketch2 or FirstFeature reliably.
    # Exit first, rebuild, then select the newest default-named sketch.
    model.SketchManager.InsertSketch(True)
    rebuild_model(model)
    generated_name = select_latest_generated_sketch(model)
    if generated_name is None:
        raise RuntimeError(
            "Sketch was created but could not be selected by a generated "
            "Chinese or English sketch name."
        )
    if sketch_name:
        rename_selected_feature(model, sketch_name)
    return sketch_name or generated_name


def draw_center_rectangle(model, length_mm: float, width_mm: float):
    model.SketchManager.CreateCenterRectangle(0, 0, 0, mm(length_mm) / 2, mm(width_mm) / 2, 0)


def draw_circle(model, center_x_mm: float, center_y_mm: float, radius_mm: float):
    x = mm(center_x_mm)
    y = mm(center_y_mm)
    r = mm(radius_mm)
    return model.SketchManager.CreateCircle(x, y, 0, x + r, y, 0)


def draw_center_arc(
    model,
    center_mm: tuple[float, float],
    start_mm: tuple[float, float],
    end_mm: tuple[float, float],
    *,
    clockwise: bool,
):
    """Create a native arc with explicit direction.

    The current SW2025 pywin32 binding uses 1 for clockwise and -1 for
    counterclockwise. Callers must choose the intended short/long path
    explicitly and validate the resulting closed profile before extrusion.
    """
    cx, cy = center_mm
    sx, sy = start_mm
    ex, ey = end_mm
    start_radius = math.hypot(sx - cx, sy - cy)
    end_radius = math.hypot(ex - cx, ey - cy)
    if not math.isclose(start_radius, end_radius, rel_tol=1e-6, abs_tol=1e-6):
        raise ValueError("Arc start and end points must have the same radius.")
    direction = 1 if clockwise else -1
    return model.SketchManager.CreateArc(
        mm(cx), mm(cy), 0.0,
        mm(sx), mm(sy), 0.0,
        mm(ex), mm(ey), 0.0,
        direction,
    )

