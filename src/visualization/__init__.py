"""Visualization package exports.

Charts are no longer produced – the ``PlotGenerator`` symbol now
refers to a tabular exporter that persists analysis artefacts as CSV
files while keeping the historical API intact.
"""

from .table_exporter import PlotGenerator

__all__ = ["PlotGenerator"]