from __future__ import annotations

from .features import rebuild_model


def add_relation(model, relation_name: str) -> None:
    """Add a SolidWorks sketch relation to the current selection.

    Common relation names include `sgCOINCIDENT`, `sgHORIZONTAL`,
    `sgVERTICAL`, `sgTANGENT`, `sgCONCENTRIC`, `sgEQUAL`,
    `sgPARALLEL`, and `sgPERPENDICULAR`.
    """
    try:
        model.SketchAddConstraints(relation_name)
    except Exception as exc:
        raise RuntimeError(f"Failed to add sketch relation {relation_name}: {exc}") from exc
    rebuild_model(model)


def add_coincident(model): add_relation(model, "sgCOINCIDENT")
def add_horizontal(model): add_relation(model, "sgHORIZONTAL")
def add_vertical(model): add_relation(model, "sgVERTICAL")
def add_tangent(model): add_relation(model, "sgTANGENT")
def add_concentric(model): add_relation(model, "sgCONCENTRIC")
def add_equal(model): add_relation(model, "sgEQUAL")
def add_parallel(model): add_relation(model, "sgPARALLEL")
def add_perpendicular(model): add_relation(model, "sgPERPENDICULAR")
