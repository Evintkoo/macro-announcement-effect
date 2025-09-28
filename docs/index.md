# Macro Announcement Effect Research Documentation

Welcome! This documentation set explains how the project collects data, engineers features, and runs econometric analysis to measure how macroeconomic announcements move cryptocurrency and U.S. equity markets. The material is organised by workflow stage so you can navigate directly to the pieces you need when auditing results, extending the code, or replicating the research.

## Navigation

- [Methodology](./methodology.md) – theoretical framing, event-study design, regression specifications, and statistical tests.
- [Pipeline Guide](./pipeline.md) – step-by-step breakdown of the automated workflow implemented in `main.py`.
- [Code Reference](./code_reference.md) – module-level reference for collectors, preprocessors, analysers, utilities, and visualisation helpers.
- [Configuration & Execution](./configuration.md) – how to tune `config/config.yaml`, command-line flags, logging, and environment considerations.
- [Output Catalogue](./output_artifacts.md) – description of persisted tables, reports, and logs created after a run.

## Project Snapshot

- **Research Focus**: Compare the magnitude, timing, and persistence of price, volatility, and volume reactions around macroeconomic announcements in digital assets versus U.S. equities.
- **Primary Questions**:
  1. Do crypto assets react differently from equities after macro announcements?
  2. Are reactions asymmetric across surprise direction, size, or volatility regimes?
  3. How persistent are the reactions through the post-announcement window?
  4. Are there spillovers between asset classes during macro news cycles?
- **Data Horizon**: Up to ten years of daily history, with optional intraday retrieval when supported by free APIs.
- **Core Methods**: Market-model event studies, pooled cross-sectional regressions, non-parametric and parametric hypothesis testing, and regime-dependent diagnostics.

## Getting Started

- Install dependencies with `uv pip install -r requirements.txt` or the environment manager of your choice.
- Populate `data/raw/` by running `uv run main.py` (full pipeline) or `uv run main.py --data-only` if you want to review intermediate datasets before analysis.
- Read [Pipeline Guide](./pipeline.md) for an end-to-end view, then consult the [Output Catalogue](./output_artifacts.md) to inspect generated artefacts.

> **Tip:** Logs are streamed to both the console and `logs/`—they provide granular traceability for data quality checks, model diagnostics, and export operations.
