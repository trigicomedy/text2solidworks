# Windows Installation

This project controls SolidWorks through the Windows COM API, so it needs:

1. Windows
2. SolidWorks installed and licensed
3. Python 3.10 or newer
4. `pywin32`

## Install Python

Download Python from:

https://www.python.org/downloads/windows/

During installation, enable:

- Add python.exe to PATH

Then open PowerShell and check:

```powershell
python --version
```

## Install dependencies

From this project folder:

```powershell
cd D:\text2solidworks
python -m pip install -r requirements.txt
```

## Run smoke tests

Create a cube and draw a circle on its top reference plane:

```powershell
python examples\box_with_top_circle.py
```

Create a cube and cut a through hole from its top reference plane:

```powershell
python examples\box_with_top_hole.py
```

Outputs are saved to:

```text
D:\text2solidworks_workspace\exports
```

If Python is not found, install it first and make sure `python.exe` is on PATH.
If `win32com` is not found, run `python -m pip install -r requirements.txt`.
