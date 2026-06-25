from __future__ import annotations

from .features import rebuild_model
from .patterns import select_feature, select_pattern_axis
from .selection import clear_selection, select_plane


def mirror_feature(model, name: str, seed_feature_name: str, mirror_plane_name: str, *, geometry_pattern: bool = False):
    """Create a native mirror feature from a seed feature and mirror plane.

    This wrapper is an initial API entry point and should be validated with a
    dedicated minimum part before production use.
    """
    clear_selection(model)
    select_feature(model, seed_feature_name, append=False, mark=1)
    try:
        select_plane(model, mirror_plane_name, append=True)
    except Exception:
        select_pattern_axis(model, mirror_plane_name, append=True, mark=2)
    attempts = [
        ("InsertMirrorFeature", lambda: model.FeatureManager.InsertMirrorFeature(False, geometry_pattern, False, False)),
        ("FeatureMirror", lambda: model.FeatureManager.FeatureMirror(False, geometry_pattern, False, False)),
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
    raise RuntimeError(f"Mirror feature failed: {name}. Attempts: {'; '.join(errors)}")
