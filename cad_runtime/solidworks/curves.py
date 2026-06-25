from __future__ import annotations

from .features import rebuild_model


def insert_helix_from_selected_circle(model, name: str, pitch_mm: float, height_mm: float, *, clockwise: bool = True):
    """Create a native helix/spiral from the currently selected circle.

    This wrapper is intentionally conservative; helix COM signatures vary and
    need validation before use in production generation.
    """
    attempts = [
        ("InsertHelix", lambda: model.InsertHelix(clockwise, False, pitch_mm / 1000.0, height_mm / 1000.0, 0, 0)),
        ("InsertHelix2", lambda: model.InsertHelix2(clockwise, False, pitch_mm / 1000.0, height_mm / 1000.0, 0, 0, 0)),
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
    raise RuntimeError(f"Helix creation failed: {name}. Attempts: {'; '.join(errors)}")


def projected_curve(*_args, **_kwargs):
    raise NotImplementedError("Projected curve wrapper is planned but not yet verified.")


def composite_curve(*_args, **_kwargs):
    raise NotImplementedError("Composite curve wrapper is planned but not yet verified.")
