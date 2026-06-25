from __future__ import annotations

import math

from .constants import SW_END_COND_BLIND
from .features import rebuild_model
from .selection import clear_selection, null_dispatch, select_by_id
from .units import mm


def select_sketch(model, name: str, *, append: bool = False, mark: int = 0) -> bool:
    return bool(model.Extension.SelectByID2(name, "SKETCH", 0.0, 0.0, 0.0, append, mark, null_dispatch(), 0))


def select_axis(model, name: str, *, append: bool = False, mark: int = 0) -> bool:
    for entity_type in ("AXIS", "REFAXIS"):
        try:
            if model.Extension.SelectByID2(name, entity_type, 0.0, 0.0, 0.0, append, mark, null_dispatch(), 0):
                return True
        except Exception:
            continue
    return False


def _finish_feature(model, feature, name: str):
    if feature is not None:
        feature.Name = name
        rebuild_model(model)
        return feature
    return None


def revolve_boss(
    model,
    name: str,
    angle_deg: float = 360.0,
    *,
    reverse_direction: bool = False,
    merge_result: bool = True,
):
    """Create a native revolved boss/base from the currently selected sketch.

    Expected selection:
    - a closed profile sketch
    - preferably a construction centerline in that sketch, or a selected datum axis

    This wrapper intentionally uses native SolidWorks revolve APIs only.
    """
    angle_rad = math.radians(angle_deg)
    attempts = [
        (
            "FeatureRevolve2 boss/base",
            lambda: model.FeatureManager.FeatureRevolve2(
                True, True, False, False,
                reverse_direction, False,
                SW_END_COND_BLIND, SW_END_COND_BLIND,
                angle_rad, 0,
                False, False,
                0, 0,
                0, 0, 0,
                merge_result, True, True,
            ),
        ),
    ]
    errors = []
    for api_name, call in attempts:
        try:
            print(f"[DEBUG] revolve_boss {name}: trying {api_name}")
            feature = call()
            print(f"[DEBUG] revolve_boss {name}: {api_name} result={feature}")
            if _finish_feature(model, feature, name):
                return feature
        except Exception as exc:
            errors.append(f"{api_name}: {exc}")
    raise RuntimeError(f"Failed to create revolved boss: {name}. Attempts: {'; '.join(errors)}")


def revolve_cut(
    model,
    name: str,
    angle_deg: float = 360.0,
    *,
    reverse_direction: bool = False,
):
    """Create a native revolved cut from the currently selected sketch."""
    angle_rad = math.radians(angle_deg)
    attempts = [
        (
            "FeatureRevolve2 cut",
            lambda: model.FeatureManager.FeatureRevolve2(
                True, True, False, True,
                reverse_direction, False,
                SW_END_COND_BLIND, SW_END_COND_BLIND,
                angle_rad, 0,
                False, False,
                0, 0,
                0, 0, 0,
                True, True, True,
            ),
        ),
    ]
    errors = []
    for api_name, call in attempts:
        try:
            print(f"[DEBUG] revolve_cut {name}: trying {api_name}")
            feature = call()
            print(f"[DEBUG] revolve_cut {name}: {api_name} result={feature}")
            if _finish_feature(model, feature, name):
                return feature
        except Exception as exc:
            errors.append(f"{api_name}: {exc}")
    raise RuntimeError(f"Failed to create revolved cut: {name}. Attempts: {'; '.join(errors)}")


def sweep_boss(
    model,
    name: str,
    profile_sketch: str,
    path_sketch: str,
    *,
    merge_result: bool = True,
):
    """Create a native swept boss/base from a selected profile and path sketch."""
    errors = []
    selection_attempts = [
        ("profile mark 1, path mark 4", 1, 4),
        ("profile mark 0, path mark 0", 0, 0),
    ]
    call_attempts = [
        (
            "InsertProtrusionSwept legacy 14-arg verified",
            lambda: model.FeatureManager.InsertProtrusionSwept(
                False, False, False, False, False, False, False,
                False, False, False, False, False, False, False,
            ),
        ),
    ]
    for selection_label, profile_mark, path_mark in selection_attempts:
        clear_selection(model)
        ok_profile = select_sketch(model, profile_sketch, append=False, mark=profile_mark)
        ok_path = select_sketch(model, path_sketch, append=True, mark=path_mark)
        if not (ok_profile and ok_path):
            errors.append(f"{selection_label}: failed to select profile/path")
            continue
        for api_name, call in call_attempts:
            try:
                print(f"[DEBUG] sweep_boss {name}: trying {selection_label}; {api_name}")
                feature = call()
                print(f"[DEBUG] sweep_boss {name}: {api_name} result={feature}")
                if _finish_feature(model, feature, name):
                    return feature
            except Exception as exc:
                errors.append(f"{selection_label}; {api_name}: {exc}")
    raise RuntimeError(f"Failed to create swept boss: {name}. Attempts: {'; '.join(errors)}")


def sweep_cut(
    model,
    name: str,
    profile_sketch: str,
    path_sketch: str,
):
    """Create a native swept cut from a selected profile and path sketch."""
    errors = []
    for selection_label, profile_mark, path_mark in (("profile mark 1, path mark 4", 1, 4), ("profile mark 0, path mark 0", 0, 0)):
        clear_selection(model)
        ok_profile = select_sketch(model, profile_sketch, append=False, mark=profile_mark)
        ok_path = select_sketch(model, path_sketch, append=True, mark=path_mark)
        if not (ok_profile and ok_path):
            errors.append(f"{selection_label}: failed to select profile/path")
            continue
        attempts = [
            (
                "InsertCutSwept legacy 13-arg",
                lambda: model.FeatureManager.InsertCutSwept(
                    False, False, False, False, False, False, False,
                    False, False, False, False, False, False,
                ),
            ),
            (
                "InsertCutSwept2 14-arg",
                lambda: model.FeatureManager.InsertCutSwept2(
                    False, False, False, False, False, False, False,
                    False, False, False, False, False, False, False,
                ),
            ),
        ]
        for api_name, call in attempts:
            try:
                print(f"[DEBUG] sweep_cut {name}: trying {selection_label}; {api_name}")
                feature = call()
                print(f"[DEBUG] sweep_cut {name}: {api_name} result={feature}")
                if _finish_feature(model, feature, name):
                    return feature
            except Exception as exc:
                errors.append(f"{selection_label}; {api_name}: {exc}")
    raise RuntimeError(f"Failed to create swept cut: {name}. Attempts: {'; '.join(errors)}")


def loft_boss(
    model,
    name: str,
    section_sketches: list[str],
    *,
    merge_result: bool = True,
):
    """Create a native lofted boss/base from ordered section sketches."""
    if len(section_sketches) < 2:
        raise ValueError("Loft requires at least two section sketches.")
    errors = []
    selection_patterns = [
        ("sections mark 1", 1),
        ("sections mark 0", 0),
    ]
    for selection_label, mark in selection_patterns:
        clear_selection(model)
        selected = []
        for index, sketch_name in enumerate(section_sketches):
            ok = select_sketch(model, sketch_name, append=index > 0, mark=mark)
            selected.append(ok)
        if not all(selected):
            errors.append(f"{selection_label}: failed selections {dict(zip(section_sketches, selected))}")
            continue
        attempts = [
            (
                "InsertProtrusionBlend legacy 17-arg verified",
                lambda: model.FeatureManager.InsertProtrusionBlend(
                    False, False, False, False, False, False, False,
                    False, False, False, False, False, False, False,
                    False, False, False,
                ),
            ),
        ]
        for api_name, call in attempts:
            try:
                print(f"[DEBUG] loft_boss {name}: trying {selection_label}; {api_name}")
                feature = call()
                print(f"[DEBUG] loft_boss {name}: {api_name} result={feature}")
                if _finish_feature(model, feature, name):
                    return feature
            except Exception as exc:
                errors.append(f"{selection_label}; {api_name}: {exc}")
    raise RuntimeError(f"Failed to create lofted boss: {name}. Attempts: {'; '.join(errors)}")


def loft_cut(model, name: str, section_sketches: list[str]):
    """Create a native lofted cut from ordered section sketches."""
    if len(section_sketches) < 2:
        raise ValueError("Loft cut requires at least two section sketches.")
    errors = []
    for selection_label, mark in (("sections mark 1", 1), ("sections mark 0", 0)):
        clear_selection(model)
        selected = []
        for index, sketch_name in enumerate(section_sketches):
            selected.append(select_sketch(model, sketch_name, append=index > 0, mark=mark))
        if not all(selected):
            errors.append(f"{selection_label}: failed selections {dict(zip(section_sketches, selected))}")
            continue
        attempts = [
            (
                "InsertCutBlend legacy 12-arg verified",
                lambda: model.FeatureManager.InsertCutBlend(
                    False, False, False, False, False, False,
                    False, False, False, False, False, False,
                ),
            ),
        ]
        for api_name, call in attempts:
            try:
                print(f"[DEBUG] loft_cut {name}: trying {selection_label}; {api_name}")
                feature = call()
                print(f"[DEBUG] loft_cut {name}: {api_name} result={feature}")
                if _finish_feature(model, feature, name):
                    return feature
            except Exception as exc:
                errors.append(f"{selection_label}; {api_name}: {exc}")
    raise RuntimeError(f"Failed to create lofted cut: {name}. Attempts: {'; '.join(errors)}")
