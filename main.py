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
import argparse
import traceback
import pandas as pd
import json
import pickle
from pathlib import Path
from datetime import datetime, timedelta
import warnings

# Add src to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Import project modules
from utils.config import Config
from utils.helpers import setup_logging
from data_collection.yahoo_finance_collector import YahooFinanceCollector
from data_collection.crypto_collector import CryptoCollector
from data_collection.economic_data_collector import EconomicDataCollector
from preprocessing.data_preprocessor import DataPreprocessor
from preprocessing.feature_engineering import FeatureEngineer
from analysis.event_study import EventStudyAnalyzer
from analysis.regression_analysis import RegressionAnalyzer
from visualization.plot_generator import PlotGenerator

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
        self.plot_generator = None
        
    def setup(self):
        """Set up configuration, logging, and directories."""
        print("🚀 Setting up Macro Announcement Effects Analysis...")
        
        # Load configuration
        try:
            self.config = Config(self.config_path)._config
            print(f"✅ Configuration loaded from {self.config_path}")
        except Exception as e:
            print(f"❌ Failed to load configuration: {e}")
            raise
        
        # Setup logging
        try:
            log_level = self.config.get('logging', {}).get('level', 'INFO')
            log_file = self.config.get('logging', {}).get('file', 'logs/analysis.log')
            self.logger = setup_logging(log_level, log_file)
            self.logger.info("Analysis pipeline started")
            print("✅ Logging configured")
        except Exception as e:
            print(f"⚠️  Logging setup failed: {e}")
            self.logger = logging.getLogger(__name__)
        
        # Create output directories
        self._create_directories()
        print("✅ Output directories created")
        
        # Initialize analyzers
        self.event_study_analyzer = EventStudyAnalyzer()
        self.regression_analyzer = RegressionAnalyzer()
        self.plot_generator = PlotGenerator(
            figures_dir=self.config['output']['figures_dir'],
            tables_dir=self.config['output']['tables_dir']
        )
        print("✅ Analyzers initialized")
    
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
        """Collect data from all sources."""
        print("\n📊 Starting Data Collection...")
        
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365*4)).strftime('%Y-%m-%d')  # 4 years
        
        print(f"📅 Date range: {start_date} to {end_date}")
        
        try:
            # Collect stock market data
            print("📈 Collecting stock market data...")
            yahoo_collector = YahooFinanceCollector()
            stock_symbols = self.config.get('data_sources', {}).get('stocks', {}).get('symbols', 
                                           ['SPY', 'QQQ', 'IWM', 'VTI', 'VEA', 'VWO'])
            self.stock_data = yahoo_collector.collect_data(
                symbols=stock_symbols,
                start_date=start_date,
                end_date=end_date
            )
            if self.stock_data is not None:
                print(f"✅ Stock data: {self.stock_data.shape[0]} days, {self.stock_data.shape[1]} assets")
                self.logger.info(f"Collected stock data: {self.stock_data.shape}")
            else:
                print("⚠️  No stock data collected")
            
            # Collect cryptocurrency data
            print("🪙 Collecting cryptocurrency data...")
            crypto_collector = CryptoCollector()
            self.crypto_data = crypto_collector.collect_data(
                symbols=['BTC-USD', 'ETH-USD', 'BNB-USD', 'ADA-USD', 'SOL-USD'],
                start_date=start_date,
                end_date=end_date
            )
            if self.crypto_data is not None:
                print(f"✅ Crypto data: {self.crypto_data.shape[0]} days, {self.crypto_data.shape[1]} assets")
                self.logger.info(f"Collected crypto data: {self.crypto_data.shape}")
            else:
                print("⚠️  No crypto data collected")
            
            # Collect economic data
            print("📊 Collecting economic data...")
            econ_collector = EconomicDataCollector()
            indicators = []
            economic_indicators = self.config.get('economic_indicators', {})
            for category in economic_indicators.values():
                if isinstance(category, list):
                    indicators.extend(category)
            
            # Fallback to default indicators if none configured
            if not indicators:
                indicators = ['^VIX', '^TNX', 'DX-Y.NYB', 'GC=F', 'CL=F']
            
            self.economic_data = econ_collector.collect_data(
                symbols=indicators[:10],  # Limit to first 10 to avoid rate limits
                start_date=start_date,
                end_date=end_date
            )
            if self.economic_data is not None:
                print(f"✅ Economic data: {self.economic_data.shape[0]} observations, {self.economic_data.shape[1]} indicators")
                self.logger.info(f"Collected economic data: {self.economic_data.shape}")
            else:
                print("⚠️  No economic data collected")
            
            # Save raw data to files
            print("💾 Saving raw data...")
            raw_data_dir = Path("data/raw")
            raw_data_dir.mkdir(parents=True, exist_ok=True)
            
            if self.stock_data is not None:
                stock_file = raw_data_dir / "stock_data.csv"
                self.stock_data.to_csv(stock_file)
                print(f"✅ Stock data saved to: {stock_file}")
                
            if self.crypto_data is not None:
                crypto_file = raw_data_dir / "crypto_data.csv"
                self.crypto_data.to_csv(crypto_file)
                print(f"✅ Crypto data saved to: {crypto_file}")
                
            if self.economic_data is not None:
                economic_file = raw_data_dir / "economic_data.csv"
                self.economic_data.to_csv(economic_file)
                print(f"✅ Economic data saved to: {economic_file}")
            
            print("✅ Data collection completed!")
            
        except Exception as e:
            print(f"❌ Data collection failed: {e}")
            self.logger.error(f"Data collection error: {e}")
            traceback.print_exc()
    
    def preprocess_data(self):
        """Clean and align all collected data."""
        print("\n🔧 Starting Data Preprocessing...")
        
        try:
            # Clean individual datasets
            if self.stock_data is not None:
                print("🧹 Cleaning stock data...")
                preprocessor = DataPreprocessor()
                self.stock_data = preprocessor.clean_price_data(self.stock_data)
                # Ensure timezone consistency only for DatetimeIndex
                if isinstance(self.stock_data.index, pd.DatetimeIndex):
                    if self.stock_data.index.tz is not None:
                        self.stock_data.index = self.stock_data.index.tz_convert(None)
                # Drop if empty
                if self.stock_data is not None and self.stock_data.empty:
                    print("⚠️  Stock data is empty after cleaning; skipping.")
                    self.stock_data = None
                else:
                    print(f"✅ Stock data cleaned: {self.stock_data.shape}")
            
            if self.crypto_data is not None:
                print("🧹 Cleaning crypto data...")
                preprocessor = DataPreprocessor()
                self.crypto_data = preprocessor.clean_price_data(self.crypto_data)
                # Ensure timezone consistency only for DatetimeIndex
                if isinstance(self.crypto_data.index, pd.DatetimeIndex):
                    if self.crypto_data.index.tz is not None:
                        self.crypto_data.index = self.crypto_data.index.tz_convert(None)
                # Drop if empty
                if self.crypto_data is not None and self.crypto_data.empty:
                    print("⚠️  Crypto data is empty after cleaning; skipping.")
                    self.crypto_data = None
                else:
                    print(f"✅ Crypto data cleaned: {self.crypto_data.shape}")
            
            if self.economic_data is not None:
                print("🧹 Cleaning economic data...")
                preprocessor = DataPreprocessor()
                self.economic_data = preprocessor.clean_price_data(self.economic_data)
                # Ensure timezone consistency only for DatetimeIndex
                if isinstance(self.economic_data.index, pd.DatetimeIndex):
                    if self.economic_data.index.tz is not None:
                        self.economic_data.index = self.economic_data.index.tz_convert(None)
                # Drop if empty
                if self.economic_data is not None and self.economic_data.empty:
                    print("⚠️  Economic data is empty after cleaning; skipping.")
                    self.economic_data = None
                else:
                    print(f"✅ Economic data cleaned: {self.economic_data.shape}")
            
            # Align all datasets
            print("🔄 Aligning data frequencies...")
            engineer = FeatureEngineer()
            # Create a simple aligned dataset for now
            aligned_datasets = {}
            if self.stock_data is not None:
                aligned_datasets['stocks'] = self.stock_data
            if self.crypto_data is not None:
                aligned_datasets['crypto'] = self.crypto_data
            if self.economic_data is not None:
                aligned_datasets['economic'] = self.economic_data
                
            if aligned_datasets:
                # Ensure all datasets have consistent timezone-naive indices before concatenating
                for key, dataset in aligned_datasets.items():
                    if isinstance(dataset.index, pd.DatetimeIndex):
                        if dataset.index.tz is not None:
                            aligned_datasets[key].index = dataset.index.tz_convert(None)
                # Filter out empty datasets before concatenation
                dfs = [df for df in aligned_datasets.values() if df is not None and not df.empty]
                # For now, just concatenate the data if any non-empty
                self.aligned_data = pd.concat(dfs, axis=1) if dfs else None
            else:
                self.aligned_data = None
            
            if self.aligned_data is not None and not self.aligned_data.empty:
                print(f"✅ Data aligned: {self.aligned_data.shape}")
                self.logger.info(f"Data preprocessing completed: {self.aligned_data.shape}")
                
                # Save processed data
                print("💾 Saving processed data...")
                processed_data_dir = Path("data/processed")
                processed_data_dir.mkdir(parents=True, exist_ok=True)
                
                aligned_file = processed_data_dir / "aligned_data.csv"
                self.aligned_data.to_csv(aligned_file)
                print(f"✅ Aligned data saved to: {aligned_file}")
                
                # Save metadata about the data
                metadata_file = processed_data_dir / "data_metadata.json"
                metadata = {
                    "processed_date": datetime.now().isoformat(),
                    "data_shape": list(self.aligned_data.shape),
                    "date_range": (
                        {
                            "start": str(self.aligned_data.index[0]),
                            "end": str(self.aligned_data.index[-1])
                        }
                        if len(self.aligned_data.index) > 0 else None
                    ),
                    "columns": list(self.aligned_data.columns),
                    "stock_columns": [col for col in self.aligned_data.columns if any(symbol in col for symbol in ['^GSPC', '^VIX', '^TNX', 'DX-Y'])],
                    "crypto_columns": [col for col in self.aligned_data.columns if any(symbol in col for symbol in ['BTC', 'ETH'])],
                    "economic_columns": [col for col in self.aligned_data.columns if any(indicator in col for indicator in ['GC=F', 'CL=F'])]
                }
                
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                print(f"✅ Data metadata saved to: {metadata_file}")
            else:
                print("❌ Data alignment failed (no non-empty datasets to align)")
                
        except Exception as e:
            print(f"❌ Data preprocessing failed: {e}")
            self.logger.error(f"Data preprocessing error: {e}")
            traceback.print_exc()
    
    def run_event_study(self):
        """Run event study analysis."""
        print("\n📈 Running Event Study Analysis...")
        
        if self.aligned_data is None:
            print("❌ No aligned data available for event study")
            return
        
        try:
            # Define sample events (major Fed announcements)
            sample_events = [
                {'date': '2020-03-15', 'type': 'monetary_policy', 'description': 'Emergency rate cut'},
                {'date': '2020-03-23', 'type': 'monetary_policy', 'description': 'Unlimited QE announcement'},
                {'date': '2021-11-03', 'type': 'monetary_policy', 'description': 'QE tapering begins'},
                {'date': '2022-03-16', 'type': 'monetary_policy', 'description': 'First rate hike'},
                {'date': '2022-06-15', 'type': 'monetary_policy', 'description': '75bps rate hike'},
                {'date': '2022-11-02', 'type': 'monetary_policy', 'description': '75bps rate hike'},
                {'date': '2023-03-22', 'type': 'monetary_policy', 'description': '25bps rate hike'},
                {'date': '2023-05-03', 'type': 'monetary_policy', 'description': '25bps rate hike'},
            ]
            
            print(f"🎯 Analyzing {len(sample_events)} events...")
            
            # Run event study
            # Convert sample events to datetime objects
            sample_event_dates = []
            for event in sample_events:
                if isinstance(event, dict) and 'date' in event:
                    date_str = event['date']
                    sample_event_dates.append(pd.to_datetime(date_str))
                elif isinstance(event, str):
                    sample_event_dates.append(pd.to_datetime(event))
                else:
                    sample_event_dates.append(event)
            
            event_results = self.event_study_analyzer.analyze_events(
                aligned_data=self.aligned_data,
                sample_events=sample_event_dates,
                event_window_days=self.config['analysis']['event_windows']['daily']['pre_days'],
                estimation_window=250
            )
            
            if event_results is not None:
                self.results['event_study'] = event_results
                print("✅ Event study completed")
                self.logger.info("Event study analysis completed")
                
                # Save event study results
                print("💾 Saving event study results...")
                results_dir = Path(self.config['output']['results_dir'])
                results_dir.mkdir(parents=True, exist_ok=True)
                
                # Save results as pickle for full preservation
                event_study_file = results_dir / "event_study_results.pkl"
                with open(event_study_file, 'wb') as f:
                    pickle.dump(event_results, f)
                print(f"✅ Event study results saved to: {event_study_file}")
                
                # Save summary statistics as CSV
                if 'summary_statistics' in event_results:
                    summary_file = results_dir / "event_study_summary.csv"
                    summary_df = pd.DataFrame(event_results['summary_statistics']).T
                    summary_df.to_csv(summary_file)
                    print(f"✅ Event study summary saved to: {summary_file}")
                
                # Generate event study plots
                try:
                    self.plot_generator.plot_event_study_results(event_results)
                    print("✅ Event study plots generated")
                except Exception as plot_error:
                    print(f"⚠️  Event study plots failed: {plot_error}")
                    self.logger.warning(f"Event study plotting error: {plot_error}")
            else:
                print("❌ Event study failed")
                
        except Exception as e:
            print(f"❌ Event study failed: {e}")
            self.logger.error(f"Event study error: {e}")
            traceback.print_exc()
    
    def run_regression_analysis(self):
        """Run regression analysis."""
        print("\n📊 Running Regression Analysis...")
        
        if self.aligned_data is None:
            print("❌ No aligned data available for regression")
            return
        
        try:
            print("🔍 Running cross-sectional regressions...")
            
            # Run regression analysis
            regression_results = self.regression_analyzer.run_pooled_regression(
                aligned_data=self.aligned_data,
                crypto_assets=None,  # Will be auto-detected
                stock_assets=None   # Will be auto-detected
            )
            
            if regression_results is not None:
                self.results['regression'] = regression_results
                print("✅ Regression analysis completed")
                self.logger.info("Regression analysis completed")
                
                # Save regression results
                print("💾 Saving regression results...")
                results_dir = Path(self.config['output']['results_dir'])
                results_dir.mkdir(parents=True, exist_ok=True)
                
                # Save full results as pickle
                regression_file = results_dir / "regression_results.pkl"
                with open(regression_file, 'wb') as f:
                    pickle.dump(regression_results, f)
                print(f"✅ Regression results saved to: {regression_file}")
                
                # Save summary statistics as CSV
                if 'summary_statistics' in regression_results:
                    summary_file = results_dir / "regression_summary.csv"
                    summary_df = pd.DataFrame(regression_results['summary_statistics']).T
                    summary_df.to_csv(summary_file)
                    print(f"✅ Regression summary saved to: {summary_file}")
                
                # Generate regression plots
                try:
                    self.plot_generator.plot_regression_results(regression_results)
                    print("✅ Regression plots generated")
                except Exception as plot_error:
                    print(f"⚠️  Regression plots failed: {plot_error}")
                    self.logger.warning(f"Regression plotting error: {plot_error}")
            else:
                print("❌ Regression analysis failed")
                
        except Exception as e:
            print(f"❌ Regression analysis failed: {e}")
            self.logger.error(f"Regression analysis error: {e}")
            traceback.print_exc()
    
    def generate_summary_report(self):
        """Generate comprehensive summary report."""
        print("\n📋 Generating Summary Report...")
        
        try:
            report_path = Path(self.config['output']['results_dir']) / "analysis_summary.md"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("# Macro Announcement Effects Analysis - Summary Report\n\n")
                f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Data summary
                f.write("## Data Summary\n\n")
                if self.aligned_data is not None:
                    f.write(f"- **Total observations:** {self.aligned_data.shape[0]}\n")
                    f.write(f"- **Variables:** {self.aligned_data.shape[1]}\n")
                    f.write(f"- **Date range:** {self.aligned_data.index[0]} to {self.aligned_data.index[-1]}\n\n")
                
                # Stock data summary
                if self.stock_data is not None:
                    f.write(f"- **Stock assets:** {self.stock_data.shape[1]} symbols\n")
                    f.write(f"- **Stock observations:** {self.stock_data.shape[0]} days\n")
                
                # Crypto data summary
                if self.crypto_data is not None:
                    f.write(f"- **Crypto assets:** {self.crypto_data.shape[1]} coins\n")
                    f.write(f"- **Crypto observations:** {self.crypto_data.shape[0]} days\n")
                
                # Economic data summary
                if self.economic_data is not None:
                    f.write(f"- **Economic indicators:** {self.economic_data.shape[1]} series\n")
                    f.write(f"- **Economic observations:** {self.economic_data.shape[0]} periods\n\n")
                
                # Analysis results
                f.write("## Analysis Results\n\n")
                
                if 'event_study' in self.results:
                    f.write("### Event Study Analysis\n")
                    f.write("- Event study analysis completed successfully\n")
                    f.write("- Results available in event study output files\n\n")
                
                if 'regression' in self.results:
                    f.write("### Regression Analysis\n")
                    f.write("- Cross-sectional regression analysis completed\n")
                    f.write("- Results available in regression output files\n\n")
                
                # Output files
                f.write("## Output Files\n\n")
                f.write("- **Figures:** `results/figures/`\n")
                f.write("- **Tables:** `results/tables/`\n")
                f.write("- **Models:** `results/models/`\n")
                f.write("- **Raw data:** `data/raw/`\n")
                f.write("- **Processed data:** `data/processed/`\n\n")
                
                # Configuration
                f.write("## Configuration\n\n")
                f.write(f"- **Config file:** {self.config_path}\n")
                f.write(f"- **Project:** {self.config['project']['name']}\n")
                f.write(f"- **Version:** {self.config['project']['version']}\n\n")
                
                f.write("---\n")
                f.write("*Report generated by macro-announcement-effect analysis pipeline*\n")
            
            print(f"✅ Summary report saved to: {report_path}")
            self.logger.info(f"Summary report generated: {report_path}")
            
        except Exception as e:
            print(f"❌ Failed to generate summary report: {e}")
            self.logger.error(f"Summary report error: {e}")
    
    def run_full_analysis(self, start_date: str = None, end_date: str = None):
        """Run the complete analysis pipeline."""
        print("="*60)
        print("🎯 MACRO ANNOUNCEMENT EFFECTS ANALYSIS")
        print("="*60)
        
        start_time = datetime.now()
        
        try:
            # Setup
            self.setup()
            
            # Run analysis pipeline
            self.collect_data(start_date, end_date)
            self.preprocess_data()
            self.run_event_study()
            self.run_regression_analysis()
            self.generate_summary_report()
            
            # Generate overview plots
            if self.aligned_data is not None:
                print("\n📊 Generating overview visualizations...")
                try:
                    self.plot_generator.plot_data_overview(self.aligned_data)
                    print("✅ Overview plots generated")
                except Exception as plot_error:
                    print(f"⚠️  Overview plots failed: {plot_error}")
                    self.logger.warning(f"Overview plotting error: {plot_error}")
            
            # Success message
            end_time = datetime.now()
            duration = end_time - start_time
            
            print("\n" + "="*60)
            print("🎉 ANALYSIS COMPLETED SUCCESSFULLY!")
            print("="*60)
            print(f"⏱️  Total duration: {duration}")
            print(f"📁 Results saved to: {self.config['output']['results_dir']}")
            print(f"📊 Figures saved to: {self.config['output']['figures_dir']}")
            print(f"📋 Summary report: {self.config['output']['results_dir']}/analysis_summary.md")
            
            self.logger.info(f"Full analysis completed successfully in {duration}")
            
        except Exception as e:
            print(f"\n❌ Analysis failed: {e}")
            self.logger.error(f"Full analysis failed: {e}")
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
            print("🔍 Running analysis only...")
            analysis.setup()
            # TODO: Load existing processed data
            analysis.run_event_study()
            analysis.run_regression_analysis()
            analysis.generate_summary_report()
            
        elif args.data_only:
            # Only collect and preprocess data
            print("📊 Running data collection and preprocessing only...")
            analysis.setup()
            analysis.collect_data(args.start_date, args.end_date)
            analysis.preprocess_data()
            
        else:
            # Run full analysis
            analysis.run_full_analysis(args.start_date, args.end_date)
            
    except KeyboardInterrupt:
        print("\n⏹️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Analysis failed with error: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()