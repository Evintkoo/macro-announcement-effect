"""Deprecated plotting module.

This module remains for backwards compatibility but now re-exports the
new table-based ``PlotGenerator`` implementation.
"""

from .table_exporter import PlotGenerator

__all__ = ["PlotGenerator"]