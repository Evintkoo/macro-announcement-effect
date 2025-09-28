# Pipeline Guide

This guide explains the end-to-end workflow executed by `main.py`, highlighting inputs, intermediate artefacts, and the modules responsible for each stage. Use it to trace data lineage, debug issues, or tailor the pipeline to custom research questions.

## High-Level Flow

1. **Setup**
   - Load configuration (`Config`) from `config/config.yaml`.
   - Bootstrap component loggers (console + rotating files in `logs/`).
   - Ensure directory structure (`results/`, `data/raw/`, `data/processed/`, etc.) exists.
   - Instantiate analysis helpers: `EventStudyAnalyzer`, `RegressionAnalyzer`, `PlotGenerator`.

2. **Data Collection** (`MacroAnnouncementAnalysis.collect_data`)
   - Attempt comprehensive multi-source retrieval via `EnhancedDataCollector.collect_comprehensive_data`:
     - Stocks, ETFs, volatility indices, commodities.
     - Cryptocurrencies.
     - Economic indicators, volatility, fixed-income series.
   - If enhanced collection fails, fall back to dedicated collectors (`YahooFinanceCollector`, `CryptoCollector`, `EconomicDataCollector`).
   - Persist raw CSV snapshots in `data/raw/` for reproducibility.

3. **Preprocessing & Feature Engineering** (`MacroAnnouncementAnalysis.preprocess_data`)
   - Merge all collected datasets, harmonising time zones and column prefixes.
   - Run `DataQualityAnalyzer.comprehensive_data_analysis` to profile missingness, outliers, stationarity, correlations, and potential structural breaks.
   - Clean series: drop columns with >80% missing data, cap extreme outliers, forward-fill macro indicators.
   - Generate derived features (`FeatureEngineer.create_analysis_features`):
     - Returns, volatility, cumulative returns, economic surprise proxies, regime indicators, lagged features.
   - Calculate additional derived variables (returns, multi-horizon volatility) via `_calculate_derived_variables`.
   - Save processed dataset (`data/processed/aligned_data.csv`), metadata (`data_metadata.json`), and quality reports (`quality_reports/`).

4. **Event Study** (`MacroAnnouncementAnalysis.run_event_study`)
   - Construct event catalogue (Fed decisions, geopolitical events, crises) via `_get_comprehensive_event_catalog`.
   - Filter events within the available data range; create synthetic events if necessary.
   - Compute returns, estimate market-model parameters, derive abnormal returns (ARs) and cumulative abnormal returns (CARs).
   - Produce summary statistics, significance metrics, and average abnormal return profiles.
   - Export tables to `results/` and `results/tables/event_study/`; generate Markdown report `event_study_detailed_report.md`.

5. **Comprehensive Regression & Statistical Analysis** (`MacroAnnouncementAnalysis.run_regression_analysis`)
   - Identify crypto and stock assets with sufficient data (limited to keep runtime manageable).
   - Fit individual return regressions against surprise features using HC3 robust errors.
   - Execute pooled regression contrasting crypto vs stock sensitivity (`crypto_dummy` interaction).
   - Trigger `ComprehensiveStatisticalAnalysis.run_complete_analysis` for concise hypothesis testing and correlation scans.
   - Persist flattened outputs (`comprehensive_analysis_results.csv`, `hypothesis_test_results.csv`, etc.) and export tables in `results/tables/regression/` and `results/tables/summary/`.

6. **Reporting** (`MacroAnnouncementAnalysis.generate_summary_report`)
   - Compile `analysis_summary.md` summarising key findings, dataset coverage, methods, and recommended next steps.
   - `MacroAnnouncementAnalysis._generate_comprehensive_research_report` produces an academic-style write-up in `comprehensive_research_report.md`.
   - All outputs referenced in [Output Catalogue](./output_artifacts.md).

7. **Completion**
   - Log total runtime, key output paths, and status in `main.log` and component logs.

## Execution Modes

`main.py` exposes CLI flags for incremental workflows:

| Flag | Description |
|------|-------------|
| `--config` | Path to alternate config YAML. |
| `--start-date`, `--end-date` | Override default 10-year lookback. |
| `--data-only` | Stop after data collection and preprocessing. |
| `--analysis-only` | Re-run analyses using existing processed data (loading logic TODO). |
| `--verbose` | Print traceback on failure. |

Scripts under `scripts/` (e.g., `scripts/run_analysis.py`) implement a narrower three-year pipeline with similar steps; prefer `main.py` for the authoritative flow.

## Data Dependencies

- **Mandatory**: Internet access for free APIs unless you seed `data/raw/` manually.
- **Optional**: `.env` variables for API keys (`FRED_API_KEY`, `COINGECKO_API_KEY`, etc.) to raise rate limits.
- **Time zones**: Collectors normalise to timezone-naïve UTC indices immediately to avoid downstream alignment issues.

## Error Handling & Fallbacks

- Missing data triggers warnings and fallback logic rather than hard failures.
- Event-study estimation gracefully switches to synthetic results when market proxies or overlaps are insufficient, ensuring the workflow completes.
- Regression routines limit the number of assets and surprise features processed to prevent very large model fits from hanging.

## Extending the Pipeline

- **Custom event lists**: Pass your own `datetime` list to `run_event_study()` or modify `_get_comprehensive_event_catalog`.
- **Additional collectors**: Implement subclasses of `BaseDataCollector` and register them inside `EnhancedDataCollector.collect_comprehensive_data`.
- **Alternative outputs**: Swap in your own exporter implementing the same API as `PlotGenerator` to generate charts instead of tables.
- **Model enhancements**: Extend `RegressionAnalyzer` for panel models, add GARCH estimators, or integrate causal inference libraries for more advanced treatments.

Refer to the [Code Reference](./code_reference.md) for module-level details on the functions invoked at each stage.
