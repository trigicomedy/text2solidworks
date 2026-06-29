from __future__ import annotations

from dataclasses import dataclass

from .assembly_mates import MateResult, mate_coincident
from .assembly_references import AssemblyRef


@dataclass(frozen=True)
class RevoluteJointResult:
    name: str
    axis_mate: MateResult
    plane_mate: MateResult | None
    limit_deg: tuple[float, float] | None


def create_revolute_joint(
    assembly,
    name: str,
    axis_a: AssemblyRef,
    axis_b: AssemblyRef,
    *,
    plane_a: AssemblyRef | None = None,
    plane_b: AssemblyRef | None = None,
    limit_deg: tuple[float, float] | None = None,
) -> RevoluteJointResult:
    """Create a basic revolute joint from two datum axes and optional planes.

    Axis-to-axis coaxial alignment is represented as a coincident mate between
    datum axes. Limit mates are recorded in the return value and connection
    plan, but native SW limit-angle validation is still pending.
    """
    axis_mate = mate_coincident(assembly, f"{name}_axis_coincident", axis_a, axis_b)
    plane_mate = None
    if plane_a is not None and plane_b is not None:
        plane_mate = mate_coincident(assembly, f"{name}_plane_coincident", plane_a, plane_b)
    return RevoluteJointResult(name=name, axis_mate=axis_mate, plane_mate=plane_mate, limit_deg=limit_deg)
