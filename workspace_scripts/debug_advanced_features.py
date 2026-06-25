from __future__ import annotations

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(r"D:\text2solidworks")
WORK_DIR = Path(r"D:\text2solidworks_workspace\debug\advanced_features")
EXPORT_DIR = WORK_DIR / "exports"
LOG_DIR = WORK_DIR / "logs"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cad_runtime.solidworks import connect_solidworks
from cad_runtime.solidworks.advanced_features import (
    loft_boss,
    loft_cut,
    revolve_boss,
    revolve_cut,
    sweep_boss,
    sweep_cut,
)
from cad_runtime.solidworks.document import save_as
from cad_runtime.solidworks.features import extrude_boss, rebuild_model
from cad_runtime.solidworks.selection import clear_selection, select_plane
from cad_runtime.solidworks.sketches import begin_sketch_on_plane, draw_circle, end_sketch
from cad_runtime.solidworks.units import mm


def log(message: str) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    print(line, flush=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with (LOG_DIR / "debug_advanced_features.log").open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def template(sw) -> str:
    path = sw.GetUserPreferenceStringValue(1)
    if path and Path(path).exists():
        return path
    for candidate in [
        Path(r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\templates\gb_part.prtdot"),
        Path(r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\templates\Part.prtdot"),
    ]:
        if candidate.exists():
            return str(candidate)
    raise RuntimeError("No part template found")


def new_part(sw, label: str):
    model = sw.NewDocument(template(sw), 0, 0, 0)
    if model is None:
        raise RuntimeError(f"Could not create part for {label}")
    log(f"New part: {label}")
    return model


def view(model):
    rebuild_model(model)
    try:
        model.ViewZoomtofit2()
    except Exception:
        pass
    time.sleep(0.3)


def save(model, name: str):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    target = EXPORT_DIR / f"{name}.SLDPRT"
    save_as(model, str(target))
    log(f"Saved: {target}")
    return str(target)


def create_offset_plane(model, name: str, offset_mm: float):
    clear_selection(model)
    select_plane(model, "Top Plane")
    feature = model.FeatureManager.InsertRefPlane(8, mm(offset_mm), 0, 0, 0, 0)
    if feature is None:
        raise RuntimeError(f"Failed to create plane {name}")
    feature.Name = name
    view(model)


def make_revolve_boss(sw):
    model = new_part(sw, "revolve_boss")
    begin_sketch_on_plane(model, "Front Plane")
    sm = model.SketchManager
    sm.CreateCenterLine(0, mm(-35), 0, 0, mm(35), 0)
    sm.CreateLine(mm(12), mm(-25), 0, mm(20), mm(-15), 0)
    sm.CreateLine(mm(20), mm(-15), 0, mm(20), mm(15), 0)
    sm.CreateLine(mm(20), mm(15), 0, mm(12), mm(25), 0)
    sm.CreateLine(mm(12), mm(25), 0, mm(12), mm(-25), 0)
    end_sketch(model, "SK_REVOLVE_BOSS_PROFILE")
    revolve_boss(model, "REVOLVE_BOSS_TEST", 360)
    view(model)
    return save(model, "revolve_boss_test")


def make_revolve_cut(sw):
    model = new_part(sw, "revolve_cut")
    begin_sketch_on_plane(model, "Top Plane")
    draw_circle(model, 0, 0, 30)
    end_sketch(model, "SK_REV_CUT_BASE")
    extrude_boss(model, "REV_CUT_BASE_CYL", 60)
    view(model)
    begin_sketch_on_plane(model, "Front Plane")
    sm = model.SketchManager
    sm.CreateCenterLine(0, mm(-40), 0, 0, mm(80), 0)
    sm.CreateLine(mm(18), mm(20), 0, mm(30), mm(28), 0)
    sm.CreateLine(mm(30), mm(28), 0, mm(30), mm(34), 0)
    sm.CreateLine(mm(30), mm(34), 0, mm(18), mm(42), 0)
    sm.CreateLine(mm(18), mm(42), 0, mm(18), mm(20), 0)
    end_sketch(model, "SK_REVOLVE_CUT_PROFILE")
    revolve_cut(model, "REVOLVE_CUT_TEST", 360)
    view(model)
    return save(model, "revolve_cut_test")


def make_sweep_boss(sw):
    model = new_part(sw, "sweep_boss")
    begin_sketch_on_plane(model, "Top Plane")
    sm = model.SketchManager
    sm.CreateLine(0, 0, 0, mm(90), 0, 0)
    end_sketch(model, "SK_SWEEP_BOSS_PATH")
    begin_sketch_on_plane(model, "Right Plane")
    draw_circle(model, 0, 0, 5)
    end_sketch(model, "SK_SWEEP_BOSS_PROFILE")
    sweep_boss(model, "SWEEP_BOSS_TEST", "SK_SWEEP_BOSS_PROFILE", "SK_SWEEP_BOSS_PATH")
    view(model)
    return save(model, "sweep_boss_test")


def make_sweep_cut(sw):
    model = new_part(sw, "sweep_cut")
    begin_sketch_on_plane(model, "Top Plane")
    model.SketchManager.CreateCenterRectangle(mm(45), 0, 0, mm(95), mm(22), 0)
    end_sketch(model, "SK_SWEEP_CUT_BLOCK")
    extrude_boss(model, "SWEEP_CUT_BASE_BLOCK", 30)
    view(model)
    begin_sketch_on_plane(model, "Top Plane")
    model.SketchManager.CreateLine(0, 0, 0, mm(80), 0, 0)
    end_sketch(model, "SK_SWEEP_CUT_PATH")
    begin_sketch_on_plane(model, "Right Plane")
    draw_circle(model, 0, 8, 3)
    end_sketch(model, "SK_SWEEP_CUT_PROFILE")
    sweep_cut(model, "SWEEP_CUT_TEST", "SK_SWEEP_CUT_PROFILE", "SK_SWEEP_CUT_PATH")
    view(model)
    return save(model, "sweep_cut_test")


def make_loft_boss(sw):
    model = new_part(sw, "loft_boss")
    begin_sketch_on_plane(model, "Top Plane")
    draw_circle(model, 0, 0, 14)
    end_sketch(model, "SK_LOFT_BOSS_SECTION_1")
    create_offset_plane(model, "PLN_LOFT_BOSS_2", 45)
    begin_sketch_on_plane(model, "PLN_LOFT_BOSS_2")
    draw_circle(model, 0, 0, 8)
    end_sketch(model, "SK_LOFT_BOSS_SECTION_2")
    loft_boss(model, "LOFT_BOSS_TEST", ["SK_LOFT_BOSS_SECTION_1", "SK_LOFT_BOSS_SECTION_2"])
    view(model)
    return save(model, "loft_boss_test")


def make_loft_cut(sw):
    model = new_part(sw, "loft_cut")
    begin_sketch_on_plane(model, "Top Plane")
    draw_circle(model, 0, 0, 25)
    end_sketch(model, "SK_LOFT_CUT_BASE")
    extrude_boss(model, "LOFT_CUT_BASE_CYL", 60)
    view(model)
    begin_sketch_on_plane(model, "Top Plane")
    draw_circle(model, 0, 0, 8)
    end_sketch(model, "SK_LOFT_CUT_SECTION_1")
    create_offset_plane(model, "PLN_LOFT_CUT_2", 60)
    begin_sketch_on_plane(model, "PLN_LOFT_CUT_2")
    draw_circle(model, 0, 0, 16)
    end_sketch(model, "SK_LOFT_CUT_SECTION_2")
    loft_cut(model, "LOFT_CUT_TEST", ["SK_LOFT_CUT_SECTION_1", "SK_LOFT_CUT_SECTION_2"])
    view(model)
    return save(model, "loft_cut_test")


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / "debug_advanced_features.log").write_text("", encoding="utf-8")
    sw = connect_solidworks(visible=True)
    sw.Visible = True
    results = {}
    for name, func in [
        ("revolve_boss", make_revolve_boss),
        ("revolve_cut", make_revolve_cut),
        ("sweep_boss", make_sweep_boss),
        ("sweep_cut", make_sweep_cut),
        ("loft_boss", make_loft_boss),
        ("loft_cut", make_loft_cut),
    ]:
        try:
            results[name] = {"status": "ok", "file": func(sw)}
        except Exception as exc:
            log(f"FAILED {name}: {type(exc).__name__}: {exc}")
            results[name] = {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
    (LOG_DIR / "debug_advanced_features_result.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(v["status"] == "ok" for v in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
