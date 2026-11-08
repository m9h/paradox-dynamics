"""Truth-value revision maps with explicit arithmetic and update schedules."""

from .engine import simulate
from .models import MODELS

__all__ = ["MODELS", "simulate"]
__version__ = "0.1.0"
