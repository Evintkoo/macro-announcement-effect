"""
Visualization module for generating plots and charts.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PlotGenerator:
    """Generate clean, non-overlapping visualizations for the analysis results."""
    
    def __init__(self, style: str = "seaborn-v0_8", figures_dir: str = "results/figures", tables_dir: str = "results/tables"):
        """
        Initialize plot generator with improved formatting for clear visualizations.
        
        Args:
            style: Matplotlib style to use
            figures_dir: Directory to save figures
            tables_dir: Directory to save tables and data
        """
        self.logger = logging.getLogger(f"{__name__}.PlotGenerator")
        
        # Set up output directories
        self.figures_dir = Path(figures_dir)
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        
        self.tables_dir = Path(tables_dir)
        self.tables_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure matplotlib for non-interactive backend
        plt.ioff()  # Turn off interactive mode
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        
        # Set style
        plt.style.use('default')  # Fallback to default if seaborn not available
        sns.set_palette("husl")
        
        # Set default parameters for better text spacing and clarity
        plt.rcParams.update({
            'figure.figsize': (12, 8),
            'font.size': 11,
            'axes.titlesize': 16,
            'axes.labelsize': 13,
            'xtick.labelsize': 11,
            'ytick.labelsize': 11,
            'legend.fontsize': 11,
            'savefig.dpi': 300,
            'savefig.bbox': 'tight',
            'savefig.format': 'png',
            'figure.subplot.bottom': 0.15,  # More space for x-axis labels
            'figure.subplot.left': 0.12,    # More space for y-axis labels
            'figure.subplot.right': 0.85,   # More space for legends
            'figure.subplot.top': 0.92,     # More space for titles
            'axes.titlepad': 15,            # Padding below title
            'axes.labelpad': 10,            # Padding for axis labels
            'xtick.major.pad': 8,           # Padding for x-tick labels
            'ytick.major.pad': 8,           # Padding for y-tick labels
            'legend.borderpad': 0.5,        # Legend border padding
            'legend.columnspacing': 1.0,    # Space between legend columns
            'legend.handletextpad': 0.5     # Space between legend handle and text
        })
    
    def _save_plot(self, filename: str, subdir: str = None) -> str:
        """
        Save the current plot to file with optimized settings to prevent text overlap.
        
        Args:
            filename: Name of the file (without extension)
            subdir: Subdirectory within figures_dir
            
        Returns:
            Full path to saved file
        """
        if subdir:
            save_dir = self.figures_dir / subdir
            save_dir.mkdir(parents=True, exist_ok=True)
        else:
            save_dir = self.figures_dir
        
        filepath = save_dir / f"{filename}.png"
        
        # Ensure tight layout before saving to prevent text overlap
        plt.tight_layout(pad=2.0)  # Add extra padding
        
        # Save with high quality and bbox_inches='tight' to prevent clipping
        plt.savefig(filepath, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()  # Close the figure to free memory
        
        self.logger.info(f"✓ Plot saved: {filepath}")
        return str(filepath)
    
    def _cleanup_old_combined_plots(self):
        """Remove old combined plots that are no longer generated."""
        old_combined_plots = [
            "all_price_series_overview.png",
            "cryptocurrency_prices_overview.png", 
            "stock_market_indices_overview.png",
            "economic_indicators_overview.png"
        ]
        
        overview_dir = self.figures_dir / "overview"
        if overview_dir.exists():
            for old_plot in old_combined_plots:
                old_plot_path = overview_dir / old_plot
                if old_plot_path.exists():
                    try:
                        old_plot_path.unlink()
                        self.logger.info(f"Removed old combined plot: {old_plot}")
                    except Exception as e:
                        self.logger.warning(f"Could not remove old plot {old_plot}: {e}")
    
    def _save_table(self, data: pd.DataFrame, filename: str, subdir: str = None) -> str:
        """
        Save data table to CSV file.
        
        Args:
            data: DataFrame to save
            filename: Name of the file (without extension)
            subdir: Subdirectory within tables_dir
            
        Returns:
            Full path to saved file
        """
        if subdir:
            save_dir = self.tables_dir / subdir
            save_dir.mkdir(parents=True, exist_ok=True)
        else:
            save_dir = self.tables_dir
        
        filepath = save_dir / f"{filename}.csv"
        data.to_csv(filepath)
        
        self.logger.info(f"Table saved: {filepath}")
        return str(filepath)
    
    def plot_data_overview(
        self,
        aligned_data: pd.DataFrame,
        save_dir: Path = None
    ) -> None:
        """
        Generate overview plots of the aligned dataset as separate, clean visualizations.
        
        Args:
            aligned_data: DataFrame with aligned data
            save_dir: Directory to save plots
        """
        self.logger.info("Generating clean data overview plots (one plot per image)")
        
        if aligned_data is None or aligned_data.empty:
            self.logger.warning("No data available for plotting")
            return
        
        if save_dir:
            save_dir = Path(save_dir)
            save_dir.mkdir(parents=True, exist_ok=True)
        
        # Separate different types of data
        price_columns = [col for col in aligned_data.columns 
                        if not any(suffix in col.lower() for suffix in ['_return', '_volatility', 'surprise', 'lag', 'dummy', 'unrate', 'payems', 'civpart', 'cpiaucsl', 'cpilfesl', 'pcepi', 'pcepilfe'])]
        
        econ_columns = [col for col in aligned_data.columns 
                       if any(econ_name in col.upper() for econ_name in ['UNRATE', 'PAYEMS', 'CIVPART', 'CPIAUCSL', 'CPILFESL', 'PCEPI', 'PCEPILFE'])]
        
        crypto_columns = [col for col in price_columns 
                         if any(crypto_name in col.upper() for crypto_name in ['BTC', 'ETH', 'BNB', 'ADA', 'SOL'])]
        
        stock_columns = [col for col in price_columns 
                        if any(stock_name in col.upper() for stock_name in ['^GSPC', 'GSPC', '^VIX', 'VIX', '^TNX', 'TNX', 'DX-Y'])]
        
        self.logger.info(f"Found {len(crypto_columns)} crypto assets, {len(stock_columns)} stock assets, {len(econ_columns)} economic indicators")
        
        # Create individual overview plots (no more subplots!)
        self.logger.info("Creating data availability heatmap...")
        self._plot_data_availability(aligned_data, save_dir)
        
        if price_columns:
            self.logger.info("Creating all price series plots...")
            self._plot_price_series_overview(aligned_data[price_columns], 'All Price Series', save_dir)
        
        if crypto_columns:
            self.logger.info("Creating cryptocurrency-specific plots...")
            self._plot_price_series_overview(aligned_data[crypto_columns], 'Cryptocurrency Prices', save_dir)
            
        if stock_columns:
            self.logger.info("Creating stock market-specific plots...")
            self._plot_price_series_overview(aligned_data[stock_columns], 'Stock Market Indices', save_dir)
            
        if econ_columns:
            self.logger.info("Creating economic indicators plots...")
            self._plot_economic_indicators_overview(aligned_data[econ_columns], save_dir)
        
        # Summary statistics table
        self.logger.info("Creating summary statistics table...")
        self._plot_summary_statistics_table(aligned_data, save_dir)
        
        self.logger.info(f"✓ All plots generated successfully in {self.figures_dir}")
        
        # Clean up any old combined plots
        self._cleanup_old_combined_plots()
    
    def _plot_data_availability(
        self,
        data: pd.DataFrame,
        save_dir: Path = None
    ) -> None:
        """Plot data availability heatmap with improved formatting."""
        
        # Create availability matrix (1 for available, 0 for missing)
        availability = (~data.isnull()).astype(int)
        
        # Save full availability matrix as CSV
        self._save_table(availability, "data_availability_matrix", "overview")
        
        # Sample data if too many observations for plotting
        sampled_availability = availability
        if len(availability) > 1000:
            step = len(availability) // 500
            sampled_availability = availability.iloc[::step]
        
        # Limit number of variables to show (select most complete ones)
        if len(availability.columns) > 30:
            completeness = availability.sum().sort_values(ascending=False)
            top_vars = completeness.head(30).index
            sampled_availability = sampled_availability[top_vars]
        
        plt.figure(figsize=(16, 10))
        
        # Clean variable names for y-axis
        clean_var_names = []
        for var in sampled_availability.columns:
            clean_name = var.replace('_price', '').replace('crypto_', '').replace('stocks_', '')
            clean_name = clean_name.replace('economic_', 'Econ: ')
            clean_name = clean_name.replace('BTC-USD', 'BTC').replace('ETH-USD', 'ETH')
            clean_name = clean_name.replace('_', ' ').title()
            if len(clean_name) > 20:
                clean_name = clean_name[:17] + '...'
            clean_var_names.append(clean_name)
        
        # Plot heatmap with better formatting
        sns.heatmap(sampled_availability.T, 
                   cbar_kws={'label': 'Data Available', 'shrink': 0.8}, 
                   cmap='RdYlGn', 
                   xticklabels=50,  # Show every 50th time label
                   yticklabels=clean_var_names,
                   cbar=True)
        
        plt.title('Data Availability Over Time', fontsize=18, fontweight='bold', pad=20)
        plt.xlabel('Time Period', fontsize=14)
        plt.ylabel('Variables', fontsize=14)
        
        # Improve tick labels
        plt.xticks(fontsize=10)
        plt.yticks(fontsize=10, rotation=0)
        
        plt.tight_layout()
        
        # Save plot
        filename = "data_availability_heatmap"
        self._save_plot(filename, "overview")
    
    def _plot_price_series_overview(
        self,
        price_data: pd.DataFrame,
        title: str,
        save_dir: Path = None
    ) -> None:
        """Plot overview of price series as separate plots."""
        
        if price_data is None or price_data.empty:
            self.logger.warning(f"No data available for {title}")
            return
        
        # Filter out columns with too many NaN values (>80% missing)
        valid_columns = []
        for col in price_data.columns:
            missing_pct = price_data[col].isnull().sum() / len(price_data)
            if missing_pct < 0.8:  # Less than 80% missing
                valid_columns.append(col)
        
        if not valid_columns:
            self.logger.warning(f"No valid columns found for {title}")
            return
        
        # Work with valid columns only
        valid_data = price_data[valid_columns].copy()
        
        # Save original price data
        clean_title = title.lower().replace(' ', '_')
        self._save_table(valid_data, f"{clean_title}_raw_prices", "overview")
        
        # Helper function to clean asset names
        def clean_asset_name(name):
            replacements = {
                'BTC-USD_price': 'BTC',
                'ETH-USD_price': 'ETH',
                'BNB-USD_price': 'BNB',
                'ADA-USD_price': 'ADA',
                'SOL-USD_price': 'SOL',
                '^GSPC': 'S&P500',
                'DX-Y.NYB': 'USD Index',
                '^VIX': 'VIX',
                '^TNX': '10Y Treasury'
            }
            for old, new in replacements.items():
                name = name.replace(old, new)
            return name
        
        # 1. Raw Prices Plot
        plt.figure(figsize=(14, 8))
        for col in valid_columns:
            clean_series = valid_data[col].dropna()
            if len(clean_series) > 10:  # Only plot if enough data
                plt.plot(clean_series.index, clean_series.values, 
                        label=clean_asset_name(col), alpha=0.8, linewidth=2)
        
        plt.title(f'{title} - Price Levels', fontsize=16, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Price', fontsize=12)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        self._save_plot(f"{clean_title}_raw_prices", "overview")
        
        # 2. Normalized Prices Plot (base = 100)
        normalized_data = pd.DataFrame(index=valid_data.index)
        for col in valid_columns:
            series = valid_data[col].dropna()
            if len(series) > 10 and series.iloc[0] > 0:  # Valid base value
                normalized_series = (series / series.iloc[0]) * 100
                normalized_data[col] = normalized_series
        
        if not normalized_data.empty:
            self._save_table(normalized_data, f"{clean_title}_normalized_prices", "overview")
            
            plt.figure(figsize=(14, 8))
            for col in normalized_data.columns:
                clean_series = normalized_data[col].dropna()
                if len(clean_series) > 10:
                    plt.plot(clean_series.index, clean_series.values, 
                            label=clean_asset_name(col), alpha=0.8, linewidth=2)
            
            plt.title(f'{title} - Normalized Prices (Base = 100)', fontsize=16, fontweight='bold')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Normalized Price', fontsize=12)
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            self._save_plot(f"{clean_title}_normalized_prices", "overview")
        
        # 3. Daily Returns Plot
        returns_dict = {}
        for col in valid_columns:
            series = valid_data[col].dropna()
            if len(series) > 10:
                returns = series.pct_change().dropna()
                # Remove extreme outliers (>20% daily change - likely data errors)
                returns = returns[np.abs(returns) < 0.20]
                returns_dict[col] = returns
        
        # Create DataFrame from dictionary to avoid fragmentation
        returns_data = pd.DataFrame(returns_dict, index=valid_data.index)
        
        if not returns_data.empty:
            self._save_table(returns_data, f"{clean_title}_daily_returns", "overview")
            
            plt.figure(figsize=(14, 8))
            for col in returns_data.columns:
                clean_series = returns_data[col].dropna()
                if len(clean_series) > 10:
                    plt.plot(clean_series.index, clean_series.values * 100, 
                            label=clean_asset_name(col), alpha=0.7, linewidth=1.5)
            
            plt.title(f'{title} - Daily Returns (%)', fontsize=16, fontweight='bold')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Return (%)', fontsize=12)
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            self._save_plot(f"{clean_title}_daily_returns", "overview")
        
        # 4. Rolling Volatility Plot
        rolling_vol_series = {}
        for col in returns_data.columns:
            clean_series = returns_data[col].dropna()
            if len(clean_series) > 30:  # Need at least 30 observations for rolling window
                rolling_vol = clean_series.rolling(window=30).std() * np.sqrt(252) * 100
                rolling_vol_series[col] = rolling_vol
        
        # Concatenate all series at once to avoid fragmentation
        if rolling_vol_series:
            rolling_vol_data = pd.concat(rolling_vol_series, axis=1)
        else:
            rolling_vol_data = pd.DataFrame()
        
        if not rolling_vol_data.empty:
            self._save_table(rolling_vol_data, f"{clean_title}_rolling_volatility", "overview")
            
            plt.figure(figsize=(14, 8))
            for col in rolling_vol_data.columns:
                clean_series = rolling_vol_data[col].dropna()
                if len(clean_series) > 10:
                    plt.plot(clean_series.index, clean_series.values, 
                            label=clean_asset_name(col), alpha=0.8, linewidth=2)
            
            plt.title(f'{title} - 30-Day Rolling Volatility (Annualized %)', fontsize=16, fontweight='bold')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Volatility (%)', fontsize=12)
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            self._save_plot(f"{clean_title}_rolling_volatility", "overview")
    
    def _plot_economic_indicators_overview(
        self,
        econ_data: pd.DataFrame,
        save_dir: Path = None
    ) -> None:
        """Plot overview of economic indicators as separate plots."""
        
        if econ_data.empty:
            return
        
        # Save economic indicators data
        self._save_table(econ_data, "economic_indicators_raw", "overview")
        
        # Create individual plots for each economic indicator
        for col in econ_data.columns:
            data_series = econ_data[col].dropna()
            
            if len(data_series) > 0:
                plt.figure(figsize=(12, 6))
                
                # Main data plot
                plt.plot(data_series.index, data_series, linewidth=2.5, color='darkblue', 
                        label=col.replace('_', ' ').title())
                
                # Add trend line if enough data
                if len(data_series) > 10:
                    z = np.polyfit(range(len(data_series)), data_series.values, 1)
                    p = np.poly1d(z)
                    plt.plot(data_series.index, p(range(len(data_series))), 
                           "r--", alpha=0.7, linewidth=2, label='Trend')
                
                # Formatting
                clean_title = col.replace('_', ' ').replace('economic ', '').title()
                plt.title(f'Economic Indicator: {clean_title}', fontsize=16, fontweight='bold')
                plt.xlabel('Date', fontsize=12)
                plt.ylabel('Value', fontsize=12)
                plt.legend(fontsize=11)
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
                # Save individual plot
                clean_filename = col.lower().replace(' ', '_').replace('economic_', '')
                self._save_plot(f"economic_indicator_{clean_filename}", "overview")
    
    def _plot_summary_statistics_table(
        self,
        data: pd.DataFrame,
        save_dir: Path = None
    ) -> None:
        """Create and plot summary statistics table with improved formatting."""
        
        # Calculate summary statistics
        summary_stats = data.describe()
        
        # Select key statistics
        key_stats = summary_stats.loc[['count', 'mean', 'std', 'min', 'max']]
        
        # Save table data as CSV
        self._save_table(key_stats, "summary_statistics", "overview")
        
        # Limit number of columns to prevent overcrowding
        max_cols = 10  # Maximum columns to display
        if len(key_stats.columns) > max_cols:
            # Select most relevant columns (those with most data)
            data_completeness = data.notna().sum().sort_values(ascending=False)
            selected_cols = data_completeness.head(max_cols).index.tolist()
            key_stats = key_stats[selected_cols]
        
        # Create plot with better sizing
        fig, ax = plt.subplots(figsize=(16, 6))
        ax.axis('tight')
        ax.axis('off')
        
        # Prepare data for table
        table_data = key_stats.round(4)
        
        # Truncate column names for better display
        col_labels = []
        for col in table_data.columns:
            if len(col) > 20:
                # Clean up column names
                clean_col = col.replace('_price', '').replace('crypto_', '').replace('stocks_', '')
                clean_col = clean_col.replace('BTC-USD', 'BTC').replace('ETH-USD', 'ETH')
                if len(clean_col) > 15:
                    clean_col = clean_col[:12] + '...'
                col_labels.append(clean_col)
            else:
                col_labels.append(col.replace('_', ' ').title())
        
        # Create table with improved styling
        table = ax.table(cellText=table_data.values.T,  # Transpose for better layout
                        rowLabels=col_labels,
                        colLabels=['Count', 'Mean', 'Std Dev', 'Min', 'Max'],
                        cellLoc='center',
                        loc='center')
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.0, 2.0)  # Increase row height
        
        # Style the header row
        for j in range(len(['Count', 'Mean', 'Std Dev', 'Min', 'Max'])):
            table[(0, j)].set_facecolor('#2E4A62')
            table[(0, j)].set_text_props(weight='bold', color='white')
            table[(0, j)].set_height(0.08)
        
        # Style the row labels (asset names)
        for i in range(1, len(col_labels) + 1):
            table[(i, -1)].set_facecolor('#E8F4FD')
            table[(i, -1)].set_text_props(weight='bold')
            table[(i, -1)].set_height(0.06)
        
        # Alternate row colors for data cells
        for i in range(1, len(col_labels) + 1):
            for j in range(len(['Count', 'Mean', 'Std Dev', 'Min', 'Max'])):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#F8F9FA')
                else:
                    table[(i, j)].set_facecolor('white')
                table[(i, j)].set_height(0.06)
        
        ax.set_title('Summary Statistics - Key Variables', fontsize=18, fontweight='bold', pad=30)
        
        plt.tight_layout()
        
        # Save plot
        filename = "summary_statistics_table"
        self._save_plot(filename, "overview")
    
    def plot_event_study_results(
        self,
        event_results: Dict,
        save_dir: Path = None
    ) -> None:
        """
        Plot event study results including CARs and significance tests.
        
        Args:
            event_results: Dictionary with event study results
            save_dir: Directory to save plots
        """
        self.logger.info("Generating event study plots")
        
        if save_dir:
            save_dir = Path(save_dir)
            save_dir.mkdir(parents=True, exist_ok=True)
        
        # Plot Average Cumulative Abnormal Returns
        if 'average_cumulative_abnormal_returns' in event_results:
            self._plot_average_cars(
                event_results['average_cumulative_abnormal_returns'],
                save_dir
            )
        
        # Plot individual event CARs
        if 'cumulative_abnormal_returns' in event_results:
            self._plot_individual_cars(
                event_results['cumulative_abnormal_returns'],
                save_dir
            )
        
        # Plot summary statistics
        if 'summary_statistics' in event_results:
            self._plot_event_summary_stats(
                event_results['summary_statistics'],
                save_dir
            )
    
    def _plot_average_cars(
        self,
        average_cars: pd.DataFrame,
        save_dir: Path = None
    ) -> None:
        """Plot average cumulative abnormal returns as separate plots."""
        
        if average_cars is None or average_cars.empty:
            self.logger.warning("No average CARs data to plot")
            return
        
        # Save CARs data as CSV
        self._save_table(average_cars, "average_cumulative_abnormal_returns", "event_study")
        
        # Helper function to clean asset names
        def clean_asset_name(name):
            replacements = {
                'BTC-USD_price': 'BTC',
                'ETH-USD_price': 'ETH',
                'BNB-USD_price': 'BNB',
                'ADA-USD_price': 'ADA',
                'SOL-USD_price': 'SOL',
                '^GSPC': 'S&P500',
                'DX-Y.NYB': 'USD Index',
                '^VIX': 'VIX',
                '^TNX': '10Y Treasury'
            }
            for old, new in replacements.items():
                name = name.replace(old, new)
            return name
        
        # Identify asset types more flexibly
        crypto_cols = [col for col in average_cars.columns if any(crypto in col.upper() for crypto in ['BTC', 'ETH', 'BNB', 'ADA', 'SOL'])]
        stock_cols = [col for col in average_cars.columns if any(stock in col.upper() for stock in ['GSPC', 'VIX', 'TNX', 'DX-Y'])]
        
        # If no clear separation, treat all columns as general assets
        if not crypto_cols and not stock_cols:
            all_cols = average_cars.columns.tolist()
            crypto_cols = all_cols[:len(all_cols)//2]  # First half as "crypto"
            stock_cols = all_cols[len(all_cols)//2:]   # Second half as "stocks"
        
        # 1. Cryptocurrency CARs Plot
        if crypto_cols:
            plt.figure(figsize=(12, 8))
            for col in crypto_cols:
                clean_data = average_cars[col].dropna()
                if not clean_data.empty:
                    plt.plot(clean_data.index, clean_data.values, 
                           label=clean_asset_name(col), linewidth=2.5, alpha=0.8)
            
            plt.title('Cryptocurrency Cumulative Abnormal Returns', fontsize=16, fontweight='bold')
            plt.xlabel('Days from Announcement', fontsize=12)
            plt.ylabel('Cumulative Abnormal Return', fontsize=12)
            plt.axhline(y=0, color='black', linestyle='--', alpha=0.6)
            plt.axvline(x=0, color='red', linestyle='-', alpha=0.8, linewidth=2, label='Announcement')
            plt.legend(fontsize=11)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            self._save_plot("crypto_cumulative_abnormal_returns", "event_study")
        
        # 2. Stock Market CARs Plot
        if stock_cols:
            plt.figure(figsize=(12, 8))
            for col in stock_cols:
                clean_data = average_cars[col].dropna()
                if not clean_data.empty:
                    plt.plot(clean_data.index, clean_data.values, 
                           label=clean_asset_name(col), linewidth=2.5, alpha=0.8)
            
            plt.title('Stock Market Cumulative Abnormal Returns', fontsize=16, fontweight='bold')
            plt.xlabel('Days from Announcement', fontsize=12)
            plt.ylabel('Cumulative Abnormal Return', fontsize=12)
            plt.axhline(y=0, color='black', linestyle='--', alpha=0.6)
            plt.axvline(x=0, color='red', linestyle='-', alpha=0.8, linewidth=2, label='Announcement')
            plt.legend(fontsize=11)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            self._save_plot("stock_cumulative_abnormal_returns", "event_study")
        
        # 3. Comparison Plot (Crypto vs Stock Averages)
        if crypto_cols and stock_cols:
            plt.figure(figsize=(12, 8))
            
            # Average across crypto and stocks (only non-null values)
            crypto_avg = average_cars[crypto_cols].mean(axis=1, skipna=True)
            stock_avg = average_cars[stock_cols].mean(axis=1, skipna=True)
            
            if not crypto_avg.empty:
                plt.plot(crypto_avg.index, crypto_avg.values, 
                        label='Cryptocurrency Average', linewidth=3, color='orange', alpha=0.9)
            if not stock_avg.empty:
                plt.plot(stock_avg.index, stock_avg.values, 
                        label='Stock Market Average', linewidth=3, color='blue', alpha=0.9)
            
            plt.title('Crypto vs Stock Market CARs Comparison', fontsize=16, fontweight='bold')
            plt.xlabel('Days from Announcement', fontsize=12)
            plt.ylabel('Average Cumulative Abnormal Return', fontsize=12)
            plt.axhline(y=0, color='black', linestyle='--', alpha=0.6)
            plt.axvline(x=0, color='red', linestyle='-', alpha=0.8, linewidth=2, label='Announcement')
            plt.legend(fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            self._save_plot("crypto_vs_stock_cars_comparison", "event_study")
        
        # 4. Final CARs Distribution Plot
        if len(average_cars) > 0:
            final_cars = average_cars.iloc[-1].dropna()
            if not final_cars.empty:
                plt.figure(figsize=(12, 8))
                
                # Create colors based on asset type
                colors = []
                labels = []
                for col in final_cars.index:
                    clean_name = clean_asset_name(col)
                    labels.append(clean_name)
                    if any(crypto in col.upper() for crypto in ['BTC', 'ETH', 'BNB', 'ADA', 'SOL']):
                        colors.append('orange')
                    else:
                        colors.append('steelblue')
                
                bars = plt.bar(range(len(final_cars)), final_cars.values, color=colors, alpha=0.7)
                plt.title('Final Cumulative Abnormal Returns by Asset', fontsize=16, fontweight='bold')
                plt.xlabel('Assets', fontsize=12)
                plt.ylabel('Final CAR', fontsize=12)
                plt.xticks(range(len(final_cars)), labels, rotation=45, ha='right')
                plt.axhline(y=0, color='black', linestyle='--', alpha=0.6)
                plt.grid(True, alpha=0.3, axis='y')
                
                # Add value labels on bars
                for bar, value in zip(bars, final_cars.values):
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + (0.01 if height >= 0 else -0.01),
                            f'{value:.3f}', ha='center', va='bottom' if height >= 0 else 'top', fontsize=10)
                
                plt.tight_layout()
                self._save_plot("final_cars_by_asset", "event_study")
        
        # 5. All Assets CARs (overview plot)
        plt.figure(figsize=(14, 8))
        for col in average_cars.columns:
            clean_data = average_cars[col].dropna()
            if not clean_data.empty:
                plt.plot(clean_data.index, clean_data.values, 
                        label=clean_asset_name(col), linewidth=2, alpha=0.7)
        
        plt.title('All Assets - Average Cumulative Abnormal Returns', fontsize=16, fontweight='bold')
        plt.xlabel('Days from Announcement', fontsize=12)
        plt.ylabel('Cumulative Abnormal Return', fontsize=12)
        plt.axhline(y=0, color='black', linestyle='--', alpha=0.6)
        plt.axvline(x=0, color='red', linestyle='-', alpha=0.8, linewidth=2, label='Announcement')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        self._save_plot("all_assets_cumulative_abnormal_returns", "event_study")
    
    def _plot_individual_cars(
        self,
        individual_cars: Dict[str, pd.DataFrame],
        save_dir: Path = None
    ) -> None:
        """Plot individual event CARs."""
        
        if not individual_cars:
            return
        
        # Save individual CARs data as separate CSV files
        for event_name, car_data in individual_cars.items():
            safe_event_name = event_name.replace('/', '_').replace(':', '_').replace(' ', '_')
            self._save_table(car_data, f"individual_cars_{safe_event_name}", "event_study")
        
        # Create subplot for each event
        n_events = len(individual_cars)
        cols = min(3, n_events)
        rows = (n_events + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 4*rows))
        if n_events == 1:
            axes = [axes]
        elif rows == 1 and cols > 1:
            axes = list(axes)
        elif rows > 1 and cols == 1:
            axes = list(axes)
        else:
            axes = axes.flatten() if hasattr(axes, 'flatten') else [axes]
        
        fig.suptitle('Individual Event Cumulative Abnormal Returns', fontsize=16)
        
        for i, (event_name, car_data) in enumerate(individual_cars.items()):
            if i < len(axes):
                ax = axes[i]
                
                # Plot each asset
                for col in car_data.columns:
                    clean_series = car_data[col].dropna()
                    if not clean_series.empty:
                        ax.plot(clean_series.index, clean_series.values, label=col, alpha=0.7)
                
                ax.set_title(f'{event_name}')
                ax.set_xlabel('Time')
                ax.set_ylabel('CAR')
                ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
                ax.grid(True, alpha=0.3)
                
                if len(car_data.columns) <= 10:  # Only show legend if not too many assets
                    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Hide unused subplots
        for i in range(n_events, len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        
        # Save plot
        filename = "individual_event_cars"
        self._save_plot(filename, "event_study")
    
    def _plot_event_summary_stats(
        self,
        summary_stats: Dict[str, Dict[str, float]],
        save_dir: Path = None
    ) -> None:
        """Plot event study summary statistics as separate plots."""
        
        if not summary_stats:
            return
        
        # Convert to DataFrame for easier plotting
        stats_df = pd.DataFrame(summary_stats).T
        
        if stats_df.empty:
            return
        
        # Save summary statistics as CSV
        self._save_table(stats_df, "event_study_summary_statistics", "event_study")
        
        assets = stats_df.index
        colors = ['orange' if 'crypto' in asset.lower() else 'steelblue' for asset in assets]
        
        # Helper function to clean asset names
        def clean_asset_labels(assets):
            return [asset.replace('crypto_', '').replace('stock_', '').replace('_', ' ').title()[:15] 
                   for asset in assets]
        
        clean_labels = clean_asset_labels(assets)
        
        # 1. Mean CARs Plot
        if 'mean_car' in stats_df.columns:
            plt.figure(figsize=(12, 8))
            mean_cars = stats_df['mean_car']
            
            bars = plt.bar(range(len(mean_cars)), mean_cars, color=colors, alpha=0.7)
            plt.title('Mean Cumulative Abnormal Returns by Asset', fontsize=16, fontweight='bold')
            plt.xlabel('Assets', fontsize=12)
            plt.ylabel('Mean CAR', fontsize=12)
            plt.xticks(range(len(assets)), clean_labels, rotation=45, ha='right')
            plt.axhline(y=0, color='black', linestyle='--', alpha=0.6)
            plt.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            for bar, value in zip(bars, mean_cars):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + (0.001 if height >= 0 else -0.001),
                        f'{value:.3f}', ha='center', va='bottom' if height >= 0 else 'top', fontsize=10)
            
            plt.tight_layout()
            self._save_plot("mean_cars_by_asset", "event_study")
        
        # 2. Standard Deviations Plot
        if 'std_car' in stats_df.columns:
            plt.figure(figsize=(12, 8))
            std_cars = stats_df['std_car']
            
            bars = plt.bar(range(len(std_cars)), std_cars, color=colors, alpha=0.7)
            plt.title('Standard Deviation of CARs by Asset', fontsize=16, fontweight='bold')
            plt.xlabel('Assets', fontsize=12)
            plt.ylabel('Standard Deviation', fontsize=12)
            plt.xticks(range(len(assets)), clean_labels, rotation=45, ha='right')
            plt.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            for bar, value in zip(bars, std_cars):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + height * 0.01,
                        f'{value:.3f}', ha='center', va='bottom', fontsize=10)
            
            plt.tight_layout()
            self._save_plot("car_volatility_by_asset", "event_study")
        
        # 3. Positive vs Negative Events Plot
        if 'positive_events' in stats_df.columns and 'negative_events' in stats_df.columns:
            plt.figure(figsize=(12, 8))
            pos_events = stats_df['positive_events']
            neg_events = stats_df['negative_events']
            
            x = np.arange(len(assets))
            width = 0.35
            
            bars1 = plt.bar(x - width/2, pos_events, width, label='Positive Events', 
                          color='green', alpha=0.7)
            bars2 = plt.bar(x + width/2, neg_events, width, label='Negative Events', 
                          color='red', alpha=0.7)
            
            plt.title('Positive vs Negative Event Reactions by Asset', fontsize=16, fontweight='bold')
            plt.xlabel('Assets', fontsize=12)
            plt.ylabel('Number of Events', fontsize=12)
            plt.xticks(x, clean_labels, rotation=45, ha='right')
            plt.legend(fontsize=12)
            plt.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            for bars in [bars1, bars2]:
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                               f'{int(height)}', ha='center', va='bottom', fontsize=10)
            
            plt.tight_layout()
            self._save_plot("positive_vs_negative_events", "event_study")
        
        # 4. CAR Range Plot (Min vs Max)
        if 'min_car' in stats_df.columns and 'max_car' in stats_df.columns:
            plt.figure(figsize=(12, 8))
            min_cars = stats_df['min_car']
            max_cars = stats_df['max_car']
            
            scatter = plt.scatter(min_cars, max_cars, c=colors, s=120, alpha=0.7, edgecolors='black')
            plt.xlabel('Minimum CAR', fontsize=12)
            plt.ylabel('Maximum CAR', fontsize=12)
            plt.title('CAR Range: Minimum vs Maximum by Asset', fontsize=16, fontweight='bold')
            plt.axhline(y=0, color='black', linestyle='--', alpha=0.6)
            plt.axvline(x=0, color='black', linestyle='--', alpha=0.6)
            plt.grid(True, alpha=0.3)
            
            # Add asset labels with better positioning
            for i, (asset, min_val, max_val) in enumerate(zip(clean_labels, min_cars, max_cars)):
                plt.annotate(asset, (min_val, max_val), xytext=(8, 8), 
                           textcoords='offset points', fontsize=10, 
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
            
            plt.tight_layout()
            self._save_plot("car_range_min_vs_max", "event_study")
    
    def plot_regression_results(
        self,
        regression_results: Dict,
        save_dir: Path = None
    ) -> None:
        """
        Plot regression analysis results.
        
        Args:
            regression_results: Dictionary with regression results
            save_dir: Directory to save plots
        """
        self.logger.info("Generating regression plots")
        
        if save_dir:
            save_dir = Path(save_dir)
            save_dir.mkdir(parents=True, exist_ok=True)
        
        # Plot coefficient comparisons
        self._plot_regression_coefficients(regression_results, save_dir)
        
        # Plot R-squared comparisons
        self._plot_regression_r_squared(regression_results, save_dir)
    
    def _plot_regression_coefficients(
        self,
        regression_results: Dict,
        save_dir: Path = None
    ) -> None:
        """Plot regression coefficients comparison as separate plots."""
        
        # Extract coefficients from return regressions
        coefficients = {}
        
        if 'return_regressions' in regression_results:
            for asset, models in regression_results['return_regressions'].items():
                if 'main_model' in models:
                    model = models['main_model']
                    coefficients[asset] = {
                        'params': model.params.to_dict(),
                        'pvalues': model.pvalues.to_dict()
                    }
        
        if not coefficients:
            return
        
        # Create DataFrame for coefficients and save as CSV
        params_df = pd.DataFrame({asset: coef['params'] for asset, coef in coefficients.items()})
        pvals_df = pd.DataFrame({asset: coef['pvalues'] for asset, coef in coefficients.items()})
        
        self._save_table(params_df, "regression_coefficients", "regression")
        self._save_table(pvals_df, "regression_pvalues", "regression")
        
        # Get surprise coefficients
        assets = list(coefficients.keys())
        surprise_coeffs = []
        surprise_pvals = []
        
        for asset in assets:
            params = coefficients[asset]['params']
            pvals = coefficients[asset]['pvalues']
            
            # Find surprise coefficient (look for terms with 'surprise')
            surprise_coeff = None
            surprise_pval = None
            
            for param_name, value in params.items():
                if 'surprise' in param_name.lower() and 'sign' not in param_name.lower():
                    surprise_coeff = value
                    surprise_pval = pvals.get(param_name, 1.0)
                    break
            
            surprise_coeffs.append(surprise_coeff if surprise_coeff is not None else 0)
            surprise_pvals.append(surprise_pval if surprise_pval is not None else 1.0)
        
        # Color by significance
        colors = ['red' if p < 0.05 else 'orange' if p < 0.10 else 'gray' 
                 for p in surprise_pvals]
        
        # Clean asset names
        clean_asset_names = [asset.replace('crypto_', '').replace('stock_', '').replace('_', ' ').title()[:12] 
                           for asset in assets]
        
        # 1. Surprise Coefficients Plot
        plt.figure(figsize=(12, 8))
        bars = plt.bar(range(len(surprise_coeffs)), surprise_coeffs, color=colors, alpha=0.7)
        plt.title('Regression Coefficients: Response to Economic Surprises', fontsize=16, fontweight='bold')
        plt.xlabel('Assets', fontsize=12)
        plt.ylabel('Coefficient Value', fontsize=12)
        plt.xticks(range(len(assets)), clean_asset_names, rotation=45, ha='right')
        plt.axhline(y=0, color='black', linestyle='--', alpha=0.6)
        plt.grid(True, alpha=0.3, axis='y')
        
        # Add significance legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='red', label='p < 0.05 (Significant)'),
            Patch(facecolor='orange', label='p < 0.10 (Marginally Significant)'), 
            Patch(facecolor='gray', label='p ≥ 0.10 (Not Significant)')
        ]
        plt.legend(handles=legend_elements, fontsize=11)
        
        # Add value labels on bars
        for bar, value, pval in zip(bars, surprise_coeffs, surprise_pvals):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + (0.001 if height >= 0 else -0.001),
                    f'{value:.3f}', ha='center', va='bottom' if height >= 0 else 'top', fontsize=9)
        
        plt.tight_layout()
        self._save_plot("surprise_coefficients", "regression")
        
        # 2. P-values Plot
        plt.figure(figsize=(12, 8))
        bars = plt.bar(range(len(surprise_pvals)), surprise_pvals, color=colors, alpha=0.7)
        plt.title('Statistical Significance of Surprise Coefficients', fontsize=16, fontweight='bold')
        plt.xlabel('Assets', fontsize=12)
        plt.ylabel('P-value', fontsize=12)
        plt.xticks(range(len(assets)), clean_asset_names, rotation=45, ha='right')
        plt.axhline(y=0.05, color='red', linestyle='--', alpha=0.7, linewidth=2, label='p = 0.05')
        plt.axhline(y=0.10, color='orange', linestyle='--', alpha=0.7, linewidth=2, label='p = 0.10')
        plt.legend(fontsize=12)
        plt.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, value in zip(bars, surprise_pvals):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + height * 0.02,
                    f'{value:.3f}', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        self._save_plot("surprise_coefficient_pvalues", "regression")
    
    def _plot_regression_r_squared(
        self,
        regression_results: Dict,
        save_dir: Path = None
    ) -> None:
        """Plot R-squared comparison across assets as separate plots."""
        
        # Extract R-squared values
        r_squared_return = {}
        r_squared_vol = {}
        
        if 'return_regressions' in regression_results:
            for asset, models in regression_results['return_regressions'].items():
                if 'main_model' in models:
                    r_squared_return[asset] = models['main_model'].rsquared
        
        if 'volatility_regressions' in regression_results:
            for asset, models in regression_results['volatility_regressions'].items():
                if 'main_model' in models:
                    r_squared_vol[asset] = models['main_model'].rsquared
        
        if not r_squared_return and not r_squared_vol:
            return
        
        # Create R-squared DataFrame and save as CSV
        r_squared_df = pd.DataFrame()
        if r_squared_return:
            r_squared_df['return_regressions'] = pd.Series(r_squared_return)
        if r_squared_vol:
            r_squared_df['volatility_regressions'] = pd.Series(r_squared_vol)
        
        self._save_table(r_squared_df, "regression_r_squared", "regression")
        
        # 1. Return Regression R-squared Plot
        if r_squared_return:
            plt.figure(figsize=(12, 8))
            assets = list(r_squared_return.keys())
            r2_values = list(r_squared_return.values())
            colors = ['orange' if 'crypto' in asset.lower() else 'steelblue' for asset in assets]
            clean_asset_names = [asset.replace('crypto_', '').replace('stock_', '').replace('_', ' ').title()[:12] 
                               for asset in assets]
            
            bars = plt.bar(range(len(r2_values)), r2_values, color=colors, alpha=0.7)
            plt.title('Model Fit: Return Regressions R-squared', fontsize=16, fontweight='bold')
            plt.xlabel('Assets', fontsize=12)
            plt.ylabel('R-squared', fontsize=12)
            plt.xticks(range(len(assets)), clean_asset_names, rotation=45, ha='right')
            plt.ylim(0, max(r2_values) * 1.1 if r2_values else 1)
            plt.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            for bar, value in zip(bars, r2_values):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + height * 0.02,
                        f'{value:.3f}', ha='center', va='bottom', fontsize=10)
            
            # Add color legend
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='orange', label='Cryptocurrency'),
                Patch(facecolor='steelblue', label='Traditional Assets')
            ]
            plt.legend(handles=legend_elements, fontsize=11)
            
            plt.tight_layout()
            self._save_plot("return_regression_r_squared", "regression")
        
        # 2. Volatility Regression R-squared Plot
        if r_squared_vol:
            plt.figure(figsize=(12, 8))
            assets = list(r_squared_vol.keys())
            r2_values = list(r_squared_vol.values())
            colors = ['orange' if 'crypto' in asset.lower() else 'steelblue' for asset in assets]
            clean_asset_names = [asset.replace('crypto_', '').replace('stock_', '').replace('_', ' ').title()[:12] 
                               for asset in assets]
            
            bars = plt.bar(range(len(r2_values)), r2_values, color=colors, alpha=0.7)
            plt.title('Model Fit: Volatility Regressions R-squared', fontsize=16, fontweight='bold')
            plt.xlabel('Assets', fontsize=12)
            plt.ylabel('R-squared', fontsize=12)
            plt.xticks(range(len(assets)), clean_asset_names, rotation=45, ha='right')
            plt.ylim(0, max(r2_values) * 1.1 if r2_values else 1)
            plt.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            for bar, value in zip(bars, r2_values):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + height * 0.02,
                        f'{value:.3f}', ha='center', va='bottom', fontsize=10)
            
            # Add color legend
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='orange', label='Cryptocurrency'),
                Patch(facecolor='steelblue', label='Traditional Assets')
            ]
            plt.legend(handles=legend_elements, fontsize=11)
            
            plt.tight_layout()
            self._save_plot("volatility_regression_r_squared", "regression")
    
    def plot_summary_statistics(
        self,
        data_dict: Dict[str, pd.DataFrame],
        save_dir: Path = None
    ) -> None:
        """
        Plot summary statistics for the datasets.
        
        Args:
            data_dict: Dictionary with datasets (e.g., {'stocks': df, 'crypto': df})
            save_dir: Directory to save plots
        """
        self.logger.info("Generating summary statistics plots")
        
        if save_dir:
            save_dir = Path(save_dir)
            save_dir.mkdir(parents=True, exist_ok=True)
        
        # Plot price evolution
        self._plot_price_evolution(data_dict, save_dir)
        
        # Plot volatility comparison
        self._plot_volatility_comparison(data_dict, save_dir)
        
        # Plot correlation matrix
        self._plot_correlation_matrix(data_dict, save_dir)
    
    def _plot_price_evolution(
        self,
        data_dict: Dict[str, pd.DataFrame],
        save_dir: Path = None
    ) -> None:
        """Plot price evolution over time as separate plots."""
        
        # Store normalized data for all categories
        all_normalized_data = pd.DataFrame()
        
        for category, data in data_dict.items():
            # Normalize prices to start at 100 for comparison
            normalized_data = data.div(data.iloc[0]) * 100
            
            # Add category prefix to column names and combine
            prefixed_data = normalized_data.add_prefix(f"{category}_")
            all_normalized_data = all_normalized_data.join(prefixed_data, how='outer')
            
            # Create individual plot for each category
            plt.figure(figsize=(14, 8))
            
            for col in normalized_data.columns:
                plt.plot(normalized_data.index, normalized_data[col], label=col, linewidth=2.5, alpha=0.8)
            
            plt.title(f'{category.title()} Price Evolution (Normalized to Base = 100)', 
                     fontsize=16, fontweight='bold')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Normalized Price (Base = 100)', fontsize=12)
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=11)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Save individual plot
            filename = f"{category}_price_evolution"
            self._save_plot(filename, "summary")
        
        # Save normalized price data as CSV
        if not all_normalized_data.empty:
            self._save_table(all_normalized_data, "normalized_price_evolution", "summary")
        
        # Create combined comparison plot
        if len(data_dict) > 1:
            plt.figure(figsize=(14, 8))
            
            # Plot average for each category
            for category, data in data_dict.items():
                normalized_data = data.div(data.iloc[0]) * 100
                category_avg = normalized_data.mean(axis=1)
                plt.plot(category_avg.index, category_avg, label=f'{category.title()} Average', 
                        linewidth=3, alpha=0.9)
            
            plt.title('Price Evolution Comparison Across Asset Classes', fontsize=16, fontweight='bold')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Normalized Price (Base = 100)', fontsize=12)
            plt.legend(fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            self._save_plot("all_categories_price_comparison", "summary")
    
    def _plot_volatility_comparison(
        self,
        data_dict: Dict[str, pd.DataFrame],
        save_dir: Path = None
    ) -> None:
        """Plot volatility comparison as separate plots."""
        
        # Calculate rolling volatility for each dataset
        volatilities = {}
        all_volatility_data = pd.DataFrame()
        
        for category, data in data_dict.items():
            vol_data = pd.DataFrame(index=data.index)
            
            for col in data.columns:
                returns = np.log(data[col] / data[col].shift(1))
                rolling_vol = returns.rolling(window=30).std() * np.sqrt(252) * 100  # Annualized %
                vol_data[col] = rolling_vol
            
            volatilities[category] = vol_data
            
            # Add category prefix to column names and combine
            prefixed_vol_data = vol_data.add_prefix(f"{category}_")
            all_volatility_data = all_volatility_data.join(prefixed_vol_data, how='outer')
            
            # Create individual plot for each category
            plt.figure(figsize=(14, 8))
            
            for col in vol_data.columns:
                plt.plot(vol_data.index, vol_data[col], label=col, linewidth=2.5, alpha=0.8)
            
            plt.title(f'{category.title()} - 30-Day Rolling Volatility (Annualized %)', 
                     fontsize=16, fontweight='bold')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Volatility (%)', fontsize=12)
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=11)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Save individual plot
            filename = f"{category}_volatility"
            self._save_plot(filename, "summary")
        
        # Save volatility data as CSV
        if not all_volatility_data.empty:
            self._save_table(all_volatility_data, "rolling_volatility_30d", "summary")
        
        # Create combined comparison plot
        if len(volatilities) > 1:
            plt.figure(figsize=(14, 8))
            
            # Plot average volatility for each category
            for category, vol_data in volatilities.items():
                category_avg_vol = vol_data.mean(axis=1, skipna=True)
                plt.plot(category_avg_vol.index, category_avg_vol, label=f'{category.title()} Average', 
                        linewidth=3, alpha=0.9)
            
            plt.title('Volatility Comparison Across Asset Classes', fontsize=16, fontweight='bold')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('30-Day Rolling Volatility (%)', fontsize=12)
            plt.legend(fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            self._save_plot("all_categories_volatility_comparison", "summary")
    
    def _plot_correlation_matrix(
        self,
        data_dict: Dict[str, pd.DataFrame],
        save_dir: Path = None
    ) -> None:
        """Plot correlation matrix."""
        
        # Combine all data for correlation analysis
        all_data = pd.DataFrame()
        
        for category, data in data_dict.items():
            # Calculate returns
            returns_data = pd.DataFrame(index=data.index)
            for col in data.columns:
                returns = np.log(data[col] / data[col].shift(1))
                returns_data[f"{category}_{col}"] = returns
            
            all_data = all_data.join(returns_data, how='outer')
        
        # Calculate correlation matrix
        corr_matrix = all_data.corr()
        
        # Save correlation matrix as CSV
        if not corr_matrix.empty:
            self._save_table(corr_matrix, "correlation_matrix", "summary")
        
        # Plot heatmap
        fig, ax = plt.subplots(figsize=(12, 10))
        
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))  # Mask upper triangle
        
        sns.heatmap(corr_matrix, mask=mask, annot=True, cmap='RdBu_r', center=0,
                   square=True, ax=ax, cbar_kws={"shrink": .8})
        
        ax.set_title('Correlation Matrix of Returns', fontsize=16)
        
        plt.tight_layout()
        
        # Save plot
        filename = "correlation_matrix"
        self._save_plot(filename, "summary")