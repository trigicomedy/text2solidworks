from __future__ import annotations

from pathlib import Path

from .assembly_components import add_component
from .assembly_documents import new_assembly, save_assembly


def create_subassembly(sw_app, path: str | Path, component_specs: list[dict]):
    """Create a simple subassembly from component specs and save it."""
    asm = new_assembly(sw_app)
    for spec in component_specs:
        add_component(
            sw_app,
            asm,
            spec["path"],
            name=spec.get("name"),
            xyz_mm=tuple(spec.get("xyz_mm", (0, 0, 0))),
        )
    save_assembly(asm, path)
    return Path(path)


def insert_subassembly(sw_app, assembly, subassembly_path: str | Path, *, name: str | None = None, xyz_mm=(0, 0, 0)):
    return add_component(sw_app, assembly, subassembly_path, name=name, xyz_mm=xyz_mm)
