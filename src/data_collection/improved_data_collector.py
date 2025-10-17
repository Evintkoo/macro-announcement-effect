"""
Improved data collector with proper yield handling and event timing.

Key improvements:
1. Separate handling for yield indices vs price indices
2. Proper unit conversion for yields (basis points)
3. Event timestamp alignment for intraday analysis
4. Clear separation of 24/7 crypto vs trading-day equity data
5. Comprehensive data provenance tracking
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import yfinance as yf
import logging
from pathlib import Path

class ImprovedDataCollector:
    """Enhanced data collector with proper methodology."""
    
    # Define asset types and their specific handling requirements
    YIELD_INSTRUMENTS = ['^TNX', '^FVX', '^TYX', 'DGS10', 'DGS2', 'DGS3MO', 'FEDFUNDS']
    PRICE_INDICES = ['^GSPC', '^DJI', '^IXIC', '^RUT']
    TOTAL_RETURN_ETFS = ['SPY', 'QQQ', 'IWM', 'TLT', 'IEF', 'SHY', 'LQD', 'HYG']
    COMMODITIES = ['GC=F', 'CL=F']
    FX = ['DX=F']
    CRYPTO = ['BTC-USD', 'ETH-USD', 'BNB-USD', 'XRP-USD', 'ADA-USD', 
              'SOL-USD', 'DOGE-USD', 'AVAX-USD', 'DOT-USD', 'MATIC-USD']
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_provenance = {}  # Track data sources and transformations
        
    def collect_aligned_data(
        self,
        start_date: str,
        end_date: str,
        use_business_days: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Collect properly aligned data across asset classes.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            use_business_days: Whether to align to business days (True for equity, False for 24/7)
            
        Returns:
            Dictionary with properly formatted data by asset class
        """
        results = {
            'prices_equity': pd.DataFrame(),      # Price indices (raw prices)
            'returns_equity': pd.DataFrame(),     # Equity returns
            'prices_crypto': pd.DataFrame(),      # Crypto prices (24/7)
            'returns_crypto': pd.DataFrame(),     # Crypto returns (24/7)
            'yields_levels': pd.DataFrame(),      # Yield levels (in percent)
            'yields_changes': pd.DataFrame(),     # Yield changes (in basis points)
            'economic': pd.DataFrame(),           # Economic indicators
            'metadata': {}                        # Data provenance information
        }
        
        # Collect equity data (business days only)
        equity_data = self._collect_equity_data(start_date, end_date)
        results['prices_equity'] = equity_data['prices']
        results['returns_equity'] = equity_data['returns']
        results['metadata']['equity'] = equity_data['metadata']
        
        # Collect crypto data (24/7)
        crypto_data = self._collect_crypto_data(start_date, end_date)
        results['prices_crypto'] = crypto_data['prices']
        results['returns_crypto'] = crypto_data['returns']
        results['metadata']['crypto'] = crypto_data['metadata']
        
        # Collect fixed income data with proper yield handling
        yield_data = self._collect_yield_data(start_date, end_date)
        results['yields_levels'] = yield_data['levels']
        results['yields_changes'] = yield_data['changes']
        results['metadata']['yields'] = yield_data['metadata']
        
        # Collect economic data
        economic_data = self._collect_economic_data(start_date, end_date)
        results['economic'] = economic_data['data']
        results['metadata']['economic'] = economic_data['metadata']
        
        return results
    
    def _collect_equity_data(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Collect equity data with proper business day alignment."""
        
        symbols = self.PRICE_INDICES + self.TOTAL_RETURN_ETFS + self.COMMODITIES + self.FX
        
        prices_df = pd.DataFrame()
        returns_df = pd.DataFrame()
        metadata = {'source': 'Yahoo Finance', 'symbols': {}}
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date, interval='1d')
                
                if not data.empty:
                    # Remove timezone for consistency
                    if hasattr(data.index, 'tz') and data.index.tz is not None:
                        data.index = data.index.tz_localize(None)
                    
                    # Use adjusted close for total return calculation
                    clean_name = symbol.replace('^', '').replace('=F', '').replace('-', '_')
                    
                    # Store prices
                    prices_df[clean_name] = data['Close']
                    
                    # Calculate log returns
                    returns = np.log(data['Close'] / data['Close'].shift(1))
                    returns_df[clean_name] = returns
                    
                    # Track metadata
                    metadata['symbols'][clean_name] = {
                        'ticker': symbol,
                        'type': self._classify_symbol(symbol),
                        'obs_count': len(data),
                        'missing_count': data['Close'].isna().sum(),
                        'date_range': (str(data.index.min()), str(data.index.max()))
                    }
                    
                    self.logger.info(f"Collected equity data for {clean_name}: {len(data)} obs")
                    
            except Exception as e:
                self.logger.warning(f"Failed to collect {symbol}: {e}")
                
        return {
            'prices': prices_df,
            'returns': returns_df,
            'metadata': metadata
        }
    
    def _collect_crypto_data(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Collect crypto data (24/7 trading)."""
        
        prices_df = pd.DataFrame()
        returns_df = pd.DataFrame()
        metadata = {'source': 'Yahoo Finance', 'trading_hours': '24/7', 'symbols': {}}
        
        for symbol in self.CRYPTO:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date, interval='1d')
                
                if not data.empty:
                    # Remove timezone
                    if hasattr(data.index, 'tz') and data.index.tz is not None:
                        data.index = data.index.tz_localize(None)
                    
                    clean_name = symbol.replace('-USD', '')
                    
                    # Store prices
                    prices_df[clean_name] = data['Close']
                    
                    # Calculate log returns
                    returns = np.log(data['Close'] / data['Close'].shift(1))
                    returns_df[clean_name] = returns
                    
                    # Track metadata
                    metadata['symbols'][clean_name] = {
                        'ticker': symbol,
                        'type': 'cryptocurrency',
                        'obs_count': len(data),
                        'missing_count': data['Close'].isna().sum(),
                        'date_range': (str(data.index.min()), str(data.index.max())),
                        'weekend_trading': True
                    }
                    
                    self.logger.info(f"Collected crypto data for {clean_name}: {len(data)} obs")
                    
            except Exception as e:
                self.logger.warning(f"Failed to collect {symbol}: {e}")
                
        return {
            'prices': prices_df,
            'returns': returns_df,
            'metadata': metadata
        }
    
    def _collect_yield_data(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Collect yield data with proper unit handling.
        
        Key fix: Yahoo Finance ^TNX, ^FVX, ^TYX are yield indices (scaled by 10).
        We convert to actual yield levels (percent) and yield changes (basis points).
        """
        
        yield_symbols = {
            '^TNX': 'Treasury_10Y',
            '^FVX': 'Treasury_5Y',
            '^TYX': 'Treasury_30Y'
        }
        
        levels_df = pd.DataFrame()  # Yield levels in percent
        changes_df = pd.DataFrame()  # Yield changes in basis points
        metadata = {'source': 'Yahoo Finance', 'units': {}}
        
        for symbol, name in yield_symbols.items():
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date, interval='1d')
                
                if not data.empty:
                    # Remove timezone
                    if hasattr(data.index, 'tz') and data.index.tz is not None:
                        data.index = data.index.tz_localize(None)
                    
                    # CRITICAL FIX: Convert from index (scaled by 10) to actual yield percent
                    # ^TNX value of 42.5 means 4.25% yield
                    yield_percent = data['Close'] / 10.0
                    levels_df[name] = yield_percent
                    
                    # Calculate changes in basis points (1 bp = 0.01%)
                    yield_change_percent = yield_percent.diff()
                    yield_change_bp = yield_change_percent * 100  # Convert to basis points
                    changes_df[name] = yield_change_bp
                    
                    # Track metadata
                    metadata['units'][name] = {
                        'ticker': symbol,
                        'level_unit': 'percent',
                        'change_unit': 'basis_points',
                        'transformation': 'close_value / 10',
                        'obs_count': len(data),
                        'missing_count': data['Close'].isna().sum()
                    }
                    
                    self.logger.info(
                        f"Collected yield data for {name}: {len(data)} obs, "
                        f"range: {yield_percent.min():.2f}% to {yield_percent.max():.2f}%"
                    )
                    
            except Exception as e:
                self.logger.warning(f"Failed to collect {symbol}: {e}")
                
        return {
            'levels': levels_df,
            'changes': changes_df,
            'metadata': metadata
        }
    
    def _collect_economic_data(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Collect economic data from FRED."""
        
        # Key economic series with units
        series_config = {
            'UNRATE': {'name': 'Unemployment_Rate', 'unit': 'percent'},
            'PAYEMS': {'name': 'Nonfarm_Payrolls', 'unit': 'thousands'},
            'CPIAUCSL': {'name': 'CPI_All_Items', 'unit': 'index'},
            'CPILFESL': {'name': 'CPI_Core', 'unit': 'index'},
            'FEDFUNDS': {'name': 'Federal_Funds_Rate', 'unit': 'percent'},
            'DGS10': {'name': 'Treasury_10Y_Constant', 'unit': 'percent'},
            'DGS2': {'name': 'Treasury_2Y_Constant', 'unit': 'percent'}
        }
        
        data_df = pd.DataFrame()
        metadata = {'source': 'FRED', 'series': {}}
        
        base_url = "https://fred.stlouisfed.org/graph/fredgraph.csv"
        
        for series_id, config in series_config.items():
            try:
                params = {
                    'id': series_id,
                    'cosd': start_date,
                    'coed': end_date
                }
                
                import requests
                from io import StringIO
                
                response = requests.get(base_url, params=params, timeout=10)
                response.raise_for_status()
                
                df = pd.read_csv(StringIO(response.text))
                
                if not df.empty:
                    df['DATE'] = pd.to_datetime(df['DATE'])
                    df = df.set_index('DATE')
                    
                    # Get value column
                    value_col = [col for col in df.columns if col != 'DATE'][0]
                    series_data = pd.to_numeric(df[value_col], errors='coerce')
                    
                    data_df[config['name']] = series_data
                    
                    # Track metadata
                    metadata['series'][config['name']] = {
                        'fred_id': series_id,
                        'unit': config['unit'],
                        'obs_count': series_data.notna().sum(),
                        'frequency': 'monthly' if series_id in ['UNRATE', 'PAYEMS'] else 'daily'
                    }
                    
                    self.logger.info(f"Collected {config['name']}: {series_data.notna().sum()} obs")
                    
            except Exception as e:
                self.logger.warning(f"Failed to collect {series_id}: {e}")
                
        return {
            'data': data_df,
            'metadata': metadata
        }
    
    def _classify_symbol(self, symbol: str) -> str:
        """Classify symbol type."""
        if symbol in self.YIELD_INSTRUMENTS:
            return 'yield_index'
        elif symbol in self.PRICE_INDICES:
            return 'price_index'
        elif symbol in self.TOTAL_RETURN_ETFS:
            return 'total_return_etf'
        elif symbol in self.COMMODITIES:
            return 'commodity_future'
        elif symbol in self.FX:
            return 'fx_index'
        elif symbol in self.CRYPTO:
            return 'cryptocurrency'
        else:
            return 'unknown'
    
    def align_to_business_days(
        self,
        equity_data: pd.DataFrame,
        crypto_data: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Align crypto data to equity business days for cross-asset analysis.
        
        Returns:
            Tuple of (aligned_equity, aligned_crypto) both on business day index
        """
        # Get business day index from equity data
        business_days = equity_data.index
        
        # Reindex crypto to business days, forward filling weekend values
        crypto_aligned = crypto_data.reindex(business_days, method='ffill')
        
        self.logger.info(
            f"Aligned {len(crypto_data)} crypto obs to {len(business_days)} business days"
        )
        
        return equity_data, crypto_aligned
    
    def create_event_aligned_dataset(
        self,
        data: Dict[str, pd.DataFrame],
        event_times: List[pd.Timestamp],
        window_hours_pre: int = 24,
        window_hours_post: int = 24
    ) -> Dict[str, pd.DataFrame]:
        """
        Create event-aligned dataset with proper timestamp handling.
        
        For intraday analysis, would use minute/hourly data.
        For daily analysis, aligns to next business day open.
        """
        event_windows = {}
        
        for i, event_time in enumerate(event_times):
            # For daily data, use date only
            event_date = event_time.normalize()
            
            # Define window
            start_date = event_date - pd.Timedelta(hours=window_hours_pre)
            end_date = event_date + pd.Timedelta(hours=window_hours_post)
            
            # Extract data for window
            window_data = {}
            for key, df in data.items():
                if isinstance(df, pd.DataFrame) and not df.empty:
                    mask = (df.index >= start_date) & (df.index <= end_date)
                    window_df = df.loc[mask].copy()
                    
                    if not window_df.empty:
                        # Calculate days relative to event
                        window_df['days_to_event'] = (window_df.index - event_date).days
                        window_data[key] = window_df
            
            if window_data:
                event_windows[f'event_{i+1}_{event_time.strftime("%Y%m%d")}'] = window_data
        
        return event_windows
