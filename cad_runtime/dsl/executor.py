from __future__ import annotations


class DslExecutor:
    """Execute a small JSON-like CAD operation list against SolidWorksPartBuilder."""

    def __init__(self, builder):
        self.builder = builder

    def execute(self, plan: dict):
        results = []
        for op in plan.get("operations", []):
            name = op["op"]
            if name == "create_box":
                results.append(self.builder.create_box(**{k: v for k, v in op.items() if k != "op"}))
            elif name == "cut_hole_on_plane":
                results.append(self.builder.cut_hole_on_plane(**{k: v for k, v in op.items() if k != "op"}))
            elif name == "draw_circle_on_plane":
                results.append(self.builder.draw_circle_on_plane(**{k: v for k, v in op.items() if k != "op"}))
            else:
                raise ValueError(f"Unsupported DSL operation: {name}")
        return results
