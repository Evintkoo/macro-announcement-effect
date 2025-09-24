"""
Utility package for the macro announcement research project.
"""

from .config import config
from .helpers import (
    setup_logging,
    ensure_datetime_index,
    calculate_returns,
    calculate_realized_volatility,
    synchronize_timestamps,
    create_event_windows,
    clean_outliers,
    save_results
)

__all__ = [
    'config',
    'setup_logging',
    'ensure_datetime_index',
    'calculate_returns',
    'calculate_realized_volatility',
    'synchronize_timestamps',
    'create_event_windows',
    'clean_outliers',
    'save_results'
]