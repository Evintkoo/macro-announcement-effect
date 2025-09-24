"""
Cryptocurrency data collector using Yahoo Finance.
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

class CryptoCollector(BaseDataCollector):
    """Collector for cryptocurrency data using Yahoo Finance."""
    
    def __init__(self):
        super().__init__("CryptoCollector")
        self.logger.info("Crypto collector initialized with Yahoo Finance")
    
    def collect_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> pd.DataFrame:
        """
        Collect cryptocurrency data.
        
        Args:
            symbols: List of cryptocurrency symbols (e.g., ['BTC-USD', 'ETH-USD'])
            start_date: Start date for data collection
            end_date: End date for data collection
            **kwargs: Additional parameters
            
        Returns:
            DataFrame with cryptocurrency data
        """
        all_data = pd.DataFrame()
        
        # Convert symbols to Yahoo Finance format
        yahoo_symbols = []
        for symbol in symbols:
            if symbol.upper().endswith('-USD'):
                yahoo_symbols.append(symbol.upper())
            elif symbol.upper() in ['BTC', 'BITCOIN']:
                yahoo_symbols.append('BTC-USD')
            elif symbol.upper() in ['ETH', 'ETHEREUM']:
                yahoo_symbols.append('ETH-USD')
            elif symbol.upper() in ['BNB', 'BINANCECOIN']:
                yahoo_symbols.append('BNB-USD')
            elif symbol.upper() in ['ADA', 'CARDANO']:
                yahoo_symbols.append('ADA-USD')
            elif symbol.upper() in ['SOL', 'SOLANA']:
                yahoo_symbols.append('SOL-USD')
            else:
                # Try adding -USD suffix
                yahoo_symbols.append(f"{symbol.upper()}-USD")
        
        for i, symbol in enumerate(yahoo_symbols):
            try:
                self.logger.info(f"Collecting data for {symbol}")
                
                # Use yfinance to get data
                ticker = yf.Ticker(symbol)
                data = ticker.history(
                    start=start_date,
                    end=end_date,
                    interval='1d'
                )
                
                if not data.empty:
                    # Use closing prices
                    original_symbol = symbols[i]
                    all_data[f"{original_symbol}_price"] = data['Close']
                    all_data[f"{original_symbol}_volume"] = data['Volume']
                    self.logger.info(f"Collected {len(data)} observations for {symbol}")
                else:
                    self.logger.warning(f"No data found for {symbol}")
                    
            except Exception as e:
                self.logger.error(f"Failed to collect data for {symbol}: {e}")
                continue
        
        if not all_data.empty:
            all_data.index.name = 'datetime'
            self.logger.info(f"Collected data for {len([c for c in all_data.columns if c.endswith('_price')])} cryptocurrencies")
        
        return all_data
    
    def collect_crypto_data(
        self,
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> pd.DataFrame:
        """
        Collect major cryptocurrency data.
        
        Args:
            start_date: Start date
            end_date: End date
            **kwargs: Additional parameters
            
        Returns:
            DataFrame with crypto data
        """
        # Default major cryptocurrencies
        symbols = ['BTC-USD', 'ETH-USD', 'BNB-USD', 'ADA-USD', 'SOL-USD']
        
        return self.collect_data(symbols, start_date, end_date, **kwargs)
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate cryptocurrency data.
        
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
        
        # Check for non-positive prices
        price_columns = [col for col in data.columns if col.endswith('_price')]
        if price_columns:
            if (data[price_columns] <= 0).any().any():
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