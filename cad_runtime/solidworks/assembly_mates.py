from __future__ import annotations

from dataclasses import dataclass

from .assembly_references import AssemblyRef, select_two_references
from .selection import clear_selection
from .units import mm


MATE_TYPES = {
    "coincident": 0,
    "concentric": 1,
    "distance": 5,
    "parallel": 3,
    "angle": 6,
}

ALIGNMENTS = {
    "aligned": 0,
    "anti_aligned": 1,
    "closest": 2,
}


@dataclass(frozen=True)
class MateResult:
    name: str
    mate_type: str
    api: str
    status: int | None
    mate: object


def mate_coincident(assembly, name: str, a: AssemblyRef, b: AssemblyRef, *, alignment: str = "aligned"):
    return add_mate(assembly, name, "coincident", a, b, alignment=alignment)


def mate_concentric(assembly, name: str, a: AssemblyRef, b: AssemblyRef, *, alignment: str = "aligned"):
    return add_mate(assembly, name, "concentric", a, b, alignment=alignment)


def mate_parallel(assembly, name: str, a: AssemblyRef, b: AssemblyRef, *, alignment: str = "aligned"):
    return add_mate(assembly, name, "parallel", a, b, alignment=alignment)


def mate_distance(assembly, name: str, a: AssemblyRef, b: AssemblyRef, distance_mm: float, *, alignment: str = "aligned"):
    return add_mate(assembly, name, "distance", a, b, distance_mm=distance_mm, alignment=alignment)


def mate_angle(assembly, name: str, a: AssemblyRef, b: AssemblyRef, angle_deg: float, *, alignment: str = "aligned"):
    return add_mate(assembly, name, "angle", a, b, angle_deg=angle_deg, alignment=alignment)


def add_mate(
    assembly,
    name: str,
    mate_type: str,
    a: AssemblyRef,
    b: AssemblyRef,
    *,
    distance_mm: float = 0.0,
    angle_deg: float = 0.0,
    alignment: str = "aligned",
):
    """Select two references and create a SolidWorks mate with fallbacks."""
    select_two_references(assembly, a, b)
    mate_code = MATE_TYPES[mate_type]
    align_code = ALIGNMENTS[alignment]
    distance = mm(distance_mm)
    angle = angle_deg * 3.141592653589793 / 180.0

    errors: list[str] = []
    attempts = [
        ("AddMate5", lambda status: assembly.AddMate5(
            mate_code, align_code, False,
            distance, distance, distance,
            angle, angle,
            0.0, 0.0, 0.0,
            False, False,
            0,
            status,
        )),
        ("AddMate3", lambda status: assembly.AddMate3(
            mate_code, align_code, False,
            distance, distance, distance,
            angle, angle,
            0.0, 0.0, 0.0,
            False,
            status,
        )),
        ("AddMate2", lambda status: assembly.AddMate2(
            mate_code, align_code, False,
            distance, distance, distance,
            angle, angle,
            0.0, 0.0, 0.0,
            False,
            status,
        )),
    ]
    try:
        for api_name, call in attempts:
            status = _byref_i4(0)
            try:
                mate = call(status)
                if mate is not None:
                    try:
                        mate.Name = name
                    except Exception:
                        pass
                    return MateResult(name, mate_type, api_name, getattr(status, "value", None), mate)
                errors.append(f"{api_name}: mate=None status={getattr(status, 'value', None)}")
            except Exception as exc:
                errors.append(f"{api_name}: {exc}")
    finally:
        clear_selection(assembly)

    raise RuntimeError(f"Failed to create mate {name} ({mate_type}). Attempts: {'; '.join(errors)}")


def _byref_i4(value: int = 0):
    import pythoncom
    import win32com.client

    return win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, value)
