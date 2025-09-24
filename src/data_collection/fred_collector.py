"""
Federal Reserve Economic Data (FRED) collector.
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from datetime import datetime
import requests
from fredapi import Fred
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from .base_collector import BaseDataCollector
from utils.config import Config

# Global config instance
config = Config()

class FREDCollector(BaseDataCollector):
    """Collector for Federal Reserve Economic Data."""
    
    def __init__(self):
        super().__init__("FRED")
        
        try:
            api_key = config.get_api_key("fred")
            self.fred = Fred(api_key=api_key)
            self.logger.info("FRED API initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize FRED API: {e}")
            self.fred = None
    
    def collect_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> pd.DataFrame:
        """
        Collect economic data from FRED.
        
        Args:
            symbols: List of FRED series IDs
            start_date: Start date for data collection
            end_date: End date for data collection
            **kwargs: Additional parameters (frequency, aggregation_method, etc.)
            
        Returns:
            DataFrame with economic data
        """
        if self.fred is None:
            raise RuntimeError("FRED API not initialized")
        
        frequency = kwargs.get('frequency', 'd')  # daily by default
        aggregation_method = kwargs.get('aggregation_method', 'avg')
        
        data = pd.DataFrame()
        
        for symbol in symbols:
            try:
                self.logger.info(f"Collecting data for {symbol}")
                
                series_data = self.fred.get_series(
                    symbol,
                    start=start_date,
                    end=end_date,
                    frequency=frequency,
                    aggregation_method=aggregation_method
                )
                
                if not series_data.empty:
                    data[symbol] = series_data
                    self.logger.info(f"Collected {len(series_data)} observations for {symbol}")
                else:
                    self.logger.warning(f"No data found for {symbol}")
                    
            except Exception as e:
                self.logger.error(f"Failed to collect data for {symbol}: {e}")
                continue
        
        if not data.empty:
            data.index.name = 'date'
            self.logger.info(f"Collected data for {len(data.columns)} series")
        
        return data
    
    def get_series_info(self, series_id: str) -> Dict[str, Any]:
        """
        Get information about a FRED series.
        
        Args:
            series_id: FRED series ID
            
        Returns:
            Dictionary with series information
        """
        if self.fred is None:
            raise RuntimeError("FRED API not initialized")
        
        try:
            info = self.fred.get_series_info(series_id)
            return info.to_dict()
        except Exception as e:
            self.logger.error(f"Failed to get info for {series_id}: {e}")
            return {}
    
    def search_series(self, search_text: str, limit: int = 10) -> pd.DataFrame:
        """
        Search for FRED series.
        
        Args:
            search_text: Text to search for
            limit: Maximum number of results
            
        Returns:
            DataFrame with search results
        """
        if self.fred is None:
            raise RuntimeError("FRED API not initialized")
        
        try:
            results = self.fred.search(search_text, limit=limit)
            return results
        except Exception as e:
            self.logger.error(f"Failed to search for '{search_text}': {e}")
            return pd.DataFrame()
    
    def collect_announcement_data(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Collect key macroeconomic announcement data.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with announcement data
        """
        # Key economic indicators from the config
        indicators = []
        
        # Get indicators from config
        for category in ['employment', 'inflation', 'gdp', 'other']:
            category_indicators = config.get(f'economic_indicators.{category}', [])
            indicators.extend(category_indicators)
        
        if not indicators:
            # Fallback to default indicators
            indicators = [
                'UNRATE',    # Unemployment Rate
                'PAYEMS',    # Nonfarm Payrolls
                'CPIAUCSL',  # Consumer Price Index
                'GDP',       # Gross Domestic Product
                'FEDFUNDS',  # Federal Funds Rate
                'VIXCLS',    # VIX
                'DGS10'      # 10-Year Treasury Rate
            ]
        
        return self.collect_data(indicators, start_date, end_date)
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate FRED data.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        if data.empty:
            self.logger.warning("Data is empty")
            return False
        
        # Check for datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            self.logger.warning("Data does not have datetime index")
            return False
        
        # Check for excessive missing values
        missing_pct = data.isnull().sum() / len(data) * 100
        max_missing = missing_pct.max()
        
        if max_missing > 50:
            self.logger.warning(f"Excessive missing values: {max_missing:.1f}%")
            return False
        
        self.logger.info("Data validation passed")
        return True