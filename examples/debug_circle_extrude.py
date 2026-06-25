from __future__ import annotations

import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pythoncom
import win32com.client

from cad_runtime.solidworks import connect_solidworks
from cad_runtime.solidworks.document import save_as
from cad_runtime.solidworks.features import extrude_boss
from cad_runtime.solidworks.sketches import (
    begin_sketch_on_plane,
    draw_circle,
    end_sketch,
)
from cad_runtime.solidworks.units import mm

WORKSPACE = Path(r"D:\text2solidworks_workspace")
OUT_DIR = WORKSPACE / "exports" / "debug"


def null_dispatch():
    return win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)


def pause(label: str, seconds: float = 1.5):
    print(f"[STEP] {label}")
    time.sleep(seconds)


def user_template(sw, kind: str) -> str:
    env_name = {"part": "TEXT2SW_PART_TEMPLATE", "assembly": "TEXT2SW_ASSEMBLY_TEMPLATE"}[kind]
    env_path = os.environ.get(env_name)
    if env_path and Path(env_path).exists():
        return env_path

    filenames = {
        "part": ["gb_part.prtdot", "Part.prtdot"],
        "assembly": ["gb_assembly.asmdot", "Assembly.asmdot"],
    }[kind]
    for root in [Path(r"C:\ProgramData\SOLIDWORKS"), Path(r"C:\ProgramData\SolidWorks")]:
        if root.exists():
            for filename in filenames:
                found = list(root.glob(f"**/{filename}"))
                if found:
                    return str(sorted(found, key=lambda p: ("2025" not in str(p), str(p)))[0])
    raise RuntimeError(f"No SolidWorks template found for {kind}.")


def rebuild(model):
    for name, args in (("ForceRebuild3", (False,)), ("EditRebuild3", ())):
        try:
            method = getattr(model, name, None)
            if callable(method):
                return method(*args)
        except Exception as exc:
            print(f"[WARN] rebuild via {name} failed: {exc}")
    return None


def select_top_plane(model):
    for name in ["Top Plane", "上视基准面", "上基准面"]:
        try:
            ok = model.Extension.SelectByID2(name, "PLANE", 0.0, 0.0, 0.0, False, 0, null_dispatch(), 0)
            print(f"[DEBUG] select plane {name!r}: {ok}")
            if ok:
                return name
        except Exception as exc:
            print(f"[WARN] select plane {name!r} failed: {exc}")
    raise RuntimeError("Could not select Top Plane.")


def try_extrude(model, depth_mm: float):
    calls = []

    def call2():
        return model.FeatureManager.FeatureExtrusion2(
            True, False, False,
            0, 0,
            mm(depth_mm), 0,
            False, False, False, False,
            0, 0,
            False, False, False, False,
            True, True, True,
            0, 0,
            False,
        )

    calls.append(("FeatureExtrusion2", call2))

    def call3():
        return model.FeatureManager.FeatureExtrusion3(
            True, False, False,
            0, 0,
            mm(depth_mm), 0,
            False, False, False, False,
            0, 0,
            False, False, False, False,
            True, True, True,
            0, 0,
            False,
            0, 0,
            False,
        )

    calls.append(("FeatureExtrusion3", call3))

    for name, fn in calls:
        try:
            print(f"[DEBUG] trying {name}")
            feat = fn()
            print(f"[DEBUG] {name} result: {feat}")
            if feat is not None:
                try:
                    feat.Name = "debug_circle_extrude"
                except Exception:
                    pass
                rebuild(model)
                return feat
        except Exception as exc:
            print(f"[WARN] {name} raised: {exc}")
    return None


def main():
    sw = connect_solidworks(visible=True)
    try:
        sw.Visible = True
        sw.FrameState = 1
    except Exception:
        pass

    template = user_template(sw, "part")
    print(f"[DEBUG] template: {template}")
    model = sw.NewDocument(template, 0, 0, 0)
    if model is None:
        raise RuntimeError("Failed to create new part document.")
    pause("created new part")

    begin_sketch_on_plane(model, "Top Plane")
    pause("entered sketch")

    circle = draw_circle(model, 0.0, 0.0, 40.0)
    print(f"[DEBUG] circle: {circle}")
    pause("created circle")

    selected_sketch = end_sketch(model, "debug_circle_profile")
    print(f"[DEBUG] selected sketch: {selected_sketch}")
    pause("exited and selected sketch")

    pause("about to extrude")
    feat = extrude_boss(model, "debug_circle_extrude", 20)
    print(f"[DEBUG] extrusion result: {feat}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    save_as(model, str(OUT_DIR / "debug_circle_extrude.SLDPRT"))
    print(f"[OK] saved: {OUT_DIR / 'debug_circle_extrude.SLDPRT'}")


if __name__ == "__main__":
    main()
