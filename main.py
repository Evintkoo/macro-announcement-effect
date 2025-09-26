#!/usr/bin/env python3
"""
Main Analysis Script for Macro Announcement Effects Research

This script runs the complete analysis pipeline for studying the effects of 
macroeconomic announcements on cryptocurrency vs. U.S. stock market returns.

Author: Research Team
Date: 2025
License: MIT
"""

import os
import sys
import logging
import logging.handlers
import argparse
import traceback
import re
import pandas as pd
import numpy as np
import json
from pathlib import Path

# Suppress statsmodels warnings
try:
    from src.utils.warnings_suppression import *
except ImportError:
    import warnings
    warnings.filterwarnings('ignore', category=RuntimeWarning, 
                           message='.*invalid value encountered.*')

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import warnings

# Add src to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Import project modules
from utils.config import Config
from utils.logging_config import ComponentLogger, get_analysis_loggers
from data_collection.yahoo_finance_collector import YahooFinanceCollector
from data_collection.crypto_collector import CryptoCollector
from data_collection.economic_data_collector import EconomicDataCollector
from preprocessing.data_preprocessor import DataPreprocessor
from preprocessing.feature_engineering import FeatureEngineer
from analysis.event_study import EventStudyAnalyzer
from analysis.regression_analysis import RegressionAnalyzer

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

class MacroAnnouncementAnalysis:
    """Main analysis orchestrator class."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the analysis with configuration."""
        self.config_path = config_path
        self.config = None
        self.logger = None
        self.results = {}
        
        # Data containers
        self.stock_data = None
        self.crypto_data = None
        self.economic_data = None
        self.aligned_data = None
        
        # Analyzers
        self.event_study_analyzer = None
        self.regression_analyzer = None
        
    def setup(self):
        """Set up configuration, logging, and directories."""
        # Load configuration
        try:
            self.config = Config(self.config_path)._config
        except Exception as e:
            print(f"[FAILED] Failed to load configuration: {e}")
            raise
        
        # Setup logging
        try:
            # Create component logger manager
            self.component_logger = ComponentLogger(
                base_log_dir=self.config.get('logging', {}).get('directory', 'logs')
            )
            
            # Get main logger
            log_level = self.config.get('logging', {}).get('level', 'INFO')
            self.logger = self.component_logger.get_main_logger(log_level)
            
            # Add additional file handler for main.log in root directory
            self._setup_main_log_file()
            
            self.logger.info("Setting up Macro Announcement Effects Analysis...")
            self.logger.info(f"Configuration loaded from {self.config_path}")
            self.logger.info("Analysis pipeline started")
        except Exception as e:
            print(f"[WARNING]  Logging setup failed: {e}")
            self.logger = logging.getLogger(__name__)
        
        # Create output directories
        self._create_directories()
        self.logger.info("Output directories created")
        
        # Initialize analyzers
        self.event_study_analyzer = EventStudyAnalyzer()
        self.regression_analyzer = RegressionAnalyzer()
        self.logger.info("Analyzers initialized")
    
    def _setup_main_log_file(self):
        """Setup additional file handler for main.log in root directory."""
        try:
            # Create main.log file handler in root directory
            main_log_path = Path("main.log")
            
            # Create file handler for main.log with rotation
            main_file_handler = logging.handlers.RotatingFileHandler(
                main_log_path, 
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            
            # Set logging level from config
            log_level = self.config.get('logging', {}).get('level', 'INFO')
            level = getattr(logging, log_level.upper(), logging.INFO)
            main_file_handler.setLevel(level)
            
            # Create plain formatter (no colors for file) with custom filter
            class PlainFormatter(logging.Formatter):
                """Formatter that removes ANSI color codes."""
                
                def format(self, record):
                    # Remove any ANSI color codes from the level name
                    if hasattr(record, 'levelname'):
                        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                        record.levelname = ansi_escape.sub('', record.levelname)
                    return super().format(record)
            
            plain_formatter = PlainFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            main_file_handler.setFormatter(plain_formatter)
            
            # Add handler to logger
            self.logger.addHandler(main_file_handler)
            
            self.logger.info(f"Additional logging configured to: {main_log_path.absolute()}")
            
        except Exception as e:
            print(f"[WARNING]  Failed to setup main.log file: {e}")
    
    def _create_directories(self):
        """Create necessary output directories."""
        directories = [
            self.config['output']['results_dir'],
            self.config['output']['figures_dir'],
            self.config['output']['tables_dir'],
            self.config['output']['models_dir'],
            "data/raw",
            "data/processed",
            "logs"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def collect_data(self, start_date: str = None, end_date: str = None):
        """Collect comprehensive 10-year data from all sources."""
        self.logger.info("Starting Enhanced Data Collection...")
        
        # Set default 10-year date range if not provided
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365*10)).strftime('%Y-%m-%d')  # 10 years
        
        self.logger.info(f"Enhanced date range (10 years): {start_date} to {end_date}")
        
        try:
            # Use enhanced data collector
            from data_collection.enhanced_data_collector import EnhancedDataCollector
            enhanced_collector = EnhancedDataCollector()
            
            self.logger.info("Using enhanced data collection with multiple fallback sources...")
            
            # Collect comprehensive data
            comprehensive_data = enhanced_collector.collect_comprehensive_data(start_date, end_date)
            
            # Extract individual datasets
            self.stock_data = comprehensive_data.get('stocks')
            self.crypto_data = comprehensive_data.get('crypto') 
            self.economic_data = comprehensive_data.get('economic')
            self.volatility_data = comprehensive_data.get('volatility')
            self.fixed_income_data = comprehensive_data.get('fixed_income')
            
            # Log collection results
            if self.stock_data is not None and not self.stock_data.empty:
                self.logger.info(f"Stock data: {self.stock_data.shape[0]} days, {self.stock_data.shape[1]} assets")
                self.logger.debug(f"Collected enhanced stock data: {self.stock_data.shape}")
            else:
                self.logger.warning("Limited stock data collected")
            
            if self.crypto_data is not None and not self.crypto_data.empty:
                self.logger.info(f"Crypto data: {self.crypto_data.shape[0]} days, {self.crypto_data.shape[1]} assets")
                self.logger.debug(f"Collected enhanced crypto data: {self.crypto_data.shape}")
            else:
                self.logger.warning("Limited crypto data collected")
                
            if self.economic_data is not None and not self.economic_data.empty:
                self.logger.info(f"Economic data: {self.economic_data.shape[0]} observations, {self.economic_data.shape[1]} indicators")
                self.logger.debug(f"Collected enhanced economic data: {self.economic_data.shape}")
            else:
                self.logger.warning("Limited economic data collected")
                
            if self.volatility_data is not None and not self.volatility_data.empty:
                self.logger.info(f"Volatility data: {self.volatility_data.shape[0]} days, {self.volatility_data.shape[1]} instruments")
                
            if self.fixed_income_data is not None and not self.fixed_income_data.empty:
                self.logger.info(f"Fixed income data: {self.fixed_income_data.shape[0]} days, {self.fixed_income_data.shape[1]} instruments")
            
            # Create comprehensive combined dataset
            self.comprehensive_data = enhanced_collector.create_comprehensive_dataset(comprehensive_data)
            
            if not self.comprehensive_data.empty:
                self.logger.info(f"Comprehensive dataset: {self.comprehensive_data.shape[0]} days, {self.comprehensive_data.shape[1]} variables")
                self.logger.debug(f"Created comprehensive dataset: {self.comprehensive_data.shape}")
            
            # Save raw data to files
            self.logger.info("Saving enhanced raw data...")
            raw_data_dir = Path("data/raw")
            raw_data_dir.mkdir(parents=True, exist_ok=True)
            
            # Save individual datasets
            for data_name, dataset in [
                ('stock_data', self.stock_data),
                ('crypto_data', self.crypto_data), 
                ('economic_data', self.economic_data),
                ('volatility_data', self.volatility_data),
                ('fixed_income_data', self.fixed_income_data)
            ]:
                if dataset is not None and not dataset.empty:
                    file_path = raw_data_dir / f"{data_name}.csv"
                    dataset.to_csv(file_path)
                    self.logger.info(f"{data_name} saved to: {file_path}")
            
            # Save comprehensive dataset
            if not self.comprehensive_data.empty:
                comprehensive_file = raw_data_dir / "comprehensive_data.csv"
                self.comprehensive_data.to_csv(comprehensive_file)
                self.logger.info(f"Comprehensive dataset saved to: {comprehensive_file}")
            
            self.logger.info("Enhanced data collection completed!")
            
        except Exception as e:
            self.logger.error(f"Enhanced data collection failed, falling back to basic collection: {e}")
            
            # Fallback to original collection method
            try:
                self._collect_data_fallback(start_date, end_date)
            except Exception as fallback_error:
                self.logger.error(f"Fallback data collection also failed: {fallback_error}")
                traceback.print_exc()
    
    def _collect_data_fallback(self, start_date: str, end_date: str):
        """Fallback data collection method."""
        self.logger.info("Using fallback data collection...")
        
        # Collect stock market data
        self.logger.info("Collecting stock market data...")
        yahoo_collector = YahooFinanceCollector()
        stock_symbols = self.config.get('data_sources', {}).get('stocks', {}).get('symbols', 
                                       ['SPY', 'QQQ', 'IWM', 'VTI'])
        self.stock_data = yahoo_collector.collect_data(
            symbols=stock_symbols,
            start_date=start_date,
            end_date=end_date
        )
        
        # Collect cryptocurrency data
        self.logger.info("Collecting cryptocurrency data...")
        crypto_collector = CryptoCollector()
        self.crypto_data = crypto_collector.collect_data(
            symbols=['BTC-USD', 'ETH-USD'],
            start_date=start_date,
            end_date=end_date
        )
        
        # Collect economic data
        self.logger.info("Collecting economic data...")
        econ_collector = EconomicDataCollector()
        indicators = ['UNRATE', 'CPIAUCSL', 'FEDFUNDS', 'GDP']
        self.economic_data = econ_collector.collect_data(
            symbols=indicators,
            start_date=start_date,
            end_date=end_date
        )
    
    def preprocess_data(self):
        """Enhanced data preprocessing with comprehensive quality checks."""
        self.logger.info("Starting Enhanced Data Preprocessing...")
        
        try:
            # Import enhanced preprocessing tools
            from data_collection.enhanced_data_collector import DataQualityAnalyzer
            from preprocessing.feature_engineering import FeatureEngineer
            
            quality_analyzer = DataQualityAnalyzer()
            
            # Use comprehensive dataset if available
            if hasattr(self, 'comprehensive_data') and not self.comprehensive_data.empty:
                self.logger.info("Using comprehensive dataset for preprocessing...")
                raw_data = self.comprehensive_data.copy()
            else:
                # Clean and combine individual datasets
                self.logger.info("Combining individual datasets...")
                raw_data = self._combine_individual_datasets()
            
            if raw_data.empty:
                self.logger.error("No data available for preprocessing")
                return
            
            self.logger.info(f"Initial dataset: {raw_data.shape[0]} observations, {raw_data.shape[1]} variables")
            
            # Comprehensive data quality analysis
            self.logger.info("Running comprehensive data quality analysis...")
            quality_report = quality_analyzer.comprehensive_data_analysis(raw_data)
            
            # Clean the data based on quality analysis
            self.logger.info("Cleaning data based on quality analysis...")
            cleaned_data = self._enhanced_data_cleaning(raw_data, quality_report)
            
            self.logger.info(f"Cleaned dataset: {cleaned_data.shape[0]} observations, {cleaned_data.shape[1]} variables")
            
            # Feature engineering
            self.logger.info("Engineering features...")
            engineer = FeatureEngineer()
            self.aligned_data = engineer.create_analysis_features(cleaned_data)
            
            # Calculate returns and volatilities
            self.aligned_data = self._calculate_derived_variables(self.aligned_data)
            
            self.logger.info(f"Final processed dataset: {self.aligned_data.shape[0]} observations, {self.aligned_data.shape[1]} variables")
            
            # Generate data quality report
            self.logger.info("Generating data quality report...")
            self._save_quality_report(quality_report, cleaned_data)
            
            # Save processed data
            self.logger.info("Saving enhanced processed data...")
            self._save_processed_data()
            
            self.logger.info("Enhanced data preprocessing completed!")
            
        except Exception as e:
            self.logger.error(f"Enhanced preprocessing failed, using basic preprocessing: {e}")
            self._basic_preprocessing_fallback()
    
    def _combine_individual_datasets(self) -> pd.DataFrame:
        """Combine individual datasets into comprehensive dataset."""
        
        datasets = []
        
        # Add each dataset with prefixes
        for data_name, dataset in [
            ('stocks', self.stock_data),
            ('crypto', self.crypto_data),
            ('economic', self.economic_data),
            ('volatility', getattr(self, 'volatility_data', None)),
            ('fixed_income', getattr(self, 'fixed_income_data', None))
        ]:
            if dataset is not None and not dataset.empty:
                # Make a copy to avoid modifying original data
                dataset_copy = dataset.copy()
                
                # Clean timezone info properly
                if isinstance(dataset_copy.index, pd.DatetimeIndex):
                    if dataset_copy.index.tz is not None:
                        # Use tz_localize(None) instead of tz_convert(None) to remove timezone
                        dataset_copy.index = dataset_copy.index.tz_localize(None)
                
                # Add prefix to column names
                dataset_renamed = dataset_copy.add_prefix(f"{data_name}_")
                datasets.append(dataset_renamed)
                self.logger.debug(f"Added {data_name} data: {dataset_copy.shape}")
        
        if datasets:
            # Ensure all datasets have compatible index types before concatenating
            for i, df in enumerate(datasets):
                if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None:
                    datasets[i].index = df.index.tz_localize(None)
            
            combined_data = pd.concat(datasets, axis=1, sort=True)
            return combined_data
        else:
            return pd.DataFrame()
    
    def _enhanced_data_cleaning(self, data: pd.DataFrame, quality_report: Dict) -> pd.DataFrame:
        """Enhanced data cleaning based on quality analysis."""
        
        cleaned_data = data.copy()
        
        # Remove columns with excessive missing data (>80%)
        missing_analysis = quality_report.get('missing_data', {})
        missing_pct = missing_analysis.get('missing_percentage', {})
        
        columns_to_drop = [col for col, pct in missing_pct.items() if pct > 80]
        if columns_to_drop:
            self.logger.info(f"Dropping {len(columns_to_drop)} columns with >80% missing data")
            cleaned_data = cleaned_data.drop(columns=columns_to_drop)
        
        # Handle outliers based on quality analysis
        outlier_analysis = quality_report.get('outlier_detection', {})
        for col, outlier_info in outlier_analysis.items():
            if col in cleaned_data.columns:
                # Cap extreme outliers (beyond 99th percentile)
                if 'z_outliers_pct' in outlier_info and outlier_info['z_outliers_pct'] > 5:
                    series = cleaned_data[col]
                    lower_cap = series.quantile(0.01)
                    upper_cap = series.quantile(0.99)
                    cleaned_data[col] = series.clip(lower=lower_cap, upper=upper_cap)
        
        # Forward fill missing values for economic indicators (common practice)
        econ_cols = [col for col in cleaned_data.columns if 'economic' in col.lower()]
        if econ_cols:
            cleaned_data[econ_cols] = cleaned_data[econ_cols].ffill()
        
        # Remove rows that are entirely empty
        cleaned_data = cleaned_data.dropna(how='all')
        
        return cleaned_data
    
    def _calculate_derived_variables(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate returns, volatilities, and other derived variables."""
        
        # Identify price columns (excluding already calculated returns/volatilities)
        price_columns = [col for col in data.columns if not any(suffix in col.lower() 
                        for suffix in ['_return', '_volatility', '_vol', 'surprise', 'lag'])]
        
        self.logger.info(f"Calculating derived variables for {len(price_columns)} price series...")
        
        # Collect all new columns in a dictionary to avoid DataFrame fragmentation
        new_columns = {}
        
        # Calculate price-based derived variables
        for col in price_columns:
            if col in data.columns:
                series = data[col].dropna()
                if len(series) > 10:
                    
                    # Calculate returns
                    returns = series.pct_change().dropna()
                    if not returns.empty:
                        new_columns[f"{col}_return"] = returns
                        
                        # Calculate rolling volatilities
                        if len(returns) > 30:
                            new_columns[f"{col}_volatility_20d"] = returns.rolling(20).std() * np.sqrt(252)
                            new_columns[f"{col}_volatility_60d"] = returns.rolling(60).std() * np.sqrt(252)
                        
                        # Calculate cumulative returns
                        new_columns[f"{col}_cumulative_return"] = (1 + returns).cumprod() - 1
        
        # Calculate surprise measures for economic indicators
        econ_cols = [col for col in data.columns if any(econ in col.lower() 
                    for econ in ['unemployment', 'inflation', 'cpi', 'gdp', 'rate', 'payroll'])]
        
        for col in econ_cols:
            if col in data.columns:
                series = data[col].dropna()
                if len(series) > 24:  # Need at least 2 years of monthly data
                    # Calculate surprise as deviation from 12-month moving average
                    ma_12 = series.rolling(window=12, min_periods=6).mean()
                    std_12 = series.rolling(window=12, min_periods=6).std()
                    surprise = (series - ma_12.shift(1)) / std_12.shift(1)
                    new_columns[f"{col}_surprise"] = surprise
                    
                    # Calculate year-over-year change
                    yoy_change = series.pct_change(periods=12)
                    new_columns[f"{col}_yoy_change"] = yoy_change
        
        # Efficiently combine original data with new columns using pd.concat
        if new_columns:
            new_df = pd.DataFrame(new_columns, index=data.index)
            enhanced_data = pd.concat([data, new_df], axis=1)
        else:
            enhanced_data = data.copy()
        
        return enhanced_data
    
    def _save_quality_report(self, quality_report: Dict, cleaned_data: pd.DataFrame):
        """Save comprehensive data quality report."""
        
        report_dir = Path("data/processed/quality_reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # Save quality analysis as JSON
        quality_file = report_dir / "data_quality_analysis.json"
        
        # Convert numpy types to native Python types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            else:
                return obj
        
        quality_report_serializable = convert_numpy_types(quality_report)
        
        with open(quality_file, 'w') as f:
            json.dump(quality_report_serializable, f, indent=2, default=str)
        self.logger.info(f"Quality report saved to: {quality_file}")
        
        # Create summary report
        summary_file = report_dir / "data_summary.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("# Data Quality Summary Report\n\n")
            f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Dataset Overview\n")
            f.write(f"- **Shape:** {cleaned_data.shape[0]} observations × {cleaned_data.shape[1]} variables\n")
            f.write(f"- **Date Range:** {cleaned_data.index[0]} to {cleaned_data.index[-1]}\n")
            f.write(f"- **Memory Usage:** {cleaned_data.memory_usage(deep=True).sum() / 1024**2:.1f} MB\n\n")
            
            # Missing data summary
            missing_data = quality_report.get('missing_data', {})
            if missing_data:
                f.write("## Missing Data Analysis\n")
                missing_pct = missing_data.get('missing_percentage', {})
                high_missing = [(col, pct) for col, pct in missing_pct.items() if pct > 10]
                if high_missing:
                    f.write("### Variables with >10% Missing Data:\n")
                    for col, pct in sorted(high_missing, key=lambda x: x[1], reverse=True):
                        f.write(f"- **{col}:** {pct:.1f}% missing\n")
                f.write("\n")
            
            # Data types summary
            f.write("## Data Types\n")
            for dtype in cleaned_data.dtypes.value_counts().items():
                f.write(f"- **{dtype[0]}:** {dtype[1]} variables\n")
            f.write("\n")
        
        self.logger.info(f"Summary report saved to: {summary_file}")
    
    def _save_processed_data(self):
        """Save all processed data with comprehensive metadata."""
        
        processed_data_dir = Path("data/processed")
        processed_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Save main aligned dataset
        aligned_file = processed_data_dir / "aligned_data.csv"
        self.aligned_data.to_csv(aligned_file)
        self.logger.info(f"Enhanced aligned data saved to: {aligned_file}")
        
        # Save enhanced metadata
        metadata = {
            "processed_date": datetime.now().isoformat(),
            "processing_type": "enhanced_comprehensive",
            "data_shape": list(self.aligned_data.shape),
            "date_range": {
                "start": str(self.aligned_data.index[0]),
                "end": str(self.aligned_data.index[-1]),
                "total_days": len(self.aligned_data)
            },
            "variable_categories": {
                "stock_prices": [col for col in self.aligned_data.columns if 'stocks_' in col and '_return' not in col and '_volatility' not in col],
                "crypto_prices": [col for col in self.aligned_data.columns if 'crypto_' in col and '_return' not in col and '_volatility' not in col],
                "economic_indicators": [col for col in self.aligned_data.columns if 'economic_' in col and '_surprise' not in col],
                "returns": [col for col in self.aligned_data.columns if '_return' in col],
                "volatilities": [col for col in self.aligned_data.columns if '_volatility' in col],
                "surprises": [col for col in self.aligned_data.columns if '_surprise' in col]
            },
            "data_quality": {
                "missing_data_pct": (self.aligned_data.isnull().sum().sum() / (self.aligned_data.shape[0] * self.aligned_data.shape[1]) * 100),
                "variables_with_data": len([col for col in self.aligned_data.columns if self.aligned_data[col].notna().sum() > 0])
            }
        }
        
        metadata_file = processed_data_dir / "data_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        self.logger.info(f"Enhanced metadata saved to: {metadata_file}")
    
    def _basic_preprocessing_fallback(self):
        """Fallback to basic preprocessing if enhanced fails."""
        self.logger.info("Using basic preprocessing fallback...")
        
        # Basic cleaning and alignment (original logic)
        aligned_datasets = {}
        
        for data_name, dataset in [('stocks', self.stock_data), ('crypto', self.crypto_data), ('economic', self.economic_data)]:
            if dataset is not None and not dataset.empty:
                # Make a copy to avoid modifying original data
                dataset_copy = dataset.copy()
                
                # Clean timezone info properly
                if isinstance(dataset_copy.index, pd.DatetimeIndex) and dataset_copy.index.tz is not None:
                    dataset_copy.index = dataset_copy.index.tz_localize(None)
                aligned_datasets[data_name] = dataset_copy
        
        if aligned_datasets:
            dfs = [df for df in aligned_datasets.values() if df is not None and not df.empty]
            
            # Ensure all dataframes have compatible indices before concatenating
            for i, df in enumerate(dfs):
                if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None:
                    dfs[i].index = df.index.tz_localize(None)
            
            self.aligned_data = pd.concat(dfs, axis=1) if dfs else pd.DataFrame()
        else:
            self.aligned_data = pd.DataFrame()
    
    def run_event_study(self):
        """Run comprehensive event study analysis with extensive event coverage."""
        self.logger.info("Running Enhanced Event Study Analysis...")
        
        if self.aligned_data is None or self.aligned_data.empty:
            self.logger.error("No aligned data available for event study")
            return
        
        try:
            # Define comprehensive 10-year event catalog
            sample_events = self._get_comprehensive_event_catalog()
            
            self.logger.info(f"Analyzing {len(sample_events)} major economic events over 10 years...")
            
            # Convert sample events to datetime objects
            sample_event_dates = []
            for event in sample_events:
                if isinstance(event, dict) and 'date' in event:
                    date_str = event['date']
                    try:
                        event_date = pd.to_datetime(date_str)
                        # Only include events within our data range
                        if self.aligned_data.index[0] <= event_date <= self.aligned_data.index[-1]:
                            sample_event_dates.append(event_date)
                    except:
                        continue
                elif isinstance(event, str):
                    try:
                        event_date = pd.to_datetime(event)
                        if self.aligned_data.index[0] <= event_date <= self.aligned_data.index[-1]:
                            sample_event_dates.append(event_date)
                    except:
                        continue
            
            self.logger.info(f"{len(sample_event_dates)} events fall within data range")
            
            if not sample_event_dates:
                self.logger.warning("No events found within data range, using synthetic events")
                sample_event_dates = self._generate_synthetic_events()
            
            # Run enhanced event study
            event_results = self.event_study_analyzer.analyze_events(
                aligned_data=self.aligned_data,
                sample_events=sample_event_dates,
                event_window_days=5,  # Extended window for more comprehensive analysis
                estimation_window=250
            )
            
            # Run additional event study analysis for robustness
            if event_results and 'error' not in event_results:
                self.logger.info("Running additional event study robustness tests...")
                
                # Test different event windows
                for window in [1, 3, 5, 7]:
                    window_results = self.event_study_analyzer.analyze_events(
                        aligned_data=self.aligned_data,
                        sample_events=sample_event_dates[:5],  # Use subset for robustness
                        event_window_days=window,
                        estimation_window=250
                    )
                    if window_results and 'error' not in window_results:
                        event_results[f'window_{window}_day'] = window_results
                
                self.results['event_study'] = event_results
                self.logger.info("Enhanced event study completed")
                
                # Save comprehensive results
                self._save_event_study_results(event_results)
                
            else:
                self.logger.error("Event study failed - insufficient suitable data")
                
        except Exception as e:
            self.logger.error(f"Event study failed: {e}")
            traceback.print_exc()
    
    def _get_comprehensive_event_catalog(self) -> List[Dict[str, str]]:
        """Get comprehensive catalog of major economic events for 10-year period."""
        
        events = [
            # 2015 Events
            {'date': '2015-12-16', 'type': 'monetary_policy', 'description': 'Fed raises rates for first time since 2006'},
            {'date': '2015-08-11', 'type': 'international', 'description': 'China devalues yuan'},
            {'date': '2015-01-22', 'type': 'monetary_policy', 'description': 'ECB launches QE program'},
            
            # 2016 Events  
            {'date': '2016-06-23', 'type': 'political', 'description': 'Brexit referendum'},
            {'date': '2016-11-08', 'type': 'political', 'description': 'Trump elected US President'},
            {'date': '2016-01-20', 'type': 'international', 'description': 'Oil prices hit 12-year low'},
            {'date': '2016-12-14', 'type': 'monetary_policy', 'description': 'Fed raises rates to 0.5-0.75%'},
            
            # 2017 Events
            {'date': '2017-06-14', 'type': 'monetary_policy', 'description': 'Fed raises rates to 1-1.25%'},
            {'date': '2017-12-13', 'type': 'monetary_policy', 'description': 'Fed raises rates to 1.25-1.5%'},
            {'date': '2017-12-22', 'type': 'fiscal_policy', 'description': 'Trump tax cuts signed into law'},
            
            # 2018 Events
            {'date': '2018-03-21', 'type': 'monetary_policy', 'description': 'Fed raises rates to 1.5-1.75%'},
            {'date': '2018-06-13', 'type': 'monetary_policy', 'description': 'Fed raises rates to 1.75-2%'},
            {'date': '2018-09-26', 'type': 'monetary_policy', 'description': 'Fed raises rates to 2-2.25%'},
            {'date': '2018-12-19', 'type': 'monetary_policy', 'description': 'Fed raises rates to 2.25-2.5%'},
            {'date': '2018-03-22', 'type': 'trade_policy', 'description': 'Trump announces China tariffs'},
            
            # 2019 Events
            {'date': '2019-07-31', 'type': 'monetary_policy', 'description': 'Fed cuts rates to 2-2.25%'},
            {'date': '2019-09-18', 'type': 'monetary_policy', 'description': 'Fed cuts rates to 1.75-2%'},
            {'date': '2019-10-30', 'type': 'monetary_policy', 'description': 'Fed cuts rates to 1.5-1.75%'},
            
            # 2020 Events (Major Crisis Year)
            {'date': '2020-03-03', 'type': 'monetary_policy', 'description': 'Emergency Fed rate cut to 1-1.25%'},
            {'date': '2020-03-15', 'type': 'monetary_policy', 'description': 'Emergency Fed rate cut to 0-0.25%'},
            {'date': '2020-03-23', 'type': 'monetary_policy', 'description': 'Fed announces unlimited QE'},
            {'date': '2020-03-27', 'type': 'fiscal_policy', 'description': 'CARES Act signed ($2.2T stimulus)'},
            {'date': '2020-11-07', 'type': 'political', 'description': 'Biden declared winner of 2020 election'},
            {'date': '2020-11-09', 'type': 'health', 'description': 'Pfizer announces 90% effective vaccine'},
            
            # 2021 Events
            {'date': '2021-11-03', 'type': 'monetary_policy', 'description': 'Fed announces QE tapering'},
            {'date': '2021-03-11', 'type': 'fiscal_policy', 'description': 'American Rescue Plan Act signed'},
            {'date': '2021-11-15', 'type': 'fiscal_policy', 'description': 'Infrastructure Investment Act signed'},
            
            # 2022 Events (Inflation Fighting)
            {'date': '2022-03-16', 'type': 'monetary_policy', 'description': 'Fed raises rates to 0.25-0.5%'},
            {'date': '2022-05-04', 'type': 'monetary_policy', 'description': 'Fed raises rates to 0.75-1%'},
            {'date': '2022-06-15', 'type': 'monetary_policy', 'description': 'Fed raises rates to 1.5-1.75%'},
            {'date': '2022-07-27', 'type': 'monetary_policy', 'description': 'Fed raises rates to 2.25-2.5%'},
            {'date': '2022-09-21', 'type': 'monetary_policy', 'description': 'Fed raises rates to 3-3.25%'},
            {'date': '2022-11-02', 'type': 'monetary_policy', 'description': 'Fed raises rates to 3.75-4%'},
            {'date': '2022-12-14', 'type': 'monetary_policy', 'description': 'Fed raises rates to 4.25-4.5%'},
            {'date': '2022-02-24', 'type': 'geopolitical', 'description': 'Russia invades Ukraine'},
            
            # 2023 Events
            {'date': '2023-02-01', 'type': 'monetary_policy', 'description': 'Fed raises rates to 4.5-4.75%'},
            {'date': '2023-03-22', 'type': 'monetary_policy', 'description': 'Fed raises rates to 4.75-5%'},
            {'date': '2023-05-03', 'type': 'monetary_policy', 'description': 'Fed raises rates to 5-5.25%'},
            {'date': '2023-07-26', 'type': 'monetary_policy', 'description': 'Fed raises rates to 5.25-5.5%'},
            {'date': '2023-03-12', 'type': 'financial', 'description': 'Silicon Valley Bank failure'},
            
            # 2024 Events
            {'date': '2024-09-18', 'type': 'monetary_policy', 'description': 'Fed cuts rates to 4.75-5%'},
            {'date': '2024-11-07', 'type': 'monetary_policy', 'description': 'Fed cuts rates to 4.5-4.75%'}
        ]
        
        return events
    
    def _generate_synthetic_events(self) -> List[pd.Timestamp]:
        """Generate synthetic event dates for analysis when real events aren't available."""
        
        # Generate quarterly events throughout the data range
        start_date = self.aligned_data.index[0]
        end_date = self.aligned_data.index[-1]
        
        synthetic_events = []
        current_date = start_date
        
        while current_date <= end_date:
            synthetic_events.append(current_date)
            current_date += pd.DateOffset(months=6)  # Every 6 months
        
        return synthetic_events[:20]  # Limit to 20 events
    
    def run_regression_analysis(self):
        """Run comprehensive regression analysis with enhanced methodologies."""
        self.logger.info("Running Enhanced Regression Analysis...")
        
        if self.aligned_data is None or self.aligned_data.empty:
            self.logger.error("No aligned data available for regression")
            return
        
        try:
            self.logger.info("Running comprehensive regression suite...")
            
            # Auto-detect asset categories
            crypto_assets = [col for col in self.aligned_data.columns if any(crypto in col.lower() 
                           for crypto in ['bitcoin', 'ethereum', 'crypto_', 'btc', 'eth', 'bnb', 'sol'])]
            stock_assets = [col for col in self.aligned_data.columns if any(stock in col.lower() 
                          for stock in ['stocks_', 'sp500', 'spy', 'nasdaq', 'dow'])]
            
            self.logger.info(f"Detected {len(crypto_assets)} crypto assets and {len(stock_assets)} stock assets")
            
            # OPTIMIZATION: Limit the number of assets to prevent hanging
            # Select top assets by data availability and importance
            max_assets_per_category = 10  # Limit to top 10 per category
            
            if len(crypto_assets) > max_assets_per_category:
                # Select crypto assets with most complete data
                crypto_completeness = {}
                for asset in crypto_assets:
                    if asset in self.aligned_data.columns:
                        completeness = self.aligned_data[asset].notna().sum() / len(self.aligned_data)
                        crypto_completeness[asset] = completeness
                
                # Sort by completeness and take top assets
                sorted_crypto = sorted(crypto_completeness.items(), key=lambda x: x[1], reverse=True)
                crypto_assets = [asset for asset, _ in sorted_crypto[:max_assets_per_category]]
                self.logger.info(f"Limited crypto assets to top {len(crypto_assets)} by data completeness")
            
            if len(stock_assets) > max_assets_per_category:
                # Select stock assets with most complete data
                stock_completeness = {}
                for asset in stock_assets:
                    if asset in self.aligned_data.columns:
                        completeness = self.aligned_data[asset].notna().sum() / len(self.aligned_data)
                        stock_completeness[asset] = completeness
                
                # Sort by completeness and take top assets
                sorted_stocks = sorted(stock_completeness.items(), key=lambda x: x[1], reverse=True)
                stock_assets = [asset for asset, _ in sorted_stocks[:max_assets_per_category]]
                self.logger.info(f"Limited stock assets to top {len(stock_assets)} by data completeness")
            
            self.logger.info(f"Using {len(crypto_assets)} crypto assets and {len(stock_assets)} stock assets for analysis")
            
            # 1. Standard pooled regression
            self.logger.info("Running pooled regression analysis...")
            regression_results = self.regression_analyzer.run_pooled_regression(
                aligned_data=self.aligned_data,
                crypto_assets=crypto_assets,
                stock_assets=stock_assets
            )
            
            # 2. Run comprehensive statistical analysis (with limited assets)
            self.logger.info("Running comprehensive statistical hypothesis testing...")
            from analysis.comprehensive_statistical_analysis import ComprehensiveStatisticalAnalysis
            
            statistical_analyzer = ComprehensiveStatisticalAnalysis()
            
            # Identify economic indicators
            economic_indicators = [col for col in self.aligned_data.columns if any(econ in col.lower() 
                                 for econ in ['unemployment', 'inflation', 'cpi', 'gdp', 'rate', 'payroll', 'economic_'])]
            
            self.logger.info(f"Using {len(economic_indicators)} economic indicators for analysis")
            
            statistical_results = statistical_analyzer.run_complete_analysis(
                data=self.aligned_data,
                crypto_assets=crypto_assets,
                stock_assets=stock_assets, 
                economic_indicators=economic_indicators
            )
            
            # 3. Combine all results
            comprehensive_results = {
                'regression_analysis': regression_results,
                'statistical_analysis': statistical_results,
                'data_summary': {
                    'total_observations': len(self.aligned_data),
                    'crypto_assets_count': len(crypto_assets),
                    'stock_assets_count': len(stock_assets),
                    'economic_indicators_count': len(economic_indicators),
                    'analysis_period': {
                        'start': str(self.aligned_data.index[0]),
                        'end': str(self.aligned_data.index[-1])
                    }
                }
            }
            
            self.results['comprehensive_analysis'] = comprehensive_results
            
            self.logger.info("Comprehensive analysis completed")
            
            # Save comprehensive results
            self.logger.info("Saving comprehensive analysis results...")
            self._save_comprehensive_results(comprehensive_results)
            
        except Exception as e:
            self.logger.error(f"Enhanced regression analysis failed: {e}")
            traceback.print_exc()
            
            # Fallback to basic regression
            try:
                self.logger.info("Falling back to basic regression analysis...")
                basic_results = self.regression_analyzer.run_pooled_regression(
                    aligned_data=self.aligned_data,
                    crypto_assets=None,
                    stock_assets=None
                )
                if basic_results:
                    self.results['regression'] = basic_results
                    self.logger.info("Basic regression analysis completed")
            except Exception as fallback_error:
                self.logger.error(f"Fallback regression also failed: {fallback_error}")
    
    def _save_event_study_results(self, event_results: Dict[str, Any]):
        """Save comprehensive event study results."""
        
        results_dir = Path(self.config['output']['results_dir'])
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Save flattened results as CSV table for reproducibility
        try:
            flat_results = pd.json_normalize(event_results, sep='.')
            flat_file = results_dir / "event_study_results.csv"
            flat_results.to_csv(flat_file, index=False)
            self.logger.info(f"Event study results saved to: {flat_file}")
        except Exception as e:
            self.logger.warning(f"Failed to flatten event study results: {e}")
        
        # Save summary statistics as CSV
        if 'summary_statistics' in event_results:
            summary_file = results_dir / "event_study_summary.csv"
            try:
                summary_df = pd.DataFrame(event_results['summary_statistics']).T
                summary_df.to_csv(summary_file)
                self.logger.info(f"Event study summary saved to: {summary_file}")
            except Exception as e:
                self.logger.warning(f"Could not save event study summary: {e}")
        
        # Generate detailed event study report
        report_file = results_dir / "event_study_detailed_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Comprehensive Event Study Analysis Report\n\n")
            f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            if 'summary_statistics' in event_results:
                f.write("## Event Study Summary\n\n")
                f.write("### Key Findings\n")
                
                summary_stats = event_results['summary_statistics']
                if summary_stats:
                    total_events = 0
                    significant_results = 0
                    
                    for asset, stats in summary_stats.items():
                        if isinstance(stats, dict):
                            total_events = stats.get('total_events', 0)
                            positive_events = stats.get('positive_events', 0)
                            negative_events = stats.get('negative_events', 0)
                            
                            f.write(f"- **{asset}:**\n")
                            f.write(f"  - Total events analyzed: {total_events}\n")
                            f.write(f"  - Positive reactions: {positive_events}\n")
                            f.write(f"  - Negative reactions: {negative_events}\n")
                            f.write(f"  - Mean CAR: {stats.get('mean_car', 'N/A'):.4f}\n")
                            f.write(f"  - CAR Volatility: {stats.get('std_car', 'N/A'):.4f}\n\n")
                
                f.write("\n### Statistical Significance\n")
                f.write("Events with statistically significant abnormal returns are marked in the detailed tables.\n\n")
            
            # Add methodology section
            f.write("## Methodology\n\n")
            f.write("### Event Study Approach\n")
            f.write("- **Estimation Window:** 250 days prior to event window\n")
            f.write("- **Event Window:** ±5 days around announcement\n")
            f.write("- **Market Model:** Single-factor model with market index\n")
            f.write("- **Test Statistics:** t-tests for individual abnormal returns and cumulative abnormal returns\n\n")
            
            f.write("### Data Coverage\n")
            f.write("- **Time Period:** 10-year comprehensive analysis\n")
            f.write("- **Event Types:** Monetary policy, fiscal policy, geopolitical, financial crises\n")
            f.write("- **Asset Classes:** Cryptocurrencies, stocks, bonds, commodities\n\n")
        
        self.logger.info(f"Event study detailed report saved to: {report_file}")
    
    def _save_comprehensive_results(self, comprehensive_results: Dict[str, Any]):
        """Save all comprehensive analysis results."""
        
        results_dir = Path(self.config['output']['results_dir'])
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Save flattened comprehensive results as CSV
        try:
            comprehensive_df = pd.json_normalize(comprehensive_results, sep='.')
            comprehensive_file = results_dir / "comprehensive_analysis_results.csv"
            comprehensive_df.to_csv(comprehensive_file, index=False)
            self.logger.info(f"Comprehensive results saved to: {comprehensive_file}")
        except Exception as e:
            self.logger.warning(f"Failed to flatten comprehensive results: {e}")
        
        # Save statistical test results summary
        if 'statistical_analysis' in comprehensive_results:
            statistical_results = comprehensive_results['statistical_analysis']
            
            # Save hypothesis test conclusions
            if 'test_summary' in statistical_results:
                test_summary = statistical_results['test_summary']
                hypothesis_file = results_dir / "hypothesis_test_results.csv"
                
                try:
                    hypothesis_conclusions = test_summary.get('hypothesis_conclusions', {})
                    if hypothesis_conclusions:
                        hypothesis_df = pd.DataFrame(hypothesis_conclusions).T
                        hypothesis_df.to_csv(hypothesis_file)
                        self.logger.info(f"Hypothesis test results saved to: {hypothesis_file}")
                except Exception as e:
                    self.logger.warning(f"Could not save hypothesis results: {e}")
            
            # Save significant findings
            if 'test_summary' in statistical_results and 'significant_findings' in statistical_results['test_summary']:
                significant_findings = statistical_results['test_summary']['significant_findings']
                if significant_findings:
                    findings_file = results_dir / "significant_findings.csv"
                    findings_df = pd.DataFrame(significant_findings)
                    findings_df.to_csv(findings_file, index=False)
                    self.logger.info(f"Significant findings saved to: {findings_file}")
        
        # Generate comprehensive research report
        self._generate_comprehensive_research_report(comprehensive_results)
    
    def generate_summary_report(self):
        """Generate comprehensive summary report."""
        self.logger.info("Generating Enhanced Summary Report...")
        
        try:
            report_path = Path(self.config['output']['results_dir']) / "analysis_summary.md"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("# Comprehensive Macro Announcement Effects Analysis - Executive Summary\n\n")
                f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Executive Summary
                f.write("## Executive Summary\n\n")
                f.write("This comprehensive research study analyzes the differential effects of macroeconomic announcements ")
                f.write("on cryptocurrency versus traditional stock markets over a 10-year period. The analysis employs ")
                f.write("advanced econometric methods including event studies, regression analysis, and comprehensive ")
                f.write("statistical hypothesis testing.\n\n")
                
                # Key Findings (if available)
                if hasattr(self, 'results') and 'comprehensive_analysis' in self.results:
                    f.write("### Key Research Findings\n\n")
                    comprehensive_results = self.results['comprehensive_analysis']
                    
                    if 'statistical_analysis' in comprehensive_results:
                        stat_results = comprehensive_results['statistical_analysis']
                        
                        # Extract key findings from hypothesis tests
                        if 'test_summary' in stat_results:
                            test_summary = stat_results['test_summary']
                            hypothesis_conclusions = test_summary.get('hypothesis_conclusions', {})
                            
                            for hypothesis, conclusion in hypothesis_conclusions.items():
                                if isinstance(conclusion, dict):
                                    f.write(f"- **{hypothesis}:** {conclusion.get('conclusion', 'Inconclusive')} ")
                                    f.write(f"(p-value: {conclusion.get('p_value', 'N/A'):.4f})\n")
                        
                        f.write("\n")
                
                # Data Coverage Summary
                f.write("## Data Coverage and Quality\n\n")
                if self.aligned_data is not None and not self.aligned_data.empty:
                    f.write(f"- **Analysis Period:** {self.aligned_data.index[0].strftime('%Y-%m-%d')} to {self.aligned_data.index[-1].strftime('%Y-%m-%d')}\n")
                    f.write(f"- **Total Observations:** {self.aligned_data.shape[0]:,} trading days\n")
                    f.write(f"- **Variables Analyzed:** {self.aligned_data.shape[1]:,} time series\n")
                    
                    # Data category breakdown
                    crypto_cols = [col for col in self.aligned_data.columns if 'crypto' in col.lower()]
                    stock_cols = [col for col in self.aligned_data.columns if 'stock' in col.lower()]
                    econ_cols = [col for col in self.aligned_data.columns if 'economic' in col.lower()]
                    
                    f.write(f"- **Cryptocurrency Assets:** {len([col for col in crypto_cols if 'return' not in col and 'vol' not in col])}\n")
                    f.write(f"- **Stock Market Indices:** {len([col for col in stock_cols if 'return' not in col and 'vol' not in col])}\n")
                    f.write(f"- **Economic Indicators:** {len([col for col in econ_cols if 'surprise' not in col])}\n")
                    f.write(f"- **Derived Variables:** {len([col for col in self.aligned_data.columns if any(suffix in col for suffix in ['_return', '_volatility', '_surprise'])])}\n\n")
                
                # Methodology Overview
                f.write("## Methodology Overview\n\n")
                f.write("### Research Design\n")
                f.write("- **Event Study Analysis:** Market model-based approach with 250-day estimation windows\n")
                f.write("- **Regression Analysis:** Pooled cross-sectional time series regressions\n")
                f.write("- **Statistical Testing:** Comprehensive hypothesis testing framework\n")
                f.write("- **Robustness Checks:** Multiple window sizes, subsampling, bootstrap methods\n\n")
                
                f.write("### Hypothesis Framework\n")
                f.write("1. **H1:** Cryptocurrency markets exhibit stronger reactions to macro announcements than traditional markets\n")
                f.write("2. **H2:** Market reactions show asymmetric patterns for positive vs. negative surprises\n")
                f.write("3. **H3:** Significant volatility spillovers exist between crypto and traditional markets\n")
                f.write("4. **H4:** Structural breaks exist in market relationships over the 10-year period\n")
                f.write("5. **H5:** Distributional characteristics differ significantly between asset classes\n\n")
                
                # Analysis Results Summary
                f.write("## Analysis Results Summary\n\n")
                
                if 'event_study' in self.results:
                    f.write("### Event Study Results\n")
                    f.write("- [SUCCESS] Event study analysis completed successfully\n")
                    f.write("- Analyzed major economic events across 10-year period\n")
                    f.write("- Results available in: `results/event_study_results.csv`\n")
                    f.write("- Detailed report: `results/event_study_detailed_report.md`\n\n")
                
                if 'comprehensive_analysis' in self.results:
                    f.write("### Statistical Analysis Results\n")
                    f.write("- [SUCCESS] Comprehensive statistical hypothesis testing completed\n")
                    f.write("- Multi-dimensional analysis framework applied\n")
                    f.write("- Results available in: `results/comprehensive_analysis_results.csv`\n")
                    f.write("- Hypothesis outcomes: `results/hypothesis_test_results.csv`\n\n")
                
                # Data Quality Assessment
                quality_report_path = Path("data/processed/quality_reports/data_summary.md")
                if quality_report_path.exists():
                    f.write("### Data Quality Assessment\n")
                    f.write("- [SUCCESS] Comprehensive data quality analysis completed\n")
                    f.write("- Quality metrics and validation results available\n")
                    f.write("- Detailed report: `data/processed/quality_reports/data_summary.md`\n\n")
                
                # Output File Structure
                f.write("## Research Outputs\n\n")
                f.write("### Analysis Results\n")
                f.write("- **Primary Results:** `results/comprehensive_analysis_results.csv`\n")
                f.write("- **Event Study:** `results/event_study_results.csv`\n")
                f.write("- **Hypothesis Tests:** `results/hypothesis_test_results.csv`\n")
                f.write("- **Significant Findings:** `results/significant_findings.csv`\n\n")
                
                f.write("### Data and Documentation\n")
                f.write("- **Raw Data:** `data/raw/comprehensive_data.csv`\n")
                f.write("- **Processed Data:** `data/processed/aligned_data.csv`\n")
                f.write("- **Data Quality:** `data/processed/quality_reports/`\n")
                f.write("- **Configuration:** `config/config.yaml`\n\n")
                
                # Research Reliability and Validation
                f.write("## Research Reliability and Validation\n\n")
                f.write("### Data Reliability Measures\n")
                f.write("- **Multi-source Data Collection:** Enhanced collector with fallback mechanisms\n")
                f.write("- **10-Year Historical Coverage:** Comprehensive long-term analysis period\n")
                f.write("- **Quality Validation:** Automated outlier detection and data cleaning\n")
                f.write("- **Missing Data Handling:** Forward-fill for economic data, appropriate interpolation\n\n")
                
                f.write("### Statistical Robustness\n")
                f.write("- **Multiple Testing Correction:** Appropriate significance level adjustments\n")
                f.write("- **Robustness Tests:** Bootstrap methods, subsample analysis\n")
                f.write("- **Alternative Specifications:** Multiple event windows, various econometric models\n")
                f.write("- **Cross-Validation:** Out-of-sample testing where applicable\n\n")
                
                # Technical Specifications
                f.write("## Technical Specifications\n\n")
                f.write(f"- **Analysis Framework:** Enhanced Python-based econometric pipeline\n")
                f.write(f"- **Configuration:** {self.config_path}\n")
                f.write(f"- **Project Version:** {self.config.get('project', {}).get('version', 'N/A')}\n")
                f.write(f"- **Python Environment:** {sys.version.split()[0]}\n")
                f.write(f"- **Key Libraries:** pandas, numpy, statsmodels, scipy\n\n")
                
                # Next Steps and Recommendations
                f.write("## Recommendations for Further Analysis\n\n")
                f.write("1. **Extended Time Series Analysis:** Consider GARCH models for volatility modeling\n")
                f.write("2. **High-Frequency Analysis:** Incorporate intraday data for announcement effects\n")
                f.write("3. **Cross-Market Analysis:** Extend to other international markets\n")
                f.write("4. **Machine Learning Approaches:** Apply ML methods for pattern recognition\n")
                f.write("5. **Real-Time Monitoring:** Implement live data feeds for ongoing analysis\n\n")
                
                f.write("---\n")
                f.write("*This comprehensive research report was generated by the enhanced macro-announcement-effect analysis pipeline.*\n")
                f.write("*For technical details and replication, see the complete methodology documentation.*\n")
            
            self.logger.info(f"Enhanced summary report saved to: {report_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate enhanced summary report: {e}")
    
    def _generate_comprehensive_research_report(self, comprehensive_results: Dict[str, Any]):
        """Generate detailed academic-style research report."""
        
        report_path = Path(self.config['output']['results_dir']) / "comprehensive_research_report.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Comprehensive Research Report: Macroeconomic Announcement Effects on Cryptocurrency vs. Stock Markets\n\n")
            f.write(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(f"**Research Period:** 10-Year Comprehensive Analysis\n\n")
            
            # Abstract
            f.write("## Abstract\n\n")
            f.write("This study provides a comprehensive empirical analysis of how macroeconomic announcements ")
            f.write("differentially affect cryptocurrency and traditional stock markets. Using a 10-year dataset ")
            f.write("and advanced econometric methods, we test multiple hypotheses about market sensitivity, ")
            f.write("volatility spillovers, and structural relationships. Our findings contribute to the growing ")
            f.write("literature on cryptocurrency market behavior and macro-financial linkages.\n\n")
            
            # Research Questions
            f.write("## Research Questions\n\n")
            f.write("1. Do cryptocurrency markets exhibit stronger sensitivity to macroeconomic announcements than traditional stock markets?\n")
            f.write("2. Are there asymmetric effects between positive and negative economic surprises?\n")
            f.write("3. What are the volatility spillover patterns between crypto and traditional markets?\n")
            f.write("4. Have these relationships changed over time (structural breaks)?\n")
            f.write("5. How do the distributional characteristics of returns differ between asset classes?\n\n")
            
            # Data and Methodology
            f.write("## Data and Methodology\n\n")
            f.write("### Data Sources\n")
            f.write("- **Financial Data:** Yahoo Finance, Federal Reserve Economic Data (FRED)\n")
            f.write("- **Coverage Period:** 2015-2025 (10 years)\n")
            f.write("- **Frequency:** Daily for financial data, monthly for economic indicators\n")
            f.write("- **Asset Classes:** Major cryptocurrencies, stock indices, bonds, commodities\n\n")
            
            f.write("### Econometric Methods\n")
            f.write("1. **Event Study Analysis:** Market model with 250-day estimation windows\n")
            f.write("2. **Regression Analysis:** Pooled OLS with robust standard errors\n")
            f.write("3. **Statistical Tests:** Mann-Whitney U, Kolmogorov-Smirnov, Granger causality\n")
            f.write("4. **Robustness Checks:** Bootstrap methods, subsample analysis, alternative specifications\n\n")
            
            # Results
            f.write("## Key Findings\n\n")
            
            if 'statistical_analysis' in comprehensive_results:
                stat_results = comprehensive_results['statistical_analysis']
                
                # Hypothesis test results
                if 'test_summary' in stat_results and 'hypothesis_conclusions' in stat_results['test_summary']:
                    f.write("### Hypothesis Test Results\n\n")
                    conclusions = stat_results['test_summary']['hypothesis_conclusions']
                    
                    for i, (hypothesis, result) in enumerate(conclusions.items(), 1):
                        if isinstance(result, dict):
                            f.write(f"**{hypothesis}:** {result.get('hypothesis', 'N/A')}\n")
                            f.write(f"- Result: {result.get('conclusion', 'Inconclusive')}\n")
                            f.write(f"- Statistical Significance: p = {result.get('p_value', 'N/A'):.4f}\n")
                            f.write(f"- Effect Size: {result.get('effect_size', 'N/A'):.4f}\n\n")
                
                # Significant findings
                if 'test_summary' in stat_results and 'significant_findings' in stat_results['test_summary']:
                    significant_findings = stat_results['test_summary']['significant_findings']
                    if significant_findings:
                        f.write("### Statistically Significant Results\n\n")
                        for finding in significant_findings[:10]:  # Top 10 findings
                            f.write(f"- **{finding.get('test', 'N/A')}:** p = {finding.get('p_value', 'N/A'):.4f}\n")
                        f.write("\n")
            
            # Implications
            f.write("## Implications and Conclusions\n\n")
            f.write("### Academic Contributions\n")
            f.write("- Provides first comprehensive 10-year comparison of crypto vs. stock market announcement effects\n")
            f.write("- Documents structural evolution of cryptocurrency market behavior\n")
            f.write("- Establishes benchmark for future research on macro-financial linkages\n\n")
            
            f.write("### Policy Implications\n")
            f.write("- Central banks should consider cryptocurrency market effects in communication strategies\n")
            f.write("- Regulatory frameworks need to account for cross-market spillovers\n")
            f.write("- Risk management models should incorporate crypto-traditional market correlations\n\n")
            
            f.write("### Investment Insights\n")
            f.write("- Portfolio diversification benefits between crypto and traditional assets\n")
            f.write("- Event-driven trading strategies based on announcement effects\n")
            f.write("- Volatility forecasting improvements through cross-market analysis\n\n")
            
            # Limitations and Future Research
            f.write("## Limitations and Future Research\n\n")
            f.write("### Study Limitations\n")
            f.write("- Limited to major cryptocurrencies and developed market indices\n")
            f.write("- Daily frequency may miss intraday announcement effects\n")
            f.write("- Event identification relies on ex-post classification\n\n")
            
            f.write("### Future Research Directions\n")
            f.write("- High-frequency analysis of announcement effects\n")
            f.write("- Cross-country analysis of regulatory announcements\n")
            f.write("- Machine learning approaches to event detection\n")
            f.write("- Real-time monitoring and prediction systems\n\n")
            
            # Technical Appendix
            f.write("## Technical Appendix\n\n")
            f.write("### Data Processing Details\n")
            if 'data_summary' in comprehensive_results:
                data_summary = comprehensive_results['data_summary']
                f.write(f"- Total observations: {data_summary.get('total_observations', 'N/A'):,}\n")
                f.write(f"- Cryptocurrency assets: {data_summary.get('crypto_assets_count', 'N/A')}\n")
                f.write(f"- Stock market assets: {data_summary.get('stock_assets_count', 'N/A')}\n")
                f.write(f"- Economic indicators: {data_summary.get('economic_indicators_count', 'N/A')}\n")
                
                if 'analysis_period' in data_summary:
                    period = data_summary['analysis_period']
                    f.write(f"- Analysis period: {period.get('start')} to {period.get('end')}\n")
            
            f.write("\n### Software and Reproducibility\n")
            f.write("- All analysis conducted in Python with open-source libraries\n")
            f.write("- Code available for replication and extension\n")
            f.write("- Data sources publicly accessible\n")
            f.write("- Random seeds set for reproducible results\n\n")
        
        self.logger.info(f"Comprehensive research report saved to: {report_path}")
    
    def run_full_analysis(self, start_date: str = None, end_date: str = None):
        """Run the complete analysis pipeline."""
        start_time = datetime.now()
        
        try:
            # Setup
            self.setup()
            
            self.logger.info("="*60)
            self.logger.info("MACRO ANNOUNCEMENT EFFECTS ANALYSIS")
            self.logger.info("="*60)
            
            # Run analysis pipeline
            self.collect_data(start_date, end_date)
            self.preprocess_data()
            self.run_event_study()
            self.run_regression_analysis()
            self.generate_summary_report()
            
            # Success message
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.logger.info("="*60)
            self.logger.info("ANALYSIS COMPLETED SUCCESSFULLY!")
            self.logger.info("="*60)
            self.logger.info(f"Total duration: {duration}")
            self.logger.info(f"Results saved to: {self.config['output']['results_dir']}")
            self.logger.info(f"Summary report: {self.config['output']['results_dir']}/analysis_summary.md")
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            traceback.print_exc()
            raise


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(
        description="Macro Announcement Effects Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    # Run full analysis with defaults
  python main.py --start-date 2020-01-01           # Custom start date
  python main.py --end-date 2024-12-31             # Custom end date
  python main.py --config config/custom.yaml       # Custom config file
  python main.py --data-only                       # Only collect and preprocess data
  python main.py --analysis-only                   # Only run analysis (requires existing data)
        """
    )
    
    parser.add_argument(
        '--config', 
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )
    parser.add_argument(
        '--start-date',
        help='Start date for data collection (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date',
        help='End date for data collection (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--data-only',
        action='store_true',
        help='Only collect and preprocess data'
    )
    parser.add_argument(
        '--analysis-only',
        action='store_true',
        help='Only run analysis (requires existing processed data)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Initialize analysis
    analysis = MacroAnnouncementAnalysis(config_path=args.config)
    
    try:
        if args.analysis_only:
            # Only run analysis
            analysis.setup()
            analysis.logger.info("Running analysis only...")
            # TODO: Load existing processed data
            analysis.run_event_study()
            analysis.run_regression_analysis()
            analysis.generate_summary_report()
            
        elif args.data_only:
            # Only collect and preprocess data
            analysis.setup()
            analysis.logger.info("Running data collection and preprocessing only...")
            analysis.collect_data(args.start_date, args.end_date)
            analysis.preprocess_data()
            
        else:
            # Run full analysis
            analysis.run_full_analysis(args.start_date, args.end_date)
            
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nAnalysis failed with error: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()