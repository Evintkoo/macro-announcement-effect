"""
Common utility functions for the macro announcement research project.
"""

import pandas as pd
import numpy as np
from typing import Union, List, Tuple, Optional
from datetime import datetime, timezone
import logging
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: str = None) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        
    Returns:
        Configured logger
    """
    # Create logs directory if needed
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    # Build handlers explicitly to set encoding for file handler
    handlers = [logging.StreamHandler()]
    if log_file:
        try:
            handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
        except TypeError:
            # For very old Python versions without encoding param, fall back without encoding
            handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    return logging.getLogger(__name__)

def ensure_datetime_index(df: pd.DataFrame, datetime_col: str = None) -> pd.DataFrame:
    """
    Ensure DataFrame has a datetime index.
    
    Args:
        df: DataFrame to process
        datetime_col: Column name to use as datetime index (if not already index)
        
    Returns:
        DataFrame with datetime index
    """
    df = df.copy()
    
    if datetime_col and datetime_col in df.columns:
        df[datetime_col] = pd.to_datetime(df[datetime_col])
        df = df.set_index(datetime_col)
    elif not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # Ensure timezone awareness
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    
    return df

def calculate_returns(prices: pd.Series, method: str = "log") -> pd.Series:
    """
    Calculate returns from price series.
    
    Args:
        prices: Price series
        method: Return calculation method ('log' or 'simple')
        
    Returns:
        Returns series
    """
    if method == "log":
        returns = np.log(prices / prices.shift(1))
    elif method == "simple":
        returns = (prices / prices.shift(1)) - 1
    else:
        raise ValueError("Method must be 'log' or 'simple'")
    
    return returns.dropna()

def calculate_realized_volatility(
    returns: pd.Series, 
    window: str = "1D",
    annualize: bool = True,
    trading_periods: int = 252
) -> pd.Series:
    """
    Calculate realized volatility from returns.
    
    Args:
        returns: Returns series
        window: Aggregation window (e.g., '1D', '1H')
        annualize: Whether to annualize volatility
        trading_periods: Number of trading periods per year for annualization
        
    Returns:
        Realized volatility series
    """
    # Calculate squared returns
    squared_returns = returns ** 2
    
    # Aggregate by window
    realized_var = squared_returns.resample(window).sum()
    realized_vol = np.sqrt(realized_var)
    
    if annualize:
        # Determine annualization factor based on window
        if window == "1D":
            factor = np.sqrt(trading_periods)
        elif window == "1H":
            factor = np.sqrt(trading_periods * 24)
        elif window == "1min":
            factor = np.sqrt(trading_periods * 24 * 60)
        else:
            factor = np.sqrt(trading_periods)  # Default
            
        realized_vol *= factor
    
    return realized_vol

def synchronize_timestamps(
    data_dict: dict, 
    freq: str = "1min",
    method: str = "ffill"
) -> dict:
    """
    Synchronize timestamps across multiple datasets.
    
    Args:
        data_dict: Dictionary of DataFrames with datetime indices
        freq: Target frequency for synchronization
        method: Method for handling missing values ('ffill', 'bfill', 'interpolate')
        
    Returns:
        Dictionary of synchronized DataFrames
    """
    # Find common time range
    start_times = []
    end_times = []
    
    for df in data_dict.values():
        if not df.empty:
            start_times.append(df.index.min())
            end_times.append(df.index.max())
    
    if not start_times:
        return data_dict
    
    common_start = max(start_times)
    common_end = min(end_times)
    
    # Create common time index
    common_index = pd.date_range(
        start=common_start,
        end=common_end,
        freq=freq
    )
    
    # Reindex all DataFrames
    synchronized_data = {}
    for name, df in data_dict.items():
        reindexed = df.reindex(common_index)
        
        if method == "ffill":
            reindexed = reindexed.fillna(method="ffill")
        elif method == "bfill":
            reindexed = reindexed.fillna(method="bfill")
        elif method == "interpolate":
            reindexed = reindexed.interpolate()
        
        synchronized_data[name] = reindexed
    
    return synchronized_data

def create_event_windows(
    announcement_times: List[datetime],
    pre_window: Union[int, str],
    post_window: Union[int, str],
    freq: str = "1min"
) -> List[Tuple[datetime, datetime]]:
    """
    Create event windows around announcement times.
    
    Args:
        announcement_times: List of announcement datetime objects
        pre_window: Pre-event window (e.g., 60 for minutes, '1H' for pandas offset)
        post_window: Post-event window (e.g., 60 for minutes, '1H' for pandas offset)
        freq: Frequency for window calculation
        
    Returns:
        List of (start_time, end_time) tuples for each event window
    """
    windows = []
    
    for announce_time in announcement_times:
        if isinstance(pre_window, int):
            # Assume minutes
            start_time = announce_time - pd.Timedelta(minutes=pre_window)
        else:
            start_time = announce_time - pd.Timedelta(pre_window)
            
        if isinstance(post_window, int):
            # Assume minutes
            end_time = announce_time + pd.Timedelta(minutes=post_window)
        else:
            end_time = announce_time + pd.Timedelta(post_window)
        
        windows.append((start_time, end_time))
    
    return windows

def clean_outliers(
    data: pd.Series, 
    method: str = "iqr",
    threshold: float = 3.0
) -> pd.Series:
    """
    Clean outliers from data series.
    
    Args:
        data: Data series to clean
        method: Outlier detection method ('iqr', 'zscore', 'modified_zscore')
        threshold: Threshold for outlier detection
        
    Returns:
        Cleaned data series
    """
    if method == "iqr":
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        mask = (data >= lower_bound) & (data <= upper_bound)
        
    elif method == "zscore":
        z_scores = np.abs((data - data.mean()) / data.std())
        mask = z_scores <= threshold
        
    elif method == "modified_zscore":
        median = data.median()
        mad = np.median(np.abs(data - median))
        modified_z_scores = 0.6745 * (data - median) / mad
        mask = np.abs(modified_z_scores) <= threshold
        
    else:
        raise ValueError("Method must be 'iqr', 'zscore', or 'modified_zscore'")
    
    return data[mask]

def save_results(
    data: Union[pd.DataFrame, pd.Series, dict],
    filename: str,
    results_dir: Path,
    file_format: str = "csv"
) -> Path:
    """
    Save results to file.
    
    Args:
        data: Data to save
        filename: Filename (without extension)
        results_dir: Results directory
        file_format: File format ('csv', 'pickle', 'json')
        
    Returns:
        Path to saved file
    """
    results_dir.mkdir(parents=True, exist_ok=True)
    filepath = results_dir / f"{filename}.{file_format}"
    
    if isinstance(data, (pd.DataFrame, pd.Series)):
        if file_format == "csv":
            data.to_csv(filepath)
        elif file_format == "pickle":
            data.to_pickle(filepath)
        elif file_format == "json":
            data.to_json(filepath)
    elif isinstance(data, dict):
        if file_format == "json":
            import json
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        elif file_format == "pickle":
            import pickle
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
    
    return filepath