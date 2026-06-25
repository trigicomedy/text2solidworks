# Model View Export Runtime

Date: 2026-06-25

This document records the first verified implementation of model-view image export.

## Runtime Module

Use:

```python
from cad_runtime.solidworks.views import export_model_nine_view_images
```

Or from the package root:

```python
from cad_runtime.solidworks import export_model_nine_view_images
```

## Verified Functionality

The module `cad_runtime.solidworks.views` supports:

- opening an existing `SLDPRT` or `SLDASM`;
- switching SolidWorks model orientation with `ShowNamedView2`;
- zooming to fit;
- saving the current visible view as PNG through the existing `document.save_as` wrapper;
- exporting the standard 9-view image set.

Verified views:

- `front`
- `back`
- `left`
- `right`
- `top`
- `bottom`
- `isometric`
- `dimetric`
- `trimetric`

## Validation Script

Run:

```powershell
cd D:\text2solidworks
python workspace_scripts\debug_views.py
```

Verified test model:

```text
D:\text2solidworks_workspace\projects\asymmetric_round_end_link\exports\asymmetric_round_end_link.SLDPRT
```

Verified output directory:

```text
D:\text2solidworks_workspace\debug\views\asymmetric_round_end_link_9views
```

The current workstation successfully exported:

- `front.png`
- `back.png`
- `left.png`
- `right.png`
- `top.png`
- `bottom.png`
- `isometric.png`
- `dimetric.png`
- `trimetric.png`

## Notes

This is a fast visual QA path and does not require a drawing template.

Formal engineering drawing generation should be implemented separately in:

- `drawings.py`
- `drawing_views.py`
- `drawing_export.py`
- `drawing_annotations.py`
