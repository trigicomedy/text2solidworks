from __future__ import annotations

from .features import rebuild_model
from .units import mm


def add_dimension(model, name: str | None, location_mm: tuple[float, float], value_mm: float | None = None):
    """Add a native sketch dimension to the current selection.

    If `value_mm` is supplied, the created dimension's system value is set in
    meters. This helper assumes the caller selected the intended sketch entity
    or entity pair first.
    """
    x, y = location_mm
    dim = model.AddDimension2(mm(x), mm(y), 0.0)
    if dim is None:
        raise RuntimeError("SolidWorks did not create a dimension for the current selection.")
    try:
        if name:
            dim.Name = name
    except Exception:
        pass
    if value_mm is not None:
        try:
            dim.SystemValue = mm(value_mm)
        except Exception:
            try:
                dim.GetDimension().SystemValue = mm(value_mm)
            except Exception as exc:
                raise RuntimeError(f"Failed to set dimension value for {name}: {exc}") from exc
    rebuild_model(model)
    return dim


def add_smart_dimension(model, name: str | None, location_mm: tuple[float, float], value_mm: float | None = None):
    return add_dimension(model, name, location_mm, value_mm)
