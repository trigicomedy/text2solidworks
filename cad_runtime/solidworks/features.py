from __future__ import annotations

from .constants import SW_END_COND_BLIND, SW_END_COND_THROUGH_ALL
from .units import mm


def rebuild_model(model):
    try:
        rebuild = getattr(model, "ForceRebuild3", None)
        if callable(rebuild):
            return rebuild(False)
    except Exception:
        pass
    try:
        rebuild = getattr(model, "EditRebuild3", None)
        if callable(rebuild):
            return rebuild()
    except Exception:
        pass
    return None


def extrude_boss(model, name: str, depth_mm: float):
    attempts = [
        (
            "FeatureExtrusion2",
            lambda: model.FeatureManager.FeatureExtrusion2(
                True, False, False,
                SW_END_COND_BLIND, SW_END_COND_BLIND,
                mm(depth_mm), 0,
                False, False, False, False,
                0, 0,
                False, False, False, False,
                True, True, True,
                0, 0,
                False,
            ),
        ),
        (
            "FeatureExtrusion3",
            lambda: model.FeatureManager.FeatureExtrusion3(
                True, False, False,
                SW_END_COND_BLIND, SW_END_COND_BLIND,
                mm(depth_mm), 0,
                False, False, False, False,
                0, 0,
                False, False, False, False,
                True, True, True,
                0, 0,
                False,
                0, 0,
                False,
            ),
        ),
    ]
    errors = []
    for api_name, call in attempts:
        try:
            print(f"[DEBUG] extrude_boss {name}: trying {api_name}")
            feature = call()
            print(f"[DEBUG] extrude_boss {name}: {api_name} result={feature}")
            if feature is not None:
                feature.Name = name
                rebuild_model(model)
                return feature
        except Exception as exc:
            errors.append(f"{api_name}: {exc}")
    raise RuntimeError(
        f"Failed to create boss extrusion: {name}. "
        f"Confirm that one closed sketch is selected. Attempts: {'; '.join(errors)}"
    )


def extrude_cut_through_all(
    model,
    name: str,
    fallback_depth_mm: float = 1000.0,
    preferred_reverse_direction: bool | None = None,
):
    attempts = []
    directions = (
        (preferred_reverse_direction, not preferred_reverse_direction)
        if preferred_reverse_direction is not None
        else (False, True)
    )
    for reverse_direction in directions:
        attempts.extend(
            [
                (
                    f"FeatureCut4 through_all reverse={reverse_direction}",
                    lambda reverse_direction=reverse_direction: model.FeatureManager.FeatureCut4(
                        True, False, reverse_direction,
                        SW_END_COND_THROUGH_ALL, SW_END_COND_BLIND,
                        0, 0,
                        False, False, False, False,
                        0, 0,
                        False, False, False, False,
                        False, True, True, True, True,
                        False,
                        0, 0,
                        False, False,
                    ),
                ),
                (
                    f"FeatureCut3 through_all reverse={reverse_direction}",
                    lambda reverse_direction=reverse_direction: model.FeatureManager.FeatureCut3(
                        True, False, reverse_direction,
                        SW_END_COND_THROUGH_ALL, SW_END_COND_BLIND,
                        0, 0,
                        False, False, False, False,
                        0, 0,
                        False, False, False, False,
                        False, True, True, True, True,
                        False,
                        0, 0,
                        False,
                    ),
                ),
                (
                    f"FeatureCut4 blind reverse={reverse_direction}",
                    lambda reverse_direction=reverse_direction: model.FeatureManager.FeatureCut4(
                        True, False, reverse_direction,
                        SW_END_COND_BLIND, SW_END_COND_BLIND,
                        mm(fallback_depth_mm), 0,
                        False, False, False, False,
                        0, 0,
                        False, False, False, False,
                        False, True, True, True, True,
                        False,
                        0, 0,
                        False, False,
                    ),
                ),
                (
                    f"FeatureCut3 blind reverse={reverse_direction}",
                    lambda reverse_direction=reverse_direction: model.FeatureManager.FeatureCut3(
                        True, False, reverse_direction,
                        SW_END_COND_BLIND, SW_END_COND_BLIND,
                        mm(fallback_depth_mm), 0,
                        False, False, False, False,
                        0, 0,
                        False, False, False, False,
                        False, True, True, True, True,
                        False,
                        0, 0,
                        False,
                    ),
                ),
            ]
        )
    errors = []
    for api_name, call in attempts:
        try:
            print(f"[DEBUG] extrude_cut_through_all {name}: trying {api_name}")
            feature = call()
            print(f"[DEBUG] extrude_cut_through_all {name}: {api_name} result={feature}")
            if feature is not None:
                feature.Name = name
                rebuild_model(model)
                return feature
        except Exception as exc:
            errors.append(f"{api_name}: {exc}")
    raise RuntimeError(
        f"Failed to create through cut: {name}. "
        f"Confirm that a valid closed cut sketch is selected. Attempts: {'; '.join(errors)}"
    )
