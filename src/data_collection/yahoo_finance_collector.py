"""
Yahoo Finance data collector for free stock market and economic data.
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import yfinance as yf
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from .base_collector import BaseDataCollector
from utils.config import Config

# Global config instance
config = Config()

class YahooFinanceCollector(BaseDataCollector):
    """Collector for Yahoo Finance data (free)."""
    
    def __init__(self):
        super().__init__("YahooFinance")
        self.logger.info("Yahoo Finance collector initialized")
    
    def collect_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> pd.DataFrame:
        """
        Collect data from Yahoo Finance.
        
        Args:
            symbols: List of Yahoo Finance symbols
            start_date: Start date for data collection
            end_date: End date for data collection
            **kwargs: Additional parameters (interval, etc.)
            
        Returns:
            DataFrame with collected data
        """
        interval = kwargs.get('interval', '1d')  # 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
        data_type = kwargs.get('data_type', 'Close')  # Open, High, Low, Close, Volume, Adj Close
        
        all_data = pd.DataFrame()
        
        for symbol in symbols:
            try:
                self.logger.info(f"Collecting data for {symbol}")
                
                # Create ticker object
                ticker = yf.Ticker(symbol)
                
                # Download data
                hist_data = ticker.history(
                    start=start_date,
                    end=end_date,
                    interval=interval,
                    auto_adjust=True,
                    prepost=True if interval in ['1m', '2m', '5m'] else False
                )
                
                if not hist_data.empty:
                    if data_type in hist_data.columns:
                        all_data[symbol] = hist_data[data_type]
                    else:
                        # If specific column not found, use Close
                        all_data[symbol] = hist_data['Close']
                    
                    self.logger.info(f"Collected {len(hist_data)} observations for {symbol}")
                else:
                    self.logger.warning(f"No data found for {symbol}")
                    
            except Exception as e:
                self.logger.error(f"Failed to collect data for {symbol}: {e}")
                continue
        
        if not all_data.empty:
            all_data.index.name = 'datetime'
            self.logger.info(f"Collected data for {len(all_data.columns)} symbols")
        
        return all_data
    
    def collect_intraday_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str = "1m"
    ) -> pd.DataFrame:
        """
        Collect intraday data (limited to last 7 days for 1m data on free tier).
        
        Args:
            symbols: List of symbols
            start_date: Start date
            end_date: End date
            interval: Data interval (1m, 5m, 15m, 30m, 60m)
            
        Returns:
            DataFrame with intraday data
        """
        # Yahoo Finance free tier limits intraday data to last 7 days
        if interval == "1m":
            max_days = 7
            actual_start = max(start_date, datetime.now() - timedelta(days=max_days))
            if actual_start > start_date:
                self.logger.warning(f"1-minute data limited to last {max_days} days. Adjusting start date to {actual_start}")
        else:
            actual_start = start_date
        
        return self.collect_data(
            symbols, 
            actual_start, 
            end_date, 
            interval=interval,
            data_type='Close'
        )
    
    def get_ticker_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get information about a ticker.
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            Dictionary with ticker information
        """
        try:
            ticker = yf.Ticker(symbol)
            return ticker.info
        except Exception as e:
            self.logger.error(f"Failed to get info for {symbol}: {e}")
            return {}
    
    def collect_market_data(
        self,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Collect key market indicators.
        
        Args:
            start_date: Start date
            end_date: End date
            interval: Data interval
            
        Returns:
            DataFrame with market data
        """
        # Get symbols from config
        symbols = config.get('data_sources.stocks.symbols', [])
        
        if not symbols:
            # Fallback to default symbols
            symbols = [
                "^GSPC",    # S&P 500
                "^TNX",     # 10-Year Treasury
                "^DJI",     # Dow Jones
                "^IXIC",    # NASDAQ
            ]
        
        return self.collect_data(symbols, start_date, end_date, interval=interval)
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate Yahoo Finance data.
        
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
        
        # Check for non-positive prices (likely data error)
        if (data <= 0).any().any():
            self.logger.warning("Found non-positive prices in data")
            return False
        
        # Check for excessive missing values
        missing_pct = data.isnull().sum() / len(data) * 100
        max_missing = missing_pct.max()
        
        if max_missing > 50:
            self.logger.warning(f"Excessive missing values: {max_missing:.1f}%")
            return False
        
        self.logger.info("Data validation passed")
        return True