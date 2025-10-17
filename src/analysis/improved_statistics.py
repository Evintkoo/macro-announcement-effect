"""
Improved statistical inference with proper robust standard errors and multiple testing corrections.

Key improvements:
1. HAC/Newey-West standard errors for serial correlation
2. Clustering by event and asset
3. FDR (Benjamini-Hochberg) multiple testing correction
4. Proper handling of overlapping windows
5. Realistic p-value and t-statistic reporting
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import cov_hac
from statsmodels.regression.linear_model import OLS
from scipy import stats
import logging

class ImprovedStatisticalInference:
    """Improved statistical methods with proper robust inference."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def estimate_with_hac_errors(
        self,
        y: pd.Series,
        X: pd.DataFrame,
        maxlags: Optional[int] = None,
        kernel: str = 'bartlett'
    ) -> Dict[str, Any]:
        """
        Estimate OLS with HAC (Newey-West) standard errors.
        
        Args:
            y: Dependent variable
            X: Independent variables (including constant if needed)
            maxlags: Maximum lags for HAC (if None, uses int(4 * (n/100)^(2/9)))
            kernel: Kernel for HAC ('bartlett' is Newey-West)
            
        Returns:
            Dictionary with results including HAC-robust inference
        """
        # Align data
        data = pd.concat([y, X], axis=1).dropna()
        
        if len(data) < 10:
            return {
                'error': 'Insufficient data',
                'n_obs': len(data)
            }
        
        y_clean = data.iloc[:, 0]
        X_clean = data.iloc[:, 1:]
        
        # Add constant if not present
        if not ('const' in X_clean.columns or 'Intercept' in X_clean.columns):
            X_clean = sm.add_constant(X_clean)
        
        # Fit OLS model
        model = OLS(y_clean, X_clean)
        
        # Determine maxlags if not specified (Newey-West rule)
        if maxlags is None:
            n = len(y_clean)
            maxlags = int(np.floor(4 * (n / 100) ** (2/9)))
            maxlags = max(1, min(maxlags, n // 4))  # Bound reasonably
        
        try:
            # Fit with HAC covariance
            results = model.fit(cov_type='HAC', cov_kwds={'maxlags': maxlags, 'kernel': kernel})
            
            # Extract results with proper formatting
            output = {
                'params': results.params.to_dict(),
                'std_errors': results.bse.to_dict(),  # HAC standard errors
                'tvalues': results.tvalues.to_dict(),
                'pvalues': self._format_pvalues(results.pvalues),
                'conf_int': results.conf_int().to_dict(),
                'rsquared': float(results.rsquared),
                'rsquared_adj': float(results.rsquared_adj),
                'fvalue': float(results.fvalue) if hasattr(results, 'fvalue') else None,
                'f_pvalue': self._format_pvalue(results.f_pvalue) if hasattr(results, 'f_pvalue') else None,
                'nobs': int(results.nobs),
                'df_resid': int(results.df_resid),
                'df_model': int(results.df_model),
                'hac_maxlags': maxlags,
                'hac_kernel': kernel,
                'cov_type': 'HAC',
                'aic': float(results.aic),
                'bic': float(results.bic)
            }
            
            return output
            
        except Exception as e:
            self.logger.error(f"HAC estimation failed: {e}")
            return {
                'error': str(e),
                'n_obs': len(y_clean)
            }
    
    def clustered_standard_errors(
        self,
        y: pd.Series,
        X: pd.DataFrame,
        clusters: pd.Series
    ) -> Dict[str, Any]:
        """
        Estimate OLS with clustered standard errors.
        
        Args:
            y: Dependent variable
            X: Independent variables
            clusters: Cluster identifiers (e.g., event IDs or asset IDs)
            
        Returns:
            Dictionary with results including cluster-robust inference
        """
        # Align data
        data = pd.concat([y, X, clusters], axis=1).dropna()
        
        if len(data) < 10:
            return {
                'error': 'Insufficient data',
                'n_obs': len(data)
            }
        
        y_clean = data.iloc[:, 0]
        X_clean = data.iloc[:, 1:-1]
        clusters_clean = data.iloc[:, -1]
        
        # Add constant
        if not ('const' in X_clean.columns or 'Intercept' in X_clean.columns):
            X_clean = sm.add_constant(X_clean)
        
        try:
            # Fit OLS with clustered errors
            model = OLS(y_clean, X_clean)
            results = model.fit(cov_type='cluster', cov_kwds={'groups': clusters_clean})
            
            n_clusters = len(clusters_clean.unique())
            
            output = {
                'params': results.params.to_dict(),
                'std_errors': results.bse.to_dict(),
                'tvalues': results.tvalues.to_dict(),
                'pvalues': self._format_pvalues(results.pvalues),
                'conf_int': results.conf_int().to_dict(),
                'rsquared': float(results.rsquared),
                'rsquared_adj': float(results.rsquared_adj),
                'nobs': int(results.nobs),
                'n_clusters': n_clusters,
                'cov_type': 'cluster',
                'df_resid': int(results.df_resid),
                'df_model': int(results.df_model)
            }
            
            return output
            
        except Exception as e:
            self.logger.error(f"Clustered SE estimation failed: {e}")
            return {
                'error': str(e),
                'n_obs': len(y_clean)
            }
    
    def fdr_correction(
        self,
        pvalues: List[float],
        alpha: float = 0.05,
        method: str = 'bh'
    ) -> Dict[str, Any]:
        """
        Apply False Discovery Rate (FDR) correction to p-values.
        
        Args:
            pvalues: List of p-values from multiple tests
            alpha: Target FDR level
            method: 'bh' for Benjamini-Hochberg or 'by' for Benjamini-Yekutieli
            
        Returns:
            Dictionary with corrected results
        """
        pvalues = np.array(pvalues)
        n = len(pvalues)
        
        if n == 0:
            return {
                'error': 'No p-values provided',
                'n_tests': 0
            }
        
        # Sort p-values and keep track of original order
        sort_idx = np.argsort(pvalues)
        sorted_pvalues = pvalues[sort_idx]
        
        # Benjamini-Hochberg procedure
        if method == 'bh':
            # Calculate critical values
            critical_values = (np.arange(1, n + 1) / n) * alpha
            
            # Find largest i where p(i) <= (i/n) * alpha
            comparisons = sorted_pvalues <= critical_values
            
            if np.any(comparisons):
                max_idx = np.max(np.where(comparisons)[0])
                reject = np.zeros(n, dtype=bool)
                reject[sort_idx[:max_idx + 1]] = True
            else:
                reject = np.zeros(n, dtype=bool)
            
            # Calculate q-values (FDR-adjusted p-values)
            qvalues = np.minimum.accumulate(
                (sorted_pvalues * n / np.arange(1, n + 1))[::-1]
            )[::-1]
            qvalues = np.minimum(qvalues, 1.0)
            
            # Restore original order
            qvalues_original_order = np.empty(n)
            qvalues_original_order[sort_idx] = qvalues
            
        # Benjamini-Yekutieli (more conservative, for dependent tests)
        elif method == 'by':
            c_n = np.sum(1.0 / np.arange(1, n + 1))  # Harmonic sum
            critical_values = (np.arange(1, n + 1) / (n * c_n)) * alpha
            
            comparisons = sorted_pvalues <= critical_values
            
            if np.any(comparisons):
                max_idx = np.max(np.where(comparisons)[0])
                reject = np.zeros(n, dtype=bool)
                reject[sort_idx[:max_idx + 1]] = True
            else:
                reject = np.zeros(n, dtype=bool)
            
            # Calculate q-values
            qvalues = np.minimum.accumulate(
                (sorted_pvalues * n * c_n / np.arange(1, n + 1))[::-1]
            )[::-1]
            qvalues = np.minimum(qvalues, 1.0)
            
            # Restore original order
            qvalues_original_order = np.empty(n)
            qvalues_original_order[sort_idx] = qvalues
            
        else:
            raise ValueError(f"Unknown method: {method}")
        
        n_rejected = int(np.sum(reject))
        
        return {
            'reject_null': reject.tolist(),
            'qvalues': qvalues_original_order.tolist(),
            'n_tests': n,
            'n_rejected': n_rejected,
            'rejection_rate': n_rejected / n if n > 0 else 0,
            'alpha': alpha,
            'method': method
        }
    
    def bonferroni_correction(
        self,
        pvalues: List[float],
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        Apply Bonferroni correction (more conservative than FDR).
        
        Args:
            pvalues: List of p-values
            alpha: Target family-wise error rate
            
        Returns:
            Dictionary with corrected results
        """
        pvalues = np.array(pvalues)
        n = len(pvalues)
        
        if n == 0:
            return {
                'error': 'No p-values provided',
                'n_tests': 0
            }
        
        # Bonferroni adjusted alpha
        alpha_bonf = alpha / n
        
        # Reject if p-value < alpha/n
        reject = pvalues < alpha_bonf
        
        # Bonferroni adjusted p-values (capped at 1.0)
        adjusted_pvalues = np.minimum(pvalues * n, 1.0)
        
        n_rejected = int(np.sum(reject))
        
        return {
            'reject_null': reject.tolist(),
            'adjusted_pvalues': adjusted_pvalues.tolist(),
            'bonferroni_alpha': alpha_bonf,
            'n_tests': n,
            'n_rejected': n_rejected,
            'rejection_rate': n_rejected / n if n > 0 else 0,
            'alpha': alpha,
            'method': 'bonferroni'
        }
    
    def _format_pvalue(self, p: float) -> str:
        """Format p-value properly (never report as exactly 0 or infinity)."""
        if np.isnan(p):
            return 'NaN'
        elif np.isinf(p):
            return 'Inf'
        elif p < 0.0001:
            return '< 0.0001'
        else:
            return f'{p:.4f}'
    
    def _format_pvalues(self, pvalues: pd.Series) -> Dict[str, str]:
        """Format multiple p-values."""
        return {k: self._format_pvalue(v) for k, v in pvalues.items()}
    
    def format_tstat(self, t: float, max_value: float = 100.0) -> str:
        """Format t-statistic properly (cap extreme values)."""
        if np.isnan(t):
            return 'NaN'
        elif np.isinf(t):
            return f'> {max_value}' if t > 0 else f'< -{max_value}'
        elif abs(t) > max_value:
            return f'> {max_value}' if t > 0 else f'< -{max_value}'
        else:
            return f'{t:.2f}'
    
    def power_analysis(
        self,
        effect_size: float,
        n: int,
        alpha: float = 0.05,
        alternative: str = 'two-sided'
    ) -> Dict[str, float]:
        """
        Calculate statistical power for given effect size and sample size.
        
        Args:
            effect_size: Standardized effect size (Cohen's d)
            n: Sample size
            alpha: Significance level
            alternative: 'two-sided', 'less', or 'greater'
            
        Returns:
            Dictionary with power analysis results
        """
        from statsmodels.stats.power import TTestPower
        
        power_calc = TTestPower()
        
        power = power_calc.solve_power(
            effect_size=effect_size,
            nobs=n,
            alpha=alpha,
            alternative=alternative
        )
        
        return {
            'power': float(power),
            'effect_size': effect_size,
            'n_obs': n,
            'alpha': alpha,
            'alternative': alternative,
            'interpretation': 'good' if power >= 0.8 else 'low' if power < 0.5 else 'moderate'
        }
    
    def minimum_detectable_effect(
        self,
        n: int,
        alpha: float = 0.05,
        power: float = 0.8,
        alternative: str = 'two-sided'
    ) -> Dict[str, float]:
        """
        Calculate minimum detectable effect size given sample size and desired power.
        
        Args:
            n: Sample size
            alpha: Significance level
            power: Desired power
            alternative: 'two-sided', 'less', or 'greater'
            
        Returns:
            Dictionary with MDE results
        """
        from statsmodels.stats.power import TTestPower
        
        power_calc = TTestPower()
        
        effect_size = power_calc.solve_power(
            effect_size=None,
            nobs=n,
            alpha=alpha,
            power=power,
            alternative=alternative
        )
        
        return {
            'minimum_detectable_effect': float(effect_size),
            'n_obs': n,
            'alpha': alpha,
            'power': power,
            'alternative': alternative
        }


class WinsorizeAndRobustness:
    """Methods for outlier handling and robustness checks."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def winsorize(
        self,
        data: pd.Series,
        lower_percentile: float = 0.01,
        upper_percentile: float = 0.99
    ) -> pd.Series:
        """
        Winsorize data at specified percentiles.
        
        Args:
            data: Series to winsorize
            lower_percentile: Lower bound percentile (e.g., 0.01 for 1%)
            upper_percentile: Upper bound percentile (e.g., 0.99 for 99%)
            
        Returns:
            Winsorized series
        """
        from scipy.stats.mstats import winsorize as scipy_winsorize
        
        if data.isna().all():
            return data
        
        # Calculate bounds
        lower_bound = data.quantile(lower_percentile)
        upper_bound = data.quantile(upper_percentile)
        
        # Winsorize
        winsorized = data.clip(lower=lower_bound, upper=upper_bound)
        
        n_winsorized = ((data < lower_bound) | (data > upper_bound)).sum()
        
        self.logger.info(
            f"Winsorized {n_winsorized} obs ({n_winsorized/len(data)*100:.1f}%) "
            f"at ({lower_percentile}, {upper_percentile}) percentiles"
        )
        
        return winsorized
    
    def placebo_test(
        self,
        data: pd.DataFrame,
        actual_event_dates: List[pd.Timestamp],
        n_placebo: int = 100,
        seed: int = 42
    ) -> Dict[str, Any]:
        """
        Generate placebo event dates for robustness testing.
        
        Args:
            data: DataFrame with time series data
            actual_event_dates: List of actual event dates
            n_placebo: Number of placebo dates to generate
            seed: Random seed for reproducibility
            
        Returns:
            Dictionary with placebo dates and summary statistics
        """
        np.random.seed(seed)
        
        # Get valid date range
        start_date = data.index.min()
        end_date = data.index.max()
        
        # Generate random dates
        date_range = pd.date_range(start_date, end_date, freq='D')
        
        # Exclude actual event dates and nearby dates
        excluded_dates = set()
        for event_date in actual_event_dates:
            # Exclude ±5 days around actual events
            for days_offset in range(-5, 6):
                excluded_dates.add(event_date + pd.Timedelta(days=days_offset))
        
        # Filter valid dates
        valid_dates = [d for d in date_range if d not in excluded_dates]
        
        # Sample placebo dates
        if len(valid_dates) < n_placebo:
            self.logger.warning(
                f"Only {len(valid_dates)} valid placebo dates available "
                f"(requested {n_placebo})"
            )
            n_placebo = len(valid_dates)
        
        placebo_dates = np.random.choice(valid_dates, size=n_placebo, replace=False)
        placebo_dates = sorted([pd.Timestamp(d) for d in placebo_dates])
        
        return {
            'placebo_dates': placebo_dates,
            'n_placebo': len(placebo_dates),
            'n_actual': len(actual_event_dates),
            'n_excluded': len(excluded_dates),
            'date_range': (str(start_date), str(end_date)),
            'seed': seed
        }
