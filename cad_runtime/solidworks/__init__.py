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
from .assembly_joints import create_revolute_joint
from .assembly_mates import (
    add_mate_from_current_selection,
    mate_angle,
    mate_coincident,
    mate_concentric,
    mate_distance,
    mate_parallel,
)
from .assembly_references import AssemblyRef
from .assembly_subassemblies import create_subassembly, insert_subassembly
from .assembly_transforms import (
    fix_component_in_assembly,
    float_component_in_assembly,
    move_component,
    rotate_component,
    set_component_transform,
)
from .assembly_validation import check_interference, summarize_assembly

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
    "add_mate_from_current_selection",
    "mate_coincident",
    "mate_concentric",
    "mate_distance",
    "mate_angle",
    "mate_parallel",
    "set_component_transform",
    "move_component",
    "rotate_component",
    "fix_component_in_assembly",
    "float_component_in_assembly",
    "create_revolute_joint",
    "create_subassembly",
    "insert_subassembly",
    "check_interference",
    "summarize_assembly",
]
