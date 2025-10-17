"""
Improved surprise construction with proper standardization and documentation.

Key improvements:
1. Separate handling of survey-based vs proxy surprises
2. Per-indicator z-score standardization with pre-sample windows
3. Clear flagging of surprise sources
4. Indicator-specific analysis before pooling
5. Comprehensive provenance tracking
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

class SurpriseConstructor:
    """Construct standardized economic surprises for event study analysis."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.surprise_metadata = {}
        
    def construct_surprises(
        self,
        announcements: pd.DataFrame,
        standardization_window: int = 60,  # 60 months ≈ 5 years
        min_obs_for_standardization: int = 12  # Minimum 1 year of data
    ) -> Dict[str, pd.DataFrame]:
        """
        Construct standardized surprises from announcement data.
        
        Args:
            announcements: DataFrame with columns:
                - date: announcement date
                - indicator: economic indicator name
                - actual: actual released value
                - forecast: consensus forecast (if available)
                - previous: previous period value
            standardization_window: Months for rolling standardization
            min_obs_for_standardization: Minimum observations required
            
        Returns:
            Dictionary with:
                - 'survey_based': Surprises using consensus forecasts
                - 'proxy_based': Surprises using statistical proxies
                - 'combined': Combined with clear flags
                - 'metadata': Provenance information
        """
        results = {
            'survey_based': pd.DataFrame(),
            'proxy_based': pd.DataFrame(),
            'combined': pd.DataFrame(),
            'metadata': {}
        }
        
        # Process each indicator separately
        indicators = announcements['indicator'].unique()
        
        for indicator in indicators:
            indicator_data = announcements[announcements['indicator'] == indicator].copy()
            indicator_data = indicator_data.sort_values('date')
            
            # Attempt survey-based surprise first
            if 'forecast' in indicator_data.columns and indicator_data['forecast'].notna().any():
                survey_surprise = self._construct_survey_surprise(
                    indicator_data,
                    indicator,
                    standardization_window,
                    min_obs_for_standardization
                )
                
                if not survey_surprise.empty:
                    results['survey_based'] = pd.concat([
                        results['survey_based'],
                        survey_surprise
                    ])
                    
                    self.logger.info(
                        f"Created survey-based surprises for {indicator}: "
                        f"{len(survey_surprise)} observations"
                    )
            
            # Construct proxy surprise as fallback
            proxy_surprise = self._construct_proxy_surprise(
                indicator_data,
                indicator,
                standardization_window,
                min_obs_for_standardization
            )
            
            if not proxy_surprise.empty:
                results['proxy_based'] = pd.concat([
                    results['proxy_based'],
                    proxy_surprise
                ])
                
                self.logger.info(
                    f"Created proxy surprises for {indicator}: "
                    f"{len(proxy_surprise)} observations"
                )
        
        # Combine with clear flags
        results['combined'] = self._combine_surprises(
            results['survey_based'],
            results['proxy_based']
        )
        
        # Store metadata
        results['metadata'] = self.surprise_metadata
        
        return results
    
    def _construct_survey_surprise(
        self,
        data: pd.DataFrame,
        indicator: str,
        window: int,
        min_obs: int
    ) -> pd.DataFrame:
        """
        Construct surprise using consensus forecasts.
        
        Surprise = (Actual - Forecast) / σ(Actual - Forecast)
        """
        # Calculate raw surprise
        data = data.copy()
        data['raw_surprise'] = data['actual'] - data['forecast']
        
        # Remove missing values
        valid_data = data[data['raw_surprise'].notna()].copy()
        
        if len(valid_data) < min_obs:
            self.logger.warning(
                f"Insufficient data for {indicator} survey surprise: "
                f"{len(valid_data)} < {min_obs}"
            )
            return pd.DataFrame()
        
        # Calculate rolling standardization using pre-sample window
        # For each date t, use data from t-window to t-1 for standardization
        standardized_surprises = []
        
        for idx in range(len(valid_data)):
            if idx < min_obs:
                # Skip until we have enough historical data
                continue
            
            # Use previous window observations for standardization
            start_idx = max(0, idx - window)
            historical_surprises = valid_data['raw_surprise'].iloc[start_idx:idx]
            
            if len(historical_surprises) >= min_obs:
                # Standardize current surprise using historical distribution
                mean = historical_surprises.mean()
                std = historical_surprises.std()
                
                if std > 0:
                    current_surprise = valid_data['raw_surprise'].iloc[idx]
                    z_score = (current_surprise - mean) / std
                    
                    standardized_surprises.append({
                        'date': valid_data.iloc[idx]['date'],
                        'indicator': indicator,
                        'surprise': z_score,
                        'raw_surprise': current_surprise,
                        'standardization_mean': mean,
                        'standardization_std': std,
                        'n_historical_obs': len(historical_surprises),
                        'source': 'survey_forecast'
                    })
        
        if not standardized_surprises:
            return pd.DataFrame()
        
        result_df = pd.DataFrame(standardized_surprises)
        result_df = result_df.set_index('date')
        
        # Store metadata
        self.surprise_metadata[f'{indicator}_survey'] = {
            'indicator': indicator,
            'source': 'consensus_forecast',
            'n_obs': len(result_df),
            'standardization_window': window,
            'mean_surprise': float(result_df['surprise'].mean()),
            'std_surprise': float(result_df['surprise'].std()),
            'min_date': str(result_df.index.min()),
            'max_date': str(result_df.index.max())
        }
        
        return result_df
    
    def _construct_proxy_surprise(
        self,
        data: pd.DataFrame,
        indicator: str,
        window: int,
        min_obs: int
    ) -> pd.DataFrame:
        """
        Construct proxy surprise using statistical expectation.
        
        Proxy Forecast = Rolling Mean (lagged)
        Surprise = (Actual - Proxy Forecast) / σ(Actual - Proxy Forecast)
        """
        data = data.copy()
        
        if len(data) < min_obs:
            return pd.DataFrame()
        
        # Calculate rolling mean as proxy forecast (lagged to avoid look-ahead bias)
        data['proxy_forecast'] = data['actual'].rolling(
            window=12,
            min_periods=min_obs
        ).mean().shift(1)
        
        # Calculate raw proxy surprise
        data['raw_surprise'] = data['actual'] - data['proxy_forecast']
        
        # Remove missing values
        valid_data = data[data['raw_surprise'].notna()].copy()
        
        if len(valid_data) < min_obs:
            return pd.DataFrame()
        
        # Standardize using rolling window
        standardized_surprises = []
        
        for idx in range(len(valid_data)):
            if idx < min_obs:
                continue
            
            start_idx = max(0, idx - window)
            historical_surprises = valid_data['raw_surprise'].iloc[start_idx:idx]
            
            if len(historical_surprises) >= min_obs:
                mean = historical_surprises.mean()
                std = historical_surprises.std()
                
                if std > 0:
                    current_surprise = valid_data['raw_surprise'].iloc[idx]
                    z_score = (current_surprise - mean) / std
                    
                    standardized_surprises.append({
                        'date': valid_data.iloc[idx]['date'],
                        'indicator': indicator,
                        'surprise': z_score,
                        'raw_surprise': current_surprise,
                        'proxy_forecast': valid_data.iloc[idx]['proxy_forecast'],
                        'actual': valid_data.iloc[idx]['actual'],
                        'standardization_mean': mean,
                        'standardization_std': std,
                        'n_historical_obs': len(historical_surprises),
                        'source': 'statistical_proxy'
                    })
        
        if not standardized_surprises:
            return pd.DataFrame()
        
        result_df = pd.DataFrame(standardized_surprises)
        result_df = result_df.set_index('date')
        
        # Store metadata
        self.surprise_metadata[f'{indicator}_proxy'] = {
            'indicator': indicator,
            'source': 'rolling_mean_proxy',
            'proxy_window': 12,
            'n_obs': len(result_df),
            'standardization_window': window,
            'mean_surprise': float(result_df['surprise'].mean()),
            'std_surprise': float(result_df['surprise'].std()),
            'min_date': str(result_df.index.min()),
            'max_date': str(result_df.index.max()),
            'warning': 'Proxy-based surprise - use with caution'
        }
        
        return result_df
    
    def _combine_surprises(
        self,
        survey_surprises: pd.DataFrame,
        proxy_surprises: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Combine survey and proxy surprises with clear flags.
        
        Priority: Survey-based > Proxy-based
        """
        combined = pd.DataFrame()
        
        # Add survey surprises with flag
        if not survey_surprises.empty:
            survey_copy = survey_surprises.copy()
            survey_copy['surprise_type'] = 'survey'
            survey_copy['use_with_confidence'] = True
            combined = pd.concat([combined, survey_copy])
        
        # Add proxy surprises that don't overlap with survey surprises
        if not proxy_surprises.empty:
            proxy_copy = proxy_surprises.copy()
            proxy_copy['surprise_type'] = 'proxy'
            proxy_copy['use_with_confidence'] = False
            
            # Only add proxy where survey doesn't exist
            if not survey_surprises.empty:
                # Filter out overlapping (indicator, date) pairs
                survey_keys = set(
                    (row['indicator'], idx) 
                    for idx, row in survey_surprises.iterrows()
                )
                
                proxy_filtered = proxy_copy[
                    ~proxy_copy.apply(
                        lambda row: (row['indicator'], row.name) in survey_keys,
                        axis=1
                    )
                ]
                
                combined = pd.concat([combined, proxy_filtered])
            else:
                combined = pd.concat([combined, proxy_copy])
        
        # Add warning column for proxy surprises
        if not combined.empty:
            combined['data_quality_note'] = combined.apply(
                lambda row: 'Use with caution - statistical proxy' 
                if row['surprise_type'] == 'proxy' 
                else 'Survey-based - reliable',
                axis=1
            )
        
        return combined.sort_index()
    
    def analyze_surprise_quality(
        self,
        surprises: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Analyze quality and characteristics of constructed surprises.
        
        Returns quality metrics and diagnostics.
        """
        quality_report = {
            'overall': {},
            'by_indicator': {},
            'by_source': {}
        }
        
        if surprises.empty:
            return quality_report
        
        # Overall statistics
        quality_report['overall'] = {
            'n_total': len(surprises),
            'n_indicators': surprises['indicator'].nunique() if 'indicator' in surprises.columns else 0,
            'date_range': (str(surprises.index.min()), str(surprises.index.max())),
            'mean_surprise': float(surprises['surprise'].mean()),
            'std_surprise': float(surprises['surprise'].std()),
            'skewness': float(surprises['surprise'].skew()),
            'kurtosis': float(surprises['surprise'].kurtosis())
        }
        
        # By indicator
        if 'indicator' in surprises.columns:
            for indicator in surprises['indicator'].unique():
                ind_data = surprises[surprises['indicator'] == indicator]
                
                quality_report['by_indicator'][indicator] = {
                    'n_obs': len(ind_data),
                    'mean_surprise': float(ind_data['surprise'].mean()),
                    'std_surprise': float(ind_data['surprise'].std()),
                    'min_surprise': float(ind_data['surprise'].min()),
                    'max_surprise': float(ind_data['surprise'].max())
                }
        
        # By source type
        if 'surprise_type' in surprises.columns:
            for source in surprises['surprise_type'].unique():
                source_data = surprises[surprises['surprise_type'] == source]
                
                quality_report['by_source'][source] = {
                    'n_obs': len(source_data),
                    'share': len(source_data) / len(surprises),
                    'mean_surprise': float(source_data['surprise'].mean()),
                    'std_surprise': float(source_data['surprise'].std())
                }
        
        return quality_report
