from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .assembly_components import component_name, get_component
from .assembly_documents import document_title
from .selection import clear_selection, null_dispatch


REFERENCE_TYPES = {
    "plane": ("PLANE", "DATUMPLANE", ""),
    "axis": ("AXIS", "DATUMAXIS", ""),
    "coordinate_system": ("COORDSYS", "COORDINATESYSTEM", ""),
    "face": ("FACE", ""),
    "edge": ("EDGE", ""),
    "feature": ("BODYFEATURE", "FEATURE", ""),
}


@dataclass(frozen=True)
class AssemblyRef:
    """A planned reference inside one assembly component."""

    component: str
    entity_type: str
    name: str


def select_component_reference(assembly, ref: AssemblyRef, *, append: bool = False, mark: int = 0) -> str:
    """Select a named reference inside a component.

    The most reliable SW2025 form observed so far is:
    `reference@ComponentInstance@AssemblyTitle`.
    """
    component = get_component(assembly, ref.component)
    comp_name = component_name(component) or f"{ref.component}-1"
    asm_title = document_title(assembly)
    asm_stem = Path(asm_title).stem if asm_title else ""

    names = []
    if asm_title:
        names.append(f"{ref.name}@{comp_name}@{asm_title}")
    if asm_stem and asm_stem != asm_title:
        names.append(f"{ref.name}@{comp_name}@{asm_stem}")
    names.extend([
        f"{ref.name}@{comp_name}",
        f"{ref.name}@{ref.component}@{comp_name}",
        f"{ref.name}@{ref.component}-1@{comp_name}",
    ])

    ref_types = REFERENCE_TYPES.get(ref.entity_type, (ref.entity_type.upper(), ""))
    errors: list[str] = []
    if not append:
        clear_selection(assembly)

    for full_name in dict.fromkeys(names):
        for typ in ref_types:
            try:
                ok = assembly.Extension.SelectByID2(full_name, typ, 0.0, 0.0, 0.0, append, mark, null_dispatch(), 0)
                if ok:
                    return full_name
            except Exception as exc:
                errors.append(f"{full_name}/{typ}: {exc}")
    raise RuntimeError(
        f"Failed to select assembly reference {ref.component}.{ref.name} "
        f"as {ref.entity_type}. Tried {len(names) * len(ref_types)} forms. "
        f"{'; '.join(errors[:5])}"
    )


def select_two_references(assembly, a: AssemblyRef, b: AssemblyRef) -> tuple[str, str]:
    first = select_component_reference(assembly, a, append=False)
    second = select_component_reference(assembly, b, append=True)
    return first, second
