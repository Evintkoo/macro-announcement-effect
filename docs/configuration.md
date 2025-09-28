# Configuration & Execution

This document pairs `config/config.yaml` with runtime options so you can customise data sources, analysis parameters, logging, and export locations.

## YAML Structure

```yaml
project:
  name: ...
  version: ...

data_sources:
  fred: {...}
  yahoo_finance: {...}
  coingecko: {...}
  economic_calendar: {...}
  crypto: {...}
  stocks: {...}

economic_indicators:
  monetary_policy: [...]
  employment: [...]
  inflation: [...]
  gdp: [...]
  other: [...]

analysis:
  event_windows:
    intraday: {...}
    daily: {...}
  returns: {...}
  volatility: {...}
  regressions: {...}
  var: {...}

statistics:
  significance_level: ...
  bootstrap_iterations: ...
  var_confidence_intervals: [...]

output:
  results_dir: ...
  figures_dir: ...
  tables_dir: ...
  models_dir: ...
  figure_format: ...
  figure_dpi: ...

logging:
  level: ...
  format: ...
  file: ...
  directory: ...
  console_output: ...
  file_rotation: ...
  max_file_size: ...
  backup_count: ...
```

### Key Sections

- **`project`**: Metadata printed in reports; update version/name to track releases.
- **`data_sources`**:
  - `fred`: Enables optional API key injection (via `.env`) for higher rate limits.
  - `yahoo_finance` / `coingecko`: Base URLs; set `api_key` when premium keys are available.
  - `crypto.symbols` & `stocks.symbols`: Default instrument lists for collectors; modify to target specific assets.
- **`economic_indicators`**: Organised references used by collectors and feature engineering; extend with additional series IDs.
- **`analysis`**:
  - `event_windows`: Configure pre/post periods for intraday vs daily studies.
  - `returns.method`: Choose `log` or `simple` returns (applied in preprocessing).
  - `volatility.annualization_factor`: Adjust if using alternative trading day conventions.
  - `regressions.controls`: Baseline control variable list for regression builder.
  - `var`: Placeholder for VAR modelling parameters (currently not executed but preserved for future enhancement).
- **`statistics`**: Global significance levels, bootstrap iterations (reserved for future use), and VAR confidence intervals.
- **`output`**: Primary directories; tabs exported as CSV via `PlotGenerator` using these paths.
- **`logging`**: Default log level/format; `ComponentLogger` reads these values when instantiating per-component loggers.

## Environment Variables

Set via `.env` or OS environment variables:

| Variable | Used For |
|----------|----------|
| `FRED_API_KEY` | Higher-rate access to FRED endpoints. |
| `COINGECKO_API_KEY` | Premium CoinGecko tier (optional). |
| `ALPHA_VANTAGE_API_KEY`, `BINANCE_API_KEY` | Reserved for future collectors. |

## CLI Flags (main.py)

| Flag | Description |
|------|-------------|
| `--config PATH` | Use an alternate YAML configuration. |
| `--start-date YYYY-MM-DD` | Custom start date (overrides default 10-year window). |
| `--end-date YYYY-MM-DD` | Custom end date. |
| `--data-only` | Run collection + preprocessing only. |
| `--analysis-only` | Execute analyses assuming processed data already exists. |
| `--verbose` | Print full traceback on failure. |

Examples (PowerShell because the project targets Windows by default):

```powershell
# Full pipeline with defaults
uv run python main.py

# Data collection for the COVID crisis period only
uv run python main.py --start-date 2019-01-01 --end-date 2021-12-31 --data-only

# Use alternate config and rerun analyses
uv run python main.py --config config/custom.yaml --analysis-only
```

## Logging

- **Console**: Colour-coded levels via `ColoredFormatter`; falls back to ASCII on Windows.
- **Files**: Rotating logs are stored under `logs/` with component-specific filenames (`data_collection.log`, `preprocessing.log`, etc.). Main orchestrator additionally writes to `main.log` at the repository root.
- Adjust log verbosity globally via `logging.level` or per component by reconfiguring loggers in `MacroAnnouncementAnalysis.setup()`.

## Directory Expectations

At execution time the pipeline ensures these directories exist:

- `data/raw/` – raw CSV snapshots from collectors.
- `data/processed/` – aligned dataset, metadata, quality reports.
- `logs/` – log files for each component.
- `results/` – analysis summaries, tables, and reports (see [Output Catalogue](./output_artifacts.md)).

## Reconfiguration Tips

- **Adding new series**: Append symbols to the relevant lists and ensure collectors support them; update feature engineering filters if necessary.
- **Changing event windows**: Modify `analysis.event_windows` and reboot the pipeline; event-study functions read these values indirectly through orchestrator parameters.
- **Switching outputs**: Change directories in the `output` section; the pipeline creates them automatically.
- **Tuning logging**: Increase `logging.level` to `DEBUG` during development; consider disabling console output in headless runs.

## Execution Shortcuts

- `scripts/run_analysis.py` demonstrates a simplified runner with separate logging; invoke it via `uv run python scripts/run_analysis.py`.
- Use `uv run python main.py --analysis-only` after editing methodological code to avoid re-downloading data.

For testing or extension, consult the [Code Reference](./code_reference.md) to identify the module to modify.
