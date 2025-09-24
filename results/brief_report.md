# Macro Announcement Effects — Brief Report

Generated on: 2025-09-23

## Objective
Compare how major U.S. macroeconomic announcements affect cryptocurrencies versus U.S. stock market indices using event studies and regressions.

## Data Snapshot
- Total observations: 2,462; variables: 21
- Date range: 2021-09-24 to 2025-09-22
- Stocks: 4 symbols, 1,002 daily observations
- Crypto: 10 coins, 1,460 daily observations
- Economic indicators: 7 series, 47 periods

Sources include Yahoo Finance (stocks), CoinGecko (crypto), and public economic indicators.

## Methods
- Event study (±3 trading days) using market-model abnormal returns and CARs
- Pooled regressions contrasting crypto vs stocks with macro surprise controls

## Results (High-Level)
- Pipeline executed successfully; data aligned and analyses completed
- Regression outputs saved: `results/regression_results.pkl`
- Overview figures and tables generated under:
  - Figures: `results/figures/overview/`
  - Tables: `results/tables/overview/`
- Full run summary: `results/analysis_summary.md`

## Notes
- Use figures and tables to inspect event-time dynamics and coefficient patterns.
- Re-run `main.py` to refresh results for different date ranges or configurations.
