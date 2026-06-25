def mm(value: float) -> float:
    """Convert millimeters to SolidWorks internal meters."""
    return float(value) / 1000.0


def m_to_mm(value: float) -> float:
    """Convert SolidWorks internal meters to millimeters."""
    return float(value) * 1000.0
