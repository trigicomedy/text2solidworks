from __future__ import annotations

from dataclasses import dataclass

from .assembly_components import component_name, list_components


@dataclass(frozen=True)
class AssemblySummary:
    component_count: int
    mate_count: int | None
    component_names: list[str]


def summarize_assembly(assembly) -> AssemblySummary:
    components = list_components(assembly, top_level_only=True)
    return AssemblySummary(
        component_count=len(components),
        mate_count=count_mates(assembly),
        component_names=[component_name(comp) for comp in components],
    )


def count_mates(assembly) -> int | None:
    """Best-effort count of assembly mates."""
    for method_name in ("GetMateCount",):
        method = getattr(assembly, method_name, None)
        if callable(method):
            try:
                return int(method())
            except Exception:
                pass
    try:
        feature = assembly.FirstFeature()
        count = 0
        while feature is not None:
            try:
                type_attr = getattr(feature, "GetTypeName2", None)
                type_name = type_attr() if callable(type_attr) else type_attr
                if "Mate" in str(type_name):
                    count += 1
            except Exception:
                pass
            feature = feature.GetNextFeature()
        return count
    except Exception:
        return None


def assert_components_present(assembly, names: list[str]) -> None:
    existing = set(summary_name.split("-")[0] for summary_name in summarize_assembly(assembly).component_names)
    missing = [name for name in names if name not in existing]
    if missing:
        raise RuntimeError(f"Assembly missing expected components: {missing}")


def check_interference_placeholder(assembly):
    """Reserved entry point for future native interference checks."""
    raise NotImplementedError("Native interference checking needs dedicated SW2025 COM validation.")


def check_interference(assembly, components: list | None = None, *, coincident_interference: bool = True):
    """Best-effort native interference check.

    Returns the raw SolidWorks result. The exact result shape depends on COM
    binding and needs per-workstation validation.
    """
    if components is None:
        components = list_components(assembly, top_level_only=True)
    attempts = [
        ("ToolsCheckInterference2", lambda: assembly.ToolsCheckInterference2(len(components), components, coincident_interference)),
        ("ToolsCheckInterference", lambda: assembly.ToolsCheckInterference()),
    ]
    errors: list[str] = []
    for label, call in attempts:
        try:
            return {"api": label, "result": call()}
        except Exception as exc:
            errors.append(f"{label}: {exc}")
    raise RuntimeError(f"Interference check failed. Attempts: {'; '.join(errors)}")
