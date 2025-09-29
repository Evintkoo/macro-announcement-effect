"""
Enhanced Plot Generator with Actual Visualizations

This module creates publication-quality figures for the research project,
complementing the table exports from table_exporter.py.

Generates:
- Event study plots (CAR, AAR, by event and asset)
- Regression diagnostic plots
- Distribution comparisons (crypto vs stocks)
- Time series plots with event markers
- Correlation heatmaps
- GARCH volatility plots
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
import warnings

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class VisualPlotGenerator:
    """
    Generates actual visual plots (PNG/PDF) for research presentation.
    
    Complements the table_exporter.PlotGenerator which creates CSV files.
    """
    
    def __init__(
        self,
        figures_dir: str = "results/figures",
        style: str = "seaborn-v0_8-darkgrid",
        dpi: int = 300,
        figsize: Tuple[int, int] = (12, 8)
    ):
        """
        Initialize the visual plot generator
        
        Parameters:
        -----------
        figures_dir : str
            Directory to save figures
        style : str
            Matplotlib style
        dpi : int
            Resolution for saved figures
        figsize : Tuple[int, int]
            Default figure size
        """
        self.logger = logging.getLogger(__name__)
        self.figures_dir = Path(figures_dir)
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        
        # Set style
        try:
            plt.style.use(style)
        except:
            plt.style.use('seaborn-v0_8')
        
        self.dpi = dpi
        self.figsize = figsize
        
        # Color schemes
        self.colors = {
            'crypto': '#FF6B35',
            'stocks': '#004E89',
            'positive': '#06A77D',
            'negative': '#D62246',
            'neutral': '#7D8491'
        }
        
        self.logger.info(f"VisualPlotGenerator initialized. Figures will be saved to: {self.figures_dir}")
    
    def plot_event_study_results(
        self,
        event_results: Dict[str, Any],
        save_dir: Optional[Path] = None
    ) -> None:
        """
        Generate comprehensive event study visualizations
        
        Parameters:
        -----------
        event_results : Dict
            Event study results from analysis
        save_dir : Optional[Path]
            Custom save directory
        """
        save_dir = save_dir or self.figures_dir / "event_study"
        save_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Generating event study visualizations...")
        
        try:
            # 1. Average Abnormal Returns (AAR) plot
            if 'average_abnormal_returns' in event_results:
                self._plot_aar(event_results['average_abnormal_returns'], save_dir)
            
            # 2. Cumulative Abnormal Returns (CAR) plot
            if 'average_cumulative_abnormal_returns' in event_results:
                self._plot_car(event_results['average_cumulative_abnormal_returns'], save_dir)
            
            # 3. CAR by asset type (crypto vs stocks)
            if 'cumulative_abnormal_returns' in event_results:
                self._plot_car_by_asset_type(event_results['cumulative_abnormal_returns'], save_dir)
            
            # 4. Significance heatmap
            if 'significance_tests' in event_results:
                self._plot_significance_heatmap(event_results['significance_tests'], save_dir)
            
            # 5. Distribution comparison
            if 'abnormal_returns' in event_results:
                self._plot_return_distributions(event_results['abnormal_returns'], save_dir)
            
            self.logger.info(f"Event study visualizations saved to {save_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate event study plots: {e}")
            import traceback
            traceback.print_exc()
    
    def _plot_aar(self, aar_data: pd.DataFrame, save_dir: Path) -> None:
        """Plot Average Abnormal Returns"""
        try:
            fig, axes = plt.subplots(2, 1, figsize=(14, 10))
            
            # Separate crypto and stock columns
            crypto_cols = [col for col in aar_data.columns if 'crypto' in col.lower() or 'btc' in col.lower()]
            stock_cols = [col for col in aar_data.columns if 'stock' in col.lower() or 'spy' in col.lower() or 'nasdaq' in col.lower()]
            
            # Plot 1: Crypto AAR
            if crypto_cols:
                for col in crypto_cols[:10]:  # Limit to first 10 for readability
                    axes[0].plot(aar_data.index, aar_data[col], alpha=0.7, linewidth=1.5, label=col[:30])
                axes[0].axhline(y=0, color='black', linestyle='--', linewidth=1)
                axes[0].axvline(x=0, color='red', linestyle='--', linewidth=2, label='Event')
                axes[0].set_title('Average Abnormal Returns - Cryptocurrency Assets', fontsize=14, fontweight='bold')
                axes[0].set_xlabel('Days Relative to Event', fontsize=12)
                axes[0].set_ylabel('AAR (%)', fontsize=12)
                axes[0].legend(loc='best', fontsize=8, ncol=2)
                axes[0].grid(True, alpha=0.3)
            
            # Plot 2: Stock AAR
            if stock_cols:
                for col in stock_cols[:10]:
                    axes[1].plot(aar_data.index, aar_data[col], alpha=0.7, linewidth=1.5, label=col[:30])
                axes[1].axhline(y=0, color='black', linestyle='--', linewidth=1)
                axes[1].axvline(x=0, color='red', linestyle='--', linewidth=2, label='Event')
                axes[1].set_title('Average Abnormal Returns - Stock Market Indices', fontsize=14, fontweight='bold')
                axes[1].set_xlabel('Days Relative to Event', fontsize=12)
                axes[1].set_ylabel('AAR (%)', fontsize=12)
                axes[1].legend(loc='best', fontsize=8, ncol=2)
                axes[1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            save_path = save_dir / "average_abnormal_returns.png"
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"Saved AAR plot: {save_path}")
            
        except Exception as e:
            self.logger.warning(f"Failed to plot AAR: {e}")
    
    def _plot_car(self, car_data: pd.DataFrame, save_dir: Path) -> None:
        """Plot Cumulative Abnormal Returns"""
        try:
            fig, axes = plt.subplots(2, 1, figsize=(14, 10))
            
            # Separate crypto and stock columns
            crypto_cols = [col for col in car_data.columns if 'crypto' in col.lower() or 'btc' in col.lower()]
            stock_cols = [col for col in car_data.columns if 'stock' in col.lower() or 'spy' in col.lower() or 'nasdaq' in col.lower()]
            
            # Plot 1: Crypto CAR
            if crypto_cols:
                for col in crypto_cols[:10]:
                    axes[0].plot(car_data.index, car_data[col], alpha=0.7, linewidth=2, label=col[:30])
                axes[0].axhline(y=0, color='black', linestyle='--', linewidth=1)
                axes[0].axvline(x=0, color='red', linestyle='--', linewidth=2, label='Event')
                axes[0].set_title('Cumulative Abnormal Returns - Cryptocurrency Assets', fontsize=14, fontweight='bold')
                axes[0].set_xlabel('Days Relative to Event', fontsize=12)
                axes[0].set_ylabel('CAR (%)', fontsize=12)
                axes[0].legend(loc='best', fontsize=8, ncol=2)
                axes[0].grid(True, alpha=0.3)
            
            # Plot 2: Stock CAR
            if stock_cols:
                for col in stock_cols[:10]:
                    axes[1].plot(car_data.index, car_data[col], alpha=0.7, linewidth=2, label=col[:30])
                axes[1].axhline(y=0, color='black', linestyle='--', linewidth=1)
                axes[1].axvline(x=0, color='red', linestyle='--', linewidth=2, label='Event')
                axes[1].set_title('Cumulative Abnormal Returns - Stock Market Indices', fontsize=14, fontweight='bold')
                axes[1].set_xlabel('Days Relative to Event', fontsize=12)
                axes[1].set_ylabel('CAR (%)', fontsize=12)
                axes[1].legend(loc='best', fontsize=8, ncol=2)
                axes[1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            save_path = save_dir / "cumulative_abnormal_returns.png"
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"Saved CAR plot: {save_path}")
            
        except Exception as e:
            self.logger.warning(f"Failed to plot CAR: {e}")
    
    def _plot_car_by_asset_type(self, car_dict: Dict[str, pd.DataFrame], save_dir: Path) -> None:
        """Plot CAR comparison between crypto and stocks"""
        try:
            # Calculate average CAR for crypto vs stocks
            crypto_cars = []
            stock_cars = []
            
            for asset_name, car_df in car_dict.items():
                if isinstance(car_df, pd.DataFrame) and not car_df.empty:
                    if 'crypto' in asset_name.lower() or 'btc' in asset_name.lower():
                        crypto_cars.append(car_df.mean(axis=1))
                    elif 'stock' in asset_name.lower() or 'spy' in asset_name.lower():
                        stock_cars.append(car_df.mean(axis=1))
            
            if not crypto_cars and not stock_cars:
                return
            
            fig, ax = plt.subplots(figsize=(12, 7))
            
            # Plot average CAR with confidence bands
            if crypto_cars:
                crypto_avg = pd.concat(crypto_cars, axis=1).mean(axis=1)
                crypto_std = pd.concat(crypto_cars, axis=1).std(axis=1)
                ax.plot(crypto_avg.index, crypto_avg, color=self.colors['crypto'], 
                       linewidth=3, label='Cryptocurrency (Average)', alpha=0.9)
                ax.fill_between(crypto_avg.index, 
                               crypto_avg - 1.96*crypto_std, 
                               crypto_avg + 1.96*crypto_std,
                               color=self.colors['crypto'], alpha=0.2)
            
            if stock_cars:
                stock_avg = pd.concat(stock_cars, axis=1).mean(axis=1)
                stock_std = pd.concat(stock_cars, axis=1).std(axis=1)
                ax.plot(stock_avg.index, stock_avg, color=self.colors['stocks'], 
                       linewidth=3, label='Stock Markets (Average)', alpha=0.9)
                ax.fill_between(stock_avg.index, 
                               stock_avg - 1.96*stock_std, 
                               stock_avg + 1.96*stock_std,
                               color=self.colors['stocks'], alpha=0.2)
            
            ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.7)
            ax.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Event')
            
            ax.set_title('Cumulative Abnormal Returns: Crypto vs Stock Markets', 
                        fontsize=16, fontweight='bold')
            ax.set_xlabel('Days Relative to Event', fontsize=13)
            ax.set_ylabel('Average CAR (%) with 95% CI', fontsize=13)
            ax.legend(loc='best', fontsize=12)
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            save_path = save_dir / "car_crypto_vs_stocks.png"
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"Saved CAR comparison plot: {save_path}")
            
        except Exception as e:
            self.logger.warning(f"Failed to plot CAR comparison: {e}")
    
    def _plot_significance_heatmap(self, significance_tests: Dict, save_dir: Path) -> None:
        """Plot heatmap of significance tests"""
        try:
            # Convert to DataFrame for plotting
            rows = []
            for event, assets in significance_tests.items():
                for asset, tests in assets.items():
                    if isinstance(tests, dict):
                        p_value = tests.get('p_value', tests.get('t_test', {}).get('p_value', np.nan))
                        rows.append({
                            'event': event[:30],
                            'asset': asset[:30],
                            'p_value': p_value
                        })
            
            if not rows:
                return
            
            df = pd.DataFrame(rows)
            pivot = df.pivot(index='asset', columns='event', values='p_value')
            
            # Create heatmap
            fig, ax = plt.subplots(figsize=(14, 10))
            
            # Significance levels: <0.01 (***), <0.05 (**), <0.1 (*), >0.1 (ns)
            sns.heatmap(pivot, annot=True, fmt='.3f', cmap='RdYlGn_r', 
                       center=0.05, vmin=0, vmax=0.15,
                       cbar_kws={'label': 'P-value'},
                       ax=ax)
            
            ax.set_title('Statistical Significance of Event Study Results\n(Green = Significant, Red = Not Significant)',
                        fontsize=14, fontweight='bold')
            ax.set_xlabel('Event', fontsize=12)
            ax.set_ylabel('Asset', fontsize=12)
            
            plt.tight_layout()
            save_path = save_dir / "significance_heatmap.png"
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"Saved significance heatmap: {save_path}")
            
        except Exception as e:
            self.logger.warning(f"Failed to plot significance heatmap: {e}")
    
    def _plot_return_distributions(self, ar_dict: Dict[str, pd.DataFrame], save_dir: Path) -> None:
        """Plot distribution comparison of abnormal returns"""
        try:
            # Collect returns
            crypto_returns = []
            stock_returns = []
            
            for asset_name, ar_df in ar_dict.items():
                if isinstance(ar_df, pd.DataFrame) and not ar_df.empty:
                    returns = ar_df.values.flatten()
                    returns = returns[~np.isnan(returns)]
                    
                    if 'crypto' in asset_name.lower() or 'btc' in asset_name.lower():
                        crypto_returns.extend(returns)
                    elif 'stock' in asset_name.lower() or 'spy' in asset_name.lower():
                        stock_returns.extend(returns)
            
            if not crypto_returns and not stock_returns:
                return
            
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))
            
            # Histogram comparison
            if crypto_returns:
                axes[0].hist(crypto_returns, bins=50, alpha=0.6, color=self.colors['crypto'], 
                           label='Crypto', density=True, edgecolor='black')
            if stock_returns:
                axes[0].hist(stock_returns, bins=50, alpha=0.6, color=self.colors['stocks'], 
                           label='Stocks', density=True, edgecolor='black')
            
            axes[0].axvline(x=0, color='black', linestyle='--', linewidth=2)
            axes[0].set_title('Distribution of Abnormal Returns', fontsize=14, fontweight='bold')
            axes[0].set_xlabel('Abnormal Returns (%)', fontsize=12)
            axes[0].set_ylabel('Density', fontsize=12)
            axes[0].legend(fontsize=12)
            axes[0].grid(True, alpha=0.3)
            
            # Box plot comparison
            data_to_plot = []
            labels = []
            if crypto_returns:
                data_to_plot.append(crypto_returns)
                labels.append('Crypto')
            if stock_returns:
                data_to_plot.append(stock_returns)
                labels.append('Stocks')
            
            bp = axes[1].boxplot(data_to_plot, labels=labels, patch_artist=True)
            for patch, color in zip(bp['boxes'], [self.colors['crypto'], self.colors['stocks']]):
                patch.set_facecolor(color)
                patch.set_alpha(0.6)
            
            axes[1].axhline(y=0, color='black', linestyle='--', linewidth=1)
            axes[1].set_title('Abnormal Returns Distribution', fontsize=14, fontweight='bold')
            axes[1].set_ylabel('Abnormal Returns (%)', fontsize=12)
            axes[1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            save_path = save_dir / "return_distributions.png"
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"Saved distribution plots: {save_path}")
            
        except Exception as e:
            self.logger.warning(f"Failed to plot distributions: {e}")
    
    def plot_regression_results(
        self,
        regression_results: Dict[str, Any],
        save_dir: Optional[Path] = None
    ) -> None:
        """
        Generate regression diagnostic and results visualizations
        
        Parameters:
        -----------
        regression_results : Dict
            Regression results from analysis
        save_dir : Optional[Path]
            Custom save directory
        """
        save_dir = save_dir or self.figures_dir / "regression"
        save_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Generating regression visualizations...")
        
        try:
            # 1. Coefficient comparison plot
            self._plot_coefficient_comparison(regression_results, save_dir)
            
            # 2. R-squared comparison
            self._plot_rsquared_comparison(regression_results, save_dir)
            
            # 3. Residual diagnostics (if available)
            if 'residuals' in regression_results:
                self._plot_residual_diagnostics(regression_results['residuals'], save_dir)
            
            self.logger.info(f"Regression visualizations saved to {save_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate regression plots: {e}")
            import traceback
            traceback.print_exc()
    
    def _plot_coefficient_comparison(self, results: Dict, save_dir: Path) -> None:
        """Plot coefficient comparison across models"""
        try:
            # Extract coefficients from results
            coef_data = []
            
            for model_name, model_results in results.items():
                if hasattr(model_results, 'params'):
                    for var, coef in model_results.params.items():
                        pval = model_results.pvalues.get(var, np.nan)
                        coef_data.append({
                            'model': model_name,
                            'variable': var,
                            'coefficient': coef,
                            'p_value': pval,
                            'significant': pval < 0.05
                        })
            
            if not coef_data:
                return
            
            df = pd.DataFrame(coef_data)
            
            # Create coefficient plot
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Group by variable
            variables = df['variable'].unique()[:15]  # Limit to first 15
            x = np.arange(len(variables))
            width = 0.35
            
            models = df['model'].unique()[:2]  # Compare max 2 models
            
            for i, model in enumerate(models):
                model_data = df[df['model'] == model]
                coeffs = [model_data[model_data['variable'] == var]['coefficient'].values[0] 
                         if var in model_data['variable'].values else 0 
                         for var in variables]
                
                ax.bar(x + i*width, coeffs, width, label=model, alpha=0.8)
            
            ax.set_xlabel('Variables', fontsize=12)
            ax.set_ylabel('Coefficient', fontsize=12)
            ax.set_title('Regression Coefficients Comparison', fontsize=14, fontweight='bold')
            ax.set_xticks(x + width / 2)
            ax.set_xticklabels(variables, rotation=45, ha='right')
            ax.axhline(y=0, color='black', linestyle='--', linewidth=1)
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
            
            plt.tight_layout()
            save_path = save_dir / "coefficient_comparison.png"
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"Saved coefficient plot: {save_path}")
            
        except Exception as e:
            self.logger.warning(f"Failed to plot coefficients: {e}")
    
    def _plot_rsquared_comparison(self, results: Dict, save_dir: Path) -> None:
        """Plot R-squared comparison"""
        try:
            r2_data = []
            
            for model_name, model_results in results.items():
                if hasattr(model_results, 'rsquared'):
                    r2_data.append({
                        'model': model_name,
                        'r_squared': model_results.rsquared,
                        'adj_r_squared': getattr(model_results, 'rsquared_adj', np.nan)
                    })
            
            if not r2_data:
                return
            
            df = pd.DataFrame(r2_data)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            x = np.arange(len(df))
            width = 0.35
            
            ax.bar(x - width/2, df['r_squared'], width, label='R²', alpha=0.8)
            ax.bar(x + width/2, df['adj_r_squared'], width, label='Adjusted R²', alpha=0.8)
            
            ax.set_xlabel('Model', fontsize=12)
            ax.set_ylabel('R² Value', fontsize=12)
            ax.set_title('Model Fit Comparison', fontsize=14, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(df['model'], rotation=45, ha='right')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
            ax.set_ylim([0, 1])
            
            plt.tight_layout()
            save_path = save_dir / "rsquared_comparison.png"
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"Saved R² plot: {save_path}")
            
        except Exception as e:
            self.logger.warning(f"Failed to plot R²: {e}")
    
    def _plot_residual_diagnostics(self, residuals: pd.Series, save_dir: Path) -> None:
        """Plot residual diagnostic plots"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            
            # 1. Residuals vs Fitted
            axes[0, 0].scatter(range(len(residuals)), residuals, alpha=0.5)
            axes[0, 0].axhline(y=0, color='red', linestyle='--')
            axes[0, 0].set_title('Residuals vs Fitted', fontsize=12, fontweight='bold')
            axes[0, 0].set_xlabel('Fitted values')
            axes[0, 0].set_ylabel('Residuals')
            axes[0, 0].grid(True, alpha=0.3)
            
            # 2. Q-Q plot
            from scipy import stats
            stats.probplot(residuals.dropna(), dist="norm", plot=axes[0, 1])
            axes[0, 1].set_title('Q-Q Plot', fontsize=12, fontweight='bold')
            axes[0, 1].grid(True, alpha=0.3)
            
            # 3. Histogram of residuals
            axes[1, 0].hist(residuals.dropna(), bins=50, alpha=0.7, edgecolor='black')
            axes[1, 0].axvline(x=0, color='red', linestyle='--')
            axes[1, 0].set_title('Distribution of Residuals', fontsize=12, fontweight='bold')
            axes[1, 0].set_xlabel('Residuals')
            axes[1, 0].set_ylabel('Frequency')
            axes[1, 0].grid(True, alpha=0.3)
            
            # 4. Residuals over time
            axes[1, 1].plot(residuals, alpha=0.7)
            axes[1, 1].axhline(y=0, color='red', linestyle='--')
            axes[1, 1].set_title('Residuals Over Time', fontsize=12, fontweight='bold')
            axes[1, 1].set_xlabel('Observation')
            axes[1, 1].set_ylabel('Residuals')
            axes[1, 1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            save_path = save_dir / "residual_diagnostics.png"
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"Saved residual diagnostics: {save_path}")
            
        except Exception as e:
            self.logger.warning(f"Failed to plot residual diagnostics: {e}")
    
    def plot_garch_volatility(
        self,
        garch_results: Dict[str, Dict],
        save_dir: Optional[Path] = None
    ) -> None:
        """
        Plot GARCH conditional volatility
        
        Parameters:
        -----------
        garch_results : Dict
            GARCH model results
        save_dir : Optional[Path]
            Custom save directory
        """
        save_dir = save_dir or self.figures_dir / "garch"
        save_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Generating GARCH volatility plots...")
        
        try:
            # Plot conditional volatility for each asset
            for asset, results in list(garch_results.items())[:10]:  # Limit to 10 assets
                if 'conditional_volatility' not in results:
                    continue
                
                fig, ax = plt.subplots(figsize=(12, 6))
                
                vol = results['conditional_volatility']
                ax.plot(vol.index if hasattr(vol, 'index') else range(len(vol)), 
                       vol, linewidth=1.5, color=self.colors['crypto'])
                
                # Add unconditional volatility line
                if 'unconditional_volatility' in results:
                    ax.axhline(y=results['unconditional_volatility'], 
                             color='red', linestyle='--', linewidth=2,
                             label=f'Unconditional Vol: {results["unconditional_volatility"]:.4f}')
                
                ax.set_title(f'GARCH Conditional Volatility: {asset}', 
                           fontsize=14, fontweight='bold')
                ax.set_xlabel('Time', fontsize=12)
                ax.set_ylabel('Volatility', fontsize=12)
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                plt.tight_layout()
                safe_name = asset.replace('/', '_').replace(':', '_')
                save_path = save_dir / f"garch_volatility_{safe_name}.png"
                plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
                plt.close()
            
            self.logger.info(f"GARCH volatility plots saved to {save_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate GARCH plots: {e}")


__all__ = ['VisualPlotGenerator']
