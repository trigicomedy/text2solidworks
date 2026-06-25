from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from pathlib import Path

from cad_runtime.solidworks import SolidWorksPartBuilder, connect_solidworks
from cad_runtime.solidworks.document import new_part, save_as


PROJECT_WORKSPACE = Path(r"D:\text2solidworks_workspace")
EXPORT_DIR = PROJECT_WORKSPACE / "exports"
LOG_DIR = PROJECT_WORKSPACE / "logs"


def main():
    sw = connect_solidworks(visible=True)
    model = new_part(sw)
    cad = SolidWorksPartBuilder(model)

    box = cad.create_box("base_block", length_mm=50, width_mm=50, height_mm=50)
    cad.draw_circle_on_plane(
        plane_name=box["refs"]["top_plane"],
        sketch_name="base_block_top_circle_sketch",
        center_mm=(0, 0),
        radius_mm=10,
    )

    faces = cad.list_faces()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / "box_with_top_circle_faces.json").write_text(
        json.dumps(faces, indent=2),
        encoding="utf-8",
    )

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    save_as(model, str(EXPORT_DIR / "box_with_top_circle.SLDPRT"))
    print("Created box_with_top_circle.SLDPRT")
    print(json.dumps(cad.registry.parts, indent=2))


if __name__ == "__main__":
    main()

