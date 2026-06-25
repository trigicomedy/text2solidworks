from __future__ import annotations

from collections.abc import Iterable

from .units import mm


Point2D = tuple[float, float]


def draw_line(model, start_mm: Point2D, end_mm: Point2D):
    x1, y1 = start_mm
    x2, y2 = end_mm
    return model.SketchManager.CreateLine(mm(x1), mm(y1), 0.0, mm(x2), mm(y2), 0.0)


def draw_centerline(model, start_mm: Point2D, end_mm: Point2D):
    x1, y1 = start_mm
    x2, y2 = end_mm
    return model.SketchManager.CreateCenterLine(mm(x1), mm(y1), 0.0, mm(x2), mm(y2), 0.0)


def draw_corner_rectangle(model, corner1_mm: Point2D, corner2_mm: Point2D):
    x1, y1 = corner1_mm
    x2, y2 = corner2_mm
    return model.SketchManager.CreateCornerRectangle(mm(x1), mm(y1), 0.0, mm(x2), mm(y2), 0.0)


def draw_center_rectangle(model, center_mm: Point2D, corner_mm: Point2D):
    cx, cy = center_mm
    x, y = corner_mm
    return model.SketchManager.CreateCenterRectangle(mm(cx), mm(cy), 0.0, mm(x), mm(y), 0.0)


def draw_circle(model, center_mm: Point2D, radius_mm: float):
    cx, cy = center_mm
    return model.SketchManager.CreateCircle(mm(cx), mm(cy), 0.0, mm(cx + radius_mm), mm(cy), 0.0)


def draw_circle_by_diameter(model, center_mm: Point2D, diameter_mm: float):
    return draw_circle(model, center_mm, diameter_mm / 2)


def draw_3point_arc(model, start_mm: Point2D, end_mm: Point2D, through_mm: Point2D):
    sx, sy = start_mm
    ex, ey = end_mm
    tx, ty = through_mm
    return model.SketchManager.Create3PointArc(
        mm(sx), mm(sy), 0.0,
        mm(ex), mm(ey), 0.0,
        mm(tx), mm(ty), 0.0,
    )


def draw_ellipse(model, center_mm: Point2D, major_axis_point_mm: Point2D, minor_axis_point_mm: Point2D):
    cx, cy = center_mm
    mx, my = major_axis_point_mm
    nx, ny = minor_axis_point_mm
    return model.SketchManager.CreateEllipse(
        mm(cx), mm(cy), 0.0,
        mm(mx), mm(my), 0.0,
        mm(nx), mm(ny), 0.0,
    )


def draw_polygon(model, center_mm: Point2D, vertex_mm: Point2D, side_count: int, *, inscribed: bool = True):
    if side_count < 3:
        raise ValueError("Polygon requires at least three sides.")
    cx, cy = center_mm
    vx, vy = vertex_mm
    return model.SketchManager.CreatePolygon(
        mm(cx), mm(cy), 0.0,
        mm(vx), mm(vy), 0.0,
        side_count,
        inscribed,
    )


def draw_spline(model, points_mm: Iterable[Point2D]):
    create_spline = getattr(model.SketchManager, "CreateSpline", None)
    if not callable(create_spline):
        raise RuntimeError("SketchManager.CreateSpline is not callable in this SW2025 COM binding.")
    coords: list[float] = []
    for x, y in points_mm:
        coords.extend([mm(x), mm(y), 0.0])
    if len(coords) < 6:
        raise ValueError("Spline requires at least two points.")
    return create_spline(coords)


def draw_text(model, text: str, origin_mm: Point2D, height_mm: float = 5.0, angle_rad: float = 0.0):
    """Create native sketch text when the COM binding exposes CreateText."""
    create_text = getattr(model.SketchManager, "CreateText", None)
    if not callable(create_text):
        raise RuntimeError("SketchManager.CreateText is not callable in this SW2025 COM binding.")
    x, y = origin_mm
    try:
        return create_text(text, mm(x), mm(y), 0.0, mm(height_mm), angle_rad)
    except Exception as exc:
        raise RuntimeError(f"Sketch text creation is not available with this COM signature: {exc}") from exc


def draw_centerpoint_straight_slot(model, center_mm: Point2D, end_mm: Point2D, width_mm: float):
    """Create a native slot if the current SketchManager binding supports it.

    Slot API signatures vary across SolidWorks versions, so this helper is kept
    behind a wrapper and must be validated in the current environment before it
    is used in production generation.
    """
    cx, cy = center_mm
    ex, ey = end_mm
    attempts = [
        ("CreateSketchSlot centerpoint straight", lambda: model.SketchManager.CreateSketchSlot(0, 1, mm(width_mm), mm(cx), mm(cy), 0.0, mm(ex), mm(ey), 0.0, 0.0, 0.0, 0.0)),
        ("CreateSketchSlot alternate", lambda: model.SketchManager.CreateSketchSlot(1, 0, mm(width_mm), mm(cx), mm(cy), 0.0, mm(ex), mm(ey), 0.0, 0.0, 0.0, 0.0)),
    ]
    errors = []
    for label, call in attempts:
        try:
            result = call()
            if result is not None:
                return result
        except Exception as exc:
            errors.append(f"{label}: {exc}")
    raise RuntimeError(f"Failed to create native slot. Attempts: {'; '.join(errors)}")
