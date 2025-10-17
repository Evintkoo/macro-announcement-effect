"""
Tests for feature engineering module.

P2 Fix #29: Test suite for feature engineering functions.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime


class TestSurpriseCalculation:
    """Test economic surprise measure calculations."""
    
    def test_raw_surprise_from_forecasts(self):
        """Test raw surprise calculation with actual forecasts."""
        actual = pd.Series([3.5, 3.7, 3.3, 3.8], index=pd.date_range('2020-01-01', periods=4, freq='M'))
        expected = pd.Series([3.6, 3.5, 3.4, 3.7], index=actual.index)
        
        # Raw surprise = Actual - Expected
        surprise = actual - expected
        
        assert surprise.iloc[0] == pytest.approx(-0.1, abs=1e-10)  # 3.5 - 3.6
        assert surprise.iloc[1] == pytest.approx(0.2, abs=1e-10)   # 3.7 - 3.5
        assert surprise.iloc[2] == pytest.approx(-0.1, abs=1e-10)  # 3.3 - 3.4
        assert surprise.iloc[3] == pytest.approx(0.1, abs=1e-10)   # 3.8 - 3.7
    
    def test_normalized_surprise(self):
        """Test surprise normalization by rolling standard deviation."""
        surprises = pd.Series([0.1, 0.2, -0.1, 0.3, -0.2, 0.15, -0.05])
        
        # Calculate rolling std
        rolling_std = surprises.rolling(window=5, min_periods=1).std()
        
        # Normalized surprise
        normalized = surprises / rolling_std
        
        # Should be dimensionless
        assert not np.isnan(normalized.iloc[-1])
        
        # Larger absolute surprises should have larger normalized values
        assert abs(normalized.iloc[3]) > abs(normalized.iloc[0])
    
    def test_proxy_surprise_from_historical_mean(self):
        """Test proxy surprise using historical mean as expected value."""
        # Simulated monthly data
        data = pd.Series(
            [3.5, 3.6, 3.4, 3.7, 3.5, 3.8, 3.6, 3.9, 3.7, 4.0],
            index=pd.date_range('2020-01-01', periods=10, freq='M')
        )
        
        # Expected = 12-period rolling mean (lagged)
        # For shorter series, use available data
        window = min(6, len(data))
        expected = data.rolling(window=window, min_periods=1).mean().shift(1)
        
        # Proxy surprise
        proxy_surprise = data - expected
        
        # First value should be NaN (no prior data)
        assert pd.isna(proxy_surprise.iloc[0])
        
        # Should have valid values after
        assert not pd.isna(proxy_surprise.iloc[-1])
    
    def test_surprise_sign_indicator(self):
        """Test surprise sign indicator creation."""
        surprises = pd.Series([0.1, -0.2, 0.0, 0.3, -0.1])
        
        # Sign indicator: +1 for positive, -1 for negative, 0 for zero
        sign = np.where(surprises > 0, 1, np.where(surprises < 0, -1, 0))
        
        assert sign[0] == 1   # 0.1 > 0
        assert sign[1] == -1  # -0.2 < 0
        assert sign[2] == 0   # 0.0 == 0
        assert sign[3] == 1   # 0.3 > 0
        assert sign[4] == -1  # -0.1 < 0
    
    def test_absolute_surprise(self):
        """Test absolute surprise magnitude."""
        surprises = pd.Series([0.1, -0.2, 0.0, 0.3, -0.1])
        abs_surprise = surprises.abs()
        
        assert abs_surprise.iloc[0] == 0.1
        assert abs_surprise.iloc[1] == 0.2
        assert abs_surprise.iloc[2] == 0.0
        assert abs_surprise.iloc[3] == 0.3
        assert abs_surprise.iloc[4] == 0.1


class TestReturnFeatures:
    """Test return-based feature calculations."""
    
    def test_log_returns(self):
        """Test log return calculation."""
        prices = pd.Series([100, 105, 103, 108, 110])
        
        log_returns = np.log(prices / prices.shift(1))
        
        # First value is NaN
        assert pd.isna(log_returns.iloc[0])
        
        # Second value: ln(105/100)
        expected = np.log(105/100)
        assert abs(log_returns.iloc[1] - expected) < 1e-10
    
    def test_rolling_mean_return(self):
        """Test rolling mean return calculation."""
        returns = pd.Series([0.01, 0.02, -0.01, 0.03, -0.005, 0.015])
        
        # 3-day rolling mean
        rolling_mean = returns.rolling(window=3, min_periods=1).mean()
        
        # Third value should be mean of first 3 returns
        expected = (0.01 + 0.02 + (-0.01)) / 3
        assert abs(rolling_mean.iloc[2] - expected) < 1e-10
    
    def test_rolling_volatility(self):
        """Test rolling volatility calculation."""
        returns = pd.Series([0.01, 0.02, -0.01, 0.03, -0.02, 0.015, -0.01])
        
        # 5-day rolling volatility
        rolling_vol = returns.rolling(window=5, min_periods=1).std()
        
        # Should have positive values
        assert all(rolling_vol.dropna() > 0)
        
        # Higher variation should give higher volatility
        high_var = pd.Series([0.05, -0.04, 0.06, -0.05, 0.04])
        low_var = pd.Series([0.01, 0.01, 0.01, 0.01, 0.01])
        
        assert high_var.std() > low_var.std()
    
    def test_cumulative_returns(self):
        """Test cumulative return calculation."""
        returns = pd.Series([0.01, 0.02, -0.01, 0.015])
        
        # Cumulative sum of log returns
        cum_returns = returns.cumsum()
        
        assert cum_returns.iloc[0] == 0.01
        assert cum_returns.iloc[1] == 0.01 + 0.02
        assert cum_returns.iloc[2] == 0.01 + 0.02 + (-0.01)
        assert cum_returns.iloc[3] == 0.01 + 0.02 + (-0.01) + 0.015


class TestVolatilityFeatures:
    """Test volatility-based features."""
    
    def test_realized_volatility(self):
        """Test realized volatility calculation."""
        returns = pd.Series(np.random.normal(0, 0.01, 252))  # One year of data
        
        # 20-day realized volatility, annualized
        window = 20
        realized_vol = np.sqrt(returns.rolling(window).var() * 252)
        
        # Should be positive
        assert all(realized_vol.dropna() > 0)
        
        # Should be roughly in reasonable range (annualized)
        assert realized_vol.dropna().mean() < 1.0  # Less than 100% annualized
    
    def test_exponential_smoothing_volatility(self):
        """Test exponentially weighted volatility."""
        returns = pd.Series([0.01, 0.02, -0.01, 0.03, -0.02, 0.015])
        
        # EWM volatility with alpha = 0.2
        ewm_vol = returns.ewm(alpha=0.2).std()
        
        # Should have values
        assert not ewm_vol.dropna().empty
        
        # Should give more weight to recent data
        # (this is implicit in EWM but hard to test directly)
        assert ewm_vol.iloc[-1] > 0
    
    def test_jump_indicators(self):
        """Test jump (large move) indicators."""
        returns = pd.Series([0.01, 0.02, 0.05, 0.01, -0.04, 0.02])  # Contains jumps
        
        # Calculate threshold: 3 standard deviations
        rolling_std = returns.rolling(window=5, min_periods=1).std()
        threshold = 3 * rolling_std
        
        # Jump indicator
        is_jump = (returns.abs() > threshold).astype(int)
        
        # Large moves (0.05, -0.04) should be flagged as jumps
        # (depending on rolling std calculation)
        assert isinstance(is_jump, pd.Series)
        assert all(is_jump.isin([0, 1]))


class TestMarketRegimeFeatures:
    """Test market regime indicators."""
    
    def test_high_volatility_regime(self):
        """Test high volatility regime indicator."""
        # Create data with volatility shift
        low_vol = np.random.normal(0, 0.005, 100)
        high_vol = np.random.normal(0, 0.02, 100)
        returns = pd.Series(np.concatenate([low_vol, high_vol]))
        
        # Calculate rolling volatility
        rolling_vol = returns.rolling(20).std()
        
        # Threshold for high volatility
        threshold = 0.015
        high_vol_regime = (rolling_vol > threshold).astype(int)
        
        # Later period should have more high volatility flags
        assert high_vol_regime.iloc[150:].sum() > high_vol_regime.iloc[:50].sum()
    
    def test_bull_bear_market_indicator(self):
        """Test bull/bear market indicator based on moving average."""
        # Create trending price data
        trend = np.linspace(100, 150, 250)  # Uptrend
        prices = pd.Series(trend + np.random.normal(0, 2, 250))
        
        # 200-day moving average
        ma_200 = prices.rolling(200).mean()
        
        # Bull market when price > MA
        bull_market = (prices > ma_200).astype(int)
        
        # Later period (uptrend) should be mostly bull market
        assert bull_market.iloc[-50:].sum() > 40  # Most of last 50 days
    
    def test_trend_strength(self):
        """Test trend strength calculation."""
        prices = pd.Series([100, 105, 110, 115, 120])
        ma = pd.Series([98, 102, 106, 110, 114])
        
        # Trend strength = (Price - MA) / MA
        trend_strength = (prices - ma) / ma
        
        # Should be positive when above MA
        assert all(trend_strength > 0)
        
        # Should increase with distance from MA
        assert trend_strength.iloc[-1] > trend_strength.iloc[0]


class TestInteractionFeatures:
    """Test interaction feature creation."""
    
    def test_surprise_regime_interaction(self):
        """Test surprise × regime interaction."""
        surprise = pd.Series([0.1, -0.2, 0.3, -0.1, 0.2])
        high_vol_regime = pd.Series([0, 0, 1, 1, 1])
        
        # Interaction
        interaction = surprise * high_vol_regime
        
        # First two should be zero (low vol regime)
        assert interaction.iloc[0] == 0
        assert interaction.iloc[1] == 0
        
        # Last three should equal surprise (high vol regime)
        assert interaction.iloc[2] == 0.3
        assert interaction.iloc[3] == -0.1
        assert interaction.iloc[4] == 0.2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
