from __future__ import annotations

import platform
import sys


def main() -> int:
    print(f"Python: {sys.version.split()[0]}")
    print(f"Executable: {sys.executable}")
    print(f"Platform: {platform.platform()}")

    if sys.version_info < (3, 10):
        print("ERROR: Python 3.10 or newer is recommended.")
        return 1

    if platform.system() != "Windows":
        print("ERROR: SolidWorks COM automation requires Windows.")
        return 1

    try:
        import win32com.client  # noqa: F401
    except ImportError:
        print("ERROR: pywin32 is not installed.")
        print("Install it with:")
        print("  python -m pip install -r requirements.txt")
        return 1

    print("pywin32: ok")
    print("Environment check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
