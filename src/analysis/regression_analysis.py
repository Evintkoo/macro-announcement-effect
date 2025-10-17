"""
Regression analysis implementation for studying announcement effects.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.stattools import durbin_watson
import logging
import warnings

# Suppress statsmodels warnings to prevent "invalid value encountered" warnings
warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*invalid value encountered.*')
# Note: np.RankWarning was removed in NumPy 2.0
if hasattr(np, 'RankWarning'):
    warnings.filterwarnings('ignore', category=np.RankWarning)

logger = logging.getLogger(__name__)

def safe_ols_fit(y, X, **kwargs):
    """Safely fit OLS model with warning suppression and data cleaning."""
    try:
        # Clean data first
        combined_data = pd.concat([pd.Series(y, name='y'), pd.DataFrame(X)], axis=1).dropna()
        if len(combined_data) < 5:
            return None
        
        y_clean = combined_data['y']
        X_clean = combined_data.drop('y', axis=1)
        
        # Replace infinite values
        y_clean = y_clean.replace([np.inf, -np.inf], np.nan).dropna()
        X_clean = X_clean.replace([np.inf, -np.inf], np.nan).dropna()
        
        # Align again after cleaning
        common_index = y_clean.index.intersection(X_clean.index)
        if len(common_index) < 5:
            return None
            
        y_final = y_clean.loc[common_index]
        X_final = X_clean.loc[common_index]
        
        # Fit model with warnings suppressed
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=RuntimeWarning)
            # Note: np.RankWarning was removed in NumPy 2.0
            if hasattr(np, 'RankWarning'):
                warnings.filterwarnings('ignore', category=np.RankWarning)
            model = sm.OLS(y_final, X_final)
            return model.fit(**kwargs)
    except Exception as e:
        logger.debug(f"OLS fitting failed: {e}")
        return None

class RegressionAnalyzer:
    """Regression analysis implementation following the research methodology."""
    

    def extract_safe_ols_results(self, ols_result):
        """
        Extract safe, serializable results from OLS result object.
        """
        try:
            return {
                'params': ols_result.params.to_dict() if hasattr(ols_result.params, 'to_dict') else dict(ols_result.params),
                'pvalues': ols_result.pvalues.to_dict() if hasattr(ols_result.pvalues, 'to_dict') else dict(ols_result.pvalues),
                'tvalues': ols_result.tvalues.to_dict() if hasattr(ols_result.tvalues, 'to_dict') else dict(ols_result.tvalues),
                'rsquared': float(ols_result.rsquared),
                'rsquared_adj': float(ols_result.rsquared_adj),
                'fvalue': float(ols_result.fvalue) if hasattr(ols_result, 'fvalue') else None,
                'f_pvalue': float(ols_result.f_pvalue) if hasattr(ols_result, 'f_pvalue') else None,
                'aic': float(ols_result.aic) if hasattr(ols_result, 'aic') else None,
                'bic': float(ols_result.bic) if hasattr(ols_result, 'bic') else None,
                'nobs': int(ols_result.nobs),
                'df_resid': int(ols_result.df_resid) if hasattr(ols_result, 'df_resid') else None,
                'df_model': int(ols_result.df_model) if hasattr(ols_result, 'df_model') else None,
                'mse_resid': float(ols_result.mse_resid) if hasattr(ols_result, 'mse_resid') else None,
                'summary_text': str(ols_result.summary()) if hasattr(ols_result, 'summary') else None
            }
        except Exception as e:
            self.logger.error(f"Failed to extract safe OLS results: {e}")
            return {
                'error': f"Failed to extract results: {str(e)}",
                'params': {},
                'rsquared': 0.0,
                'nobs': 0
            }

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.RegressionAnalyzer")
    
    def run_pooled_regression(
        self,
        aligned_data: pd.DataFrame,
        crypto_assets: List[str] = None,
        stock_assets: List[str] = None
    ) -> Dict[str, any]:
        """
        Run pooled regression analysis on aligned data.
        
        Args:
            aligned_data: DataFrame with aligned asset and economic data
            crypto_assets: List of cryptocurrency asset names
            stock_assets: List of stock asset names
            
        Returns:
            Dictionary with regression results
        """
        self.logger.info("Running pooled regression analysis")
        
        # OPTIMIZATION: Limit the scope to prevent hanging
        max_assets_to_analyze = 5  # Conservative limit to prevent hanging
        
        # Identify asset columns and calculate returns if needed
        price_columns = [col for col in aligned_data.columns 
                        if not any(suffix in col.lower() for suffix in ['_return', '_volatility', 'surprise', 'lag', 'dummy'])]
        
        # Calculate returns from prices (limit to key assets)
        returns_data = pd.DataFrame(index=aligned_data.index)
        processed_count = 0
        
        for col in price_columns:
            if processed_count >= max_assets_to_analyze:  # Conservative total limit
                break
                
            if col in aligned_data.columns:
                prices = aligned_data[col].dropna()
                if len(prices) > 100:  # Higher threshold for data quality
                    returns = prices.pct_change().dropna()
                    if len(returns) > 50:
                        returns_data[col] = returns
                        processed_count += 1
        
        self.logger.info(f"Calculated returns for {len(returns_data.columns)} assets")
        
        # Identify surprise columns
        surprise_columns = [col for col in aligned_data.columns if 'surprise' in col.lower()]
        surprise_data = aligned_data[surprise_columns] if surprise_columns else pd.DataFrame()
        
        # If no specific asset lists provided, try to infer from column names
        if crypto_assets is None:
            crypto_assets = [col for col in returns_data.columns 
                           if any(crypto_name in col.upper() for crypto_name in ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'CRYPTO'])]
        
        if stock_assets is None:
            stock_assets = [col for col in returns_data.columns 
                          if any(stock_name in col.upper() for stock_name in ['^GSPC', 'SPY', '^TNX', 'DX-Y', 'GSPC', 'TNX'])]
        
        # Further limit assets for individual regressions
        crypto_assets = crypto_assets[:max_assets_to_analyze]
        stock_assets = stock_assets[:max_assets_to_analyze]
        
        self.logger.info(f"Limited to {len(crypto_assets)} crypto and {len(stock_assets)} stock assets for individual regressions")
        
        results = {}
        
        # Run individual asset regressions if we have surprise data
        if not surprise_data.empty and not returns_data.empty:
            # Create simple surprise indicators if we don't have proper surprises
            if surprise_data.empty:
                # Create dummy surprise data based on economic indicators
                econ_columns = [col for col in aligned_data.columns 
                              if any(econ_name in col.upper() for econ_name in ['UNRATE', 'PAYEMS', 'CPIAUCSL', 'PCEPI'])][:3]  # Limit to 3
                
                if econ_columns:
                    surprise_data = pd.DataFrame(index=aligned_data.index)
                    for col in econ_columns:
                        if col in aligned_data.columns:
                            series = aligned_data[col].dropna()
                            if len(series) > 12:
                                # Calculate surprise as deviation from 12-month moving average
                                ma_12 = series.rolling(window=12, min_periods=1).mean().shift(1)
                                surprise = (series - ma_12) / series.rolling(window=12, min_periods=1).std().shift(1)
                                surprise_data[f"{col}_surprise"] = surprise
            
            # Limit surprise measures too
            surprise_columns = surprise_data.columns[:3]  # Max 3 surprise measures
            
            # Run regressions for limited set of assets
            target_assets = (crypto_assets + stock_assets)[:max_assets_to_analyze]
            
            self.logger.info(f"Running individual regressions for {len(target_assets)} assets against {len(surprise_columns)} surprise measures")
            
            for i, asset in enumerate(target_assets):
                if asset in returns_data.columns:
                    asset_returns = returns_data[asset].dropna()
                    
                    if len(asset_returns) > 30:
                        asset_results = {}
                        
                        # Run regression against limited surprise measures
                        for surprise_col in surprise_columns:
                            if surprise_col in surprise_data.columns:
                                reg_data = pd.DataFrame({
                                    'return': asset_returns,
                                    'surprise': surprise_data[surprise_col]
                                }).dropna()
                                
                                if len(reg_data) > 15:  # Higher threshold
                                    try:
                                        # Use matrix approach instead of formula to avoid patsy issues
                                        y = reg_data['return']
                                        X = sm.add_constant(reg_data['surprise'])
                                        
                                        # Clean data to prevent warnings
                                        if not (np.isfinite(y).all() and np.isfinite(X).all().all()):
                                            self.logger.debug(f"Skipping {asset} vs {surprise_col} due to non-finite values")
                                            continue
                                            
                                        model = sm.OLS(y, X)
                                        reg_result = model.fit(cov_type='HC3')
                                        asset_results[surprise_col] = reg_result
                                        
                                    except Exception as e:
                                        self.logger.debug(f"Regression failed for {asset} vs {surprise_col}: {e}")
                        
                        if asset_results:
                            results[asset] = asset_results
                
                # Progress logging
                if (i + 1) % 3 == 0:
                    self.logger.info(f"Completed regressions for {i + 1}/{len(target_assets)} assets")
        
        # Run pooled regression if we have both crypto and stock assets
        if crypto_assets and stock_assets and not surprise_data.empty:
            try:
                pooled_result = self.pooled_crypto_stock_regression(
                    returns_data=returns_data,
                    surprise_data=surprise_data,
                    crypto_assets=crypto_assets,
                    stock_assets=stock_assets
                )
                if pooled_result:
                    results['pooled_crypto_vs_stock'] = pooled_result
            except Exception as e:
                self.logger.warning(f"Pooled regression failed: {e}")
        
        # Calculate summary statistics
        if results:
            summary_stats = self._calculate_regression_summary(results)
            results['summary_statistics'] = summary_stats
        
        self.logger.info(f"Completed regression analysis for {len(results)} assets/models")
        return results
    
    def _calculate_regression_summary(self, results: Dict) -> Dict[str, Dict[str, float]]:
        """Calculate summary statistics from regression results."""
        summary = {}
        
        for asset, asset_results in results.items():
            if isinstance(asset_results, dict) and asset != 'summary_statistics':
                asset_summary = {}
                
                for surprise_measure, reg_result in asset_results.items():
                    if hasattr(reg_result, 'params') and hasattr(reg_result, 'rsquared'):
                        try:
                            # Get surprise coefficient (should be second parameter after intercept)
                            if len(reg_result.params) > 1:
                                surprise_coef = reg_result.params.iloc[1]
                                surprise_pvalue = reg_result.pvalues.iloc[1]
                                
                                asset_summary[f"{surprise_measure}_coefficient"] = surprise_coef
                                asset_summary[f"{surprise_measure}_pvalue"] = surprise_pvalue
                                asset_summary[f"{surprise_measure}_rsquared"] = reg_result.rsquared
                                asset_summary[f"{surprise_measure}_significant"] = surprise_pvalue < 0.05
                        except Exception as e:
                            self.logger.warning(f"Could not extract summary for {asset} {surprise_measure}: {e}")
                
                if asset_summary:
                    summary[asset] = asset_summary
        
        return summary
    
    def return_volatility_regression(
        self,
        returns_data: pd.DataFrame,
        volatility_data: pd.DataFrame,
        surprise_data: pd.DataFrame,
        control_variables: pd.DataFrame = None
    ) -> Dict[str, Dict[str, sm.regression.linear_model.RegressionResultsWrapper]]:
        """
        Run return and volatility regressions as specified in the methodology.
        
        Formula: r_{i,t} = α_i + β_{1,i} * Surprise_t + β_{2,i} * D_t + γ_i * X_t + ε_{i,t}
        Formula: RVOL_{i,t} = α'_i + β'_{1,i} * Surprise_t + β'_{2,i} * D_t + γ'_i * X_t + u_{i,t}
        
        Args:
            returns_data: DataFrame with asset returns
            volatility_data: DataFrame with asset volatilities
            surprise_data: DataFrame with surprise measures
            control_variables: DataFrame with control variables
            
        Returns:
            Dictionary with regression results for returns and volatility
        """
        results = {
            'return_regressions': {},
            'volatility_regressions': {}
        }
        
        # Prepare regression data
        regression_data = self._prepare_regression_data(
            returns_data, volatility_data, surprise_data, control_variables
        )
        
        # Get surprise columns
        surprise_cols = [col for col in surprise_data.columns if 'surprise' in col and 'sign' not in col]
        sign_cols = [col for col in surprise_data.columns if 'sign' in col]
        
        # Run regressions for each asset
        for asset in returns_data.columns:
            self.logger.info(f"Running regressions for {asset}")
            
            asset_return_col = f"{asset}_return" if f"{asset}_return" in regression_data.columns else asset
            asset_vol_col = f"{asset}_volatility" if f"{asset}_volatility" in regression_data.columns else f"{asset}_vol"
            
            if asset_return_col in regression_data.columns:
                # Return regression
                results['return_regressions'][asset] = self._run_individual_regression(
                    regression_data, asset_return_col, surprise_cols, sign_cols, control_variables
                )
            
            if asset_vol_col in regression_data.columns:
                # Volatility regression
                results['volatility_regressions'][asset] = self._run_individual_regression(
                    regression_data, asset_vol_col, surprise_cols, sign_cols, control_variables
                )
        
        return results
    
    def pooled_crypto_stock_regression(
        self,
        returns_data: pd.DataFrame,
        surprise_data: pd.DataFrame,
        crypto_assets: List[str],
        stock_assets: List[str],
        control_variables: pd.DataFrame = None
    ) -> sm.regression.linear_model.RegressionResultsWrapper:
        """
        Run pooled regression comparing crypto vs stock sensitivity.
        
        Formula: r_{i,t} = α + β_1 * Surprise_t + β_2 * Crypto_i + β_3 * (Surprise_t × Crypto_i) + β_4 * X_t + ε_{i,t}
        
        Args:
            returns_data: DataFrame with asset returns
            surprise_data: DataFrame with surprise measures
            crypto_assets: List of cryptocurrency asset names
            stock_assets: List of stock asset names
            control_variables: DataFrame with control variables
            
        Returns:
            Regression results
        """
        self.logger.info("Running pooled crypto vs stock regression")
        
        # Create long-form dataset
        pooled_data = []
        
        for date in returns_data.index:
            if date in surprise_data.index:
                # Get surprise measures for this date
                surprises = surprise_data.loc[date]
                controls = control_variables.loc[date] if control_variables is not None else {}
                
                # Add crypto assets
                for asset in crypto_assets:
                    if asset in returns_data.columns:
                        asset_return = returns_data.loc[date, asset]
                        if pd.notna(asset_return):
                            row = {
                                'date': date,
                                'asset': asset,
                                'return': asset_return,
                                'crypto_dummy': 1,
                                **surprises.to_dict(),
                                **controls
                            }
                            pooled_data.append(row)
                
                # Add stock assets
                for asset in stock_assets:
                    if asset in returns_data.columns:
                        asset_return = returns_data.loc[date, asset]
                        if pd.notna(asset_return):
                            row = {
                                'date': date,
                                'asset': asset,
                                'return': asset_return,
                                'crypto_dummy': 0,
                                **surprises.to_dict(),
                                **controls
                            }
                            pooled_data.append(row)
        
        pooled_df = pd.DataFrame(pooled_data)
        
        if not pooled_df.empty:
            # Create interaction terms
            surprise_cols = [col for col in surprise_data.columns if 'surprise' in col and 'normalized' in col]
            
            for surprise_col in surprise_cols:
                if surprise_col in pooled_df.columns:
                    interaction_col = f"{surprise_col}_x_crypto"
                    pooled_df[interaction_col] = pooled_df[surprise_col] * pooled_df['crypto_dummy']
            
            # Build regression formula
            formula_parts = ['return ~ crypto_dummy']
            
            # Add surprise variables
            for surprise_col in surprise_cols:
                if surprise_col in pooled_df.columns:
                    formula_parts.append(surprise_col)
                    interaction_col = f"{surprise_col}_x_crypto"
                    if interaction_col in pooled_df.columns:
                        formula_parts.append(interaction_col)
            
            # Add controls
            if control_variables is not None:
                control_cols = [col for col in control_variables.columns if col in pooled_df.columns]
                formula_parts.extend(control_cols)
            
            formula = ' + '.join(formula_parts)
            
            try:
                # Use matrix approach instead of formula to avoid patsy issues
                y = pooled_df['return']
                
                # Build X matrix manually
                X_columns = ['crypto_dummy']
                if surprise_cols:
                    X_columns.extend(surprise_cols)
                if control_variables is not None:
                    control_cols = [col for col in control_variables.columns if col in pooled_df.columns]
                    X_columns.extend(control_cols)
                
                X = sm.add_constant(pooled_df[X_columns])
                model = sm.OLS(y, X)
                results = model.fit(cov_type='HC3')  # Robust standard errors
                
                self.logger.info(f"Pooled regression completed with {len(pooled_df)} observations")
                return results
                
            except Exception as e:
                self.logger.error(f"Error in pooled regression: {e}")
                return None
        
        return None
    
    def _prepare_regression_data(
        self,
        returns_data: pd.DataFrame,
        volatility_data: pd.DataFrame,
        surprise_data: pd.DataFrame,
        control_variables: pd.DataFrame = None
    ) -> pd.DataFrame:
        """Prepare combined dataset for regression analysis."""
        
        # Start with returns data
        regression_data = returns_data.copy()
        
        # Add volatility data
        for col in volatility_data.columns:
            vol_col_name = f"{col}_volatility" if col in returns_data.columns else col
            regression_data[vol_col_name] = volatility_data[col]
        
        # Add surprise data
        regression_data = regression_data.join(surprise_data, how='outer')
        
        # Add control variables
        if control_variables is not None:
            regression_data = regression_data.join(control_variables, how='outer')
        
        # Add lagged variables
        return_cols = [col for col in returns_data.columns]
        for col in return_cols:
            if col in regression_data.columns:
                regression_data[f"{col}_lag1"] = regression_data[col].shift(1)
        
        # Remove rows with all NaN values
        regression_data = regression_data.dropna(how='all')
        
        return regression_data
    
    def _run_individual_regression(
        self,
        data: pd.DataFrame,
        dependent_var: str,
        surprise_cols: List[str],
        sign_cols: List[str],
        control_variables: pd.DataFrame = None
    ) -> Dict[str, sm.regression.linear_model.RegressionResultsWrapper]:
        """Run regression for individual asset."""
        
        results = {}
        
        # Basic regression with main surprise
        if surprise_cols:
            main_surprise = surprise_cols[0]  # Use first surprise measure
            
            # Get corresponding sign variable
            main_sign = None
            for sign_col in sign_cols:
                if main_surprise.replace('_surprise', '') in sign_col:
                    main_sign = sign_col
                    break
            
            # Prepare data for regression
            reg_data = data[[dependent_var, main_surprise]].copy()
            if main_sign and main_sign in data.columns:
                reg_data[main_sign] = data[main_sign]
            
            # Add lagged dependent variable
            lagged_dep = f"{dependent_var}_lag1"
            if lagged_dep in data.columns:
                reg_data[lagged_dep] = data[lagged_dep]
            
            # Add control variables
            if control_variables is not None:
                for col in control_variables.columns:
                    if col in data.columns:
                        reg_data[col] = data[col]
            
            # Remove rows with missing values
            reg_data = reg_data.dropna()
            
            if len(reg_data) > 10:  # Minimum observations
                try:
                    # Build formula
                    formula_parts = [dependent_var, '~', main_surprise]
                    
                    if main_sign and main_sign in reg_data.columns:
                        formula_parts.append(f"+ {main_sign}")
                    
                    if lagged_dep in reg_data.columns:
                        formula_parts.append(f"+ {lagged_dep}")
                    
                    if control_variables is not None:
                        for col in control_variables.columns:
                            if col in reg_data.columns and col != dependent_var:
                                formula_parts.append(f"+ {col}")
                    
                    formula = ' '.join(formula_parts)
                    
                    # Use matrix approach instead of formula to avoid patsy issues
                    y = reg_data[dependent_var]
                    
                    X_columns = [main_surprise]
                    if main_sign and main_sign in reg_data.columns:
                        X_columns.append(main_sign)
                    if lagged_dep in reg_data.columns:
                        X_columns.append(lagged_dep)
                    if control_variables is not None:
                        for col in control_variables.columns:
                            if col in reg_data.columns and col != dependent_var:
                                X_columns.append(col)
                    
                    X = sm.add_constant(reg_data[X_columns])
                    model = sm.OLS(y, X)
                    reg_result = model.fit(cov_type='HC3')  # Robust standard errors
                    
                    # Add diagnostic tests
                    reg_result.durbin_watson = durbin_watson(reg_result.resid)
                    
                    # Breusch-Pagan test for heteroscedasticity
                    try:
                        bp_stat, bp_pvalue, _, _ = het_breuschpagan(reg_result.resid, reg_result.model.exog)
                        reg_result.breusch_pagan = {'statistic': bp_stat, 'pvalue': bp_pvalue}
                    except:
                        reg_result.breusch_pagan = None
                    
                    results['main_model'] = reg_result
                    
                    # Avoid non-ASCII characters in logs for Windows consoles
                    self.logger.info(f"Regression completed for {dependent_var}: R2 = {reg_result.rsquared:.4f}")
                    
                except Exception as e:
                    self.logger.error(f"Error in regression for {dependent_var}: {e}")
        
        return results
    
    def asymmetric_effects_analysis(
        self,
        returns_data: pd.DataFrame,
        surprise_data: pd.DataFrame,
        control_variables: pd.DataFrame = None
    ) -> Dict[str, Dict[str, sm.regression.linear_model.RegressionResultsWrapper]]:
        """
        Analyze asymmetric effects of positive vs negative surprises.
        
        Args:
            returns_data: DataFrame with asset returns
            surprise_data: DataFrame with surprise measures
            control_variables: DataFrame with control variables
            
        Returns:
            Dictionary with regression results for positive and negative surprises
        """
        results = {}
        
        # Split surprises into positive and negative
        surprise_cols = [col for col in surprise_data.columns if 'surprise' in col and 'sign' not in col]
        
        for asset in returns_data.columns:
            results[asset] = {}
            
            asset_data = returns_data[asset].dropna()
            
            for surprise_col in surprise_cols:
                if surprise_col in surprise_data.columns:
                    surprise_series = surprise_data[surprise_col]
                    
                    # Positive surprises
                    pos_mask = surprise_series > 0
                    pos_data = pd.DataFrame({
                        'return': asset_data,
                        'surprise': surprise_series
                    }).loc[pos_mask].dropna()
                    
                    if len(pos_data) > 10:
                        try:
                            # Use matrix approach instead of formula to avoid patsy issues
                            y = pos_data['return']
                            X = sm.add_constant(pos_data['surprise'])
                            model = sm.OLS(y, X)
                            results[asset][f'{surprise_col}_positive'] = model.fit(cov_type='HC3')
                        except:
                            pass
                    
                    # Negative surprises
                    neg_mask = surprise_series < 0
                    neg_data = pd.DataFrame({
                        'return': asset_data,
                        'surprise': surprise_series
                    }).loc[neg_mask].dropna()
                    
                    if len(neg_data) > 10:
                        try:
                            # Use matrix approach instead of formula to avoid patsy issues
                            y = neg_data['return']
                            X = sm.add_constant(neg_data['surprise'])
                            model = sm.OLS(y, X)
                            results[asset][f'{surprise_col}_negative'] = model.fit(cov_type='HC3')
                        except:
                            pass
        
        return results
    
    def regime_dependent_analysis(
        self,
        returns_data: pd.DataFrame,
        surprise_data: pd.DataFrame,
        regime_data: pd.DataFrame,
        control_variables: pd.DataFrame = None
    ) -> Dict[str, Dict[str, sm.regression.linear_model.RegressionResultsWrapper]]:
        """
        Analyze regime-dependent effects (e.g., high vs low volatility periods).
        
        Args:
            returns_data: DataFrame with asset returns
            surprise_data: DataFrame with surprise measures
            regime_data: DataFrame with regime indicators
            control_variables: DataFrame with control variables
            
        Returns:
            Dictionary with regime-specific regression results
        """
        results = {}
        
        # Get regime columns
        regime_cols = regime_data.columns
        
        for asset in returns_data.columns:
            results[asset] = {}
            
            for regime_col in regime_cols:
                if regime_col in regime_data.columns:
                    regime_series = regime_data[regime_col]
                    
                    # High regime (regime = 1)
                    high_regime_mask = regime_series == 1
                    high_regime_data = self._prepare_regime_data(
                        returns_data[asset], surprise_data, high_regime_mask, control_variables
                    )
                    
                    if len(high_regime_data) > 10:
                        try:
                            high_model = self._run_regime_regression(high_regime_data)
                            if high_model:
                                results[asset][f'{regime_col}_high'] = high_model
                        except Exception as e:
                            self.logger.error(f"Error in high regime regression: {e}")
                    
                    # Low regime (regime = 0)
                    low_regime_mask = regime_series == 0
                    low_regime_data = self._prepare_regime_data(
                        returns_data[asset], surprise_data, low_regime_mask, control_variables
                    )
                    
                    if len(low_regime_data) > 10:
                        try:
                            low_model = self._run_regime_regression(low_regime_data)
                            if low_model:
                                results[asset][f'{regime_col}_low'] = low_model
                        except Exception as e:
                            self.logger.error(f"Error in low regime regression: {e}")
        
        return results
    
    def _prepare_regime_data(
        self,
        asset_returns: pd.Series,
        surprise_data: pd.DataFrame,
        regime_mask: pd.Series,
        control_variables: pd.DataFrame = None
    ) -> pd.DataFrame:
        """Prepare data for regime-specific regression."""
        
        # Apply regime mask
        regime_returns = asset_returns.loc[regime_mask]
        regime_surprises = surprise_data.loc[regime_mask]
        
        # Combine data
        regime_data = pd.DataFrame({'return': regime_returns})
        regime_data = regime_data.join(regime_surprises, how='inner')
        
        if control_variables is not None:
            regime_controls = control_variables.loc[regime_mask]
            regime_data = regime_data.join(regime_controls, how='inner')
        
        return regime_data.dropna()
    
    def _run_regime_regression(self, data: pd.DataFrame) -> Optional[sm.regression.linear_model.RegressionResultsWrapper]:
        """Run regression for regime-specific data."""
        
        # Find surprise columns
        surprise_cols = [col for col in data.columns if 'surprise' in col and 'normalized' in col]
        
        if surprise_cols and 'return' in data.columns:
            main_surprise = surprise_cols[0]
            
            # Simple regression using matrix approach
            try:
                y = data['return']
                X = sm.add_constant(data[main_surprise])
                model = sm.OLS(y, X)
                return model.fit(cov_type='HC3')
            except:
                return None
        
        return None