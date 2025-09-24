"""
Feature engineering module for creating analysis variables.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging
from scipy import stats

logger = logging.getLogger(__name__)

class FeatureEngineer:
    """Class for creating features for analysis."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.FeatureEngineer")
    
    def create_surprise_measures(
        self,
        actual_data: pd.DataFrame,
        expected_data: pd.DataFrame = None
    ) -> pd.DataFrame:
        """
        Create surprise measures as defined in the research plan.
        
        Args:
            actual_data: DataFrame with actual announcement values
            expected_data: DataFrame with expected/forecast values (optional)
            
        Returns:
            DataFrame with surprise measures
        """
        if expected_data is None:
            # If no forecast data, use historical mean as proxy for expected
            return self._create_surprise_from_historical(actual_data)
        else:
            return self._create_surprise_from_forecasts(actual_data, expected_data)
    
    def _create_surprise_from_forecasts(
        self,
        actual_data: pd.DataFrame,
        expected_data: pd.DataFrame
    ) -> pd.DataFrame:
        """Create surprises using actual forecast data."""
        surprises = pd.DataFrame(index=actual_data.index)
        
        for col in actual_data.columns:
            if col in expected_data.columns:
                # Raw surprise: A_t - E_t
                raw_surprise = actual_data[col] - expected_data[col]
                surprises[f"{col}_surprise"] = raw_surprise
                
                # Normalized surprise: (A_t - E_t) / σ(E_t)
                # Use rolling standard deviation of surprises
                surprise_std = raw_surprise.rolling(window=12, min_periods=1).std()
                normalized_surprise = raw_surprise / surprise_std
                surprises[f"{col}_normalized_surprise"] = normalized_surprise
                
                # Sign indicator
                sign_indicator = np.where(raw_surprise > 0, 1, 
                                        np.where(raw_surprise < 0, -1, 0))
                surprises[f"{col}_sign"] = sign_indicator
                
                # Absolute surprise
                surprises[f"{col}_abs_surprise"] = np.abs(raw_surprise)
        
        return surprises
    
    def _create_surprise_from_historical(self, actual_data: pd.DataFrame) -> pd.DataFrame:
        """Create surprises using historical mean as expected value."""
        surprises = pd.DataFrame(index=actual_data.index)
        
        for col in actual_data.columns:
            series = actual_data[col].dropna()
            
            # Use rolling mean as "expected" value (12-period window)
            expected = series.rolling(window=12, min_periods=1).mean().shift(1)
            
            # Raw surprise
            raw_surprise = series - expected
            surprises[f"{col}_surprise"] = raw_surprise
            
            # Normalized surprise
            surprise_std = raw_surprise.rolling(window=12, min_periods=1).std()
            normalized_surprise = raw_surprise / surprise_std
            surprises[f"{col}_normalized_surprise"] = normalized_surprise
            
            # Sign indicator
            sign_indicator = np.where(raw_surprise > 0, 1,
                                    np.where(raw_surprise < 0, -1, 0))
            surprises[f"{col}_sign"] = sign_indicator
            
            # Absolute surprise
            surprises[f"{col}_abs_surprise"] = np.abs(raw_surprise)
        
        return surprises
    
    def create_return_features(
        self,
        price_data: pd.DataFrame,
        windows: List[int] = [1, 5, 10, 20]
    ) -> pd.DataFrame:
        """
        Create return-based features.
        
        Args:
            price_data: DataFrame with price data
            windows: List of window sizes for features
            
        Returns:
            DataFrame with return features
        """
        features = pd.DataFrame(index=price_data.index)
        
        for col in price_data.columns:
            prices = price_data[col].dropna()
            
            if len(prices) > max(windows):
                # Log returns
                returns = np.log(prices / prices.shift(1))
                features[f"{col}_return"] = returns
                
                # Rolling return statistics
                for window in windows:
                    # Rolling mean return
                    features[f"{col}_return_mean_{window}d"] = returns.rolling(window).mean()
                    
                    # Rolling volatility
                    features[f"{col}_volatility_{window}d"] = returns.rolling(window).std()
                    
                    # Rolling skewness
                    features[f"{col}_skewness_{window}d"] = returns.rolling(window).skew()
                    
                    # Rolling kurtosis
                    features[f"{col}_kurtosis_{window}d"] = returns.rolling(window).kurt()
                    
                    # Cumulative returns
                    features[f"{col}_cumret_{window}d"] = returns.rolling(window).sum()
        
        return features
    
    def create_volatility_features(
        self,
        returns_data: pd.DataFrame,
        windows: List[int] = [5, 10, 20, 60]
    ) -> pd.DataFrame:
        """
        Create volatility-based features.
        
        Args:
            returns_data: DataFrame with return data
            windows: List of window sizes
            
        Returns:
            DataFrame with volatility features
        """
        features = pd.DataFrame(index=returns_data.index)
        
        for col in returns_data.columns:
            returns = returns_data[col].dropna()
            
            if len(returns) > max(windows):
                for window in windows:
                    # Realized volatility
                    realized_vol = np.sqrt(returns.rolling(window).var() * 252)
                    features[f"{col}_realized_vol_{window}d"] = realized_vol
                    
                    # Exponential smoothing volatility
                    alpha = 2 / (window + 1)
                    exp_vol = returns.ewm(alpha=alpha).std() * np.sqrt(252)
                    features[f"{col}_exp_vol_{window}d"] = exp_vol
                    
                    # High-low volatility (if OHLC data available)
                    # This would need OHLC data, skipping for now
                    
                    # Jump indicators (large moves)
                    threshold = returns.rolling(window).std() * 3
                    jump_indicator = (np.abs(returns) > threshold).astype(int)
                    features[f"{col}_jump_{window}d"] = jump_indicator
        
        return features
    
    def create_market_regime_features(
        self,
        market_data: pd.DataFrame,
        vix_threshold: float = 20.0
    ) -> pd.DataFrame:
        """
        Create market regime indicators.
        
        Args:
            market_data: DataFrame with market data (should include VIX)
            vix_threshold: Threshold for high/low volatility regime
            
        Returns:
            DataFrame with regime features
        """
        features = pd.DataFrame(index=market_data.index)
        
        # VIX-based regime
        if any('vix' in col.lower() for col in market_data.columns):
            vix_col = [col for col in market_data.columns if 'vix' in col.lower()][0]
            vix_data = market_data[vix_col]
            
            features['high_vix_regime'] = (vix_data > vix_threshold).astype(int)
            features['low_vix_regime'] = (vix_data <= vix_threshold).astype(int)
            
            # VIX percentile
            features['vix_percentile'] = vix_data.rolling(252).rank(pct=True)
        
        # Market trend regime (using S&P 500 if available)
        sp500_cols = [col for col in market_data.columns 
                     if any(indicator in col.lower() for indicator in ['sp500', 'gspc', '^gspc'])]
        
        if sp500_cols:
            sp500_col = sp500_cols[0]
            sp500_prices = market_data[sp500_col]
            
            # Bull/bear market based on 200-day MA
            ma_200 = sp500_prices.rolling(200).mean()
            features['bull_market'] = (sp500_prices > ma_200).astype(int)
            features['bear_market'] = (sp500_prices <= ma_200).astype(int)
            
            # Trend strength
            features['trend_strength'] = (sp500_prices - ma_200) / ma_200
        
        return features
    
    def create_interaction_features(
        self,
        surprise_data: pd.DataFrame,
        regime_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Create interaction features between surprises and market regimes.
        
        Args:
            surprise_data: DataFrame with surprise measures
            regime_data: DataFrame with regime indicators
            
        Returns:
            DataFrame with interaction features
        """
        features = pd.DataFrame(index=surprise_data.index)
        
        # Get surprise columns
        surprise_cols = [col for col in surprise_data.columns if 'surprise' in col]
        regime_cols = [col for col in regime_data.columns if 'regime' in col or 'market' in col]
        
        # Create interactions
        for surprise_col in surprise_cols:
            for regime_col in regime_cols:
                if surprise_col in surprise_data.columns and regime_col in regime_data.columns:
                    interaction_name = f"{surprise_col}_x_{regime_col}"
                    features[interaction_name] = (
                        surprise_data[surprise_col] * regime_data[regime_col]
                    )
        
        return features
    
    def create_event_window_features(
        self,
        data: pd.DataFrame,
        event_times: List[datetime],
        pre_window: int = 1,
        post_window: int = 3
    ) -> pd.DataFrame:
        """
        Create event window indicators.
        
        Args:
            data: DataFrame with time series data
            event_times: List of event times
            pre_window: Days before event
            post_window: Days after event
            
        Returns:
            DataFrame with event window indicators
        """
        features = pd.DataFrame(index=data.index, columns=[
            'pre_event', 'event_day', 'post_event_1d', 'post_event_2d', 'post_event_3d'
        ], data=0)
        
        for event_time in event_times:
            event_date = event_time.date() if hasattr(event_time, 'date') else event_time
            
            # Pre-event window
            for i in range(1, pre_window + 1):
                pre_date = event_date - pd.Timedelta(days=i)
                if pre_date in data.index:
                    features.loc[pre_date, 'pre_event'] = 1
            
            # Event day
            if event_date in data.index:
                features.loc[event_date, 'event_day'] = 1
            
            # Post-event windows
            for i in range(1, post_window + 1):
                post_date = event_date + pd.Timedelta(days=i)
                if post_date in data.index:
                    if i == 1:
                        features.loc[post_date, 'post_event_1d'] = 1
                    elif i == 2:
                        features.loc[post_date, 'post_event_2d'] = 1
                    elif i == 3:
                        features.loc[post_date, 'post_event_3d'] = 1
        
        return features
    
    def create_comprehensive_features(
        self,
        price_data: pd.DataFrame,
        economic_data: pd.DataFrame,
        announcement_times: List[datetime] = None
    ) -> pd.DataFrame:
        """
        Create comprehensive feature set for analysis.
        
        Args:
            price_data: DataFrame with price data
            economic_data: DataFrame with economic indicators
            announcement_times: List of announcement times
            
        Returns:
            DataFrame with all features
        """
        all_features = pd.DataFrame(index=price_data.index)
        
        # Return features
        return_features = self.create_return_features(price_data)
        all_features = all_features.join(return_features, how='outer')
        
        # Volatility features  
        returns_data = pd.DataFrame()
        for col in price_data.columns:
            returns_data[col] = np.log(price_data[col] / price_data[col].shift(1))
        
        volatility_features = self.create_volatility_features(returns_data)
        all_features = all_features.join(volatility_features, how='outer')
        
        # Surprise features
        surprise_features = self.create_surprise_measures(economic_data)
        all_features = all_features.join(surprise_features, how='outer')
        
        # Market regime features
        regime_features = self.create_market_regime_features(price_data)
        all_features = all_features.join(regime_features, how='outer')
        
        # Interaction features
        interaction_features = self.create_interaction_features(surprise_features, regime_features)
        all_features = all_features.join(interaction_features, how='outer')
        
        # Event window features
        if announcement_times:
            event_features = self.create_event_window_features(all_features, announcement_times)
            all_features = all_features.join(event_features, how='outer')
        
        self.logger.info(f"Created {len(all_features.columns)} features")
        return all_features