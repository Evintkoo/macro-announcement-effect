# Macro Announcement Effects on Cryptocurrency vs U.S. Stock Market

A comprehensive research project analyzing the effects of macroeconomic announcements on cryptocurrency and U.S. stock market returns, volatility, and trading volume.

## � Project Status & Issue Tracking

**Current Status:** Draft under revision (October 16, 2025)

**Comprehensive review completed** identifying 32 issues across paper and codebase:

📄 **For Paper Issues & Fixes:**
- **[QUICK_FIXES.md](./QUICK_FIXES.md)** - Start here! Top 5 critical issues with immediate actions
- **[PAPER_FIXES_PLAN.md](./PAPER_FIXES_PLAN.md)** - Complete 32-issue plan with detailed solutions
- **[ISSUES_SUMMARY.md](./ISSUES_SUMMARY.md)** - Executive summary with timelines and progress tracking

🔨 **For Code Issues:**
- **[plan.md](./plan.md)** - Technical code issues and pipeline fixes

**Priority Breakdown:**
- 🔴 P0 Critical: 8 issues (5 paper + 3 code) - Blocking scientific validity
- 🟡 P1 High: 10 issues (5 paper + 5 code) - Required for publication quality
- 🟢 P2-P3: 14 issues - Polish and completeness

**Estimated Timeline:**
- P0 fixes: 2-3 days full-time
- Publication-ready: 2 weeks full-time
- Complete polish: 4 weeks full-time

## �📋 Research Questions

1. **RQ1**: What is the effect of major U.S. macroeconomic announcements on returns, volatility, and trading volume of major cryptocurrencies?
2. **RQ2**: How do these effects compare to their impacts on the U.S. stock market?
3. **RQ3**: Are there asymmetric effects depending on surprise direction, magnitude, or market regime?
4. **RQ4**: What is the timing and persistence of responses in both asset classes?

## ✨ Key Features

- **Comprehensive Data Collection**: Automated collection of 10 cryptocurrencies, major stock indices, and 20 economic indicators (all free sources)
- **Advanced Feature Engineering**: Generates 3421+ features from 54 raw variables including:
  - Returns (1d, 5d, 10d, 20d, 60d windows)
  - Realized and exponential volatility measures
  - Skewness and kurtosis
  - Economic surprise indicators
  - Market regime indicators
  - Cross-asset interactions
- **Robust Event Study Analysis**: Market model-based methodology with statistical significance testing
- **Multiple Regression Specifications**: Pooled regressions, asymmetric effects, regime-dependent models
- **Data Quality Assurance**: Automated quality reports, missing data analysis, and validation checks
- **Publication-Ready Outputs**: LaTeX tables, high-quality figures, and comprehensive markdown reports
- **Reproducible Research Pipeline**: Complete automation from data collection to final results

## 🏗️ Project Structure

```
macro-announcement-effect/
├── src/                           # Source code
│   ├── data_collection/          # Data collection modules
│   │   ├── base_collector.py     # Base data collector class
│   │   ├── yahoo_finance_collector.py  # Yahoo Finance data (free)
│   │   ├── crypto_collector.py   # Cryptocurrency data via Yahoo Finance
│   │   └── economic_data_collector.py  # Economic indicators via FRED
│   ├── preprocessing/            # Data preprocessing
│   │   ├── data_preprocessor.py  # Data cleaning and preparation
│   │   └── feature_engineering.py # Feature creation
│   ├── analysis/                 # Statistical analysis
│   │   ├── event_study.py        # Event study methodology
│   │   └── regression_analysis.py # Regression models
│   ├── visualization/            # Plot generation
│   │   └── plot_generator.py     # Visualization tools
│   └── utils/                    # Utility functions
│       ├── config.py             # Configuration management
│       └── helpers.py            # Helper functions
├── data/                         # Data storage
│   ├── raw/                      # Raw collected data
│   └── processed/                # Processed datasets
├── config/                       # Configuration files
│   └── config.yaml               # Main configuration
├── results/                      # Analysis results
│   ├── figures/                  # Generated plots
│   ├── tables/                   # Summary tables
│   └── models/                   # Saved models
├── notebooks/                    # Jupyter notebooks
├── scripts/                      # Execution scripts
│   └── run_analysis.py           # Main analysis script
├── tests/                        # Test files
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

### 🗃️ Data Files and Sources

**Data Sources** (P1 FIX - corrected documentation):
- **Cryptocurrency Data**: Yahoo Finance (`yfinance` library) - provides free historical data for major cryptocurrencies
- **Stock Market Data**: Yahoo Finance - S&P 500, NASDAQ, Dow Jones, and individual stocks
- **Economic Indicators**: FRED (Federal Reserve Economic Data) via `pandas-datareader` - free access to macroeconomic time series
- **Event Catalog**: Externalized to `config/events/macroeconomic_events.csv` for easy maintenance and transparency

**Data Storage**:
CSV and JSON datasets are tracked in the repository for reproducibility (see `data/raw/` and `data/processed/`). The `.gitignore` is configured to exclude large intermediate files while keeping core datasets versioned.

## 🚀 Quick Start

### 📊 Data Quality Note

**This project now uses optimized date range (2020-09-01 to present) to ensure complete cryptocurrency data.**

- ✓ All major cryptocurrencies have >98% complete data
- ✓ ~5 years of high-quality data for robust analysis
- ✓ No structural missing data issues

For more details on data quality and methodology, see [`docs/methodology.md`](docs/methodology.md).

### Option 1: Automated Setup (Recommended)

```bash
# Run the main analysis pipeline
python main.py
```

### Option 2: Manual Setup

#### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd macro-announcement-effect

# Set up virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Configuration

The configuration file (`config/config.yaml`) is pre-configured with optimized settings:

```yaml
# config/config.yaml
data_collection:
  start_date: "2020-09-01"  # Optimized for complete crypto coverage
  end_date: null  # Defaults to current date
```

No API keys required for basic functionality - all data sources are free!

#### 3. Run Analysis

```bash
# Full analysis pipeline (recommended)
python main.py

# Interactive runner with menu options
python run_analysis.py

# Custom date range
python main.py --start-date 2020-01-01 --end-date 2024-12-31

# Data collection only
python main.py --data-only

# Analysis only (requires existing data)
python main.py --analysis-only
```

### 📊 Expected Output

After running the analysis, you'll find:

```
results/
├── figures/                     # Generated visualizations
│   ├── event_study_plots.png   # Event study results
│   ├── regression_plots.png    # Regression analysis
│   └── data_overview.png       # Data summary plots
├── tables/                      # Statistical results
│   ├── event_study_results.csv # Event study statistics
│   └── regression_results.csv  # Regression coefficients
├── models/                      # Saved model objects
└── analysis_summary.md         # Comprehensive report
```

### 3. Run Analysis

```bash
# Run complete analysis pipeline
python scripts/run_analysis.py
```

## 📊 Methodology

### Data Sources (All Free!)

**Coverage Period**: September 2020 - Present (~5 years of high-quality data)

- **Cryptocurrency Data** (10 assets via Yahoo Finance):
  - Major coins: Bitcoin (BTC), Ethereum (ETH), BNB, Cardano (ADA), XRP
  - DeFi/Layer-1: Solana (SOL), Polkadot (DOT), Avalanche (AVAX), Polygon (MATIC)
  - DeFi infrastructure: Chainlink (LINK)
  
- **Stock Market Data** (Yahoo Finance):
  - US indices: S&P 500, Dow Jones, NASDAQ, Russell 2000
  - Volatility: VIX
  - Fixed income: Treasury rates (10Y, 2Y), TLT
  - Commodities: Gold (GLD)
  - Crypto-related stocks
  
- **Economic Data** (20 indicators via FRED):
  - Employment: Unemployment rate, nonfarm payrolls, jobless claims
  - Inflation: CPI, core CPI, PPI
  - Growth: GDP, industrial production, retail sales
  - Monetary policy: Federal funds rate, EFFR
  - Market indicators: Consumer confidence, housing starts
  
> **Note**: The date range (2020-09-01 onwards) is optimized to ensure complete data coverage for all cryptocurrencies, as newer tokens like Polkadot and Avalanche launched in mid-2020. See [`DATA_QUALITY_FIX.md`](DATA_QUALITY_FIX.md) for methodology details.

### Statistical Methods

#### 1. Event Study Analysis
Implementation of market model-based event study:

```
Normal Return Model: r_{i,t} = α_i + β_i * m_t + ε_{i,t}
Abnormal Return: AR_{i,t} = r_{i,t} - (α̂_i + β̂_i * m_t)
Cumulative Abnormal Return: CAR_{i,T} = Σ_{t∈T} AR_{i,t}
```

#### 2. Regression Analysis
Multiple regression specifications:

```
Return Regression: r_{i,t} = α + β₁*Surprise_t + β₂*D_t + γ*X_t + ε_{i,t}
Pooled Regression: r_{i,t} = α + β₁*Surprise_t + β₂*Crypto_i + β₃*(Surprise_t × Crypto_i) + ε_{i,t}
```

#### 3. Surprise Measures
Economic surprise indicators:

```
Surprise_t = A_t - E_t
Normalized Surprise_t = (A_t - E_t) / σ(E_t)
```

**⚠️ IMPORTANT METHODOLOGICAL NOTE** (P1 FIX):

By default, this project uses **proxy surprises** based on historical rolling means when forecast data is unavailable:
- Columns prefixed with `proxy_surprise_` indicate historical-mean-based surprises
- These are NOT forecast-based surprises (Bloomberg/Refinitiv consensus)
- For publication-grade research, real forecast data should be integrated
- See `config.yaml` → `analysis.mark_proxy_surprises` to control labeling
- See `docs/methodology.md` for detailed discussion of limitations

### Key Features

- **Automated Data Collection**: Free APIs for all data sources
- **Robust Statistical Analysis**: Event studies, regressions, VAR models
- **Comprehensive Visualizations**: Interactive plots and summary charts
- **Modular Design**: Easy to extend and modify
- **Reproducible Research**: Complete pipeline with version control

## 📈 Analysis Outputs

### Event Study Results
- Cumulative Abnormal Returns (CARs) around announcements
- Statistical significance tests
- Comparison between crypto and stock responses

### Regression Results
- Coefficient estimates and significance tests
- R-squared comparisons across assets
- Asymmetric effects analysis

### Visualizations
- Price evolution charts
- Volatility comparisons
- Correlation matrices
- Event study plots
- Regression coefficient plots

## 🔧 Configuration

The project uses a YAML configuration file (`config/config.yaml`) to manage:

- Data source settings
- Analysis parameters
- Statistical test configurations
- Output preferences

Key configuration sections (P0/P1 fixes applied):
```yaml
data_sources:
  yahoo_finance:     # Free stock market data
  fred:              # Free economic data (via FRED)
  crypto:            # Cryptocurrency data (via Yahoo Finance)

analysis:
  # P0 FIX: Synthetic data policy
  allow_synthetic: false  # When false, fail fast on insufficient data
  
  # P0 FIX: Timezone handling
  timezone_policy: 'naive'  # Use tz-naive for daily data alignment
  
  # P1 FIX: Surprise methodology transparency
  mark_proxy_surprises: true  # Prefix proxy-based surprises
  
  event_windows:     # Event study windows
  returns:           # Return calculation methods
  volatility:        # Volatility estimation
  
statistics:
  significance_level: 0.05
  bootstrap_iterations: 1000
```

See `config/events/macroeconomic_events.csv` for the externalized event catalog (P1 fix).

## 📝 Usage Examples

### Basic Analysis

```python
from src.data_collection import YahooFinanceCollector, CryptoCollector
from src.analysis import EventStudyAnalyzer, RegressionAnalyzer

# Collect data
yahoo_collector = YahooFinanceCollector()
stock_data = yahoo_collector.collect_market_data(start_date, end_date)

# Run event study
analyzer = EventStudyAnalyzer()
results = analyzer.run_full_event_study(returns_data, market_returns, announcement_times)
```

### Custom Analysis

```python
from src.preprocessing import FeatureEngineer

# Create custom features
engineer = FeatureEngineer()
surprise_features = engineer.create_surprise_measures(economic_data)
regime_features = engineer.create_market_regime_features(market_data)
```

## 📊 Expected Results

Based on the methodology, the analysis will produce:

1. **Event Study Findings**:
   - Magnitude of price reactions to announcements
   - Timing and persistence of effects
   - Differences between crypto and stock markets

2. **Regression Insights**:
   - Sensitivity coefficients to economic surprises
   - Asymmetric effects of positive vs negative news
   - Regime-dependent responses

3. **Comparative Analysis**:
   - Crypto vs stock market response patterns
   - Volatility effects
   - Cross-asset correlations during announcement periods

## 📁 Additional Documentation

- **[`DATA_QUALITY_FIX.md`](DATA_QUALITY_FIX.md)**: Comprehensive documentation of data quality improvements and the rationale for the 2020-09-01 start date
- **[`DATA_QUALITY_FIX_RESULTS.md`](DATA_QUALITY_FIX_RESULTS.md)**: Before/after validation results showing improvement from 21-49% missing data to <2%
- **[`QUICK_START.md`](QUICK_START.md)**: Step-by-step guide for first-time users
- **[`docs/`](docs/)**: Detailed documentation on methodology, pipeline, and output artifacts

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Federal Reserve Economic Data (FRED) for macroeconomic indicators
- Yahoo Finance for market and cryptocurrency data
- Research methodology based on established event study and regression techniques

## 📞 Contact

For questions or collaboration opportunities, please open an issue or contact the maintainers.

---

*This project implements a comprehensive empirical framework for studying macro announcement effects on financial markets, with a focus on comparing traditional and digital assets.*
Finding behavourial pattern of macro announcement effect to crypto, with stock market as control variable
