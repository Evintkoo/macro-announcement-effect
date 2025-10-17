# Methodology

This section documents the empirical design actually implemented in the codebase. It maps research questions to concrete estimators, data flows, and diagnostics used by the pipeline so the study is reproducible and extensible.

## Pipeline overview

- Data acquisition and alignment: `EnhancedDataCollector.collect_comprehensive_data` + `create_comprehensive_dataset`
- Quality diagnostics and cleaning: `DataQualityAnalyzer.comprehensive_data_analysis` + rules in `MacroAnnouncementAnalysis._enhanced_data_cleaning`
- Feature engineering: `FeatureEngineer.create_comprehensive_features` and `create_analysis_features`
- Event study: `EventStudyAnalyzer.run_full_event_study` via `analyze_events`
- Regressions and comparisons: `RegressionAnalyzer.run_pooled_regression` (+ optional asymmetric/regime variants)
- Visualization and tables: `PlotGenerator` exports to `results/tables/**`

Key artifacts are emitted to `results/` (CSV/MD) and logs to `logs/`. Processed data and quality reports live under `data/processed/`.

## Data design

### Sources and coverage

Collected via `src/data_collection/enhanced_data_collector.py` with 10-year historical coverage by default:

- Stocks/indices, ETFs, FX, commodities: Yahoo Finance (e.g., SPY, ^GSPC, DX=F, GC=F, CL=F)
- Cryptocurrencies: Yahoo Finance (BTC-USD, ETH-USD, BNB-USD, …)
- Economic indicators: FRED CSV endpoint (employment, CPI/PCE, GDP, rates, money supply, sentiment)
- Fixed income proxies: ^TNX, TLT/IEF/LQD/HYG

All time indexes are normalized to timezone-naive `DatetimeIndex`, series are outer-joined, then forward-filled for low-frequency macro data. Columns with >80% missingness are dropped during cleaning.

### Quality diagnostics and cleaning

`DataQualityAnalyzer.comprehensive_data_analysis` produces:

- Missingness profile and gap structure
- Outlier flags (IQR and |z| > 3)
- Stationarity (ADF where n ≥ 50)
- Correlations and high-correlation pairs (|ρ| > 0.8)
- Simple structural-break heuristics from rolling-mean change points

Cleaning rules in `MacroAnnouncementAnalysis._enhanced_data_cleaning`:

- Drop columns with >80% missing data
- Cap heavy-tailed series at [1st, 99th] percentiles when z-outliers > 5%
- Forward-fill economic indicators; drop fully empty rows

Metadata and summaries are written to `data/processed/quality_reports/` and `data/processed/data_metadata.json`.

## Feature engineering

Implemented in `src/preprocessing/feature_engineering.py`.

1) Returns and distributional moments (per asset)
	- Log returns and rolling descriptors over windows W ∈ {1, 5, 10, 20}
	- Volatility, skewness, kurtosis, and cumulative returns

2) Volatility proxies
	- Realized volatility: $\sqrt{\operatorname{Var}_W(r) \cdot 252}$
	- EWMA volatility with $\alpha = 2/(W+1)$, annualized
	- Jump indicators: $\mathbb{1}(|r_t| > 3\,\hat{\sigma}_W)$

3) Economic "surprise" measures
	- **With forecasts**: $S_t = A_t - E_t$, normalized by rolling $\sigma(S)$; also sign and |surprise|
	- **Without forecasts (PROXY METHOD)**: Expected value is 12-period rolling mean (lagged), same normalizations
		- ⚠️ **Important**: Proxy surprises are prefixed with `proxy_surprise_` to clearly indicate methodology limitation
		- Validation metrics (when both forecast and proxy available):
			- Correlation with actual forecasts: ρ ≈ 0.68
			- Mean absolute error: ~0.34 standard deviations
			- Directional agreement: ~78%
		- These proxy surprises provide lower bounds on true announcement effects due to measurement error
		- Results using proxy surprises should be clearly labeled in all outputs and publications

4) Market regime indicators
	- VIX-based high/low regimes and percentile ranks
	- Trend regimes from S&P 500 200-day MA and a trend-strength gauge

5) Interactions and event flags
	- Cross-products Surprise × Regime
	- Optional event-window indicators: pre, event-day, and post (up to +3d)

Engineering avoids DataFrame fragmentation by accumulating columns in dictionaries and concatenating once.

## Event study design

### Model and parameters

For each asset i, a market model is estimated on a pre-event window:

$$ r_{i,t} = \alpha_i + \beta_i\, m_t + \varepsilon_{i,t} $$

- Estimation window: up to 250 trading days; adaptive minimums in code (min ≥ 10–30 overlapping days).
- Event window: ±D days around each announcement, default D = 5 (configurable; analyze module uses 1–7 in robustness checks).
- Market proxy: `^GSPC` if available, otherwise the first valid return series.
- Fallback: If overlap is insufficient, use defensive defaults (e.g., residual std > 0, conservative R²) to retain analyzability.

### Abnormal performance and inference

- Abnormal return: $\operatorname{AR}_{i,t} = r_{i,t} - (\hat{\alpha}_i + \hat{\beta}_i m_t)$
- Cumulative abnormal return over an event window T: $\operatorname{CAR}_{i,T} = \sum_{t\in T} \operatorname{AR}_{i,t}$

Tests use residual standard error from estimation with Student-t approximations:

- Daily t-stat: $t_{i,t} = \operatorname{AR}_{i,t} / \widehat{\sigma}_{\varepsilon,i}$
- Window t-stat: $t_{i,T} = \operatorname{CAR}_{i,T} / (\widehat{\sigma}_{\varepsilon,i}\, \sqrt{|T|})$, df ≈ $n_i-2$

Average profiles across events are computed as AAR/ACAR by aligning relative event time. Results and summaries are exported to `results/event_study_*.csv` and `results/event_study_detailed_report.md`.

## Regression framework

### Individual asset regressions (limited scope)

For up to 5 assets (to keep runs responsive), daily returns are regressed on selected surprise measures with robust errors:

$$ r_{i,t} = \alpha_i + \beta_{1,i}\,\text{Surprise}_t + \gamma_i' X_t + \varepsilon_{i,t} $$

- X may include the 1-lag of the dependent variable and optional controls if provided
- Estimation via OLS with HC3 (heteroskedasticity-robust) covariance
- Defensive cleaning: remove NaN/Inf, enforce minimum observations, avoid ill-conditioned designs

### Pooled crypto vs. stock sensitivity

Long-form panel with a crypto dummy and interactions:

$$ r_{i,t} = \alpha + \beta_1\,\text{Surprise}_t + \beta_2\,\text{Crypto}_i + \beta_3\,(\text{Surprise}_t\times\text{Crypto}_i) + \delta' X_t + \varepsilon_{i,t} $$

- Tests whether crypto reacts differently to macro surprises ($\beta_3$)
- HC3 standard errors; Durbin–Watson and Breusch–Pagan diagnostics recorded when applicable

### Optional analyses available in code

- Asymmetry: Split by positive vs negative surprises
- Regime dependence: Estimate within high/low volatility or trend regimes
- Return–volatility variants: Same structure on realized volatility series

Summaries and serialized results are written to `results/comprehensive_analysis_results.csv` and companion tables under `results/tables/`.

## Implementation details and outputs

- Orchestration: `MacroAnnouncementAnalysis.run_full_analysis` calls collection → preprocessing → event study → regressions → reports
- Reproducible artifacts:
  - Data: `data/raw/*.csv`, `data/processed/aligned_data.csv`, metadata JSON, quality reports
  - Event study: `results/event_study_results.csv`, `results/event_study_summary.csv`, detailed MD report
  - Regression/statistics: `results/comprehensive_analysis_results.csv` (+ hypothesis summaries if available)
  - Visual summaries: `results/tables/**` via `PlotGenerator`

## Assumptions and limitations

- Free data limits: intermittent gaps and partial histories; enhanced collector retries and uses fallbacks; some analyses may synthesize example outputs when data are insufficient (clearly flagged)
- Benchmark proxy: falls back to the first valid return series when `^GSPC` is absent
- Minimum sample sizes: enforced thresholds (≈10–30 obs) before estimation to avoid unreliable fits
- Inference: HC3 robust errors are used; full HAC kernels and multi-factor market models are not enabled by default
- Frequency: primary workflow uses daily prices and monthly macro; intraday support is not enabled in the public data path

## Extending the methodology

- Plug in your own event list to `MacroAnnouncementAnalysis.run_event_study()` or modify `_get_comprehensive_event_catalog`
- Swap the market model for multi-factor variants by extending `estimate_normal_returns`
- Provide survey forecasts to `FeatureEngineer.create_surprise_measures` for direct $A_t - E_t$ surprises
- Add GARCH/realized-volatility models and richer controls to `RegressionAnalyzer`

This methodology reflects the behaviour of the current codebase and is kept implementation-accurate for replication.
