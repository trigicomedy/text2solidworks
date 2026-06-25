"""SolidWorks API wrapper layer."""

from .app import connect_solidworks
from .builder import SolidWorksPartBuilder
from .advanced_features import (
    loft_boss,
    loft_cut,
    revolve_boss,
    revolve_cut,
    sweep_boss,
    sweep_cut,
)

__all__ = [
    "connect_solidworks",
    "SolidWorksPartBuilder",
    "revolve_boss",
    "revolve_cut",
    "sweep_boss",
    "sweep_cut",
    "loft_boss",
    "loft_cut",
]
