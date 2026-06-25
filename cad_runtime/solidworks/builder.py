from __future__ import annotations

from . import bodies, references, sketches, features
from .registry import CadRegistry


class SolidWorksPartBuilder:
    """Small high-level wrapper for early text-to-CAD experiments."""

    def __init__(self, model):
        self.model = model
        self.registry = CadRegistry()

    def create_box(self, name: str, length_mm: float, width_mm: float, height_mm: float, base_plane: str = "Top Plane"):
        sketches.begin_sketch_on_plane(self.model, base_plane)
        sketches.draw_center_rectangle(self.model, length_mm, width_mm)
        sketches.end_sketch(self.model, f"{name}_base_sketch")
        feature = features.extrude_boss(self.model, f"{name}_base_extrude", height_mm)

        top_plane = references.create_offset_plane(self.model, f"{name}_top_ref_plane", base_plane, height_mm)
        mid_plane = references.create_offset_plane(self.model, f"{name}_mid_ref_plane", base_plane, height_mm / 2)

        data = {
            "type": "box",
            "name": name,
            "dimensions_mm": {"length": length_mm, "width": width_mm, "height": height_mm},
            "features": {"base": feature.Name},
            "refs": {"top_plane": top_plane, "mid_plane": mid_plane},
        }
        self.registry.add_part(name, data)
        self.registry.add_ref(f"{name}.top_plane", {"kind": "reference_plane", "name": top_plane, "stability": "stable"})
        self.registry.add_ref(f"{name}.mid_plane", {"kind": "reference_plane", "name": mid_plane, "stability": "stable"})
        return data

    def draw_circle_on_plane(self, plane_name: str, sketch_name: str, center_mm: tuple[float, float], radius_mm: float):
        sketches.begin_sketch_on_plane(self.model, plane_name)
        circle = sketches.draw_circle(self.model, center_mm[0], center_mm[1], radius_mm)
        sketches.end_sketch(self.model, sketch_name)
        return circle

    def cut_hole_on_plane(self, plane_name: str, name: str, center_mm: tuple[float, float], diameter_mm: float):
        self.draw_circle_on_plane(plane_name, f"{name}_sketch", center_mm, diameter_mm / 2)
        cut = features.extrude_cut_through_all(self.model, f"{name}_cut")
        return cut.Name

    def list_faces(self):
        return bodies.summarize_faces(self.model)
