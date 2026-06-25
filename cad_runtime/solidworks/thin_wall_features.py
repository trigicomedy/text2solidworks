from __future__ import annotations

from .features import rebuild_model
from .selection import null_dispatch
from .units import mm


def shell_selected_faces(model, name: str, thickness_mm: float, *, outward: bool = False):
    """Create a native Shell feature from the current face selection.

    The current face selection defines open faces. This function needs a
    dedicated workstation validation before being used in unattended generation.
    """
    attempts = [
        ("ModelDoc.InsertFeatureShell", lambda: model.InsertFeatureShell(mm(thickness_mm), outward)),
        ("ModelDoc.InsertFeatureShell by value", lambda: model.InsertFeatureShell(mm(thickness_mm))),
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
    raise RuntimeError(f"Shell feature failed: {name}. Attempts: {'; '.join(errors)}")
