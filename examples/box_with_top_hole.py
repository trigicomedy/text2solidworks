from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pathlib import Path

from cad_runtime.solidworks import SolidWorksPartBuilder, connect_solidworks
from cad_runtime.solidworks.document import new_part, save_as


EXPORT_DIR = Path(r"D:\text2solidworks_workspace\exports")


def main():
    sw = connect_solidworks(visible=True)
    model = new_part(sw)
    cad = SolidWorksPartBuilder(model)

    box = cad.create_box("base_block", length_mm=50, width_mm=50, height_mm=50)
    cad.cut_hole_on_plane(
        plane_name=box["refs"]["top_plane"],
        name="center_top_hole",
        center_mm=(0, 0),
        diameter_mm=12,
    )

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    save_as(model, str(EXPORT_DIR / "box_with_top_hole.SLDPRT"))
    print("Created box_with_top_hole.SLDPRT")


if __name__ == "__main__":
    main()

