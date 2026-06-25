from __future__ import annotations

from pathlib import Path


def new_part(sw_app, template_path: str | None = None):
    """Create a new part document.

    If template_path is omitted, SolidWorks default part template is used when available.
    """
    if template_path:
        model = sw_app.NewDocument(str(template_path), 0, 0, 0)
    else:
        template = sw_app.GetUserPreferenceStringValue(1)  # default part template
        if not template:
            raise RuntimeError("No part template path was provided and no default template was found.")
        model = sw_app.NewDocument(template, 0, 0, 0)

    if model is None:
        raise RuntimeError("Failed to create a new SolidWorks part document.")
    return model


def save_as(model, path: str):
    """Save the active model to a path supported by SolidWorks."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target_str = str(target)

    attempts = []

    def save_as_basic():
        return model.SaveAs(target_str)

    attempts.append(("SaveAs", save_as_basic))

    def save_as2():
        return model.SaveAs2(target_str, 0, True, False)

    attempts.append(("SaveAs2", save_as2))

    def save_as3():
        return model.SaveAs3(target_str, 0, 0)

    attempts.append(("SaveAs3", save_as3))

    last_error = None
    for name, fn in attempts:
        try:
            result = fn()
            if result is True or result == 0 or target.exists():
                return target_str
        except Exception as exc:
            last_error = exc

    if target.exists():
        return target_str

    detail = f" Last error: {last_error}" if last_error else ""
    raise RuntimeError(f"Failed to save model: {target}.{detail}")

