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
    """Generate visualizations for the analysis results."""
    
    def __init__(self, style: str = "seaborn-v0_8", figures_dir: str = "results/figures", tables_dir: str = "results/tables"):
        """
        Initialize plot generator.
        
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
        
        # Set default parameters
        plt.rcParams.update({
            'figure.figsize': (12, 8),
            'font.size': 12,
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 11,
            'savefig.dpi': 300,
            'savefig.bbox': 'tight',
            'savefig.format': 'png'
        })
    
    def _save_plot(self, filename: str, subdir: str = None) -> str:
        """
        Save the current plot to file.
        
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
        plt.savefig(filepath)
        plt.close()  # Close the figure to free memory
        
        self.logger.info(f"Plot saved: {filepath}")
        return str(filepath)
    
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
        Generate overview plots of the aligned dataset.
        
        Args:
            aligned_data: DataFrame with aligned data
            save_dir: Directory to save plots
        """
        self.logger.info("Generating data overview plots")
        
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
        
        # Create overview plots
        self._plot_data_availability(aligned_data, save_dir)
        
        if price_columns:
            self._plot_price_series_overview(aligned_data[price_columns], 'All Price Series', save_dir)
        
        if crypto_columns:
            self._plot_price_series_overview(aligned_data[crypto_columns], 'Cryptocurrency Prices', save_dir)
            
        if stock_columns:
            self._plot_price_series_overview(aligned_data[stock_columns], 'Stock Market Indices', save_dir)
            
        if econ_columns:
            self._plot_economic_indicators_overview(aligned_data[econ_columns], save_dir)
        
        # Summary statistics table
        self._plot_summary_statistics_table(aligned_data, save_dir)
    
    def _plot_data_availability(
        self,
        data: pd.DataFrame,
        save_dir: Path = None
    ) -> None:
        """Plot data availability heatmap."""
        
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # Create availability matrix (1 for available, 0 for missing)
        availability = (~data.isnull()).astype(int)
        
        # Save full availability matrix as CSV
        self._save_table(availability, "data_availability_matrix", "overview")
        
        # Sample data if too many observations for plotting
        sampled_availability = availability
        if len(availability) > 500:
            step = len(availability) // 500
            sampled_availability = availability.iloc[::step]
        
        # Plot heatmap
        sns.heatmap(sampled_availability.T, cbar_kws={'label': 'Data Available'}, 
                   cmap='RdYlGn', ax=ax, xticklabels=50)
        
        ax.set_title('Data Availability Over Time', fontsize=16)
        ax.set_xlabel('Time')
        ax.set_ylabel('Variables')
        
        plt.tight_layout()
        
        # Save plot
        filename = "data_availability"
        self._save_plot(filename, "overview")
    
    def _plot_price_series_overview(
        self,
        price_data: pd.DataFrame,
        title: str,
        save_dir: Path = None
    ) -> None:
        """Plot overview of price series."""
        
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
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'{title} Overview', fontsize=16)
        
        # Raw prices
        for col in valid_columns:
            clean_series = valid_data[col].dropna()
            if len(clean_series) > 10:  # Only plot if enough data
                axes[0, 0].plot(clean_series.index, clean_series.values, 
                               label=col.replace('BTC-USD_price', 'BTC').replace('ETH-USD_price', 'ETH')
                                    .replace('^GSPC', 'S&P500').replace('DX-Y.NYB', 'USD'), alpha=0.8)
        axes[0, 0].set_title('Price Levels')
        axes[0, 0].set_ylabel('Price')
        axes[0, 0].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Normalized prices (base = 100) - use first available value for each series
        normalized_data = pd.DataFrame(index=valid_data.index)
        for col in valid_columns:
            series = valid_data[col].dropna()
            if len(series) > 10 and series.iloc[0] > 0:  # Valid base value
                normalized_series = (series / series.iloc[0]) * 100
                normalized_data[col] = normalized_series
        
        if not normalized_data.empty:
            self._save_table(normalized_data, f"{clean_title}_normalized_prices", "overview")
            
            for col in normalized_data.columns:
                clean_series = normalized_data[col].dropna()
                if len(clean_series) > 10:
                    axes[0, 1].plot(clean_series.index, clean_series.values, 
                                   label=col.replace('BTC-USD_price', 'BTC').replace('ETH-USD_price', 'ETH')
                                        .replace('^GSPC', 'S&P500').replace('DX-Y.NYB', 'USD'), alpha=0.8)
        axes[0, 1].set_title('Normalized Prices (Base = 100)')
        axes[0, 1].set_ylabel('Normalized Price')
        axes[0, 1].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Returns - calculate for each valid column
        returns_data = pd.DataFrame(index=valid_data.index)
        for col in valid_columns:
            series = valid_data[col].dropna()
            if len(series) > 10:
                returns = series.pct_change().dropna()
                # Remove extreme outliers (>20% daily change - likely data errors)
                returns = returns[np.abs(returns) < 0.20]
                returns_data[col] = returns
        
        if not returns_data.empty:
            self._save_table(returns_data, f"{clean_title}_daily_returns", "overview")
            
            for col in returns_data.columns:
                clean_series = returns_data[col].dropna()
                if len(clean_series) > 10:
                    axes[1, 0].plot(clean_series.index, clean_series.values * 100, 
                                   label=col.replace('BTC-USD_price', 'BTC').replace('ETH-USD_price', 'ETH')
                                        .replace('^GSPC', 'S&P500').replace('DX-Y.NYB', 'USD'), alpha=0.7)
        axes[1, 0].set_title('Daily Returns (%)')
        axes[1, 0].set_ylabel('Return (%)')
        axes[1, 0].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Rolling volatility
        rolling_vol_data = pd.DataFrame(index=returns_data.index)
        for col in returns_data.columns:
            clean_series = returns_data[col].dropna()
            if len(clean_series) > 30:  # Need at least 30 observations for rolling window
                rolling_vol = clean_series.rolling(window=30).std() * np.sqrt(252) * 100
                rolling_vol_data[col] = rolling_vol
        
        if not rolling_vol_data.empty:
            self._save_table(rolling_vol_data, f"{clean_title}_rolling_volatility", "overview")
            
            for col in rolling_vol_data.columns:
                clean_series = rolling_vol_data[col].dropna()
                if len(clean_series) > 10:
                    axes[1, 1].plot(clean_series.index, clean_series.values, 
                                   label=col.replace('BTC-USD_price', 'BTC').replace('ETH-USD_price', 'ETH')
                                        .replace('^GSPC', 'S&P500').replace('DX-Y.NYB', 'USD'), alpha=0.8)
        axes[1, 1].set_title('30-Day Rolling Volatility (Annualized %)')
        axes[1, 1].set_ylabel('Volatility (%)')
        axes[1, 1].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        filename = f"{clean_title}_overview"
        self._save_plot(filename, "overview")
    
    def _plot_economic_indicators_overview(
        self,
        econ_data: pd.DataFrame,
        save_dir: Path = None
    ) -> None:
        """Plot overview of economic indicators."""
        
        if econ_data.empty:
            return
        
        # Save economic indicators data
        self._save_table(econ_data, "economic_indicators_raw", "overview")
        
        n_indicators = len(econ_data.columns)
        cols = min(3, n_indicators)
        rows = (n_indicators + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 4*rows))
        if n_indicators == 1:
            axes = [axes]
        elif rows == 1:
            axes = [axes]
        else:
            axes = axes.flatten()
        
        fig.suptitle('Economic Indicators Overview', fontsize=16)
        
        for i, col in enumerate(econ_data.columns):
            if i < len(axes):
                ax = axes[i]
                
                data_series = econ_data[col].dropna()
                ax.plot(data_series.index, data_series, linewidth=2, color='darkblue')
                ax.set_title(col)
                ax.set_ylabel('Value')
                ax.grid(True, alpha=0.3)
                
                # Add trend line
                if len(data_series) > 10:
                    z = np.polyfit(range(len(data_series)), data_series.values, 1)
                    p = np.poly1d(z)
                    ax.plot(data_series.index, p(range(len(data_series))), 
                           "r--", alpha=0.6, label='Trend')
                    ax.legend()
        
        # Hide unused subplots
        for i in range(n_indicators, len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        
        # Save plot
        filename = "economic_indicators_overview"
        self._save_plot(filename, "overview")
    
    def _plot_summary_statistics_table(
        self,
        data: pd.DataFrame,
        save_dir: Path = None
    ) -> None:
        """Create and plot summary statistics table."""
        
        # Calculate summary statistics
        summary_stats = data.describe()
        
        # Select key statistics
        key_stats = summary_stats.loc[['count', 'mean', 'std', 'min', 'max']]
        
        # Save table data as CSV
        self._save_table(key_stats, "summary_statistics", "overview")
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.axis('tight')
        ax.axis('off')
        
        # Create table
        table_data = key_stats.round(4)
        table = ax.table(cellText=table_data.values,
                        rowLabels=table_data.index,
                        colLabels=[col[:15] + '...' if len(col) > 15 else col for col in table_data.columns],
                        cellLoc='center',
                        loc='center')
        
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 1.5)
        
        # Style the table
        for i in range(len(table_data.columns)):
            table[(0, i)].set_facecolor('#40466e')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        for i in range(len(table_data.index)):
            table[(i+1, -1)].set_facecolor('#f1f1f2')
            table[(i+1, -1)].set_text_props(weight='bold')
        
        ax.set_title('Summary Statistics', fontsize=16, fontweight='bold', pad=20)
        
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
        """Plot average cumulative abnormal returns."""
        
        if average_cars is None or average_cars.empty:
            self.logger.warning("No average CARs data to plot")
            return
        
        # Save CARs data as CSV
        self._save_table(average_cars, "average_cumulative_abnormal_returns", "event_study")
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Average Cumulative Abnormal Returns Around Announcements', fontsize=16)
        
        # Identify asset types more flexibly
        crypto_cols = [col for col in average_cars.columns if any(crypto in col.upper() for crypto in ['BTC', 'ETH', 'BNB', 'ADA', 'SOL'])]
        stock_cols = [col for col in average_cars.columns if any(stock in col.upper() for stock in ['GSPC', 'VIX', 'TNX', 'DX-Y'])]
        
        # If no clear separation, treat all columns as general assets
        if not crypto_cols and not stock_cols:
            all_cols = average_cars.columns.tolist()
            crypto_cols = all_cols[:len(all_cols)//2]  # First half as "crypto"
            stock_cols = all_cols[len(all_cols)//2:]   # Second half as "stocks"
        
        # Plot crypto CARs
        if crypto_cols:
            for col in crypto_cols:
                clean_data = average_cars[col].dropna()
                if not clean_data.empty:
                    axes[0, 0].plot(clean_data.index, clean_data.values, 
                                   label=col.replace('BTC-USD_price', 'BTC').replace('ETH-USD_price', 'ETH')
                                       .replace('BNB-USD_price', 'BNB').replace('ADA-USD_price', 'ADA')
                                       .replace('SOL-USD_price', 'SOL'), linewidth=2)
            axes[0, 0].set_title('Cryptocurrency CARs')
            axes[0, 0].set_xlabel('Days from Announcement')
            axes[0, 0].set_ylabel('Cumulative Abnormal Return')
            axes[0, 0].axhline(y=0, color='black', linestyle='--', alpha=0.5)
            axes[0, 0].axvline(x=0, color='red', linestyle='-', alpha=0.7, label='Announcement')
            axes[0, 0].legend()
            axes[0, 0].grid(True, alpha=0.3)
        else:
            axes[0, 0].text(0.5, 0.5, 'No cryptocurrency data available', 
                           ha='center', va='center', transform=axes[0, 0].transAxes)
        
        # Plot stock CARs
        if stock_cols:
            for col in stock_cols:
                clean_data = average_cars[col].dropna()
                if not clean_data.empty:
                    axes[0, 1].plot(clean_data.index, clean_data.values, 
                                   label=col.replace('^GSPC', 'S&P500').replace('^VIX', 'VIX')
                                       .replace('^TNX', '10Y Treasury').replace('DX-Y.NYB', 'USD Index'), linewidth=2)
            axes[0, 1].set_title('Stock Market CARs')
            axes[0, 1].set_xlabel('Days from Announcement')
            axes[0, 1].set_ylabel('Cumulative Abnormal Return')
            axes[0, 1].axhline(y=0, color='black', linestyle='--', alpha=0.5)
            axes[0, 1].axvline(x=0, color='red', linestyle='-', alpha=0.7, label='Announcement')
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3)
        else:
            axes[0, 1].text(0.5, 0.5, 'No stock market data available', 
                           ha='center', va='center', transform=axes[0, 1].transAxes)
        
        # Comparison plot
        if crypto_cols and stock_cols:
            # Average across crypto and stocks (only non-null values)
            crypto_avg = average_cars[crypto_cols].mean(axis=1, skipna=True)
            stock_avg = average_cars[stock_cols].mean(axis=1, skipna=True)
            
            if not crypto_avg.empty:
                axes[1, 0].plot(crypto_avg.index, crypto_avg.values, 
                               label='Cryptocurrency Average', linewidth=3, color='orange')
            if not stock_avg.empty:
                axes[1, 0].plot(stock_avg.index, stock_avg.values, 
                               label='Stock Market Average', linewidth=3, color='blue')
            axes[1, 0].set_title('Crypto vs Stock Market Comparison')
            axes[1, 0].set_xlabel('Days from Announcement')
            axes[1, 0].set_ylabel('Average Cumulative Abnormal Return')
            axes[1, 0].axhline(y=0, color='black', linestyle='--', alpha=0.5)
            axes[1, 0].axvline(x=0, color='red', linestyle='-', alpha=0.7, label='Announcement')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
        else:
            # Plot all assets together if no clear separation
            for col in average_cars.columns:
                clean_data = average_cars[col].dropna()
                if not clean_data.empty:
                    axes[1, 0].plot(clean_data.index, clean_data.values, label=col[:15], linewidth=2)
            axes[1, 0].set_title('All Assets CARs')
            axes[1, 0].set_xlabel('Days from Announcement')
            axes[1, 0].set_ylabel('Cumulative Abnormal Return')
            axes[1, 0].axhline(y=0, color='black', linestyle='--', alpha=0.5)
            axes[1, 0].axvline(x=0, color='red', linestyle='-', alpha=0.7, label='Announcement')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
        
        # Distribution of final CARs
        if len(average_cars) > 0:
            final_cars = average_cars.iloc[-1].dropna()
            if not final_cars.empty:
                axes[1, 1].bar(range(len(final_cars)), final_cars.values)
                axes[1, 1].set_title('Final CARs by Asset')
                axes[1, 1].set_xlabel('Assets')
                axes[1, 1].set_ylabel('Final CAR')
                axes[1, 1].set_xticks(range(len(final_cars)))
                # Clean up labels
                labels = []
                for col in final_cars.index:
                    if 'BTC' in col:
                        labels.append('BTC')
                    elif 'ETH' in col:
                        labels.append('ETH')
                    elif 'GSPC' in col:
                        labels.append('S&P500')
                    elif 'DX-Y' in col:
                        labels.append('USD')
                    else:
                        labels.append(col[:8])
                axes[1, 1].set_xticklabels(labels, rotation=45)
                axes[1, 1].axhline(y=0, color='black', linestyle='--', alpha=0.5)
                axes[1, 1].grid(True, alpha=0.3)
            else:
                axes[1, 1].text(0.5, 0.5, 'No final CAR data available', 
                               ha='center', va='center', transform=axes[1, 1].transAxes)
        else:
            axes[1, 1].text(0.5, 0.5, 'No CAR data available', 
                           ha='center', va='center', transform=axes[1, 1].transAxes)
        
        plt.tight_layout()
        
        # Save plot
        filename = "average_cumulative_abnormal_returns"
        self._save_plot(filename, "event_study")
    
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
        """Plot event study summary statistics."""
        
        if not summary_stats:
            return
        
        # Convert to DataFrame for easier plotting
        stats_df = pd.DataFrame(summary_stats).T
        
        if stats_df.empty:
            return
        
        # Save summary statistics as CSV
        self._save_table(stats_df, "event_study_summary_statistics", "event_study")
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Event Study Summary Statistics', fontsize=16)
        
        # Mean CARs
        if 'mean_car' in stats_df.columns:
            assets = stats_df.index
            mean_cars = stats_df['mean_car']
            colors = ['orange' if 'crypto' in asset.lower() else 'blue' for asset in assets]
            
            axes[0, 0].bar(range(len(mean_cars)), mean_cars, color=colors)
            axes[0, 0].set_title('Mean Cumulative Abnormal Returns')
            axes[0, 0].set_ylabel('Mean CAR')
            axes[0, 0].set_xticks(range(len(assets)))
            axes[0, 0].set_xticklabels([asset.replace('crypto_', 'C-').replace('stock_', 'S-') 
                                       for asset in assets], rotation=45)
            axes[0, 0].axhline(y=0, color='black', linestyle='--', alpha=0.5)
            axes[0, 0].grid(True, alpha=0.3)
        
        # Standard deviations
        if 'std_car' in stats_df.columns:
            std_cars = stats_df['std_car']
            axes[0, 1].bar(range(len(std_cars)), std_cars, color=colors)
            axes[0, 1].set_title('Standard Deviation of CARs')
            axes[0, 1].set_ylabel('Std Dev')
            axes[0, 1].set_xticks(range(len(assets)))
            axes[0, 1].set_xticklabels([asset.replace('crypto_', 'C-').replace('stock_', 'S-') 
                                       for asset in assets], rotation=45)
            axes[0, 1].grid(True, alpha=0.3)
        
        # Positive vs negative events
        if 'positive_events' in stats_df.columns and 'negative_events' in stats_df.columns:
            pos_events = stats_df['positive_events']
            neg_events = stats_df['negative_events']
            
            x = np.arange(len(assets))
            width = 0.35
            
            axes[1, 0].bar(x - width/2, pos_events, width, label='Positive', color='green', alpha=0.7)
            axes[1, 0].bar(x + width/2, neg_events, width, label='Negative', color='red', alpha=0.7)
            axes[1, 0].set_title('Number of Positive vs Negative Events')
            axes[1, 0].set_ylabel('Number of Events')
            axes[1, 0].set_xticks(x)
            axes[1, 0].set_xticklabels([asset.replace('crypto_', 'C-').replace('stock_', 'S-') 
                                       for asset in assets], rotation=45)
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
        
        # Min and Max CARs
        if 'min_car' in stats_df.columns and 'max_car' in stats_df.columns:
            min_cars = stats_df['min_car']
            max_cars = stats_df['max_car']
            
            axes[1, 1].scatter(min_cars, max_cars, c=colors, s=100, alpha=0.7)
            axes[1, 1].set_xlabel('Minimum CAR')
            axes[1, 1].set_ylabel('Maximum CAR')
            axes[1, 1].set_title('Range of CARs (Min vs Max)')
            axes[1, 1].axhline(y=0, color='black', linestyle='--', alpha=0.5)
            axes[1, 1].axvline(x=0, color='black', linestyle='--', alpha=0.5)
            axes[1, 1].grid(True, alpha=0.3)
            
            # Add asset labels
            for i, asset in enumerate(assets):
                axes[1, 1].annotate(asset.replace('crypto_', 'C-').replace('stock_', 'S-'),
                                   (min_cars.iloc[i], max_cars.iloc[i]),
                                   xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        plt.tight_layout()
        
        # Save plot
        filename = "event_study_summary_statistics"
        self._save_plot(filename, "event_study")
    
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
        """Plot regression coefficients comparison."""
        
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
        
        # Create coefficient comparison plot
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Regression Coefficients: Response to Surprises', fontsize=16)
        
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
        
        # Plot coefficients
        axes[0].bar(range(len(surprise_coeffs)), surprise_coeffs, color=colors)
        axes[0].set_title('Surprise Coefficients')
        axes[0].set_ylabel('Coefficient Value')
        axes[0].set_xticks(range(len(assets)))
        axes[0].set_xticklabels([asset.replace('crypto_', 'C-').replace('stock_', 'S-') 
                                for asset in assets], rotation=45)
        axes[0].axhline(y=0, color='black', linestyle='--', alpha=0.5)
        axes[0].grid(True, alpha=0.3)
        
        # Add significance legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='red', label='p < 0.05'),
            Patch(facecolor='orange', label='p < 0.10'), 
            Patch(facecolor='gray', label='p ≥ 0.10')
        ]
        axes[0].legend(handles=legend_elements)
        
        # Plot p-values
        axes[1].bar(range(len(surprise_pvals)), surprise_pvals, color=colors)
        axes[1].set_title('P-values')
        axes[1].set_ylabel('P-value')
        axes[1].set_xticks(range(len(assets)))
        axes[1].set_xticklabels([asset.replace('crypto_', 'C-').replace('stock_', 'S-') 
                                for asset in assets], rotation=45)
        axes[1].axhline(y=0.05, color='red', linestyle='--', alpha=0.7, label='p = 0.05')
        axes[1].axhline(y=0.10, color='orange', linestyle='--', alpha=0.7, label='p = 0.10')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        filename = "regression_coefficients"
        self._save_plot(filename, "regression")
    
    def _plot_regression_r_squared(
        self,
        regression_results: Dict,
        save_dir: Path = None
    ) -> None:
        """Plot R-squared comparison across assets."""
        
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
        
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Model Fit: R-squared Values', fontsize=16)
        
        # Return regression R-squared
        if r_squared_return:
            assets = list(r_squared_return.keys())
            r2_values = list(r_squared_return.values())
            colors = ['orange' if 'crypto' in asset.lower() else 'blue' for asset in assets]
            
            axes[0].bar(range(len(r2_values)), r2_values, color=colors)
            axes[0].set_title('Return Regressions')
            axes[0].set_ylabel('R-squared')
            axes[0].set_xticks(range(len(assets)))
            axes[0].set_xticklabels([asset.replace('crypto_', 'C-').replace('stock_', 'S-') 
                                    for asset in assets], rotation=45)
            axes[0].set_ylim(0, max(r2_values) * 1.1)
            axes[0].grid(True, alpha=0.3)
        
        # Volatility regression R-squared
        if r_squared_vol:
            assets = list(r_squared_vol.keys())
            r2_values = list(r_squared_vol.values())
            colors = ['orange' if 'crypto' in asset.lower() else 'blue' for asset in assets]
            
            axes[1].bar(range(len(r2_values)), r2_values, color=colors)
            axes[1].set_title('Volatility Regressions')
            axes[1].set_ylabel('R-squared')
            axes[1].set_xticks(range(len(assets)))
            axes[1].set_xticklabels([asset.replace('crypto_', 'C-').replace('stock_', 'S-') 
                                    for asset in assets], rotation=45)
            axes[1].set_ylim(0, max(r2_values) * 1.1)
            axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        filename = "regression_r_squared"
        self._save_plot(filename, "regression")
    
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
        """Plot price evolution over time."""
        
        fig, axes = plt.subplots(len(data_dict), 1, figsize=(15, 6*len(data_dict)))
        if len(data_dict) == 1:
            axes = [axes]
        
        fig.suptitle('Price Evolution Over Time', fontsize=16)
        
        # Store normalized data for all categories
        all_normalized_data = pd.DataFrame()
        
        for i, (category, data) in enumerate(data_dict.items()):
            ax = axes[i]
            
            # Normalize prices to start at 100 for comparison
            normalized_data = data.div(data.iloc[0]) * 100
            
            # Add category prefix to column names and combine
            prefixed_data = normalized_data.add_prefix(f"{category}_")
            all_normalized_data = all_normalized_data.join(prefixed_data, how='outer')
            
            for col in normalized_data.columns:
                ax.plot(normalized_data.index, normalized_data[col], label=col, linewidth=2)
            
            ax.set_title(f'{category.title()} Price Evolution (Normalized)')
            ax.set_ylabel('Normalized Price (Base = 100)')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.grid(True, alpha=0.3)
        
        # Save normalized price data as CSV
        if not all_normalized_data.empty:
            self._save_table(all_normalized_data, "normalized_price_evolution", "summary")
        
        plt.tight_layout()
        
        # Save plot
        filename = "price_evolution"
        self._save_plot(filename, "summary")
    
    def _plot_volatility_comparison(
        self,
        data_dict: Dict[str, pd.DataFrame],
        save_dir: Path = None
    ) -> None:
        """Plot volatility comparison."""
        
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
        
        # Save volatility data as CSV
        if not all_volatility_data.empty:
            self._save_table(all_volatility_data, "rolling_volatility_30d", "summary")
        
        # Plot
        fig, axes = plt.subplots(len(volatilities), 1, figsize=(15, 6*len(volatilities)))
        if len(volatilities) == 1:
            axes = [axes]
        
        fig.suptitle('30-Day Rolling Volatility (Annualized %)', fontsize=16)
        
        for i, (category, vol_data) in enumerate(volatilities.items()):
            ax = axes[i]
            
            for col in vol_data.columns:
                ax.plot(vol_data.index, vol_data[col], label=col, linewidth=2)
            
            ax.set_title(f'{category.title()} Volatility')
            ax.set_ylabel('Volatility (%)')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        filename = "volatility_comparison"
        self._save_plot(filename, "summary")
    
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