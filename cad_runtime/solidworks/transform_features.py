from __future__ import annotations

from .features import rebuild_model
from .patterns import iter_features, select_by_id_with_mark, select_feature, select_pattern_axis
from .selection import clear_selection, select_plane


def _select_plane_with_mark(model, plane_name: str, append: bool, mark: int) -> bool:
    for entity_type in ("PLANE", "DATUMPLANE"):
        if select_by_id_with_mark(model, plane_name, entity_type, append, mark):
            return True
        if plane_name == "Right Plane" and select_by_id_with_mark(model, "右视基准面", entity_type, append, mark):
            return True
        if plane_name == "Front Plane" and select_by_id_with_mark(model, "前视基准面", entity_type, append, mark):
            return True
        if plane_name == "Top Plane" and select_by_id_with_mark(model, "上视基准面", entity_type, append, mark):
            return True
    return False


def _finish_feature_result(model, result, name: str):
    if result is True:
        features = iter_features(model)
        feature = features[-1] if features else None
        if feature is not None:
            try:
                feature.Name = name
            except Exception:
                pass
        rebuild_model(model)
        return feature or True
    if result is not None and result is not False:
        result.Name = name
        rebuild_model(model)
        return result
    return None


def mirror_feature(model, name: str, seed_feature_name: str, mirror_plane_name: str, *, geometry_pattern: bool = False):
    """Create a native mirror feature from a seed feature and mirror plane.

    This wrapper is an initial API entry point and should be validated with a
    dedicated minimum part before production use.
    """
    errors = []

    def select_feature_then_plane(feature_mark: int, plane_mark: int) -> None:
        clear_selection(model)
        select_feature(model, seed_feature_name, append=False, mark=feature_mark)
        if not _select_plane_with_mark(model, mirror_plane_name, append=True, mark=plane_mark):
            select_pattern_axis(model, mirror_plane_name, append=True, mark=plane_mark)

    def select_plane_then_feature(plane_mark: int, feature_mark: int) -> None:
        clear_selection(model)
        if not _select_plane_with_mark(model, mirror_plane_name, append=False, mark=plane_mark):
            select_plane(model, mirror_plane_name, append=False)
        select_feature(model, seed_feature_name, append=True, mark=feature_mark)

    strategies = [
        ("feature0_plane0", lambda: select_feature_then_plane(0, 0)),
        ("plane0_feature0", lambda: select_plane_then_feature(0, 0)),
        ("feature1_plane2", lambda: select_feature_then_plane(1, 2)),
        ("feature4_plane1", lambda: select_feature_then_plane(4, 1)),
    ]
    calls = [
        ("ModelDoc.InsertMirrorFeature", lambda: model.InsertMirrorFeature(geometry_pattern)),
        ("FeatureManager.InsertMirrorFeature", lambda: model.FeatureManager.InsertMirrorFeature(False, geometry_pattern, False, False)),
        ("FeatureManager.InsertMirrorFeature2", lambda: model.FeatureManager.InsertMirrorFeature2(False, geometry_pattern, False, False, 0)),
    ]

    for strategy_label, select_strategy in strategies:
        try:
            select_strategy()
        except Exception as exc:
            errors.append(f"{strategy_label} selection: {exc}")
            continue
        for label, call in calls:
            try:
                feature = _finish_feature_result(model, call(), name)
                if feature is not None:
                    return feature
            except Exception as exc:
                errors.append(f"{strategy_label} {label}: {exc}")
            try:
                select_strategy()
            except Exception:
                break
    for label, call in [("FeatureMirror", lambda: model.FeatureManager.FeatureMirror(False, geometry_pattern, False, False))]:
        try:
            select_feature_then_plane(0, 0)
            feature = _finish_feature_result(model, call(), name)
            if feature is not None:
                return feature
        except Exception as exc:
            errors.append(f"{label}: {exc}")
    raise RuntimeError(f"Mirror feature failed: {name}. Attempts: {'; '.join(errors)}")
