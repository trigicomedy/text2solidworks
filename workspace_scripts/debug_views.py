from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(r"D:\text2solidworks")
MODEL_PATH = Path(r"D:\text2solidworks_workspace\projects\asymmetric_round_end_link\exports\asymmetric_round_end_link.SLDPRT")
OUTPUT_DIR = Path(r"D:\text2solidworks_workspace\debug\views\asymmetric_round_end_link_9views")

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cad_runtime.solidworks import connect_solidworks
from cad_runtime.solidworks.views import export_model_nine_view_images


def main() -> int:
    sw = connect_solidworks(visible=True)
    results = export_model_nine_view_images(sw, MODEL_PATH, OUTPUT_DIR, visible=True, pause_s=0.25)
    result_file = OUTPUT_DIR / "nine_view_result.json"
    result_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    missing = [path for path in results.values() if not Path(path).exists()]
    if missing:
        raise RuntimeError(f"Missing exported view images: {missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
