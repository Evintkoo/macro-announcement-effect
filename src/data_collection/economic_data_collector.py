"""
Free economic data collector using pandas-datareader and web scraping.
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import pandas_datareader.data as web
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from .base_collector import BaseDataCollector
from utils.config import Config

# Global config instance
config = Config()

class EconomicDataCollector(BaseDataCollector):
    """Collector for free economic data."""
    
    def __init__(self):
        super().__init__("EconomicData")
        self.logger.info("Economic data collector initialized")
    
    def collect_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> pd.DataFrame:
        """
        Collect economic data from free sources.
        
        Args:
            symbols: List of economic indicators
            start_date: Start date for data collection
            end_date: End date for data collection
            **kwargs: Additional parameters
            
        Returns:
            DataFrame with economic data
        """
        source = kwargs.get('source', 'fred')
        
        all_data = pd.DataFrame()
        
        # Some configured entries are pseudo-series (e.g., event labels) not valid FRED series; skip them
        invalid_fred_series = {"FOMC_meetings", "interest_rate_decisions", "QE_announcements"}

        for symbol in symbols:
            try:
                self.logger.info(f"Collecting data for {symbol}")
                
                if source == 'fred':
                    if symbol in invalid_fred_series:
                        self.logger.warning(f"Skipping non-FRED series id '{symbol}'")
                        continue
                    # Use pandas-datareader for FRED data (no API key needed, but limited)
                    data = web.DataReader(symbol, 'fred', start_date, end_date)
                    if not data.empty:
                        all_data[symbol] = data.iloc[:, 0]  # First column
                        self.logger.info(f"Collected {len(data)} observations for {symbol}")
                
            except Exception as e:
                self.logger.error(f"Failed to collect data for {symbol}: {e}")
                continue
        
        if not all_data.empty:
            all_data.index.name = 'date'
            self.logger.info(f"Collected data for {len(all_data.columns)} indicators")
        
        return all_data
    
    def collect_economic_indicators(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Collect key economic indicators.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with economic indicators
        """
        # Key indicators that are freely available
        indicators = [
            'UNRATE',     # Unemployment Rate
            'CPIAUCSL',   # Consumer Price Index
            'GDP',        # Gross Domestic Product
            'FEDFUNDS',   # Federal Funds Rate
            'DGS10',      # 10-Year Treasury Rate
            'VIXCLS',     # VIX
            'DEXUSEU',    # USD/EUR Exchange Rate
        ]
        
        return self.collect_data(indicators, start_date, end_date, source='fred')
    
    def scrape_fomc_dates(self, year: int = None) -> pd.DataFrame:
        """
        Scrape FOMC meeting dates from Fed website.
        
        Args:
            year: Year to scrape (if None, scrapes current year)
            
        Returns:
            DataFrame with FOMC dates
        """
        try:
            if year is None:
                year = datetime.now().year
            
            url = f"https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
            
            response = requests.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # This is a simplified scraper - actual implementation would need
            # to parse the specific HTML structure of the Fed website
            fomc_dates = []
            
            # Look for date patterns in the HTML
            # (This would need to be customized based on actual website structure)
            
            return pd.DataFrame({'fomc_date': fomc_dates})
            
        except Exception as e:
            self.logger.error(f"Failed to scrape FOMC dates: {e}")
            return pd.DataFrame()
    
    def get_economic_calendar_sample(self) -> pd.DataFrame:
        """
        Create a sample economic calendar with major announcement dates.
        This is a simplified version - in practice, you'd scrape from economic calendars.
        
        Returns:
            DataFrame with sample economic events
        """
        # Sample data for demonstration
        sample_events = [
            {'date': '2024-01-12', 'event': 'CPI Release', 'importance': 'High'},
            {'date': '2024-01-26', 'event': 'GDP Release', 'importance': 'High'},
            {'date': '2024-01-31', 'event': 'FOMC Meeting', 'importance': 'High'},
            {'date': '2024-02-02', 'event': 'Employment Report', 'importance': 'High'},
            {'date': '2024-02-13', 'event': 'CPI Release', 'importance': 'High'},
            {'date': '2024-02-20', 'event': 'FOMC Minutes', 'importance': 'Medium'},
        ]
        
        df = pd.DataFrame(sample_events)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        return df
    
    def calculate_surprise_indicators(
        self,
        actual_data: pd.DataFrame,
        forecast_data: pd.DataFrame = None
    ) -> pd.DataFrame:
        """
        Calculate surprise indicators (simplified version without forecast data).
        
        Args:
            actual_data: DataFrame with actual values
            forecast_data: DataFrame with forecast values (if available)
            
        Returns:
            DataFrame with surprise indicators
        """
        if forecast_data is None:
            # Without forecast data, calculate surprises based on historical mean/trend
            surprises = pd.DataFrame(index=actual_data.index)
            
            for col in actual_data.columns:
                series = actual_data[col].dropna()
                
                # Calculate rolling mean as "expected" value
                rolling_mean = series.rolling(window=12, min_periods=1).mean().shift(1)
                
                # Calculate surprise as actual minus expected
                surprise = series - rolling_mean
                
                # Normalize by rolling standard deviation
                rolling_std = series.rolling(window=12, min_periods=1).std().shift(1)
                normalized_surprise = surprise / rolling_std
                
                surprises[f"{col}_surprise"] = surprise
                surprises[f"{col}_normalized_surprise"] = normalized_surprise
            
            return surprises
        
        else:
            # Calculate surprises using actual forecast data
            surprises = actual_data - forecast_data
            return surprises
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate economic data.
        
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
        
        # Economic data can have some missing values, so be more lenient
        missing_pct = data.isnull().sum() / len(data) * 100
        max_missing = missing_pct.max()
        
        if max_missing > 80:  # More lenient for economic data
            self.logger.warning(f"Excessive missing values: {max_missing:.1f}%")
            return False
        
        self.logger.info("Data validation passed")
        return True