from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class ReferenceGeometry:
    name: str
    kind: str
    role: str


@dataclass
class MateRelation:
    relation_type: str
    self_reference: str
    other_reference: str
    remaining_dof: list[str] = field(default_factory=list)


@dataclass
class MateInterface:
    name: str
    interface_type: str
    references: list[ReferenceGeometry]
    expected_relations: list[MateRelation]
    design_intent: str = ""


def pin_interface(name: str, axis_name: str, mid_plane_name: str, *, other_axis: str = "pin_axis", other_mid_plane: str = "joint_mid_plane") -> MateInterface:
    return MateInterface(
        name=name,
        interface_type="pin",
        references=[
            ReferenceGeometry(axis_name, "axis", "primary_rotation_axis"),
            ReferenceGeometry(mid_plane_name, "plane", "centering_plane"),
        ],
        expected_relations=[
            MateRelation("concentric", axis_name, other_axis, ["translation_along_axis", "rotation_about_axis"]),
            MateRelation("coincident_or_distance", mid_plane_name, other_mid_plane, ["rotation_about_axis"]),
        ],
        design_intent="Rotating pin or shaft interface.",
    )


def flange_interface(name: str, axis_name: str, mounting_plane_name: str, bolt_pattern_name: str | None = None) -> MateInterface:
    refs = [
        ReferenceGeometry(axis_name, "axis", "flange_center_axis"),
        ReferenceGeometry(mounting_plane_name, "plane", "mounting_plane"),
    ]
    if bolt_pattern_name:
        refs.append(ReferenceGeometry(bolt_pattern_name, "pattern", "bolt_pattern"))
    return MateInterface(
        name=name,
        interface_type="flange",
        references=refs,
        expected_relations=[
            MateRelation("concentric", axis_name, "other_flange_axis", ["translation_along_axis", "rotation_about_axis"]),
            MateRelation("coincident", mounting_plane_name, "other_mounting_plane", ["rotation_about_axis"]),
        ],
        design_intent="Bolted flange interface.",
    )


def write_interfaces_json(path: str | Path, interfaces: list[MateInterface]) -> str:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps([asdict(item) for item in interfaces], ensure_ascii=False, indent=2), encoding="utf-8")
    return str(target)
