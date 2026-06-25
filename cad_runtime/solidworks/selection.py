from __future__ import annotations

import pythoncom
import win32com.client

PLANE_ALIASES = {
    "Top Plane": ("Top Plane", "上视基准面", "上基准面"),
    "Front Plane": ("Front Plane", "前视基准面", "前基准面"),
    "Right Plane": ("Right Plane", "右视基准面", "右基准面"),
}


def null_dispatch():
    """Typed null IDispatch for SolidWorks API arguments that reject Python None."""
    return win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)


def clear_selection(model):
    model.ClearSelection2(True)


def select_by_id(model, name: str, entity_type: str, append: bool = False) -> bool:
    return bool(model.Extension.SelectByID2(name, entity_type, 0.0, 0.0, 0.0, append, 0, null_dispatch(), 0))


def select_plane(model, plane_name: str, append: bool = False):
    if not append:
        clear_selection(model)
    aliases = PLANE_ALIASES.get(plane_name, (plane_name,))
    errors = []
    for alias in aliases:
        try:
            if select_by_id(model, alias, "PLANE", append):
                return alias
        except Exception as exc:
            errors.append(f"{alias}: {exc}")
    detail = f" Errors: {'; '.join(errors)}" if errors else ""
    raise RuntimeError(f"Failed to select plane: {plane_name}. Tried {aliases}.{detail}")


def select_latest_generated_sketch(model, max_index: int = 50) -> str | None:
    """Select the newest default-named sketch without traversing the feature tree."""
    clear_selection(model)
    for index in range(max_index, 0, -1):
        for sketch_name in (f"草图{index}", f"Sketch{index}"):
            try:
                if select_by_id(model, sketch_name, "SKETCH"):
                    return sketch_name
            except Exception:
                continue
    return None


def rename_selected_feature(model, name: str) -> bool:
    """Best-effort rename of the currently selected sketch or feature."""
    try:
        selected = model.SelectionManager.GetSelectedObject6(1, -1)
        if selected is not None:
            selected.Name = name
            return True
    except Exception:
        pass
    return False


def select_named_face(model, face_name: str):
    # Selection type 2 is face in many API examples. Keep this behind a wrapper.
    entity = model.Extension.GetEntityByName(face_name, 2)
    if entity is None:
        raise RuntimeError(f"Named face not found: {face_name}")
    if not entity.Select4(False, None):
        raise RuntimeError(f"Failed to select named face: {face_name}")
    return entity

