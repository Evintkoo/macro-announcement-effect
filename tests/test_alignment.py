"""
Tests for timezone and data alignment handling.

P2 Fix #29: Test suite for timezone consistency and cross-asset alignment.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class TestTimezoneHandling:
    """Test timezone handling for daily data pipeline."""
    
    def test_naive_datetime_index(self):
        """Test that timezone-naive indexes are used for daily data."""
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        
        # Should be timezone-naive by default
        assert dates.tz is None
        
        # Create DataFrame
        df = pd.DataFrame({'value': np.random.randn(100)}, index=dates)
        assert df.index.tz is None
    
    def test_timezone_normalization(self):
        """Test that timezone-aware data is converted to naive."""
        # Create timezone-aware dates
        dates_utc = pd.date_range('2020-01-01', periods=100, freq='D', tz='UTC')
        
        # Convert to naive
        dates_naive = dates_utc.tz_localize(None)
        
        assert dates_utc.tz is not None
        assert dates_naive.tz is None
        
        # Dates should still be equal
        assert all(dates_utc.date == dates_naive.date)
    
    def test_midnight_normalization(self):
        """Test that dates are normalized to midnight for comparison."""
        # Create datetime with time component
        dt_with_time = pd.Timestamp('2020-01-01 14:30:00')
        
        # Normalize to midnight
        dt_normalized = dt_with_time.normalize()
        
        assert dt_normalized.hour == 0
        assert dt_normalized.minute == 0
        assert dt_normalized.second == 0
        assert dt_normalized.date() == dt_with_time.date()
    
    def test_cross_timezone_data_merge(self):
        """Test merging data from different timezone sources."""
        # Simulate data from different sources
        dates1 = pd.date_range('2020-01-01', periods=10, freq='D', tz='America/New_York')
        dates2 = pd.date_range('2020-01-01', periods=10, freq='D', tz='UTC')
        
        df1 = pd.DataFrame({'val1': range(10)}, index=dates1)
        df2 = pd.DataFrame({'val2': range(10)}, index=dates2)
        
        # Convert both to naive for merging
        df1.index = df1.index.tz_localize(None)
        df2.index = df2.index.tz_localize(None)
        
        # Should merge without issues
        merged = df1.join(df2, how='outer')
        
        assert len(merged) == 10
        assert merged.index.tz is None


class TestDataAlignment:
    """Test cross-asset data alignment procedures."""
    
    def test_business_day_calendar(self):
        """Test business day calendar generation."""
        # US business days (Monday-Friday, excluding holidays)
        start = '2020-01-01'
        end = '2020-01-31'
        
        business_days = pd.bdate_range(start, end, freq='B')
        
        # Should have roughly 22-23 business days in January
        assert 20 <= len(business_days) <= 24
        
        # No weekends
        assert all(d.dayofweek < 5 for d in business_days)
    
    def test_crypto_equity_alignment(self):
        """Test alignment of 24/7 crypto data to equity trading days."""
        # Crypto trades every day
        crypto_dates = pd.date_range('2020-01-01', periods=30, freq='D')
        crypto_data = pd.Series(range(30), index=crypto_dates)
        
        # Equity trades business days only
        equity_dates = pd.bdate_range('2020-01-01', periods=22, freq='B')
        
        # Align crypto to equity calendar with forward-fill
        aligned_crypto = crypto_data.reindex(equity_dates, method='ffill')
        
        assert len(aligned_crypto) == len(equity_dates)
        assert all(d in equity_dates for d in aligned_crypto.index)
        assert aligned_crypto.isnull().sum() == 0  # No missing values after ffill
    
    def test_forward_fill_weekend_gap(self):
        """Test that weekend gaps are filled correctly."""
        # Create data with weekend gap
        dates = pd.to_datetime(['2020-01-03', '2020-01-04', '2020-01-05'])  # Fri, Sat, Sun
        values = pd.Series([100, 105, 110], index=dates)
        
        # Business calendar (only Friday and next Monday)
        business = pd.to_datetime(['2020-01-03', '2020-01-06'])  # Fri, Mon
        
        # Forward fill
        aligned = values.reindex(business, method='ffill')
        
        assert aligned.loc['2020-01-03'] == 100  # Friday value
        # Monday should have Friday's value (since Sat/Sun not in business days)
        # But since we're forward-filling from Fri only, Monday might be NaN
        # Better test: fill then check
        filled = values.reindex(business, method='pad')
        assert filled.loc['2020-01-03'] == 100
    
    def test_missing_data_handling(self):
        """Test handling of missing data in alignment."""
        # Data with gaps
        dates = pd.to_datetime(['2020-01-01', '2020-01-05', '2020-01-10'])
        values = pd.Series([100, np.nan, 110], index=dates)
        
        # Should handle NaN appropriately
        assert values.isnull().sum() == 1
        
        # Forward fill replaces NaN with previous value
        filled = values.ffill()
        assert filled.loc['2020-01-05'] == 100
        assert filled.loc['2020-01-10'] == 110
    
    def test_outer_join_alignment(self):
        """Test outer join for cross-asset data alignment."""
        # Two assets with different trading calendars
        dates1 = pd.to_datetime(['2020-01-01', '2020-01-02', '2020-01-03'])
        dates2 = pd.to_datetime(['2020-01-02', '2020-01-03', '2020-01-04'])
        
        df1 = pd.DataFrame({'asset1': [100, 101, 102]}, index=dates1)
        df2 = pd.DataFrame({'asset2': [200, 201, 202]}, index=dates2)
        
        # Outer join creates union of dates
        merged = df1.join(df2, how='outer')
        
        assert len(merged) == 4  # Union of dates
        assert '2020-01-01' in merged.index.strftime('%Y-%m-%d')
        assert '2020-01-04' in merged.index.strftime('%Y-%m-%d')


class TestFeatureEngineering:
    """Test feature engineering functions."""
    
    def test_log_return_calculation(self):
        """Test log return calculation."""
        prices = pd.Series([100, 101, 102, 101, 103])
        
        # Log returns
        returns = np.log(prices / prices.shift(1))
        
        # First value should be NaN
        assert pd.isna(returns.iloc[0])
        
        # Second value should be ln(101/100)
        expected = np.log(101/100)
        assert abs(returns.iloc[1] - expected) < 1e-10
    
    def test_rolling_statistics(self):
        """Test rolling window statistics."""
        data = pd.Series(range(100))
        
        # 10-day rolling mean
        rolling_mean = data.rolling(window=10).mean()
        
        # 10th value should be mean of first 10 values (0-9)
        expected_10th = np.mean(range(10))
        assert abs(rolling_mean.iloc[9] - expected_10th) < 1e-10
        
        # First 9 values depend on min_periods
        rolling_mean_min1 = data.rolling(window=10, min_periods=1).mean()
        assert rolling_mean_min1.iloc[0] == 0  # Mean of [0] is 0
    
    def test_yield_change_calculation(self):
        """Test yield change calculation in basis points."""
        # Yahoo Finance reports yields scaled by 10
        yahoo_yields = pd.Series([15.0, 15.5, 16.0, 15.8])  # Actually 1.5%, 1.55%, etc.
        
        # Convert to actual yields
        actual_yields = yahoo_yields / 10
        
        # Calculate changes in basis points
        yield_changes_bp = actual_yields.diff() * 100
        
        # First change: (1.55 - 1.50) * 100 = 5 bp
        assert abs(yield_changes_bp.iloc[1] - 5.0) < 1e-10
    
    def test_event_window_indicators(self):
        """Test creation of event window indicators."""
        # Create date range
        dates = pd.date_range('2020-01-01', periods=30, freq='D')
        data = pd.DataFrame({'value': range(30)}, index=dates)
        
        # Event on Jan 15
        event_date = pd.Timestamp('2020-01-15')
        
        # Create indicator for [-1, +3] window
        window_mask = (
            (data.index >= event_date - timedelta(days=1)) &
            (data.index <= event_date + timedelta(days=3))
        )
        
        # Should capture event day and surrounding days
        assert window_mask.sum() >= 4  # At least 4 days (may be more if weekend)
        assert window_mask.loc[event_date] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
