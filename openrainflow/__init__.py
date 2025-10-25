"""
OpenRainflow - High-performance fatigue analysis package.

This package provides optimized implementations of:
- Rainflow cycle counting
- Eurocode fatigue curves
- Miner's linear damage accumulation
"""

__version__ = "1.0.0"
__author__ = "OpenRainflow Contributors"
__license__ = "MIT"

from .rainflow import rainflow_count, rainflow_count_parallel
from .damage import calculate_damage, calculate_life
from .eurocode import EurocodeCategory, FatigueCurve

# Try to import visualization (optional dependency)
try:
    from . import visualization
    _HAS_VISUALIZATION = True
except ImportError:
    _HAS_VISUALIZATION = False
    visualization = None

__all__ = [
    "rainflow_count",
    "rainflow_count_parallel",
    "calculate_damage",
    "calculate_life",
    "EurocodeCategory",
    "FatigueCurve",
    "__version__",
]

if _HAS_VISUALIZATION:
    __all__.append("visualization")

