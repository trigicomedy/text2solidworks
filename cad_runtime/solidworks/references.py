from __future__ import annotations

from .constants import REF_PLANE_OFFSET
from .selection import clear_selection, select_plane
from .units import mm
from .features import rebuild_model


def create_offset_plane(model, name: str, reference_plane: str, offset_mm: float):
    clear_selection(model)
    select_plane(model, reference_plane)
    feature = model.FeatureManager.InsertRefPlane(REF_PLANE_OFFSET, mm(offset_mm), 0, 0, 0, 0)
    if feature is None:
        raise RuntimeError(f"Failed to create offset plane: {name}")
    feature.Name = name
    rebuild_model(model)
    return name
