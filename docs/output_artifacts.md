# Output Catalogue

After a successful run, the project produces a structured set of artefacts spanning processed datasets, statistical tables, narrative reports, and logs. This catalogue explains what to expect and how to interpret each output.

## Data

| Location | Description |
|----------|-------------|
| `data/raw/*.csv` | Snapshots from collectors (stocks, crypto, economic, comprehensive). Useful for auditing upstream data or seeding new analyses without re-pulling APIs. |
| `data/processed/aligned_data.csv` | Master feature matrix combining prices, returns, volatility, economic surprises, regime indicators, and lagged features. |
| `data/processed/data_metadata.json` | Metadata describing dataset shape, coverage, variable categories, and missing-data stats. |
| `data/processed/quality_reports/data_quality_analysis.json` | Detailed quality diagnostics (missingness, outliers, stationarity, correlations). |
| `data/processed/quality_reports/data_summary.md` | Human-readable summary of quality checks with counts, date range, and variable-type breakdown. |

## Results (CSV & Markdown)

| File | Purpose |
|------|---------|
| `results/event_study_results.csv` | Flattened representation of event-study metrics for quick spreadsheet review. |
| `results/event_study_summary.csv` | Aggregated CAR statistics per asset (mean, std, positive/negative hits). |
| `results/event_study_detailed_report.md` | Narrative description of event study setup, key findings, and methodology. |
| `results/comprehensive_analysis_results.csv` | JSON-normalised view of regression, statistical, and summary outputs. |
| `results/hypothesis_test_results.csv` | Table of hypothesis labels, conclusions, p-values, effect sizes (when available). |
| `results/significant_findings.csv` | Extracted subset of statistically significant tests for quick consumption. |
| `results/analysis_summary.md` | Executive summary with highlights, dataset coverage, hypotheses, and recommendations. |
| `results/comprehensive_research_report.md` | Long-form report formatted like an academic paper (abstract, methodology, findings, implications). |

## Tabular Exports (`results/tables/`)

`PlotGenerator` writes CSV tables instead of plots, organised by topic:

- `event_study/`
  - `average_abnormal_returns.csv`, `average_cumulative_abnormal_returns.csv`
  - Per-event abnormal/CAR tables (`abnormal_returns/event_X.csv`, `cumulative_abnormal_returns/event_X.csv`)
  - `model_parameters.csv`, `summary_statistics.csv`, `significance_tests.csv`
- `regression/`
  - Coefficient tables for individual regressions and pooled models.
  - Nested directories follow the structure of the regression result dictionary.
- `summary/`
  - Raw data snapshots with `.csv` suffixes (e.g., `stocks_raw.csv`, `crypto_raw.csv`).
  - `*_summary.csv` files capturing descriptive statistics.
- `overview/`
  - `aligned_data.csv` (duplicate of processed data for convenience).
  - `summary_statistics.csv` derived from the aligned dataset.

## Logs

| File | Source |
|------|--------|
| `main.log` | Top-level orchestrator logging progress, duration, and high-level warnings. |
| `logs/main.log` | Rotating log (via `ComponentLogger`) for the main component. |
| `logs/data_collection.log`, `logs/preprocessing.log`, `logs/analysis.log`, `logs/visualization.log` | Component-specific logs with granular trace statements, errors, and fallbacks. |
| Additional `analysis.log`, `data_collection.log`, etc. | Generated during earlier runs or alternate scripts (`scripts/run_analysis.py`). |

## Notebooks & Interactive Artefacts

- `notebooks/free_data_analysis.ipynb`: Optional exploratory notebook (not updated automatically). Use it for ad-hoc inspection; it is not part of the automated pipeline.

## Logs & Run Metadata

- `main.log` at repository root ensures a lightweight audit trail; rotate logs live inside `logs/`.
- Each run prints summary information (duration, result directories) to both console and log files.

## Post-Run Checklist

1. Inspect `analysis_summary.md` to confirm high-level success.
2. Review `results/tables/event_study/summary_statistics.csv` to verify CAR behaviour.
3. Check `results/tables/regression/` for coefficient signs and significance.
4. Consult `data/processed/quality_reports` for data issues worth addressing before deeper analysis.
5. Archive `data/raw/` if you need a reproducible snapshot of the collected dataset.

## Troubleshooting Artefacts

- Empty CSVs in `results/tables/` indicate insufficient data for that output; consult component logs for warnings.
- Synthetic event-study results are flagged in `event_study_detailed_report.md` (look for "Results are synthetic" note) when real data were insufficient.
- If regressions skip assets, check the limits enforced in `RegressionAnalyzer` (`max_assets_to_analyze`, minimum observation thresholds).

By referencing this catalogue after each run, you can quickly locate the artefacts needed for reporting, replication, or further modelling.
