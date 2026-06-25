from __future__ import annotations

import time
from pathlib import Path

from .document import save_as
from .features import rebuild_model


STANDARD_MODEL_VIEWS = {
    "front": ("*Front", 1),
    "back": ("*Back", 2),
    "left": ("*Left", 3),
    "right": ("*Right", 4),
    "top": ("*Top", 5),
    "bottom": ("*Bottom", 6),
    "isometric": ("*Isometric", 7),
    "dimetric": ("*Dimetric", 8),
    "trimetric": ("*Trimetric", 9),
}

DEFAULT_NINE_VIEW_ORDER = (
    "front",
    "back",
    "left",
    "right",
    "top",
    "bottom",
    "isometric",
    "dimetric",
    "trimetric",
)


def open_model(sw_app, model_path: str | Path, *, visible: bool = True):
    """Open a SolidWorks model document and return the active document.

    The wrapper intentionally keeps this simple and compatible. If the document
    is already open, SolidWorks usually activates/reuses it.
    """
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(path)
    try:
        sw_app.Visible = visible
    except Exception:
        pass

    # OpenDoc6 type: 1=part, 2=assembly, 3=drawing. Silent option is 1.
    suffix = path.suffix.lower()
    doc_type = 2 if suffix == ".sldasm" else 1 if suffix == ".sldprt" else 0
    errors = 0
    warnings = 0
    try:
        model = sw_app.OpenDoc6(str(path), doc_type, 1, "", errors, warnings)
    except Exception:
        model = None
    if model is None:
        # Fallback for pywin32 bindings that dislike integer byref arguments.
        model = sw_app.OpenDoc(str(path), doc_type)
    if model is None:
        raise RuntimeError(f"Failed to open SolidWorks model: {path}")
    return model


def fit_view(model) -> None:
    rebuild_model(model)
    for name in ("ViewZoomtofit2", "ViewZoomToFit2"):
        try:
            method = getattr(model, name)
            if callable(method):
                method()
                return
        except Exception:
            continue


def show_named_view(model, view_key: str) -> None:
    """Switch to a standard model view.

    `view_key` can be one of `front/back/left/right/top/bottom/isometric/
    dimetric/trimetric`, case-insensitive.
    """
    key = view_key.strip().lower()
    if key not in STANDARD_MODEL_VIEWS:
        raise ValueError(f"Unknown model view: {view_key}")
    view_name, view_id = STANDARD_MODEL_VIEWS[key]
    try:
        result = model.ShowNamedView2(view_name, view_id)
    except Exception as exc:
        raise RuntimeError(f"Failed to show model view {view_key}: {exc}") from exc
    if result is False:
        raise RuntimeError(f"SolidWorks rejected model view: {view_key}")
    fit_view(model)


def export_current_view_image(model, output_path: str | Path) -> str:
    """Save the currently displayed model view as an image file."""
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    return save_as(model, str(target))


def export_named_view_image(
    model,
    view_key: str,
    output_path: str | Path,
    *,
    pause_s: float = 0.2,
) -> str:
    show_named_view(model, view_key)
    if pause_s > 0:
        time.sleep(pause_s)
    return export_current_view_image(model, output_path)


def export_named_view_images(
    model,
    output_dir: str | Path,
    *,
    views: tuple[str, ...] = DEFAULT_NINE_VIEW_ORDER,
    image_extension: str = ".png",
    pause_s: float = 0.2,
) -> dict[str, str]:
    """Export a set of named model views as image files."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, str] = {}
    ext = image_extension if image_extension.startswith(".") else f".{image_extension}"
    for view_key in views:
        target = out_dir / f"{view_key.lower()}{ext}"
        results[view_key] = export_named_view_image(model, view_key, target, pause_s=pause_s)
    return results


def export_model_nine_view_images(
    sw_app,
    model_path: str | Path,
    output_dir: str | Path,
    *,
    visible: bool = True,
    pause_s: float = 0.2,
) -> dict[str, str]:
    """Open a part/assembly and export the standard 9-view PNG set."""
    model = open_model(sw_app, model_path, visible=visible)
    return export_named_view_images(
        model,
        output_dir,
        views=DEFAULT_NINE_VIEW_ORDER,
        image_extension=".png",
        pause_s=pause_s,
    )
