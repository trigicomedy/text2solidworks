from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(r"D:\text2solidworks")
WORK_DIR = Path(r"D:\text2solidworks_workspace\debug\foundation_features")
EXPORT_DIR = WORK_DIR / "exports"
VIEW_DIR = WORK_DIR / "views"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cad_runtime.solidworks import connect_solidworks
from cad_runtime.solidworks.document import save_as
from cad_runtime.solidworks.edge_features import fillet_all_current_body_edges
from cad_runtime.solidworks.features import extrude_boss, rebuild_model
from cad_runtime.solidworks.holes import cut_counterbore_hole, cut_simple_through_hole
from cad_runtime.solidworks.references import create_offset_plane
from cad_runtime.solidworks.sketch_entities import draw_center_rectangle
from cad_runtime.solidworks.sketches import begin_sketch_on_plane, end_sketch
from cad_runtime.solidworks.views import export_named_view_images


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
    raise RuntimeError("No SolidWorks part template found.")


def main() -> int:
    sw = connect_solidworks(visible=True)
    sw.Visible = True
    model = sw.NewDocument(template(sw), 0, 0, 0)
    if model is None:
        raise RuntimeError("Failed to create part document.")

    begin_sketch_on_plane(model, "Top Plane")
    draw_center_rectangle(model, (0, 0), (50, 30))
    end_sketch(model, "SK_FOUNDATION_BLOCK")
    extrude_boss(model, "FOUNDATION_BLOCK_100X60X20", 20)
    fillet_all_current_body_edges(model, "FOUNDATION_OUTER_FILLET_R2", 2)

    cut_simple_through_hole(
        model,
        "CENTER_THROUGH_HOLE_D12",
        "Top Plane",
        (0, 0),
        12,
        preferred_reverse_direction=True,
    )
    cut_counterbore_hole(
        model,
        "RIGHT_COUNTERBORE_HOLE",
        "Top Plane",
        (28, 0),
        through_diameter_mm=8,
        counterbore_diameter_mm=18,
        counterbore_depth_mm=5,
        preferred_reverse_direction=True,
    )

    create_offset_plane(model, "PLN_MID_THICKNESS", "Top Plane", 10)
    rebuild_model(model)

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    part_path = EXPORT_DIR / "foundation_features_test.SLDPRT"
    step_path = EXPORT_DIR / "foundation_features_test.STEP"
    save_as(model, str(part_path))
    save_as(model, str(step_path))
    views = export_named_view_images(model, VIEW_DIR, pause_s=0.15)
    result = {
        "part": str(part_path),
        "step": str(step_path),
        "views": views,
    }
    (WORK_DIR / "foundation_features_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
