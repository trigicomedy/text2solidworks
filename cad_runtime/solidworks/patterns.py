from __future__ import annotations

import math
from collections.abc import Callable

from .features import rebuild_model
from .selection import clear_selection, null_dispatch, select_by_id


def iter_features(model):
    try:
        return list(model.FeatureManager.GetFeatures(False) or [])
    except Exception:
        return []


def select_feature_object_by_name(model, feature_name: str, append: bool = False, mark: int = 0) -> bool:
    for feature in iter_features(model):
        try:
            if feature.Name == feature_name:
                return bool(feature.Select2(append, mark))
        except Exception:
            continue
    return False


def select_by_id_with_mark(model, name: str, entity_type: str, append: bool, mark: int) -> bool:
    try:
        return bool(model.Extension.SelectByID2(name, entity_type, 0.0, 0.0, 0.0, append, mark, null_dispatch(), 0))
    except Exception:
        return select_by_id(model, name, entity_type, append)


def select_feature(model, feature_name: str, append: bool = False, mark: int = 0) -> None:
    """Select a named feature for pattern operations."""
    if select_by_id_with_mark(model, feature_name, "BODYFEATURE", append, mark):
        return
    if select_by_id_with_mark(model, feature_name, "FEATURE", append, mark):
        return
    if select_feature_object_by_name(model, feature_name, append, mark):
        return
    raise RuntimeError(f"Failed to select feature for pattern: {feature_name}")


def select_pattern_axis(model, axis_name: str, append: bool = True, mark: int = 1) -> None:
    """Select a named axis or temporary axis for a pattern."""
    if select_by_id_with_mark(model, axis_name, "AXIS", append, mark):
        return
    if select_by_id_with_mark(model, axis_name, "DATUMAXIS", append, mark):
        return
    if select_feature_object_by_name(model, axis_name, append, mark):
        return
    raise RuntimeError(f"Failed to select pattern axis or direction: {axis_name}")


def _try_pattern_calls(name: str, calls: list[tuple[str, Callable[[], object]]]):
    errors = []
    for api_name, call in calls:
        try:
            print(f"[DEBUG] {name}: trying {api_name}")
            feature = call()
            print(f"[DEBUG] {name}: {api_name} result={feature}")
            if feature is not None:
                return feature
        except Exception as exc:
            errors.append(f"{api_name}: {exc}")
    raise RuntimeError(
        f"Native SolidWorks pattern failed: {name}. "
        f"Do not replace it with manual copies; fix selection or API signature. "
        f"Attempts: {'; '.join(errors)}"
    )


def circular_feature_pattern(
    model,
    name: str,
    seed_feature_name: str,
    axis_name: str,
    instance_count: int,
    total_angle_deg: float = 360.0,
    *,
    equal_spacing: bool = True,
    geometry_pattern: bool = True,
):
    """Create a native SolidWorks circular feature pattern.

    With SolidWorks equal spacing enabled, the Spacing argument is the total
    angular span of the pattern, not the angle between neighboring instances.
    Thus a full 4-hole bolt circle must pass 360 degrees, not 90 degrees.
    """
    if instance_count < 2:
        raise ValueError("Circular pattern requires at least 2 instances.")
    clear_selection(model)
    # Verified SW2025 selection marks: seed feature = 4, pattern axis = 1.
    select_feature(model, seed_feature_name, append=False, mark=4)
    select_pattern_axis(model, axis_name, append=True, mark=1)

    total_angle_rad = math.radians(total_angle_deg)
    spacing_rad = total_angle_rad if equal_spacing else total_angle_rad / instance_count
    fm = model.FeatureManager
    calls = [
        (
            "FeatureCircularPattern5",
            lambda: fm.FeatureCircularPattern5(
                instance_count,
                spacing_rad,
                False,
                "",
                geometry_pattern,
                equal_spacing,
                False,
                False,
                False,
                False,
                1,
                0.0,
                "",
                False,
            ),
        ),
        (
            "FeatureCircularPattern4",
            lambda: fm.FeatureCircularPattern4(
                instance_count,
                spacing_rad,
                False,
                "",
                geometry_pattern,
                equal_spacing,
                False,
            ),
        ),
        (
            "FeatureCircularPattern3",
            lambda: fm.FeatureCircularPattern3(
                instance_count,
                spacing_rad,
                False,
                "",
                geometry_pattern,
                equal_spacing,
            ),
        ),
        (
            "FeatureCircularPattern2",
            lambda: fm.FeatureCircularPattern2(
                instance_count,
                spacing_rad,
                False,
                "",
                geometry_pattern,
            ),
        ),
        (
            "FeatureCircularPattern",
            lambda: fm.FeatureCircularPattern(
                instance_count,
                spacing_rad,
                False,
                "",
            ),
        ),
    ]
    feature = _try_pattern_calls(name, calls)
    feature.Name = name
    rebuild_model(model)
    return feature


def linear_feature_pattern(
    model,
    name: str,
    seed_feature_name: str,
    direction1_name: str,
    instance_count: int,
    spacing_mm: float,
    *,
    direction2_name: str | None = None,
    instance_count_2: int = 1,
    spacing_2_mm: float = 0.0,
    geometry_pattern: bool = True,
):
    """Create a native SolidWorks linear feature pattern.

    The seed feature and direction reference must already exist and be named.
    This wrapper has no manual-copy fallback.
    """
    if instance_count < 2:
        raise ValueError("Linear pattern direction 1 requires at least 2 instances.")
    clear_selection(model)
    select_feature(model, seed_feature_name, append=False, mark=4)
    select_pattern_axis(model, direction1_name, append=True, mark=1)
    if direction2_name:
        select_pattern_axis(model, direction2_name, append=True, mark=2)

    fm = model.FeatureManager
    distance1 = spacing_mm / 1000.0
    distance2 = spacing_2_mm / 1000.0
    calls = [
        (
            "FeatureLinearPattern5",
            lambda: fm.FeatureLinearPattern5(
                instance_count,
                distance1,
                instance_count_2,
                distance2,
                False,
                False,
                direction1_name,
                direction2_name or "",
                geometry_pattern,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                0.0,
                0.0,
                False,
                False,
            ),
        ),
        (
            "FeatureLinearPattern4",
            lambda: fm.FeatureLinearPattern4(
                instance_count,
                distance1,
                instance_count_2,
                distance2,
                False,
                False,
                direction1_name,
                direction2_name or "",
                geometry_pattern,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                0.0,
                0.0,
            ),
        ),
        (
            "FeatureLinearPattern3",
            lambda: fm.FeatureLinearPattern3(
                instance_count,
                distance1,
                instance_count_2,
                distance2,
                False,
                False,
                direction1_name,
                direction2_name or "",
                geometry_pattern,
                False,
            ),
        ),
        (
            "FeatureLinearPattern2",
            lambda: fm.FeatureLinearPattern2(
                instance_count,
                distance1,
                instance_count_2,
                distance2,
                False,
                False,
                direction1_name,
                direction2_name or "",
                geometry_pattern,
            ),
        ),
        (
            "FeatureLinearPattern",
            lambda: fm.FeatureLinearPattern(
                instance_count,
                distance1,
                instance_count_2,
                distance2,
                False,
                False,
                direction1_name,
                direction2_name or "",
            ),
        ),
    ]
    feature = _try_pattern_calls(name, calls)
    feature.Name = name
    rebuild_model(model)
    return feature
