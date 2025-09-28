# Code Reference

This reference catalogues the core modules and classes that power the macro announcement effect pipeline. Use it alongside the [Pipeline Guide](./pipeline.md) to navigate the codebase.

## Directory Map

```
src/
├── analysis/
├── data_collection/
├── preprocessing/
├── utils/
└── visualization/
```

## Analysis Layer (`src/analysis/`)

| Module | Key Classes/Functions | Responsibilities | Notes |
|--------|-----------------------|------------------|-------|
| `event_study.py` | `EventStudyAnalyzer` | Market-model estimation, abnormal return computation, CAR aggregation, significance testing, average profiles, summary stats, synthetic fallbacks. | Accepts aligned return panel and market proxy; uses adaptive thresholds to avoid zero-variance issues. |
| `regression_analysis.py` | `RegressionAnalyzer`, `safe_ols_fit` | Individual return/volatility regressions, pooled crypto vs stock regression, asymmetric/regime-dependent analysis, diagnostic extraction. | Caps number of assets and surprise variables to maintain stability; applies HC3 robust errors. |
| `comprehensive_statistical_analysis.py` | `ComprehensiveStatisticalAnalysis` | Lightweight descriptive stats, volatility/mean comparison tests, correlation scans, hypothesis summaries. | Optimised for speed; limits inputs to top three assets/indicators per category. |

## Data Collection Layer (`src/data_collection/`)

| Module | Class | Description |
|--------|-------|-------------|
| `base_collector.py` | `BaseDataCollector` | Abstract interface; includes save/load helpers using project config. |
| `yahoo_finance_collector.py` | `YahooFinanceCollector` | Fetches equities, ETFs, vol indices via `yfinance` (daily/intraday). Includes validation for positivity, missingness, timezone normalisation. |
| `crypto_collector.py` | `CryptoCollector` | Retrieves crypto spot prices/volumes via `yfinance` symbols (BTC-USD, ETH-USD, etc.). |
| `economic_data_collector.py` | `EconomicDataCollector` | Pulls FRED series using `pandas_datareader`, with optional scraping stubs for event calendars. Skips pseudo-series placeholders automatically. |
| `enhanced_data_collector.py` | `EnhancedDataCollector`, `DataQualityAnalyzer` | Unified collector combining all series with retries, timezone normalisation, and additional volatility/fixed-income sources; includes data-quality suite (missingness, outliers, stationarity, correlation, structural breaks). |

## Preprocessing Layer (`src/preprocessing/`)

| Module | Class/Function | Description |
|--------|----------------|-------------|
| `data_preprocessor.py` | `DataPreprocessor` | Cleans prices (outlier clipping, fill strategies), computes returns/volatility, synchronises datasets, builds analysis dataset with announcement indicators, time features, lagged variables. |
| `feature_engineering.py` | `FeatureEngineer` | Configurable logger setup; generates surprise measures, rolling return stats, volatility proxies, regime indicators, interaction features, event windows, and consolidated feature matrix (`create_comprehensive_features`). |

## Utility Layer (`src/utils/`)

| Module | Highlights |
|--------|------------|
| `config.py` | `Config` manager loads YAML and resolves project-relative paths (`get_data_dir`, `get_results_dir`). Exposes global `config`. |
| `helpers.py` | Logging setup, datetime utilities, return/volatility calculators, timestamp synchronisation, event-window builder, outlier cleaning, result persistence. |
| `logging_config.py` | `EnhancedLogger`, `ComponentLogger`, `ColoredFormatter`; centralised logging with rotating files, ANSI-safe console formatting, and component-level helpers (data collection, preprocessing, analysis, visualisation). |
| `warnings_suppression.py` | Globally suppresses noisy statsmodels warnings while respecting NumPy version differences. |

## Visualisation & Export (`src/visualization/`)

| Module | Role |
|--------|------|
| `table_exporter.py` | Implements `PlotGenerator` alias that exports DataFrames to CSV tables, preserving legacy API. Handles directory creation, summary exports, regression artefacts, and nested mappings. |
| `plot_generator.py` | Thin compatibility shim that re-exports `table_exporter.PlotGenerator`. |

## Orchestration Scripts

| Path | Description |
|------|-------------|
| `main.py` | Primary orchestrator (`MacroAnnouncementAnalysis`) executing setup → data collection → preprocessing → event study → regression → reporting. Exposes CLI flags for partial runs. |
| `scripts/run_analysis.py` | Alternate runner demonstrating a simplified three-year workflow; retains older plotting API but leverages the same modules. |

## Results & Logging

- Logs: Initialised through `ComponentLogger`; main log file `main.log` plus per-component logs under `logs/`.
- Tables: Exported via `PlotGenerator` into `results/tables/` subdirectories (`event_study/`, `regression/`, `summary/`, etc.).
- Reports: Markdown summaries stored in `results/` (analysis summary, detailed reports, research report).

For configuration details, see [configuration.md](./configuration.md). For generated artefacts, see [output_artifacts.md](./output_artifacts.md).
