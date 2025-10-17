"""
Data preprocessing module for cleaning and preparing data for analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime
import logging
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from utils.config import Config
from utils.helpers import calculate_returns, calculate_realized_volatility, synchronize_timestamps, ensure_datetime_index, get_timezone_policy

# Global config instance
config = Config()
logger = logging.getLogger(__name__)

class DataPreprocessor:
    """Main class for data preprocessing operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.DataPreprocessor")
        
    def clean_price_data(
        self,
        price_data: pd.DataFrame,
        method: str = "forward_fill",
        outlier_threshold: float = 3.0
    ) -> pd.DataFrame:
        """
        Clean price data by handling missing values and outliers.
        
        Args:
            price_data: DataFrame with price data
            method: Method for handling missing values ('forward_fill', 'interpolate', 'drop')
            outlier_threshold: Z-score threshold for outlier detection
            
        Returns:
            Cleaned DataFrame
        """
        cleaned_data = price_data.copy()
        
        # Handle missing values
        if method == "forward_fill":
            cleaned_data = cleaned_data.fillna(method='ffill')
        elif method == "interpolate":
            cleaned_data = cleaned_data.interpolate(method='time')
        elif method == "drop":
            cleaned_data = cleaned_data.dropna()
        
        # Remove outliers
        for col in cleaned_data.columns:
            if cleaned_data[col].dtype in ['float64', 'int64']:
                # Calculate z-scores
                z_scores = np.abs((cleaned_data[col] - cleaned_data[col].mean()) / cleaned_data[col].std())
                
                # Replace outliers with NaN and forward fill
                outlier_mask = z_scores > outlier_threshold
                cleaned_data.loc[outlier_mask, col] = np.nan
                cleaned_data[col] = cleaned_data[col].fillna(method='ffill')
        
        self.logger.info(f"Cleaned data shape: {cleaned_data.shape}")
        return cleaned_data
    
    def calculate_returns_and_volatility(
        self,
        price_data: pd.DataFrame,
        return_method: str = "log",
        volatility_window: str = "1D",
        annualize: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Calculate returns and volatility from price data.
        
        Args:
            price_data: DataFrame with price data
            return_method: Return calculation method ('log' or 'simple')
            volatility_window: Window for volatility calculation
            annualize: Whether to annualize volatility
            
        Returns:
            Dictionary with 'returns', 'volatility', and 'prices' DataFrames
        """
        results = {}
        
        # Calculate returns for each asset
        returns_data = pd.DataFrame(index=price_data.index)
        volatility_data = pd.DataFrame()
        
        for col in price_data.columns:
            prices = price_data[col].dropna()
            
            if len(prices) > 1:
                # Calculate returns
                returns = calculate_returns(prices, method=return_method)
                returns_data[col] = returns
                
                # Calculate realized volatility
                volatility = calculate_realized_volatility(
                    returns, 
                    window=volatility_window,
                    annualize=annualize
                )
                
                if not volatility.empty:
                    volatility_data[col] = volatility
        
        results['prices'] = price_data
        results['returns'] = returns_data
        results['volatility'] = volatility_data
        
        self.logger.info(f"Calculated returns and volatility for {len(price_data.columns)} assets")
        return results
    
    def synchronize_datasets(
        self,
        datasets: Dict[str, pd.DataFrame],
        freq: str = "1H",
        method: str = "ffill"
    ) -> Dict[str, pd.DataFrame]:
        """
        Synchronize multiple datasets to common timestamps.
        
        Args:
            datasets: Dictionary of DataFrames to synchronize
            freq: Target frequency
            method: Method for handling missing values
            
        Returns:
            Dictionary of synchronized DataFrames
        """
        synchronized = synchronize_timestamps(datasets, freq=freq, method=method)
        
        self.logger.info(f"Synchronized {len(datasets)} datasets to {freq} frequency")
        return synchronized
    
    def create_analysis_dataset(
        self,
        crypto_data: pd.DataFrame,
        stock_data: pd.DataFrame,
        economic_data: pd.DataFrame,
        announcement_dates: pd.DataFrame = None
    ) -> pd.DataFrame:
        """
        Create a comprehensive dataset for analysis.
        
        Args:
            crypto_data: Cryptocurrency returns/prices
            stock_data: Stock market returns/prices  
            economic_data: Economic indicators
            announcement_dates: DataFrame with announcement dates
            
        Returns:
            Combined analysis dataset
        """
        # Ensure all data has datetime index
        crypto_data = self._ensure_datetime_index(crypto_data)
        stock_data = self._ensure_datetime_index(stock_data)
        economic_data = self._ensure_datetime_index(economic_data)
        
        # Synchronize to daily frequency for main analysis
        datasets = {
            'crypto': crypto_data,
            'stocks': stock_data,
            'economic': economic_data
        }
        
        synchronized = self.synchronize_datasets(datasets, freq="1D", method="ffill")
        
        # Combine into single DataFrame
        analysis_data = pd.DataFrame()
        
        # Add crypto data with prefix
        for col in synchronized['crypto'].columns:
            analysis_data[f"crypto_{col}"] = synchronized['crypto'][col]
        
        # Add stock data with prefix
        for col in synchronized['stocks'].columns:
            analysis_data[f"stock_{col}"] = synchronized['stocks'][col]
        
        # Add economic data with prefix
        for col in synchronized['economic'].columns:
            analysis_data[f"econ_{col}"] = synchronized['economic'][col]
        
        # Add announcement indicators if provided
        if announcement_dates is not None:
            announcement_dates = self._ensure_datetime_index(announcement_dates)
            analysis_data = self._add_announcement_indicators(analysis_data, announcement_dates)
        
        # Add time-based features
        analysis_data = self._add_time_features(analysis_data)
        
        # Add lagged variables
        analysis_data = self._add_lagged_variables(analysis_data)
        
        self.logger.info(f"Created analysis dataset with {len(analysis_data.columns)} features")
        return analysis_data
    
    def _ensure_datetime_index(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure DataFrame has datetime index with consistent timezone handling.
        
        Uses centralized timezone policy from config to maintain consistency
        across all data sources (P0 FIX).
        """
        try:
            timezone_policy = get_timezone_policy()
            return ensure_datetime_index(data, timezone_policy=timezone_policy)
        except Exception as e:
            self.logger.warning(f"Could not ensure datetime index: {e}")
            # Fallback to basic datetime conversion
            if not isinstance(data.index, pd.DatetimeIndex):
                try:
                    data.index = pd.to_datetime(data.index)
                except:
                    pass
            return data
    
    def _add_announcement_indicators(
        self,
        data: pd.DataFrame,
        announcement_dates: pd.DataFrame
    ) -> pd.DataFrame:
        """Add binary indicators for announcement dates."""
        result = data.copy()
        
        # Create binary indicators for different types of announcements
        if 'event' in announcement_dates.columns:
            event_types = announcement_dates['event'].unique()
            
            for event_type in event_types:
                event_dates = announcement_dates[
                    announcement_dates['event'] == event_type
                ].index
                
                # Create binary indicator
                indicator_name = f"announcement_{event_type.lower().replace(' ', '_')}"
                result[indicator_name] = 0
                
                # Set to 1 on announcement dates
                for date in event_dates:
                    if date in result.index:
                        result.loc[date, indicator_name] = 1
        
        return result
    
    def _add_time_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features."""
        result = data.copy()
        
        # Day of week (Monday=0, Sunday=6)
        result['day_of_week'] = data.index.dayofweek
        
        # Month
        result['month'] = data.index.month
        
        # Quarter
        result['quarter'] = data.index.quarter
        
        # Year
        result['year'] = data.index.year
        
        # Weekend indicator
        result['is_weekend'] = (data.index.dayofweek >= 5).astype(int)
        
        return result
    
    def _add_lagged_variables(
        self,
        data: pd.DataFrame,
        lags: List[int] = [1, 2, 3, 5]
    ) -> pd.DataFrame:
        """Add lagged variables for relevant columns."""
        result = data.copy()
        
        # Add lags for return and volatility columns
        lag_columns = [col for col in data.columns 
                      if any(keyword in col.lower() 
                            for keyword in ['return', 'volatility', 'rate'])]
        
        for col in lag_columns:
            for lag in lags:
                result[f"{col}_lag{lag}"] = data[col].shift(lag)
        
        return result
    
    def prepare_event_study_data(
        self,
        price_data: pd.DataFrame,
        announcement_times: List[datetime],
        pre_window_minutes: int = 60,
        post_window_minutes: int = 60
    ) -> Dict[str, pd.DataFrame]:
        """
        Prepare data for event study analysis.
        
        Args:
            price_data: High-frequency price data
            announcement_times: List of announcement times
            pre_window_minutes: Minutes before announcement
            post_window_minutes: Minutes after announcement
            
        Returns:
            Dictionary with event study data
        """
        event_data = {}
        
        for i, announce_time in enumerate(announcement_times):
            # Define event window
            start_time = announce_time - pd.Timedelta(minutes=pre_window_minutes)
            end_time = announce_time + pd.Timedelta(minutes=post_window_minutes)
            
            # Extract data for this event window
            mask = (price_data.index >= start_time) & (price_data.index <= end_time)
            event_window_data = price_data.loc[mask].copy()
            
            if not event_window_data.empty:
                # Calculate minutes relative to announcement
                event_window_data['minutes_to_announcement'] = (
                    event_window_data.index - announce_time
                ).total_seconds() / 60
                
                # Calculate returns in event window
                event_returns = pd.DataFrame()
                for col in event_window_data.columns:
                    if col != 'minutes_to_announcement':
                        prices = event_window_data[col]
                        returns = calculate_returns(prices, method='log')
                        event_returns[col] = returns
                
                event_returns['minutes_to_announcement'] = event_window_data['minutes_to_announcement'][1:]
                
                event_data[f'event_{i+1}'] = {
                    'prices': event_window_data,
                    'returns': event_returns,
                    'announcement_time': announce_time
                }
        
        self.logger.info(f"Prepared event study data for {len(event_data)} events")
        return event_data