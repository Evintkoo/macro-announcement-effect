"""
Advanced Econometric Analysis Module

This module provides sophisticated econometric methods for analyzing
macroeconomic announcement effects, including:
- GARCH volatility models
- Granger causality tests
- Structural break detection
- Quantile regression
- Panel data analysis

Author: Research Team
Date: 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import warnings
from scipy import stats
import logging

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class AdvancedEconometrics:
    """Advanced econometric analysis tools"""
    
    def __init__(self):
        """Initialize the advanced econometrics analyzer"""
        self.logger = logging.getLogger(__name__)
    
    def run_garch_analysis(
        self,
        returns_data: pd.DataFrame,
        assets: List[str],
        p: int = 1,
        q: int = 1
    ) -> Dict[str, Dict]:
        """
        Fit GARCH(p,q) models for volatility analysis
        
        Parameters:
        -----------
        returns_data : pd.DataFrame
            DataFrame with returns data
        assets : List[str]
            List of asset column names
        p : int
            GARCH lag order for squared residuals
        q : int
            GARCH lag order for conditional variance
            
        Returns:
        --------
        Dict with GARCH model results for each asset
        """
        self.logger.info(f"Running GARCH({p},{q}) analysis for {len(assets)} assets...")
        
        try:
            from arch import arch_model
        except ImportError:
            self.logger.warning("arch package not installed. Install with: pip install arch")
            return {}
        
        results = {}
        
        for asset in assets:
            try:
                # Get returns and clean data
                returns = returns_data[asset].dropna()
                
                if len(returns) < 100:
                    self.logger.warning(f"Insufficient data for {asset}: {len(returns)} observations")
                    continue
                
                # Scale returns for numerical stability (GARCH works better with percentage returns)
                returns_scaled = returns * 100
                
                # Fit GARCH model
                model = arch_model(
                    returns_scaled,
                    vol='Garch',
                    p=p,
                    q=q,
                    dist='normal'
                )
                
                fitted = model.fit(disp='off', show_warning=False)
                
                # Extract results
                results[asset] = {
                    'omega': fitted.params.get('omega', np.nan),
                    'alpha': fitted.params.get(f'alpha[{p}]', np.nan),
                    'beta': fitted.params.get(f'beta[{q}]', np.nan),
                    'persistence': fitted.params.get(f'alpha[{p}]', 0) + fitted.params.get(f'beta[{q}]', 0),
                    'log_likelihood': fitted.loglikelihood,
                    'aic': fitted.aic,
                    'bic': fitted.bic,
                    'conditional_volatility': fitted.conditional_volatility / 100,  # Unscale
                    'unconditional_volatility': np.sqrt(fitted.params.get('omega', 0) / 
                                                       (1 - fitted.params.get(f'alpha[{p}]', 0) - 
                                                        fitted.params.get(f'beta[{q}]', 0))) / 100
                }
                
                self.logger.info(f"GARCH model fitted for {asset}: persistence = {results[asset]['persistence']:.3f}")
                
            except Exception as e:
                self.logger.warning(f"Failed to fit GARCH model for {asset}: {e}")
                continue
        
        return results
    
    def test_granger_causality(
        self,
        data: pd.DataFrame,
        cause_vars: List[str],
        effect_vars: List[str],
        max_lag: int = 5,
        significance_level: float = 0.05
    ) -> pd.DataFrame:
        """
        Test Granger causality between variables
        
        Parameters:
        -----------
        data : pd.DataFrame
            DataFrame with time series data
        cause_vars : List[str]
            Variables to test as potential causes
        effect_vars : List[str]
            Variables to test as effects
        max_lag : int
            Maximum number of lags to test
        significance_level : float
            Significance level for tests
            
        Returns:
        --------
        DataFrame with Granger causality test results
        """
        self.logger.info(f"Testing Granger causality: {len(cause_vars)} causes -> {len(effect_vars)} effects")
        
        try:
            from statsmodels.tsa.stattools import grangercausalitytests
        except ImportError:
            self.logger.warning("statsmodels not installed")
            return pd.DataFrame()
        
        results_list = []
        
        for cause in cause_vars:
            for effect in effect_vars:
                if cause == effect:
                    continue
                
                try:
                    # Prepare data (remove NaN)
                    test_data = data[[effect, cause]].dropna()
                    
                    if len(test_data) < max_lag * 3:
                        continue
                    
                    # Run Granger causality test
                    test_results = grangercausalitytests(
                        test_data,
                        maxlag=max_lag,
                        verbose=False
                    )
                    
                    # Extract F-test results for each lag
                    for lag in range(1, max_lag + 1):
                        lag_result = test_results[lag][0]
                        f_test = lag_result['ssr_ftest']
                        
                        results_list.append({
                            'cause': cause,
                            'effect': effect,
                            'lag': lag,
                            'f_statistic': f_test[0],
                            'p_value': f_test[1],
                            'significant': f_test[1] < significance_level,
                            'test_type': 'F-test'
                        })
                    
                except Exception as e:
                    self.logger.warning(f"Granger causality test failed for {cause} -> {effect}: {e}")
                    continue
        
        results_df = pd.DataFrame(results_list)
        
        if not results_df.empty:
            # Summarize significant relationships
            significant = results_df[results_df['significant']]
            self.logger.info(f"Found {len(significant)} significant Granger causality relationships")
        
        return results_df
    
    def detect_structural_breaks(
        self,
        data: pd.DataFrame,
        dependent_var: str,
        independent_vars: List[str],
        break_test: str = 'chow'
    ) -> Dict:
        """
        Detect structural breaks in regression relationships
        
        Parameters:
        -----------
        data : pd.DataFrame
            DataFrame with regression data
        dependent_var : str
            Dependent variable name
        independent_vars : List[str]
            Independent variable names
        break_test : str
            Type of test: 'chow', 'cusum', or 'qlr'
            
        Returns:
        --------
        Dict with structural break test results
        """
        self.logger.info(f"Testing for structural breaks in {dependent_var}")
        
        try:
            import statsmodels.api as sm
            from statsmodels.stats.diagnostic import breaks_cusumolsresid
        except ImportError:
            self.logger.warning("statsmodels not installed")
            return {}
        
        try:
            # Prepare data
            y = data[dependent_var].dropna()
            X = data[independent_vars].loc[y.index].dropna()
            y = y.loc[X.index]
            X = sm.add_constant(X)
            
            if len(y) < 50:
                return {'error': 'Insufficient data for structural break test'}
            
            # Fit OLS model
            model = sm.OLS(y, X).fit()
            
            results = {
                'dependent_var': dependent_var,
                'independent_vars': independent_vars,
                'n_observations': len(y)
            }
            
            # CUSUM test
            if break_test in ['cusum', 'all']:
                try:
                    cusum_stat, cusum_pval = breaks_cusumolsresid(
                        model.resid,
                        ddof=len(independent_vars) + 1
                    )
                    
                    results['cusum'] = {
                        'statistic': float(cusum_stat),
                        'p_value': float(cusum_pval) if cusum_pval is not None else None,
                        'has_break': bool(cusum_stat > 1.36) if cusum_stat is not None else None  # 5% critical value
                    }
                except Exception as e:
                    self.logger.warning(f"CUSUM test failed: {e}")
            
            # Chow test (if break point specified)
            if break_test == 'chow':
                # Use midpoint as potential break
                break_point = len(y) // 2
                
                try:
                    # Split sample
                    y1, y2 = y.iloc[:break_point], y.iloc[break_point:]
                    X1, X2 = X.iloc[:break_point], X.iloc[break_point:]
                    
                    # Fit separate models
                    model1 = sm.OLS(y1, X1).fit()
                    model2 = sm.OLS(y2, X2).fit()
                    
                    # Chow test statistic
                    rss_pooled = model.ssr
                    rss1 = model1.ssr
                    rss2 = model2.ssr
                    rss_separate = rss1 + rss2
                    
                    n = len(y)
                    k = len(independent_vars) + 1
                    
                    chow_stat = ((rss_pooled - rss_separate) / k) / (rss_separate / (n - 2*k))
                    chow_pval = 1 - stats.f.cdf(chow_stat, k, n - 2*k)
                    
                    results['chow'] = {
                        'break_point': break_point,
                        'break_date': y.index[break_point],
                        'statistic': float(chow_stat),
                        'p_value': float(chow_pval),
                        'has_break': bool(chow_pval < 0.05)
                    }
                    
                except Exception as e:
                    self.logger.warning(f"Chow test failed: {e}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Structural break detection failed: {e}")
            return {'error': str(e)}
    
    def quantile_regression_analysis(
        self,
        data: pd.DataFrame,
        dependent_var: str,
        independent_vars: List[str],
        quantiles: List[float] = [0.1, 0.25, 0.5, 0.75, 0.9]
    ) -> pd.DataFrame:
        """
        Run quantile regression to analyze distributional effects
        
        Parameters:
        -----------
        data : pd.DataFrame
            DataFrame with regression data
        dependent_var : str
            Dependent variable name
        independent_vars : List[str]
            Independent variable names
        quantiles : List[float]
            Quantiles to estimate
            
        Returns:
        --------
        DataFrame with quantile regression results
        """
        self.logger.info(f"Running quantile regression for {dependent_var}")
        
        try:
            from statsmodels.regression.quantile_regression import QuantReg
        except ImportError:
            self.logger.warning("statsmodels not installed")
            return pd.DataFrame()
        
        try:
            # Prepare data
            y = data[dependent_var].dropna()
            X = data[independent_vars].loc[y.index].dropna()
            y = y.loc[X.index]
            
            if len(y) < 50:
                return pd.DataFrame()
            
            results_list = []
            
            for q in quantiles:
                try:
                    # Fit quantile regression
                    model = QuantReg(y, X)
                    fitted = model.fit(q=q)
                    
                    # Extract results for each variable
                    for var in independent_vars:
                        results_list.append({
                            'dependent_var': dependent_var,
                            'independent_var': var,
                            'quantile': q,
                            'coefficient': fitted.params[var],
                            'std_error': fitted.bse[var],
                            't_statistic': fitted.tvalues[var],
                            'p_value': fitted.pvalues[var],
                            'significant': fitted.pvalues[var] < 0.05
                        })
                    
                except Exception as e:
                    self.logger.warning(f"Quantile regression failed for q={q}: {e}")
                    continue
            
            results_df = pd.DataFrame(results_list)
            
            if not results_df.empty:
                self.logger.info(f"Quantile regression completed for {len(quantiles)} quantiles")
            
            return results_df
            
        except Exception as e:
            self.logger.error(f"Quantile regression analysis failed: {e}")
            return pd.DataFrame()
    
    def panel_regression_analysis(
        self,
        data: pd.DataFrame,
        entity_col: str,
        time_col: str,
        dependent_var: str,
        independent_vars: List[str],
        entity_effects: bool = True,
        time_effects: bool = False
    ) -> Dict:
        """
        Run panel data regression with fixed effects
        
        Parameters:
        -----------
        data : pd.DataFrame
            Panel data in long format
        entity_col : str
            Column name for entity/cross-section identifier
        time_col : str
            Column name for time identifier
        dependent_var : str
            Dependent variable name
        independent_vars : List[str]
            Independent variable names
        entity_effects : bool
            Include entity fixed effects
        time_effects : bool
            Include time fixed effects
            
        Returns:
        --------
        Dict with panel regression results
        """
        self.logger.info("Running panel regression with fixed effects")
        
        try:
            from linearmodels import PanelOLS
        except ImportError:
            self.logger.warning("linearmodels not installed. Install with: pip install linearmodels")
            # Fallback to regular OLS
            return self._fallback_ols_regression(data, dependent_var, independent_vars)
        
        try:
            # Set multi-index for panel data
            panel_data = data.set_index([entity_col, time_col])
            
            # Prepare variables
            y = panel_data[dependent_var]
            X = panel_data[independent_vars]
            
            # Fit panel regression
            model = PanelOLS(
                y,
                X,
                entity_effects=entity_effects,
                time_effects=time_effects
            )
            
            fitted = model.fit(cov_type='clustered', cluster_entity=True)
            
            # Extract results
            results = {
                'coefficients': fitted.params.to_dict(),
                'std_errors': fitted.std_errors.to_dict(),
                't_statistics': fitted.tstats.to_dict(),
                'p_values': fitted.pvalues.to_dict(),
                'r_squared': fitted.rsquared,
                'r_squared_within': fitted.rsquared_within,
                'r_squared_between': fitted.rsquared_between,
                'r_squared_overall': fitted.rsquared_overall,
                'f_statistic': fitted.f_statistic.stat,
                'f_pvalue': fitted.f_statistic.pval,
                'n_observations': fitted.nobs,
                'n_entities': fitted.entity_info.total,
                'entity_effects': entity_effects,
                'time_effects': time_effects
            }
            
            self.logger.info(f"Panel regression completed: R² = {results['r_squared']:.4f}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Panel regression failed: {e}")
            return {}
    
    def _fallback_ols_regression(
        self,
        data: pd.DataFrame,
        dependent_var: str,
        independent_vars: List[str]
    ) -> Dict:
        """Fallback to regular OLS if panel methods not available"""
        
        try:
            import statsmodels.api as sm
            
            y = data[dependent_var].dropna()
            X = data[independent_vars].loc[y.index].dropna()
            y = y.loc[X.index]
            X = sm.add_constant(X)
            
            model = sm.OLS(y, X).fit()
            
            return {
                'coefficients': model.params.to_dict(),
                'std_errors': model.bse.to_dict(),
                't_statistics': model.tvalues.to_dict(),
                'p_values': model.pvalues.to_dict(),
                'r_squared': model.rsquared,
                'f_statistic': model.fvalue,
                'f_pvalue': model.f_pvalue,
                'n_observations': model.nobs,
                'method': 'OLS (fallback)'
            }
            
        except Exception as e:
            self.logger.error(f"Fallback OLS regression failed: {e}")
            return {}


class RobustnessTests:
    """Robustness testing suite"""
    
    def __init__(self):
        """Initialize robustness test suite"""
        self.logger = logging.getLogger(__name__)
    
    def bootstrap_inference(
        self,
        data: pd.DataFrame,
        analysis_func: callable,
        n_bootstrap: int = 1000,
        confidence_level: float = 0.95
    ) -> Dict:
        """
        Bootstrap inference for confidence intervals
        
        Parameters:
        -----------
        data : pd.DataFrame
            Original data
        analysis_func : callable
            Function that performs analysis and returns results
        n_bootstrap : int
            Number of bootstrap iterations
        confidence_level : float
            Confidence level for intervals
            
        Returns:
        --------
        Dict with bootstrap results and confidence intervals
        """
        self.logger.info(f"Running bootstrap inference with {n_bootstrap} iterations...")
        
        bootstrap_results = []
        
        for i in range(n_bootstrap):
            if i % 100 == 0:
                self.logger.info(f"Bootstrap iteration {i}/{n_bootstrap}")
            
            # Resample with replacement
            sample = data.sample(n=len(data), replace=True)
            
            try:
                # Run analysis on bootstrap sample
                result = analysis_func(sample)
                bootstrap_results.append(result)
            except Exception as e:
                self.logger.warning(f"Bootstrap iteration {i} failed: {e}")
                continue
        
        # Calculate confidence intervals
        alpha = 1 - confidence_level
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100
        
        ci_results = {}
        
        if bootstrap_results:
            # Convert list of dicts to arrays for percentile calculation
            for key in bootstrap_results[0].keys():
                values = [r[key] for r in bootstrap_results if key in r]
                if values:
                    ci_results[key] = {
                        'mean': np.mean(values),
                        'std': np.std(values),
                        'ci_lower': np.percentile(values, lower_percentile),
                        'ci_upper': np.percentile(values, upper_percentile)
                    }
        
        return ci_results
    
    def placebo_test(
        self,
        data: pd.DataFrame,
        real_events: pd.DatetimeIndex,
        analysis_func: callable,
        n_placebo: int = 20
    ) -> Dict:
        """
        Placebo test using pseudo-events
        
        Parameters:
        -----------
        data : pd.DataFrame
            Time series data
        real_events : pd.DatetimeIndex
            Real event dates
        analysis_func : callable
            Event study analysis function
        n_placebo : int
            Number of placebo events to generate
            
        Returns:
        --------
        Dict with placebo test results
        """
        self.logger.info(f"Running placebo test with {n_placebo} pseudo-events...")
        
        # Generate random dates that are not real events
        available_dates = data.index.difference(real_events)
        placebo_dates = np.random.choice(available_dates, size=n_placebo, replace=False)
        placebo_dates = pd.DatetimeIndex(placebo_dates)
        
        # Run analysis on placebo events
        try:
            placebo_results = analysis_func(data, placebo_dates)
            
            # Check significance rate (should be close to significance level, e.g., 5%)
            if isinstance(placebo_results, dict) and 'p_values' in placebo_results:
                p_values = placebo_results['p_values']
                significance_rate = np.mean([p < 0.05 for p in p_values])
                
                return {
                    'n_placebo_events': n_placebo,
                    'significance_rate': significance_rate,
                    'passes_placebo_test': 0.01 < significance_rate < 0.10,
                    'interpretation': 'Pass' if 0.01 < significance_rate < 0.10 else 'Fail'
                }
            
        except Exception as e:
            self.logger.error(f"Placebo test failed: {e}")
        
        return {}
