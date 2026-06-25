from __future__ import annotations

from .features import rebuild_model
from .units import mm


def rib_from_selected_sketch(model, name: str, thickness_mm: float, *, flip: bool = False):
    """Create a native rib from the currently selected sketch.

    This is an initial wrapper and should be validated before production use.
    """
    attempts = [
        ("ModelDoc.InsertRib 6-arg", lambda: model.InsertRib(mm(thickness_mm), flip, False, 0, 0, False)),
        ("FeatureManager.InsertRib 6-arg", lambda: model.FeatureManager.InsertRib(mm(thickness_mm), flip, False, 0, 0, False)),
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
    raise RuntimeError(f"Rib feature failed: {name}. Attempts: {'; '.join(errors)}")


def draft_selected_faces(model, name: str, angle_deg: float):
    raise NotImplementedError("Draft wrapper needs a dedicated SW2025 COM signature validation.")
