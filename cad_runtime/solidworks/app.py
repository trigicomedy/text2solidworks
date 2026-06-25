from __future__ import annotations

try:
    import win32com.client
except ImportError as exc:
    raise RuntimeError(
        "pywin32 is required for SolidWorks COM automation. "
        "Install Python 3.10+ and run: python -m pip install -r requirements.txt"
    ) from exc


def connect_solidworks(visible: bool = True):
    """Connect to a running SolidWorks instance or start one through COM."""
    sw_app = win32com.client.Dispatch("SldWorks.Application")
    sw_app.Visible = visible
    return sw_app
