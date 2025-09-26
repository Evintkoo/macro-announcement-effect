"""
Main script to run the complete macro announcement effects analysis.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from utils import config, setup_logging, save_results
from data_collection import YahooFinanceCollector, CryptoCollector, EconomicDataCollector
from preprocessing import DataPreprocessor, FeatureEngineer
from analysis import EventStudyAnalyzer, RegressionAnalyzer
from visualization import PlotGenerator

def main():
    """Main analysis pipeline."""
    
    # Setup logging
    logger = setup_logging(
        log_level=config.get('logging.level', 'INFO'),
        log_file='logs/main_analysis.log'
    )
    
    logger.info("Starting macro announcement effects analysis")
    
    try:
        # Step 1: Data Collection
        logger.info("Step 1: Collecting data")
        
        # Define date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*3)  # 3 years of data
        
        # Collect stock market data
        yahoo_collector = YahooFinanceCollector()
        stock_data = yahoo_collector.collect_market_data(start_date, end_date)
        logger.info(f"Collected stock data: {stock_data.shape}")
        
        # Collect cryptocurrency data
        crypto_collector = CryptoCollector()
        crypto_data = crypto_collector.collect_crypto_data(start_date, end_date)
        logger.info(f"Collected crypto data: {crypto_data.shape}")
        
        # Collect economic data
        econ_collector = EconomicDataCollector()
        economic_data = econ_collector.collect_economic_indicators(start_date, end_date)
        logger.info(f"Collected economic data: {economic_data.shape}")
        
        # Get sample announcement dates (in practice, you'd scrape these)
        announcement_dates = econ_collector.get_economic_calendar_sample()
        announcement_times = announcement_dates.index.tolist()
        logger.info(f"Using {len(announcement_times)} announcement dates")
        
        # Save raw data
        save_results(stock_data, "stock_data_raw", config.get_data_dir("raw"))
        save_results(crypto_data, "crypto_data_raw", config.get_data_dir("raw"))
        save_results(economic_data, "economic_data_raw", config.get_data_dir("raw"))
        
        # Step 2: Data Preprocessing
        logger.info("Step 2: Preprocessing data")
        
        preprocessor = DataPreprocessor()
        
        # Clean and calculate returns/volatility
        clean_stock_data = preprocessor.clean_price_data(stock_data)
        clean_crypto_data = preprocessor.clean_price_data(crypto_data)
        
        stock_metrics = preprocessor.calculate_returns_and_volatility(clean_stock_data)
        crypto_metrics = preprocessor.calculate_returns_and_volatility(clean_crypto_data)
        
        # Create comprehensive dataset
        analysis_dataset = preprocessor.create_analysis_dataset(
            crypto_metrics['returns'],
            stock_metrics['returns'],
            economic_data,
            announcement_dates
        )
        
        logger.info(f"Created analysis dataset: {analysis_dataset.shape}")
        
        # Step 3: Feature Engineering
        logger.info("Step 3: Engineering features")
        
        feature_engineer = FeatureEngineer()
        
        # Create surprise measures
        surprise_features = feature_engineer.create_surprise_measures(economic_data)
        
        # Create comprehensive features
        all_features = feature_engineer.create_comprehensive_features(
            pd.concat([clean_stock_data, clean_crypto_data], axis=1),
            economic_data,
            announcement_times
        )
        
        logger.info(f"Created {len(all_features.columns)} features")
        
        # Save processed data
        save_results(analysis_dataset, "analysis_dataset", config.get_data_dir("processed"))
        save_results(surprise_features, "surprise_features", config.get_data_dir("processed"))
        save_results(all_features, "all_features", config.get_data_dir("processed"))
        
        # Step 4: Event Study Analysis
        logger.info("Step 4: Running event study analysis")
        
        event_analyzer = EventStudyAnalyzer()
        
        # Combine crypto and stock returns
        all_returns = pd.concat([
            crypto_metrics['returns'].add_prefix('crypto_'),
            stock_metrics['returns'].add_prefix('stock_')
        ], axis=1)
        
        # Use S&P 500 as market return
        market_return_col = [col for col in stock_metrics['returns'].columns 
                           if 'gspc' in col.lower() or 'sp500' in col.lower()]
        
        if market_return_col:
            market_returns = stock_metrics['returns'][market_return_col[0]]
        else:
            # Use first stock return as proxy
            market_returns = stock_metrics['returns'].iloc[:, 0]
        
        # Run event study
        event_results = event_analyzer.run_full_event_study(
            all_returns,
            market_returns,
            announcement_times,
            event_window_days=3
        )
        
        logger.info("Event study completed")
        
        # Step 5: Regression Analysis
        logger.info("Step 5: Running regression analysis")
        
        regression_analyzer = RegressionAnalyzer()
        
        # Prepare volatility data
        all_volatility = pd.concat([
            crypto_metrics['volatility'].add_prefix('crypto_'),
            stock_metrics['volatility'].add_prefix('stock_')
        ], axis=1)
        
        # Run return and volatility regressions
        regression_results = regression_analyzer.return_volatility_regression(
            all_returns,
            all_volatility,
            surprise_features
        )
        
        # Run pooled regression (crypto vs stocks)
        crypto_assets = [col for col in all_returns.columns if 'crypto_' in col]
        stock_assets = [col for col in all_returns.columns if 'stock_' in col]
        
        pooled_results = regression_analyzer.pooled_crypto_stock_regression(
            all_returns,
            surprise_features,
            crypto_assets,
            stock_assets
        )
        
        logger.info("Regression analysis completed")
        
        # Step 6: Generate tabular result exports
        logger.info("Step 6: Generating tabular result exports")
        
        plot_generator = PlotGenerator()
        
        # Export summary tables
        tables_dir = config.get_results_dir("tables")

        # Event study tables
        plot_generator.plot_event_study_results(event_results, save_dir=tables_dir)

        # Regression results tables
        plot_generator.plot_regression_results(regression_results, save_dir=tables_dir)

        # Summary statistics tables
        plot_generator.plot_summary_statistics(
            {'stocks': clean_stock_data, 'crypto': clean_crypto_data},
            save_dir=tables_dir
        )
        
        # Step 7: Save Results
        logger.info("Step 7: Saving results")
        
        results_dir = config.get_results_dir()
        
        # Save event study results
        save_results(event_results['summary_statistics'], "event_study_summary", results_dir)
        save_results(event_results['average_abnormal_returns'], "average_abnormal_returns", results_dir)
        
        # Save regression coefficients
        if pooled_results:
            pooled_summary = {
                'params': pooled_results.params.to_dict(),
                'pvalues': pooled_results.pvalues.to_dict(),
                'rsquared': pooled_results.rsquared,
                'nobs': pooled_results.nobs
            }
            save_results(pooled_summary, "pooled_regression_results", results_dir, "json")
        
        # Create final summary report
        create_summary_report(
            event_results, 
            regression_results, 
            pooled_results,
            results_dir
        )
        
        logger.info("Analysis completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in main analysis: {e}", exc_info=True)
        raise

def create_summary_report(event_results, regression_results, pooled_results, output_dir):
    """Create a summary report of the analysis."""
    
    report_lines = [
        "# Macro Announcement Effects Analysis - Summary Report",
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Event Study Results",
        ""
    ]
    
    # Event study summary
    if 'summary_statistics' in event_results:
        summary_stats = event_results['summary_statistics']
        
        report_lines.append("### Summary Statistics (Cumulative Abnormal Returns)")
        report_lines.append("")
        
        for asset, stats in summary_stats.items():
            report_lines.extend([
                f"**{asset}:**",
                f"- Mean CAR: {stats.get('mean_car', 0):.4f}",
                f"- Standard Deviation: {stats.get('std_car', 0):.4f}",
                f"- Positive Events: {stats.get('positive_events', 0)}",
                f"- Negative Events: {stats.get('negative_events', 0)}",
                f"- Total Events: {stats.get('total_events', 0)}",
                ""
            ])
    
    # Regression results summary
    report_lines.extend([
        "## Regression Analysis Results",
        ""
    ])
    
    if pooled_results:
        report_lines.extend([
            "### Pooled Regression (Crypto vs Stocks)",
            f"- R-squared: {pooled_results.rsquared:.4f}",
            f"- Number of observations: {pooled_results.nobs}",
            "",
            "#### Key Coefficients:",
            ""
        ])
        
        for param, value in pooled_results.params.items():
            pvalue = pooled_results.pvalues.get(param, 1.0)
            significance = "***" if pvalue < 0.01 else "**" if pvalue < 0.05 else "*" if pvalue < 0.10 else ""
            report_lines.append(f"- {param}: {value:.4f}{significance} (p={pvalue:.4f})")
        
        report_lines.extend(["", "Significance levels: *** p<0.01, ** p<0.05, * p<0.10", ""])
    
    # Write report
    report_path = output_dir / "summary_report.md"
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))

if __name__ == "__main__":
    main()