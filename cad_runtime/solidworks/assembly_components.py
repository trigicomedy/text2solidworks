from __future__ import annotations

from pathlib import Path

from .assembly_documents import activate_document, document_title
from .units import mm


def open_part_for_insert(sw_app, path: str | Path, *, silent: bool = True):
    """Open a part before insertion when AddComponent needs the model loaded."""
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(target)
    errors = _byref_i4(0)
    warnings = _byref_i4(0)
    options = 1 if silent else 0
    try:
        return sw_app.OpenDoc6(str(target), 1, options, "", errors, warnings)
    except Exception:
        return None


def add_component(
    sw_app,
    assembly,
    part_path: str | Path,
    *,
    name: str | None = None,
    xyz_mm: tuple[float, float, float] = (0.0, 0.0, 0.0),
):
    """Insert a part component into an assembly with SW2025-friendly fallbacks."""
    path = Path(part_path)
    if not path.exists():
        raise FileNotFoundError(path)

    x, y, z = (mm(v) for v in xyz_mm)
    asm_title = document_title(assembly)
    attempts = [
        ("AddComponent5(path)", lambda: assembly.AddComponent5(str(path), 0, "", False, "", x, y, z)),
        ("AddComponent(path)", lambda: assembly.AddComponent(str(path), x, y, z)),
    ]

    open_part_for_insert(sw_app, path)
    if asm_title:
        try:
            activate_document(sw_app, asm_title)
        except Exception:
            pass

    attempts.extend([
        ("AddComponent5(opened path)", lambda: assembly.AddComponent5(str(path), 0, "", False, "", x, y, z)),
        ("AddComponent(opened path)", lambda: assembly.AddComponent(str(path), x, y, z)),
    ])

    errors: list[str] = []
    component = None
    for label, call in attempts:
        try:
            result = call()
            if result not in (None, False):
                component = result
                break
            errors.append(f"{label}: {result}")
        except Exception as exc:
            errors.append(f"{label}: {exc}")

    if component is None:
        raise RuntimeError(f"Failed to insert component {path}. Attempts: {'; '.join(errors)}")

    if name:
        try:
            component.Name2 = name
        except Exception:
            pass
    return component


def component_name(component) -> str:
    try:
        return str(component.Name2)
    except Exception:
        return ""


def list_components(assembly, *, top_level_only: bool = True) -> list:
    """List components in an assembly."""
    try:
        config = assembly.GetActiveConfiguration()
        root = config.GetRootComponent3(True)
        children = root.GetChildren() or []
        if top_level_only:
            return list(children)
        result = []

        def walk(comp):
            result.append(comp)
            for child in comp.GetChildren() or []:
                walk(child)

        for child in children:
            walk(child)
        return result
    except Exception:
        return []


def get_component(assembly, name: str):
    """Find a component by exact Name2 or by base instance prefix."""
    for comp in list_components(assembly, top_level_only=False):
        comp_name = component_name(comp)
        if comp_name == name or comp_name.split("-")[0] == name:
            return comp
    raise RuntimeError(f"Component not found in assembly: {name}")


def fix_component(component):
    """Fix a component in place when the COM object exposes the operation."""
    for method_name in ("Fix", "SetFixed"):
        method = getattr(component, method_name, None)
        if callable(method):
            return method()
    raise RuntimeError(f"Component does not expose a known fix method: {component_name(component)}")


def float_component(component):
    """Float a component when the COM object exposes the operation."""
    for method_name in ("Float", "SetFloating"):
        method = getattr(component, method_name, None)
        if callable(method):
            return method()
    raise RuntimeError(f"Component does not expose a known float method: {component_name(component)}")


def _byref_i4(value: int = 0):
    import pythoncom
    import win32com.client

    return win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, value)
