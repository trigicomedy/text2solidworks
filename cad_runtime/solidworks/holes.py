from __future__ import annotations

from .features import extrude_cut_through_all, rebuild_model
from .selection import clear_selection
from .sketches import begin_sketch_on_plane, draw_circle, end_sketch
from .units import mm


def cut_simple_through_hole(
    model,
    name: str,
    plane_name: str,
    center_mm: tuple[float, float],
    diameter_mm: float,
    *,
    preferred_reverse_direction: bool | None = True,
):
    sketch_name = f"SK_{name}"
    begin_sketch_on_plane(model, plane_name)
    draw_circle(model, center_mm[0], center_mm[1], diameter_mm / 2)
    end_sketch(model, sketch_name)
    return extrude_cut_through_all(model, name, preferred_reverse_direction=preferred_reverse_direction)


def cut_blind_hole(
    model,
    name: str,
    plane_name: str,
    center_mm: tuple[float, float],
    diameter_mm: float,
    depth_mm: float,
    *,
    reverse_direction: bool = True,
):
    sketch_name = f"SK_{name}"
    begin_sketch_on_plane(model, plane_name)
    draw_circle(model, center_mm[0], center_mm[1], diameter_mm / 2)
    end_sketch(model, sketch_name)
    attempts = [
        ("FeatureCut4 blind", lambda: model.FeatureManager.FeatureCut4(
            True, False, reverse_direction,
            0, 0,
            mm(depth_mm), 0,
            False, False, False, False,
            0, 0,
            False, False, False, False,
            False, True, True, True, True,
            False,
            0, 0,
            False, False,
        )),
        ("FeatureCut3 blind", lambda: model.FeatureManager.FeatureCut3(
            True, False, reverse_direction,
            0, 0,
            mm(depth_mm), 0,
            False, False, False, False,
            0, 0,
            False, False, False, False,
            False, True, True, True, True,
            False,
            0, 0,
            False,
        )),
    ]
    errors = []
    for label, call in attempts:
        try:
            feature = call()
            if feature is not None:
                feature.Name = name
                rebuild_model(model)
                return feature
        except Exception as exc:
            errors.append(f"{label}: {exc}")
    raise RuntimeError(f"Blind hole cut failed: {name}. Attempts: {'; '.join(errors)}")


def cut_counterbore_hole(
    model,
    name: str,
    plane_name: str,
    center_mm: tuple[float, float],
    through_diameter_mm: float,
    counterbore_diameter_mm: float,
    counterbore_depth_mm: float,
    *,
    preferred_reverse_direction: bool | None = True,
):
    through = cut_simple_through_hole(
        model,
        f"{name}_THROUGH_D{through_diameter_mm:g}",
        plane_name,
        center_mm,
        through_diameter_mm,
        preferred_reverse_direction=preferred_reverse_direction,
    )
    counterbore = cut_blind_hole(
        model,
        f"{name}_COUNTERBORE_D{counterbore_diameter_mm:g}",
        plane_name,
        center_mm,
        counterbore_diameter_mm,
        counterbore_depth_mm,
        reverse_direction=bool(preferred_reverse_direction),
    )
    return {"through": through, "counterbore": counterbore}


def create_hole_wizard_placeholder(*_args, **_kwargs):
    raise NotImplementedError("Hole Wizard wrapper is planned but not yet verified in this SW2025 COM environment.")
