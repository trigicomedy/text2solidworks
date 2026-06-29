from __future__ import annotations

import os
from pathlib import Path

from .document import save_as


ASSEMBLY_TEMPLATE_ENV = "TEXT2SW_ASSEMBLY_TEMPLATE"


def assembly_template(sw_app, template_path: str | None = None) -> str:
    """Return a usable SolidWorks assembly template path."""
    if template_path and Path(template_path).exists():
        return str(template_path)

    env_path = os.environ.get(ASSEMBLY_TEMPLATE_ENV)
    if env_path and Path(env_path).exists():
        return env_path

    try:
        template = sw_app.GetUserPreferenceStringValue(2)
        if template and Path(template).exists():
            return template
    except Exception:
        pass

    roots = [
        Path(r"C:\ProgramData\SOLIDWORKS"),
        Path(r"C:\ProgramData\SolidWorks"),
    ]
    for root in roots:
        if not root.exists():
            continue
        for name in ("gb_assembly.asmdot", "Assembly.asmdot"):
            matches = list(root.rglob(name))
            if matches:
                return str(matches[0])

    raise RuntimeError(
        "No SolidWorks assembly template found. "
        f"Set {ASSEMBLY_TEMPLATE_ENV} to a .asmdot template path."
    )


def new_assembly(sw_app, template_path: str | None = None):
    """Create a new SolidWorks assembly document."""
    template = assembly_template(sw_app, template_path)
    model = sw_app.NewDocument(template, 0, 0, 0)
    if model is None:
        raise RuntimeError(f"Failed to create a new SolidWorks assembly from template: {template}")
    return model


def open_assembly(sw_app, path: str | Path, *, silent: bool = True):
    """Open an existing SolidWorks assembly document."""
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(target)
    options = 1 if silent else 0
    errors = _byref_i4(0)
    warnings = _byref_i4(0)
    try:
        model = sw_app.OpenDoc6(str(target), 2, options, "", errors, warnings)
    except Exception as exc:
        raise RuntimeError(f"Failed to open assembly: {target}. {exc}") from exc
    if model is None:
        raise RuntimeError(f"SolidWorks returned no assembly for: {target}. errors={errors.value}, warnings={warnings.value}")
    return model


def save_assembly(assembly, path: str | Path) -> str:
    """Save an assembly as SLDASM or another SolidWorks-supported path."""
    return save_as(assembly, str(path))


def activate_document(sw_app, title: str):
    """Best-effort activate an open SolidWorks document by title."""
    errors = _byref_i4(0)
    try:
        doc = sw_app.ActivateDoc3(title, False, 0, errors)
        if doc is not None:
            return doc
    except Exception:
        pass
    try:
        return sw_app.ActivateDoc2(title, False, 0)
    except Exception as exc:
        raise RuntimeError(f"Failed to activate SolidWorks document: {title}") from exc


def document_title(model) -> str:
    """Return a document title across dynamic COM property/method variants."""
    title_attr = getattr(model, "GetTitle", None)
    title = title_attr() if callable(title_attr) else title_attr
    return str(title or "")


def _byref_i4(value: int = 0):
    import pythoncom
    import win32com.client

    return win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, value)
