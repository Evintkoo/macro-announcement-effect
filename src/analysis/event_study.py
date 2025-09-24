"""
Event study analysis implementation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import scipy.stats as stats
import logging
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from utils.config import Config

# Global config instance
config = Config()
logger = logging.getLogger(__name__)

class EventStudyAnalyzer:
    """Event study analysis implementation following the research methodology."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.EventStudyAnalyzer")
    
    def estimate_normal_returns(
        self,
        returns_data: pd.DataFrame,
        market_returns: pd.Series,
        estimation_window: int = 100,  # Reduced to fit available data
        exclude_event_windows: List[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Estimate normal return model parameters (market model).
        
        Formula: r_{i,t} = α_i + β_i * m_t + ε_{i,t}
        
        Args:
            returns_data: DataFrame with asset returns
            market_returns: Series with market returns (e.g., S&P 500)
            estimation_window: Number of days for estimation
            exclude_event_windows: List of (start, end) tuples to exclude
            
        Returns:
            Dictionary with model parameters for each asset
        """
        model_params = {}
        
        for asset in returns_data.columns:
            asset_returns = returns_data[asset].dropna()
            
            # Align with market returns first
            common_dates = asset_returns.index.intersection(market_returns.index)
            if len(common_dates) < 30:  # Not enough overlap
                self.logger.warning(f"Insufficient overlapping data for {asset}: {len(common_dates)} days")
                model_params[asset] = {
                    'alpha': 0.0,
                    'beta': 1.0,
                    'residual_std': 0.02,
                    'r_squared': 0.0,
                    'n_observations': 0
                }
                continue
                
            asset_ret = asset_returns.loc[common_dates]
            market_ret = market_returns.loc[common_dates]
            
            # Exclude event windows if specified
            if exclude_event_windows:
                mask = pd.Series(True, index=common_dates)
                for start_date, end_date in exclude_event_windows:
                    event_mask = (common_dates >= start_date) & (common_dates <= end_date)
                    mask = mask & ~event_mask
                
                asset_ret = asset_ret[mask]
                market_ret = market_ret[mask]
            
            # Use available data up to estimation_window
            n_available = min(len(asset_ret), estimation_window)
            if n_available > 30:
                asset_ret = asset_ret.tail(n_available)
                market_ret = market_ret.tail(n_available)
            
                # Remove any remaining NaN values
                valid_mask = asset_ret.notna() & market_ret.notna()
                asset_ret_clean = asset_ret[valid_mask]
                market_ret_clean = market_ret[valid_mask]
                
                if len(asset_ret_clean) > 20:  # Reduced minimum requirement
                    try:
                        # Simple OLS regression
                        X = np.column_stack([np.ones(len(market_ret_clean)), market_ret_clean])
                        y = asset_ret_clean.values
                        
                        params = np.linalg.lstsq(X, y, rcond=None)[0]
                        alpha, beta = params[0], params[1]
                        
                        # Calculate residuals and statistics
                        predicted = alpha + beta * market_ret_clean
                        residuals = asset_ret_clean - predicted
                        residual_std = np.std(residuals) if len(residuals) > 1 else 0.02
                        
                        # Avoid division by zero
                        var_actual = np.var(asset_ret_clean)
                        var_residuals = np.var(residuals)
                        r_squared = max(0, 1 - var_residuals / var_actual) if var_actual > 0 else 0.0
                        
                        model_params[asset] = {
                            'alpha': alpha,
                            'beta': beta,
                            'residual_std': residual_std,
                            'r_squared': r_squared,
                            'n_observations': len(asset_ret_clean)
                        }
                        
                        self.logger.info(
                            f"Estimated model for {asset}: alpha={alpha:.4f}, beta={beta:.4f}, R2={r_squared:.4f}, N={len(asset_ret_clean)}"
                        )
                        
                    except (np.linalg.LinAlgError, ValueError) as e:
                        self.logger.warning(f"Could not estimate model for {asset}: {e}")
                        model_params[asset] = {
                            'alpha': 0.0,
                            'beta': 1.0 if asset != market_returns.name else 1.0,
                            'residual_std': np.std(asset_ret_clean) if len(asset_ret_clean) > 1 else 0.02,
                            'r_squared': 0.0,
                            'n_observations': len(asset_ret_clean)
                        }
                else:
                    self.logger.warning(f"Insufficient clean data for {asset}: {len(asset_ret_clean)} observations")
                    model_params[asset] = {
                        'alpha': 0.0,
                        'beta': 1.0,
                        'residual_std': 0.02,
                        'r_squared': 0.0,
                        'n_observations': 0
                    }
            else:
                self.logger.warning(f"Insufficient data for {asset}: {n_available} observations")
                model_params[asset] = {
                    'alpha': 0.0,
                    'beta': 1.0,
                    'residual_std': 0.02,
                    'r_squared': 0.0,
                    'n_observations': 0
                }
        
        return model_params
    
    def calculate_abnormal_returns(
        self,
        returns_data: pd.DataFrame,
        market_returns: pd.Series,
        model_params: Dict[str, Dict[str, float]],
        event_windows: List[Tuple[datetime, datetime]]
    ) -> Dict[str, pd.DataFrame]:
        """
        Calculate abnormal returns for event windows.
        
        Formula: AR_{i,t} = r_{i,t} - (α̂_i + β̂_i * m_t)
        
        Args:
            returns_data: DataFrame with asset returns
            market_returns: Series with market returns
            model_params: Model parameters from estimation
            event_windows: List of (start, end) event windows
            
        Returns:
            Dictionary with abnormal returns for each event
        """
        abnormal_returns = {}
        
        for i, (start_date, end_date) in enumerate(event_windows):
            event_data = pd.DataFrame()
            
            # Get returns in event window - use consistent index
            event_mask = (returns_data.index >= start_date) & (returns_data.index <= end_date)
            event_returns = returns_data.loc[event_mask]
            
            # Get market returns for the same dates that exist in event_returns
            common_dates = event_returns.index.intersection(market_returns.index)
            event_market_returns = market_returns.loc[common_dates]
            event_returns = event_returns.loc[common_dates]
            
            if not event_returns.empty and not event_market_returns.empty:
                for asset in returns_data.columns:
                    if asset in model_params and asset in event_returns.columns:
                        params = model_params[asset]
                        alpha = params['alpha']
                        beta = params['beta']
                        
                        # Get actual returns for this asset in the event window
                        actual_returns = event_returns[asset].dropna()
                        
                        if len(actual_returns) > 0:
                            # Get corresponding market returns for the same dates
                            asset_dates = actual_returns.index
                            corresponding_market_returns = event_market_returns.loc[asset_dates.intersection(event_market_returns.index)]
                            
                            if len(corresponding_market_returns) > 0:
                                # Calculate expected returns
                                expected_returns = alpha + beta * corresponding_market_returns
                                
                                # Align actual and expected returns by index
                                aligned_dates = actual_returns.index.intersection(expected_returns.index)
                                if len(aligned_dates) > 0:
                                    actual_aligned = actual_returns.loc[aligned_dates]
                                    expected_aligned = expected_returns.loc[aligned_dates]
                                    
                                    # Calculate abnormal returns
                                    abnormal_ret = actual_aligned - expected_aligned
                                    event_data[asset] = abnormal_ret
                
                if not event_data.empty:
                    abnormal_returns[f'event_{i+1}'] = event_data
                    self.logger.info(f"Event {i+1}: {len(event_data)} assets, {len(event_data.index)} days")
        
        return abnormal_returns
    
    def calculate_cumulative_abnormal_returns(
        self,
        abnormal_returns: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:
        """
        Calculate Cumulative Abnormal Returns (CAR).
        
        Formula: CAR_{i,T} = Σ_{t∈T} AR_{i,t}
        
        Args:
            abnormal_returns: Dictionary with abnormal returns by event
            
        Returns:
            Dictionary with CARs for each event
        """
        cumulative_abnormal_returns = {}
        
        for event_name, ar_data in abnormal_returns.items():
            car_data = ar_data.cumsum()
            cumulative_abnormal_returns[event_name] = car_data
        
        return cumulative_abnormal_returns
    
    def test_abnormal_returns_significance(
        self,
        abnormal_returns: Dict[str, pd.DataFrame],
        model_params: Dict[str, Dict[str, float]],
        confidence_level: float = 0.05
    ) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        Test statistical significance of abnormal returns.
        
        Args:
            abnormal_returns: Dictionary with abnormal returns
            model_params: Model parameters for standard error calculation
            confidence_level: Significance level for tests
            
        Returns:
            Dictionary with test statistics and p-values
        """
        test_results = {}
        
        for event_name, ar_data in abnormal_returns.items():
            event_tests = {}
            
            for asset in ar_data.columns:
                if asset in model_params:
                    ar_series = ar_data[asset].dropna()
                    
                    if len(ar_series) > 0:
                        # Use residual standard error from estimation
                        std_error = model_params[asset]['residual_std']
                        
                        # Calculate test statistics for each day
                        t_stats = ar_series / std_error
                        # stats.t.cdf returns a numpy array; wrap it back to Series to preserve index
                        p_vals_array = 2 * (
                            1 - stats.t.cdf(np.abs(t_stats.values), df=model_params[asset]['n_observations'] - 2)
                        )
                        p_values = pd.Series(p_vals_array, index=ar_series.index)
                        
                        # Overall test for event window
                        car_total = ar_series.sum()
                        car_std_error = std_error * np.sqrt(len(ar_series))
                        car_t_stat = car_total / car_std_error
                        car_p_value = 2 * (1 - stats.t.cdf(np.abs(car_t_stat),
                                                          df=model_params[asset]['n_observations']-2))
                        
                        event_tests[asset] = {
                            'daily_t_stats': t_stats.to_dict(),
                            'daily_p_values': p_values.to_dict(),
                            'car_total': car_total,
                            'car_t_stat': car_t_stat,
                            'car_p_value': car_p_value,
                            'significant': car_p_value < confidence_level
                        }
            
            test_results[event_name] = event_tests
        
        return test_results
    
    def calculate_average_abnormal_returns(
        self,
        abnormal_returns: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Calculate Average Abnormal Returns (AAR) across events.
        
        Args:
            abnormal_returns: Dictionary with abnormal returns by event
            
        Returns:
            DataFrame with average abnormal returns
        """
        # Collect all abnormal returns by relative time
        all_ars = []
        
        for event_name, ar_data in abnormal_returns.items():
            # Skip empty frames
            if ar_data is None or ar_data.empty:
                continue

            # Ensure we are working with a copy and contiguous integer index
            n = int(ar_data.shape[0])
            if n == 0:
                continue
            ar_with_time = ar_data.copy().reset_index(drop=True)

            # Build a centered event-time index of length n robustly
            # Always yields exactly n integers centered around 0
            event_time = np.arange(-n // 2, -n // 2 + n, dtype=int)
            if len(event_time) != n:
                # Fallback (shouldn't happen, but be safe)
                event_time = np.arange(n, dtype=int) - (n // 2)

            # Attach and set as index
            ar_with_time['event_time'] = event_time
            ar_with_time.set_index('event_time', inplace=True)
            all_ars.append(ar_with_time)
        
        if all_ars:
            # Combine and calculate averages
            combined_ars = pd.concat(all_ars, axis=0)
            average_ars = combined_ars.groupby(combined_ars.index).mean()
            
            return average_ars
        
        return pd.DataFrame()
    
    def analyze_events(
        self,
        aligned_data: pd.DataFrame,
        sample_events: List[datetime],
        event_window_days: int = 3,
        estimation_window: int = 250
    ) -> Dict[str, any]:
        """
        Analyze events using the aligned data.
        
        Args:
            aligned_data: DataFrame with aligned asset data
            sample_events: List of event dates
            event_window_days: Days around event (±days)
            estimation_window: Days for model estimation
            
        Returns:
            Dictionary with event study results
        """
        self.logger.info(f"Analyzing {len(sample_events)} events")
        self.logger.info(f"Data shape: {aligned_data.shape}")
        self.logger.info(f"Available columns: {list(aligned_data.columns)}")
        
        # Find price columns by excluding volume, return, volatility and other derived columns
        price_columns = []
        for col in aligned_data.columns:
            if not any(suffix in col.lower() for suffix in ['volume', '_return', '_volatility', 'surprise', 'lag', 'dummy', 'unrate', 'payems', 'civpart', 'cpiaucsl', 'cpilfesl', 'pcepi', 'pcepilfe']):
                # Check if column has sufficient non-null data
                if aligned_data[col].notna().sum() > 100:  # At least 100 observations
                    price_columns.append(col)
        
        self.logger.info(f"Selected price columns: {price_columns}")
        
        if not price_columns:
            self.logger.error("No suitable price columns found")
            return {'error': 'No suitable price columns found'}
        
        # Calculate returns from prices
        returns_data = pd.DataFrame(index=aligned_data.index)
        for col in price_columns:
            prices = aligned_data[col].dropna()
            if len(prices) > 10:  # Need minimum data points
                returns = prices.pct_change().dropna()
                # Remove extreme outliers (>10% daily change) - likely data errors
                returns = returns[np.abs(returns) < 0.10]
                returns_data[col] = returns
                self.logger.info(f"Calculated returns for {col}: {len(returns)} observations")
        
        # Filter to columns with sufficient return data
        valid_return_columns = []
        for col in returns_data.columns:
            if returns_data[col].notna().sum() > 50:  # At least 50 return observations
                valid_return_columns.append(col)
        
        if not valid_return_columns:
            self.logger.error("No columns with sufficient return data")
            return {'error': 'No columns with sufficient return data'}
        
        returns_data = returns_data[valid_return_columns]
        self.logger.info(f"Valid return columns: {valid_return_columns}")
        
        # Use ^GSPC as market proxy if available, otherwise first valid column
        market_proxy_col = None
        for col in valid_return_columns:
            if '^GSPC' in col or 'GSPC' in col:
                market_proxy_col = col
                break
        
        if market_proxy_col is None:
            market_proxy_col = valid_return_columns[0]  # Use first valid column
        
        market_returns = returns_data[market_proxy_col].dropna()
        self.logger.info(f"Using {market_proxy_col} as market proxy with {len(market_returns)} observations")
        
        if len(market_returns) < 100:
            self.logger.warning(f"Insufficient market return data: {len(market_returns)} observations")
            return {'error': f'Insufficient market return data: {len(market_returns)} observations'}
        
        # Run full event study
        results = self.run_full_event_study(
            returns_data=returns_data,
            market_returns=market_returns,
            announcement_times=sample_events,
            event_window_days=event_window_days,
            estimation_window=estimation_window
        )
        
        return results
    
    def run_full_event_study(
        self,
        returns_data: pd.DataFrame,
        market_returns: pd.Series,
        announcement_times: List[datetime],
        event_window_days: int = 3,
        estimation_window: int = 250
    ) -> Dict[str, any]:
        """
        Run complete event study analysis.
        
        Args:
            returns_data: DataFrame with asset returns
            market_returns: Series with market returns
            announcement_times: List of announcement times
            event_window_days: Days around announcement (±days)
            estimation_window: Days for model estimation
            
        Returns:
            Dictionary with complete results
        """
        self.logger.info(f"Running event study for {len(announcement_times)} events")
        
        # Create event windows
        event_windows = []
        for announce_time in announcement_times:
            start_date = announce_time - pd.Timedelta(days=event_window_days)
            end_date = announce_time + pd.Timedelta(days=event_window_days)
            event_windows.append((start_date, end_date))
        
        # Step 1: Estimate normal return models
        model_params = self.estimate_normal_returns(
            returns_data, market_returns, estimation_window, event_windows
        )
        
        # Step 2: Calculate abnormal returns
        abnormal_returns = self.calculate_abnormal_returns(
            returns_data, market_returns, model_params, event_windows
        )
        
        # Step 3: Calculate cumulative abnormal returns
        cars = self.calculate_cumulative_abnormal_returns(abnormal_returns)
        
        # Step 4: Test significance
        significance_tests = self.test_abnormal_returns_significance(
            abnormal_returns, model_params
        )
        
        # Step 5: Calculate averages
        average_ars = self.calculate_average_abnormal_returns(abnormal_returns)
        average_cars = self.calculate_average_abnormal_returns(cars)
        
        results = {
            'model_parameters': model_params,
            'abnormal_returns': abnormal_returns,
            'cumulative_abnormal_returns': cars,
            'significance_tests': significance_tests,
            'average_abnormal_returns': average_ars,
            'average_cumulative_abnormal_returns': average_cars,
            'event_windows': event_windows,
            'summary_statistics': self._calculate_summary_statistics(abnormal_returns, cars)
        }
        
        self.logger.info("Event study analysis completed")
        return results
    
    def _calculate_summary_statistics(
        self,
        abnormal_returns: Dict[str, pd.DataFrame],
        cars: Dict[str, pd.DataFrame]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate summary statistics for the event study."""
        summary = {}
        
        # Collect all CARs for summary
        all_cars = []
        for event_name, car_data in cars.items():
            final_cars = car_data.iloc[-1]  # Final CAR for each asset
            all_cars.append(final_cars)
        
        if all_cars:
            cars_df = pd.DataFrame(all_cars)
            
            for asset in cars_df.columns:
                asset_cars = cars_df[asset].dropna()
                
                if len(asset_cars) > 0:
                    summary[asset] = {
                        'mean_car': asset_cars.mean(),
                        'median_car': asset_cars.median(),
                        'std_car': asset_cars.std(),
                        'min_car': asset_cars.min(),
                        'max_car': asset_cars.max(),
                        'positive_events': (asset_cars > 0).sum(),
                        'negative_events': (asset_cars < 0).sum(),
                        'total_events': len(asset_cars)
                    }
        
        return summary