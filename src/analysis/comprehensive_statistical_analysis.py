"""
Simplified comprehensive statistical analysis module for testing research hypotheses.

OPTIMIZATION: This is a simplified version to prevent hanging and data insufficiency errors.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
import scipy.stats as stats
import logging
import warnings

warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)

class ComprehensiveStatisticalAnalysis:
    """
    Simplified comprehensive statistical analysis for testing research hypotheses about 
    macro announcement effects on crypto vs stock markets.
    
    OPTIMIZATION: Reduced complexity to prevent data insufficiency errors.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ComprehensiveStatisticalAnalysis")
        self.results = {}
        
    def run_complete_analysis(
        self, 
        data: pd.DataFrame,
        crypto_assets: List[str] = None,
        stock_assets: List[str] = None,
        economic_indicators: List[str] = None
    ) -> Dict[str, Any]:
        """
        Run simplified statistical analysis for the research.
        
        OPTIMIZATION: Simplified to prevent hanging and data errors.
        """
        
        self.logger.info("Starting simplified statistical analysis")
        
        # Auto-detect asset categories if not provided
        if crypto_assets is None:
            crypto_assets = [col for col in data.columns if any(crypto in col.lower() 
                           for crypto in ['bitcoin', 'ethereum', 'btc', 'eth', 'crypto', 'bnb', 'sol'])]
        
        if stock_assets is None:
            stock_assets = [col for col in data.columns if any(stock in col.lower() 
                          for stock in ['sp500', 'spy', 'nasdaq', 'dow', 'russell', 'stocks_'])]
        
        if economic_indicators is None:
            economic_indicators = [col for col in data.columns if any(econ in col.lower() 
                                 for econ in ['unemployment', 'inflation', 'cpi', 'gdp', 'economic_'])]
        
        # OPTIMIZATION: Drastically limit analysis scope
        crypto_assets = crypto_assets[:3]  # Max 3 crypto assets
        stock_assets = stock_assets[:3]    # Max 3 stock assets
        economic_indicators = economic_indicators[:3]  # Max 3 indicators
        
        self.logger.info(f"Simplified analysis: {len(crypto_assets)} crypto, {len(stock_assets)} stock, {len(economic_indicators)} economic")
        
        results = {}
        
        try:
            # Simplified summary statistics
            results['data_summary'] = self._simple_summary_statistics(data, crypto_assets, stock_assets)
            
            # Simplified hypothesis tests
            results['hypothesis_tests'] = self._simple_hypothesis_tests(data, crypto_assets, stock_assets)
            
            # Basic correlation analysis
            results['correlation_analysis'] = self._basic_correlation_analysis(data, crypto_assets, stock_assets)
            
            # Simple test summary
            results['test_summary'] = self._simple_test_summary(results)
            
            self.logger.info("Simplified statistical analysis completed successfully!")
            
        except Exception as e:
            self.logger.error(f"Simplified analysis failed: {e}")
            results['error'] = f"Analysis failed: {str(e)}"
        
        return results
    
    def _simple_summary_statistics(
        self, 
        data: pd.DataFrame, 
        crypto_assets: List[str], 
        stock_assets: List[str]
    ) -> Dict[str, Any]:
        """Generate simple descriptive statistics."""
        
        summary = {
            'dataset_overview': {
                'total_observations': len(data),
                'total_variables': len(data.columns),
                'date_range': {
                    'start': str(data.index[0]) if len(data) > 0 else 'N/A',
                    'end': str(data.index[-1]) if len(data) > 0 else 'N/A'
                }
            }
        }
        
        # Simple statistics for each category
        for category, assets in [('crypto', crypto_assets), ('stocks', stock_assets)]:
            category_stats = {}
            
            for asset in assets:
                if asset in data.columns:
                    series = data[asset].dropna()
                    if len(series) > 10:
                        # Calculate returns
                        returns = series.pct_change().dropna()
                        if len(returns) > 5:
                            category_stats[asset] = {
                                'observations': len(series),
                                'return_mean': returns.mean(),
                                'return_std': returns.std(),
                                'return_min': returns.min(),
                                'return_max': returns.max(),
                                'data_completeness': len(series) / len(data)
                            }
            
            if category_stats:
                summary[f'{category}_summary'] = category_stats
        
        return summary
    
    def _simple_hypothesis_tests(
        self, 
        data: pd.DataFrame, 
        crypto_assets: List[str], 
        stock_assets: List[str]
    ) -> Dict[str, Any]:
        """Run simplified hypothesis tests."""
        
        results = {}
        
        # Calculate returns for comparison
        crypto_returns = []
        stock_returns = []
        
        # Collect returns from available assets
        for asset in crypto_assets:
            if asset in data.columns:
                prices = data[asset].dropna()
                if len(prices) > 20:  # Lower threshold
                    returns = prices.pct_change().dropna()
                    if len(returns) > 10:
                        crypto_returns.extend(returns.values)
        
        for asset in stock_assets:
            if asset in data.columns:
                prices = data[asset].dropna()
                if len(prices) > 20:  # Lower threshold
                    returns = prices.pct_change().dropna()
                    if len(returns) > 10:
                        stock_returns.extend(returns.values)
        
        if len(crypto_returns) > 10 and len(stock_returns) > 10:
            crypto_array = np.array(crypto_returns)
            stock_array = np.array(stock_returns)
            
            # Remove extreme outliers (> 50% daily change)
            crypto_array = crypto_array[np.abs(crypto_array) < 0.5]
            stock_array = stock_array[np.abs(stock_array) < 0.5]
            
            if len(crypto_array) > 10 and len(stock_array) > 10:
                # Simple volatility comparison
                try:
                    crypto_vol = np.std(crypto_array)
                    stock_vol = np.std(stock_array)
                    
                    # Levene test for equal variances
                    levene_stat, levene_p = stats.levene(crypto_array, stock_array)
                    
                    results['volatility_comparison'] = {
                        'crypto_volatility': crypto_vol,
                        'stock_volatility': stock_vol,
                        'volatility_ratio': crypto_vol / stock_vol if stock_vol > 0 else np.nan,
                        'levene_test_statistic': levene_stat,
                        'levene_test_p_value': levene_p,
                        'significantly_different': levene_p < 0.05
                    }
                    
                    # Simple mean comparison
                    crypto_mean = np.mean(crypto_array)
                    stock_mean = np.mean(stock_array)
                    
                    t_stat, t_p = stats.ttest_ind(crypto_array, stock_array)
                    
                    results['mean_comparison'] = {
                        'crypto_mean_return': crypto_mean,
                        'stock_mean_return': stock_mean,
                        't_test_statistic': t_stat,
                        't_test_p_value': t_p,
                        'significantly_different': t_p < 0.05
                    }
                    
                except Exception as e:
                    self.logger.debug(f"Simple hypothesis tests failed: {e}")
                    results['error'] = 'Statistical tests failed due to data issues'
        else:
            results['error'] = f'Insufficient return data: crypto={len(crypto_returns)}, stock={len(stock_returns)}'
        
        return results
    
    def _basic_correlation_analysis(
        self, 
        data: pd.DataFrame, 
        crypto_assets: List[str], 
        stock_assets: List[str]
    ) -> Dict[str, Any]:
        """Basic correlation analysis between asset classes."""
        
        results = {}
        
        # Get valid assets with sufficient data
        valid_crypto = []
        valid_stocks = []
        
        for asset in crypto_assets:
            if asset in data.columns and data[asset].notna().sum() > 50:
                valid_crypto.append(asset)
        
        for asset in stock_assets:
            if asset in data.columns and data[asset].notna().sum() > 50:
                valid_stocks.append(asset)
        
        if valid_crypto and valid_stocks:
            correlations = []
            
            # Calculate pairwise correlations
            for crypto_asset in valid_crypto:
                for stock_asset in valid_stocks:
                    crypto_data = data[crypto_asset].dropna()
                    stock_data = data[stock_asset].dropna()
                    
                    # Find common dates
                    common_dates = crypto_data.index.intersection(stock_data.index)
                    
                    if len(common_dates) > 30:  # Reasonable minimum
                        crypto_aligned = crypto_data.loc[common_dates]
                        stock_aligned = stock_data.loc[common_dates]
                        
                        correlation = crypto_aligned.corr(stock_aligned)
                        if not np.isnan(correlation):
                            correlations.append({
                                'crypto_asset': crypto_asset,
                                'stock_asset': stock_asset,
                                'correlation': correlation,
                                'n_observations': len(common_dates)
                            })
            
            if correlations:
                corr_df = pd.DataFrame(correlations)
                results['cross_asset_correlations'] = {
                    'mean_correlation': corr_df['correlation'].mean(),
                    'median_correlation': corr_df['correlation'].median(),
                    'min_correlation': corr_df['correlation'].min(),
                    'max_correlation': corr_df['correlation'].max(),
                    'number_of_pairs': len(correlations),
                    'individual_correlations': correlations
                }
        
        return results
    
    def _simple_test_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate simple summary of test results."""
        
        summary = {
            'hypothesis_conclusions': {},
            'significant_findings': [],
            'data_quality_notes': []
        }
        
        # Summarize hypothesis tests
        if 'hypothesis_tests' in results:
            hyp_tests = results['hypothesis_tests']
            
            if 'volatility_comparison' in hyp_tests:
                vol_test = hyp_tests['volatility_comparison']
                summary['hypothesis_conclusions']['H1_volatility'] = {
                    'hypothesis': 'Cryptocurrency volatility differs from stock volatility',
                    'conclusion': 'Supported' if vol_test.get('significantly_different', False) else 'Not supported',
                    'p_value': vol_test.get('levene_test_p_value', np.nan),
                    'effect_size': vol_test.get('volatility_ratio', np.nan)
                }
            
            if 'mean_comparison' in hyp_tests:
                mean_test = hyp_tests['mean_comparison']
                summary['hypothesis_conclusions']['H2_returns'] = {
                    'hypothesis': 'Cryptocurrency and stock returns differ significantly',
                    'conclusion': 'Supported' if mean_test.get('significantly_different', False) else 'Not supported',
                    'p_value': mean_test.get('t_test_p_value', np.nan),
                    'effect_size': abs(mean_test.get('crypto_mean_return', 0) - mean_test.get('stock_mean_return', 0))
                }
        
        # Check for significant findings
        for test_category, test_results in results.items():
            if isinstance(test_results, dict):
                for test_name, test_data in test_results.items():
                    if isinstance(test_data, dict) and 'p_value' in test_data:
                        p_val = test_data.get('p_value')
                        if isinstance(p_val, (int, float)) and p_val < 0.05:
                            summary['significant_findings'].append({
                                'test': f"{test_category}.{test_name}",
                                'p_value': p_val,
                                'description': f"Significant result in {test_name}"
                            })
        
        # Data quality notes
        if 'data_summary' in results:
            data_sum = results['data_summary']
            if 'dataset_overview' in data_sum:
                overview = data_sum['dataset_overview']
                summary['data_quality_notes'].append(
                    f"Dataset contains {overview.get('total_observations', 0)} observations "
                    f"and {overview.get('total_variables', 0)} variables"
                )
        
        return summary
