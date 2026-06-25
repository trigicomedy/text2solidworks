from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CadRegistry:
    """Stores stable and recoverable references created during modeling."""

    parts: dict[str, dict[str, Any]] = field(default_factory=dict)
    refs: dict[str, dict[str, Any]] = field(default_factory=dict)

    def add_part(self, name: str, data: dict[str, Any]) -> dict[str, Any]:
        self.parts[name] = data
        return data

    def add_ref(self, key: str, data: dict[str, Any]) -> dict[str, Any]:
        self.refs[key] = data
        return data

    def get_part(self, name: str) -> dict[str, Any]:
        return self.parts[name]

    def get_ref_name(self, key: str) -> str:
        ref = self.refs[key]
        return ref["name"]
