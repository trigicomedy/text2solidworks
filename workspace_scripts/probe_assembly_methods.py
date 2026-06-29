from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(r"D:\text2solidworks")
WORK_DIR = Path(r"D:\text2solidworks_workspace\debug\assembly_foundation")
PART_PATH = WORK_DIR / "parts" / "assembly_part_a.SLDPRT"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cad_runtime.solidworks import add_component, connect_solidworks, new_assembly


NAMES = [
    "Transform2",
    "Transform",
    "SetTransformAndSolve2",
    "SetTransformAndSolve",
    "SetSuppression2",
    "Select4",
    "Select2",
    "Fix",
    "Float",
    "SetFixed",
    "SetFloating",
    "GetConstrainedStatus",
    "GetChildren",
    "GetMates",
    "GetMateCount",
    "GetComponents",
    "GetComponentByName",
    "EditRebuild3",
    "ToolsCheckInterference2",
    "ToolsCheckInterference",
    "InterferenceDetectionManager",
]


def describe(obj):
    data = {}
    for name in NAMES:
        try:
            attr = getattr(obj, name)
            data[name] = {"callable": callable(attr), "repr": repr(attr)[:160]}
        except Exception as exc:
            data[name] = {"error": f"{type(exc).__name__}: {exc}"}
    return data


def main() -> int:
    sw = connect_solidworks(visible=True)
    asm = new_assembly(sw)
    comp = add_component(sw, asm, PART_PATH, name="probe_part", xyz_mm=(0, 0, 0))
    data = {
        "assembly": describe(asm),
        "component": describe(comp),
        "extension": describe(asm.Extension),
        "sw": describe(sw),
    }
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
