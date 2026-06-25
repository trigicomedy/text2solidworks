from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import win32com.client

PROJECT_ROOT = Path(r"D:\text2solidworks")

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cad_runtime.solidworks import connect_solidworks


NAMES = [
    "InsertMirrorFeature",
    "InsertMirrorFeature2",
    "InsertFeatureShell",
    "InsertRib",
    "InsertRib2",
    "InsertHelix",
]


def template(sw) -> str:
    path = sw.GetUserPreferenceStringValue(1)
    if path and Path(path).exists():
        return path
    return r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\templates\gb_part.prtdot"


def describe(obj):
    data = {}
    for name in NAMES:
        try:
            attr = getattr(obj, name)
            info = {
                "repr": repr(attr)[:200],
                "callable": callable(attr),
                "doc": (getattr(attr, "__doc__", "") or "")[:500],
            }
            try:
                info["signature"] = str(inspect.signature(attr))
            except Exception as exc:
                info["signature_error"] = f"{type(exc).__name__}: {exc}"
            data[name] = info
        except Exception as exc:
            data[name] = {"error": f"{type(exc).__name__}: {exc}"}
    return data


def safe_title(model):
    title_attr = getattr(model, "GetTitle", None)
    return title_attr() if callable(title_attr) else title_attr


def main() -> int:
    # Force pywin32 to generate wrappers if SolidWorks exposes a type library.
    sw = win32com.client.gencache.EnsureDispatch("SldWorks.Application")
    sw.Visible = True
    model = sw.NewDocument(template(sw), 0, 0, 0)
    data = {
        "sw_class": type(sw).__name__,
        "model_class": type(model).__name__,
        "feature_manager_class": type(model.FeatureManager).__name__,
        "model": describe(model),
        "feature_manager": describe(model.FeatureManager),
    }
    print(json.dumps(data, ensure_ascii=False, indent=2))
    title = safe_title(model)
    if title:
        sw.CloseDoc(title)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
