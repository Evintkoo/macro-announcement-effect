"""
Enhanced data collector with multiple fallback sources and 10-year historical coverage.
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import yfinance as yf
import requests
import time
import warnings
from pathlib import Path
import sys
import logging

# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from .base_collector import BaseDataCollector

# Suppress yfinance warnings
warnings.filterwarnings("ignore", message=".*invalid value encountered in divide.*")
warnings.filterwarnings("ignore", message=".*No timezone found.*")

class EnhancedDataCollector(BaseDataCollector):
    """Enhanced data collector with multiple sources and reliability improvements."""
    
    def __init__(self):
        super().__init__("EnhancedDataCollector")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def collect_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> pd.DataFrame:
        """
        Collect data for specified symbols and date range.
        
        Args:
            symbols: List of symbols to collect
            start_date: Start date for data collection
            end_date: End date for data collection
            **kwargs: Additional parameters
            
        Returns:
            DataFrame with collected data
        """
        # Convert datetime to string if needed
        if isinstance(start_date, datetime):
            start_str = start_date.strftime('%Y-%m-%d')
        else:
            start_str = start_date
            
        if isinstance(end_date, datetime):
            end_str = end_date.strftime('%Y-%m-%d')
        else:
            end_str = end_date
        
        # Use the comprehensive collection method
        results = self.collect_comprehensive_data(start_str, end_str)
        
        # Combine all data into a single DataFrame
        prefixed_frames: List[pd.DataFrame] = []
        for source_name, source_data in results.items():
            if isinstance(source_data, pd.DataFrame) and not source_data.empty:
                normalized = self._normalize_datetime_index(source_data.copy())
                normalized.columns = [f"{source_name}_{col}" for col in normalized.columns]
                prefixed_frames.append(normalized)
        
        if prefixed_frames:
            combined_data = pd.concat(prefixed_frames, axis=1, join='outer').sort_index()
        else:
            combined_data = pd.DataFrame()
        
        return combined_data
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate collected data.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        if data is None or data.empty:
            return False
        
        # Check for minimum data requirements
        if len(data) < 10:
            return False
        
        # Check that we have some non-null values
        if data.isnull().all().all():
            return False
        
        return True
        
    def collect_comprehensive_data(
        self, 
        start_date: str = "2015-01-01", 
        end_date: str = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Collect comprehensive 10-year dataset from multiple sources.
        
        Returns:
            Dictionary with 'stocks', 'crypto', 'economic', 'options' data
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        self.logger.info(f"Collecting comprehensive data from {start_date} to {end_date}")
        
        results = {}
        
        # 1. Stock Market Data (Enhanced with multiple attempts)
        results['stocks'] = self._collect_stock_data_enhanced(start_date, end_date)
        
        # 2. Cryptocurrency Data (Enhanced)
        results['crypto'] = self._collect_crypto_data_enhanced(start_date, end_date)
        
        # 3. Economic Data (Already working)
        results['economic'] = self._collect_economic_data_enhanced(start_date, end_date)
        
        # 4. Options/Volatility Data
        results['volatility'] = self._collect_volatility_data(start_date, end_date)
        
        # 5. Fixed Income Data
        results['fixed_income'] = self._collect_fixed_income_data(start_date, end_date)

        # Normalise indexes for consistency
        for key, df in results.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                results[key] = self._normalize_datetime_index(df)
        
        return results
    
    def _collect_stock_data_enhanced(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Enhanced stock data collection with multiple fallback methods."""
        
        # Primary stock symbols for comprehensive analysis
        stock_symbols = {
            # Major Indices
            '^GSPC': 'SP500',  # S&P 500
            '^DJI': 'DJI',     # Dow Jones
            '^IXIC': 'NASDAQ', # NASDAQ
            '^RUT': 'RUSSELL2000', # Russell 2000
            
            # ETFs (more reliable than indices)
            'SPY': 'SPY_ETF',   # SPDR S&P 500
            'QQQ': 'QQQ_ETF',   # Invesco QQQ Trust
            'IWM': 'IWM_ETF',   # iShares Russell 2000
            'VTI': 'VTI_ETF',   # Vanguard Total Stock Market
            
            # Currency
            'DX=F': 'DXY',     # US Dollar Index
            
            # Commodities  
            'GC=F': 'GOLD',    # Gold Futures
            'CL=F': 'OIL',     # Crude Oil
        }
        
        all_data = pd.DataFrame()
        
        for symbol, name in stock_symbols.items():
            data = self._fetch_with_retries(symbol, start_date, end_date)
            if data is not None and not data.empty:
                # Ensure timezone is cleaned
                data = self._normalize_datetime_index(data)
                all_data[name] = data['Close']
                self.logger.info(f"[SUCCESS] Collected {len(data)} observations for {name}")
            else:
                self.logger.warning(f"[FAILED] Failed to collect data for {name} ({symbol})")
        
        return all_data
    
    def _collect_crypto_data_enhanced(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Enhanced crypto data collection."""
        
        # Load config to get crypto symbols
        try:
            from utils.config import Config
            config = Config()
            crypto_symbols_list = config.get('data_sources.crypto.symbols', [])
        except Exception as e:
            self.logger.warning(f"Failed to load crypto symbols from config: {e}, using defaults")
            crypto_symbols_list = [
                'BTC-USD', 'ETH-USD', 'BNB-USD', 'XRP-USD', 'ADA-USD',
                'SOL-USD', 'DOGE-USD', 'MATIC-USD', 'DOT-USD', 'AVAX-USD'
            ]
        
        # Create mapping of symbols to clean names
        crypto_symbols = {}
        for symbol in crypto_symbols_list:
            # Clean name from symbol (remove -USD suffix and format)
            clean_name = symbol.replace('-USD', '').replace('-', '_')
            crypto_symbols[symbol] = clean_name
        
        all_data = pd.DataFrame()
        
        for symbol, name in crypto_symbols.items():
            data = self._fetch_with_retries(symbol, start_date, end_date)
            if data is not None and not data.empty:
                # Ensure timezone is cleaned
                data = self._normalize_datetime_index(data)
                all_data[name] = data['Close']
                self.logger.info(f"[SUCCESS] Collected {len(data)} observations for {name}")
            else:
                self.logger.warning(f"[FAILED] Failed to collect data for {name} ({symbol})")
        
        return all_data
    
    def _collect_economic_data_enhanced(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Enhanced economic data collection from FRED."""
        
        # Comprehensive economic indicators
        economic_series = {
            # Employment
            'UNRATE': 'Unemployment_Rate',
            'PAYEMS': 'Nonfarm_Payrolls',
            'CIVPART': 'Labor_Force_Participation',
            'ICSA': 'Initial_Claims',
            
            # Inflation
            'CPIAUCSL': 'CPI_All_Items',
            'CPILFESL': 'CPI_Core',
            'PCEPI': 'PCE_Price_Index',
            'PCEPILFE': 'PCE_Core',
            
            # GDP and Growth
            'GDP': 'Gross_Domestic_Product',
            'GDPC1': 'Real_GDP',
            'GDPPOT': 'Potential_GDP',
            
            # Interest Rates
            'FEDFUNDS': 'Federal_Funds_Rate',
            'DGS10': 'Treasury_10Y',
            'DGS2': 'Treasury_2Y',
            'DGS3MO': 'Treasury_3M',
            
            # Money Supply
            'M1SL': 'Money_Supply_M1',
            'M2SL': 'Money_Supply_M2',
            
            # Consumer Sentiment
            'UMCSENT': 'Consumer_Sentiment',
            
            # Industrial Production
            'INDPRO': 'Industrial_Production',
            'CAPUTLB50001SQ': 'Capacity_Utilization'
        }
        
        all_data = pd.DataFrame()
        base_url = "https://fred.stlouisfed.org/graph/fredgraph.csv"
        
        for series_id, name in economic_series.items():
            try:
                # Construct URL
                params = {
                    'id': series_id,
                    'cosd': start_date,
                    'coed': end_date,
                    'fq': 'Monthly',  # Monthly frequency
                    'fam': 'avg',     # Average aggregation
                }
                
                response = self.session.get(base_url, params=params, timeout=10)
                response.raise_for_status()
                
                # Parse CSV response
                from io import StringIO
                data = pd.read_csv(StringIO(response.text))
                
                if not data.empty and len(data.columns) >= 2:
                    # Check if 'DATE' column exists, handle different column names
                    date_col = None
                    if 'DATE' in data.columns:
                        date_col = 'DATE'
                    elif 'date' in data.columns:
                        date_col = 'date'
                    elif len(data.columns) > 0:
                        # Use first column as date if no standard date column found
                        date_col = data.columns[0]
                    
                    if date_col:
                        try:
                            data[date_col] = pd.to_datetime(data[date_col])
                            data = data.set_index(date_col)
                            
                            # Ensure timezone is normalized
                            data = self._normalize_datetime_index(data)
                            
                            # Get the value column (should be the non-date column)
                            value_cols = [col for col in data.columns if col != date_col]
                            if value_cols:
                                value_col = value_cols[0]
                                series_data = pd.to_numeric(data[value_col], errors='coerce')
                                
                                if not series_data.dropna().empty:
                                    all_data[name] = series_data
                                    self.logger.info(f"[SUCCESS] Collected {len(series_data.dropna())} observations for {name}")
                                else:
                                    self.logger.warning(f"[FAILED] No valid data for {name} after conversion")
                            else:
                                self.logger.warning(f"[FAILED] No value columns found for {name}")
                        except Exception as parse_error:
                            self.logger.warning(f"[FAILED] Failed to parse data for {name}: {parse_error}")
                    else:
                        self.logger.warning(f"[FAILED] No date column found for {name}")
                    
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                self.logger.warning(f"[FAILED] Failed to collect {name} ({series_id}): {e}")
                continue
        
        return all_data
    
    def _collect_volatility_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Collect volatility and options data."""
        
        volatility_symbols = {
            '^VXN': 'NASDAQ_Volatility'  
            # VIX and VIX-related products removed from analysis
        }
        
        all_data = pd.DataFrame()
        
        for symbol, name in volatility_symbols.items():
            data = self._fetch_with_retries(symbol, start_date, end_date)
            if data is not None and not data.empty:
                # Ensure timezone is cleaned
                if hasattr(data.index, 'tz') and data.index.tz is not None:
                    data.index = data.index.tz_localize(None)
                all_data[name] = data['Close']
                self.logger.info(f"[SUCCESS] Collected volatility data for {name}")
        
        return all_data
    
    def _collect_fixed_income_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Collect fixed income and bond data."""
        
        bond_symbols = {
            '^TNX': 'Treasury_10Y_Yield',
            '^FVX': 'Treasury_5Y_Yield', 
            '^TYX': 'Treasury_30Y_Yield',
            'TLT': 'Treasury_Bond_ETF',
            'IEF': 'Treasury_7_10Y_ETF',
            'SHY': 'Treasury_1_3Y_ETF',
            'LQD': 'Investment_Grade_Bonds',
            'HYG': 'High_Yield_Bonds'
        }
        
        all_data = pd.DataFrame()
        
        for symbol, name in bond_symbols.items():
            data = self._fetch_with_retries(symbol, start_date, end_date)
            if data is not None and not data.empty:
                # Ensure timezone is cleaned
                data = self._normalize_datetime_index(data)
                all_data[name] = data['Close']
                self.logger.info(f"[SUCCESS] Collected bond data for {name}")
        
        return all_data
    
    def _fetch_with_retries(self, symbol: str, start_date: str, end_date: str, max_retries: int = 3) -> Optional[pd.DataFrame]:
        """Fetch data with retry mechanism and multiple methods."""
        
        for attempt in range(max_retries):
            try:
                # Method 1: Standard yfinance
                ticker = yf.Ticker(symbol)
                data = ticker.history(
                    start=start_date,
                    end=end_date,
                    interval='1d',
                    auto_adjust=True,
                    prepost=False,
                    repair=True  # Attempt to repair bad data
                )
                
                if not data.empty:
                    # Clean timezone info immediately after fetching
                    data = self._normalize_datetime_index(data)
                    
                    # Clean the data
                    data = data.dropna()
                    if len(data) > 0:
                        return data
                
                # Method 2: Alternative download method
                if attempt == 1:
                    data = yf.download(
                        symbol,
                        start=start_date,
                        end=end_date,
                        progress=False,
                        show_errors=False
                    )
                    
                    if not data.empty:
                        # Clean timezone info for alternative method too
                        data = self._normalize_datetime_index(data)
                        return data
                
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                if "possibly delisted" in str(e).lower() or "no timezone found" in str(e).lower():
                    self.logger.warning(f"Symbol {symbol} appears to be delisted or has timezone issues, skipping")
                    return None
                elif attempt == max_retries - 1:
                    self.logger.error(f"Final attempt failed for {symbol}: {e}")
                else:
                    time.sleep(1)
                    continue
        
        return None

    @staticmethod
    def _normalize_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
        """Ensure datetime indexes are timezone-naive and sorted for consistency."""
        if isinstance(df.index, pd.DatetimeIndex):
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            df = df.sort_index()
        return df
    
    def create_comprehensive_dataset(self, data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Create comprehensive aligned dataset from all sources."""
        
        all_dataframes = []
        
        for source_name, df in data_dict.items():
            if df is not None and not df.empty:
                # Ensure timezone is normalized before combining
                if isinstance(df.index, pd.DatetimeIndex):
                    if df.index.tz is not None:
                        df.index = df.index.tz_localize(None)
                
                # Add source prefix to column names
                df_renamed = df.add_prefix(f"{source_name}_")
                all_dataframes.append(df_renamed)
                self.logger.info(f"Added {source_name} data: {df.shape}")
        
        if all_dataframes:
            # Ensure all dataframes have timezone-naive indices before concatenation
            for i, df in enumerate(all_dataframes):
                if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None:
                    all_dataframes[i].index = df.index.tz_localize(None)
            
            # Combine all data
            combined_data = pd.concat(all_dataframes, axis=1, sort=True)
            
            # Forward fill missing values (common for economic data)
            combined_data = combined_data.ffill()
            
            # Remove columns that are mostly empty
            min_data_points = len(combined_data) * 0.1  # At least 10% data
            combined_data = combined_data.loc[:, combined_data.count() >= min_data_points]
            
            self.logger.info(f"Final combined dataset: {combined_data.shape}")
            return combined_data
        
        return pd.DataFrame()

class DataQualityAnalyzer:
    """Analyze and ensure data quality for research reliability."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.DataQualityAnalyzer")
    
    def comprehensive_data_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform comprehensive data quality analysis."""
        
        analysis = {
            'basic_stats': self._basic_statistics(data),
            'missing_data': self._missing_data_analysis(data),
            'outlier_detection': self._outlier_detection(data),
            'stationarity_tests': self._stationarity_tests(data),
            'correlation_analysis': self._correlation_analysis(data),
            'data_breaks': self._structural_break_detection(data)
        }
        
        return analysis
    
    def _basic_statistics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic statistics for all series."""
        
        stats = {}
        
        for col in data.columns:
            series = data[col].dropna()
            if len(series) > 0:
                stats[col] = {
                    'count': len(series),
                    'mean': series.mean(),
                    'std': series.std(),
                    'min': series.min(),
                    'max': series.max(),
                    'skewness': series.skew(),
                    'kurtosis': series.kurtosis(),
                    'missing_pct': (len(data) - len(series)) / len(data) * 100
                }
        
        return stats
    
    def _missing_data_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze missing data patterns."""
        
        missing_analysis = {
            'total_missing': data.isnull().sum().to_dict(),
            'missing_percentage': (data.isnull().sum() / len(data) * 100).to_dict(),
            'missing_patterns': {}
        }
        
        # Identify patterns of missingness
        missing_matrix = data.isnull()
        for col in data.columns:
            col_missing = missing_matrix[col]
            if col_missing.sum() > 0:
                # Find consecutive missing periods
                missing_groups = col_missing.groupby((~col_missing).cumsum()).sum()
                missing_analysis['missing_patterns'][col] = {
                    'max_consecutive': missing_groups.max(),
                    'avg_consecutive': missing_groups.mean(),
                    'num_gaps': len(missing_groups[missing_groups > 0])
                }
        
        return missing_analysis
    
    def _outlier_detection(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect outliers using multiple methods."""
        
        outliers = {}
        
        for col in data.select_dtypes(include=[np.number]).columns:
            series = data[col].dropna()
            if len(series) > 10:
                # IQR method
                Q1 = series.quantile(0.25)
                Q3 = series.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                iqr_outliers = series[(series < lower_bound) | (series > upper_bound)]
                
                # Z-score method
                z_scores = np.abs((series - series.mean()) / series.std())
                z_outliers = series[z_scores > 3]
                
                outliers[col] = {
                    'iqr_outliers_count': len(iqr_outliers),
                    'iqr_outliers_pct': len(iqr_outliers) / len(series) * 100,
                    'z_outliers_count': len(z_outliers),
                    'z_outliers_pct': len(z_outliers) / len(series) * 100
                }
        
        return outliers
    
    def _stationarity_tests(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Test for stationarity using ADF test."""
        
        try:
            from statsmodels.tsa.stattools import adfuller
        except ImportError:
            return {'error': 'statsmodels not available for stationarity tests'}
        
        stationarity = {}
        
        for col in data.select_dtypes(include=[np.number]).columns:
            series = data[col].dropna()
            if len(series) > 50:  # Minimum observations for reliable test
                try:
                    result = adfuller(series)
                    stationarity[col] = {
                        'adf_statistic': result[0],
                        'p_value': result[1],
                        'critical_values': result[4],
                        'is_stationary': result[1] < 0.05
                    }
                except:
                    stationarity[col] = {'error': 'ADF test failed'}
        
        return stationarity
    
    def _correlation_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze correlations between series."""
        
        numeric_data = data.select_dtypes(include=[np.number])
        
        if numeric_data.shape[1] > 1:
            correlation_matrix = numeric_data.corr()
            
            # Find high correlations (excluding self-correlations)
            high_corr_pairs = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr_value = correlation_matrix.iloc[i, j]
                    if abs(corr_value) > 0.8:  # High correlation threshold
                        high_corr_pairs.append({
                            'series1': correlation_matrix.columns[i],
                            'series2': correlation_matrix.columns[j],
                            'correlation': corr_value
                        })
            
            return {
                'correlation_matrix': correlation_matrix.to_dict(),
                'high_correlations': high_corr_pairs,
                'mean_abs_correlation': correlation_matrix.abs().mean().mean()
            }
        
        return {'error': 'Insufficient numeric columns for correlation analysis'}
    
    def _structural_break_detection(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect potential structural breaks in the data."""
        
        breaks = {}
        
        for col in data.select_dtypes(include=[np.number]).columns:
            series = data[col].dropna()
            if len(series) > 100:  # Need sufficient data
                # Simple approach: look for large changes in rolling mean
                rolling_mean = series.rolling(window=30, center=True).mean()
                mean_changes = rolling_mean.diff().abs()
                
                # Identify potential break points (large deviations)
                threshold = mean_changes.quantile(0.95)  # Top 5% of changes
                potential_breaks = mean_changes[mean_changes > threshold]
                
                breaks[col] = {
                    'potential_break_dates': potential_breaks.index.tolist(),
                    'max_change': mean_changes.max(),
                    'avg_change': mean_changes.mean()
                }
        
        return breaks