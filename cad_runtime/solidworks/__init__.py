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
from .views import (
    export_model_nine_view_images,
    export_named_view_image,
    export_named_view_images,
    show_named_view,
)
from .assembly_components import add_component, get_component, list_components
from .assembly_documents import new_assembly, open_assembly, save_assembly
from .assembly_mates import (
    mate_angle,
    mate_coincident,
    mate_concentric,
    mate_distance,
    mate_parallel,
)
from .assembly_references import AssemblyRef
from .assembly_validation import summarize_assembly

__all__ = [
    "connect_solidworks",
    "SolidWorksPartBuilder",
    "revolve_boss",
    "revolve_cut",
    "sweep_boss",
    "sweep_cut",
    "loft_boss",
    "loft_cut",
    "show_named_view",
    "export_named_view_image",
    "export_named_view_images",
    "export_model_nine_view_images",
    "new_assembly",
    "open_assembly",
    "save_assembly",
    "add_component",
    "get_component",
    "list_components",
    "AssemblyRef",
    "mate_coincident",
    "mate_concentric",
    "mate_distance",
    "mate_angle",
    "mate_parallel",
    "summarize_assembly",
]
