from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(r"D:\text2solidworks")

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cad_runtime.solidworks import connect_solidworks


MODEL_CANDIDATES = [
    "FeatureMirror",
    "InsertMirrorFeature",
    "InsertMirrorFeature2",
    "InsertFeatureShell",
    "InsertFeatureShell2",
    "InsertRib",
    "InsertRib2",
    "InsertHelix",
    "InsertHelix2",
    "InsertDraft",
]

FEATURE_MANAGER_CANDIDATES = [
    "FeatureMirror",
    "InsertMirrorFeature",
    "InsertMirrorFeature2",
    "InsertFeatureShell",
    "InsertFeatureShell2",
    "InsertRib",
    "InsertRib2",
    "InsertHelix",
    "InsertHelix2",
    "InsertDraft",
]


def callable_info(obj, names):
    data = {}
    for name in names:
        try:
            attr = getattr(obj, name)
            data[name] = {
                "callable": callable(attr),
                "repr": repr(attr)[:200],
            }
        except Exception as exc:
            data[name] = {"error": f"{type(exc).__name__}: {exc}"}
    return data


def template(sw) -> str:
    path = sw.GetUserPreferenceStringValue(1)
    if path and Path(path).exists():
        return path
    return r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\templates\gb_part.prtdot"


def safe_title(model):
    title_attr = getattr(model, "GetTitle", None)
    return title_attr() if callable(title_attr) else title_attr


def main() -> int:
    sw = connect_solidworks(visible=True)
    model = sw.NewDocument(template(sw), 0, 0, 0)
    feature_manager = model.FeatureManager
    data = {
        "model": callable_info(model, MODEL_CANDIDATES),
        "feature_manager": callable_info(feature_manager, FEATURE_MANAGER_CANDIDATES),
    }
    print(json.dumps(data, ensure_ascii=False, indent=2))
    title = safe_title(model)
    if title:
        sw.CloseDoc(title)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
