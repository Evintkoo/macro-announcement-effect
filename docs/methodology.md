# Methodology

This document summarises the empirical design implemented in the repository. It aligns the theoretical framing from the research plan with the concrete estimators and diagnostics executed by the Python pipeline.

## Analytical Overview

| Component | Purpose | Primary Implementation |
|-----------|---------|------------------------|
| Data quality and feature construction | Harmonise heterogeneous financial and macro series, derive return/volatility/surprise features, and enforce reproducibility through metadata and reports. | `MacroAnnouncementAnalysis.preprocess_data`, `FeatureEngineer.create_comprehensive_features`, `DataQualityAnalyzer.comprehensive_data_analysis` |
| Event study | Measure short-run abnormal returns and cumulative abnormal returns (CARs) around key macro events. | `EventStudyAnalyzer.run_full_event_study` |
| Regression suite | Quantify sensitivity of crypto and equity returns/volatility to macro surprises, with pooled models contrasting asset classes. | `RegressionAnalyzer.run_pooled_regression`, `RegressionAnalyzer.return_volatility_regression` |
| Hypothesis testing | Produce lightweight but robust non-parametric and parametric tests for cross-asset comparisons. | `ComprehensiveStatisticalAnalysis.run_complete_analysis` |

## Data and Feature Construction

### Sources

Free datasets are harvested through the collectors in `src/data_collection/`:

- **Yahoo Finance (`YahooFinanceCollector`)**: Index-level equities, ETFs, volatility indices, rates, commodities.
- **Cryptocurrency (`CryptoCollector`)**: Major crypto spot pairs via Yahoo Finance (BTC, ETH, BNB, ADA, SOL, etc.).
- **FRED/economic indicators (`EconomicDataCollector` and `EnhancedDataCollector`)**: Employment, inflation, rates, GDP, money supply, sentiment.
- **Enhanced collector**: Aggregates and harmonises all available series, including volatility and fixed-income proxies.

### Cleaning & Diagnostics

`MacroAnnouncementAnalysis.preprocess_data` orchestrates the following checks via `DataQualityAnalyzer`:

1. **Missingness and continuity** – missing percentages, longest gap detection, and imputation strategy (forward-fill for macro series).
2. **Outlier controls** – IQR- and z-score-based clipping to the 1st–99th percentiles when a column exhibits >5% extreme values.
3. **Stationarity signals** – Augmented Dickey-Fuller tests where enough observations exist.
4. **Structural breaks** – Heuristic rolling-mean change detection to flag possible regime shifts.
5. **Correlation scan** – High-correlation pairs (`|ρ| > 0.8`) to aid multicollinearity assessment.

Outputs are persisted to `data/processed/quality_reports/` (JSON + Markdown summary) along with an enriched metadata file describing variable categories and coverage.

### Feature Engineering Highlights

`FeatureEngineer.create_comprehensive_features` creates a dense feature matrix by combining:

- **Returns**: Log returns, rolling means, volatility, skewness, kurtosis, cumulative returns over configurable windows.
- **Volatility proxies**: Rolling realised volatility, exponentially weighted volatility, jump indicators.
- **Economic surprises**: Raw, normalised, absolute, and sign indicators using rolling means/standard deviations when explicit forecasts are unavailable.
- **Regime markers**: VIX-based high/low volatility flags, moving-average-based bull/bear indicators, percentile ranks.
- **Interaction terms**: Surprise × regime cross-products to study conditional sensitivities.
- **Temporal features**: Day-of-week, month, quarter, year, weekend flags, and lagged variants for relevant columns.

Feature creation emphasises avoiding DataFrame fragmentation by constructing column dictionaries before concatenation, thereby maintaining performance on large panels.

## Event Study Design

### Model

The pipeline estimates a market-model baseline for each asset:

\[
 r_{i,t} = \alpha_i + \beta_i m_t + \varepsilon_{i,t}
\]

where `m_t` is the chosen market factor (default: S&P 500 proxy). `EventStudyAnalyzer.estimate_normal_returns` falls back to heuristics if insufficient overlapping data exist, ensuring the pipeline still produces interpretable synthetic diagnostics.

### Windows & Estimation

- **Estimation window**: up to 250 trading days (minimum adaptive threshold of ~30 valid observations).
- **Event window**: configurable; default ±5 trading days around each event date.
- **Event catalogue**: `MacroAnnouncementAnalysis._get_comprehensive_event_catalog()` enumerates critical macro, policy, geopolitical, and crisis events from 2015 onwards. Synthetic semi-annual events are generated when empirical overlaps are insufficient.

### Outputs

For each event and asset, the analyser computes:

- Abnormal returns (AR) and cumulative abnormal returns (CAR).
- Significance statistics using residual standard errors and Student-t approximations.
- Average abnormal returns across events grouped by relative day (AAR, ACAR).
- Summary tables (mean, dispersion, hit ratios) exported via `PlotGenerator` to `results/tables/event_study/`.
- Narrative report `results/event_study_detailed_report.md` documenting setup and key findings.

## Regression Framework

### Individual Asset Regressions

`RegressionAnalyzer.run_pooled_regression` (despite the name) currently performs two tasks:

1. **Asset-level regressions**: For a capped number of assets (default 5) it regresses daily returns on selected surprise measures and optional controls, using HC3 robust errors. Lagged dependent variables can be included for autocorrelation control.
2. **Pooled crypto vs stock model**: Constructs a long-form panel with a `crypto_dummy` and interaction terms `surprise × crypto_dummy` to test sensitivity differences.

Model estimation is wrapped in defensive utilities (`safe_ols_fit`) to handle NaNs, infinite values, and unstable design matrices gracefully.

### Volatility and Asymmetric Effects

- `RegressionAnalyzer.return_volatility_regression` fits similar linear models to realised volatility series.
- `RegressionAnalyzer.asymmetric_effects_analysis` splits samples into positive/negative surprises to test directional asymmetry.
- `RegressionAnalyzer.regime_dependent_analysis` evaluates surprise impacts conditional on high/low volatility regimes or other binary markers.

### Statistical Extensions

`ComprehensiveStatisticalAnalysis.run_complete_analysis` provides a low-complexity but informative snapshot:

- Descriptive statistics for crypto and stock return distributions.
- Simple volatility and mean comparison tests (Levene, t-tests) after outlier trimming.
- Pairwise cross-asset correlations.
- Aggregated hypothesis conclusions and significant findings with effect-size notes.

Outputs coalesce into `results/comprehensive_analysis_results.csv`, `hypothesis_test_results.csv`, and supporting tables under `results/tables/`.

## Assumptions & Limitations

- **Data coverage**: Free APIs impose rate limits and occasionally return partial histories; the enhanced collector includes retries, alternative proxies, and synthesised results when real data are unavailable.
- **Market proxy selection**: In absence of `^GSPC`, the first available return series acts as the market benchmark—documented in logs.
- **Statistical power**: The pipeline enforces minimum observation thresholds (typically ≥10–30) before fitting models; otherwise it records fallbacks or synthetic outcomes.
- **Heteroskedasticity/autocorrelation**: Robust HC3 errors and diagnostic statistics (Durbin-Watson, Breusch–Pagan) are attached to regression summaries; however, full HAC corrections are not yet implemented.
- **Intraday analysis**: Infrastructure exists for intraday data (support for 1-minute intervals) but primary workflow operates on daily data due to public API constraints.

## Extending the Methodology

- **Custom event sets**: Supply your own list of `datetime` objects to `MacroAnnouncementAnalysis.run_event_study()` or modify the catalogue helper.
- **Alternative factor models**: Replace the single-factor market model with multi-factor regressions by adjusting `estimate_normal_returns` and the expected return formula.
- **Enhanced surprise calculations**: Inject forecaster consensus data into `FeatureEngineer.create_surprise_measures` to override rolling-average proxies.
- **Advanced volatility models**: Integrate GARCH or realised volatility estimators in `FeatureEngineer` and extend `RegressionAnalyzer` accordingly.

By grounding the codebase in the methodology described above, the project offers a reproducible, extensible foundation for studying macro news effects across traditional and digital markets.
