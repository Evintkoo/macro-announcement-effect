# Macro Announcement Effects on Cryptocurrency vs U.S. Stock Market

A comprehensive research project analyzing the effects of macroeconomic announcements on cryptocurrency and U.S. stock market returns, volatility, and trading volume.

## 📋 Research Questions

1. **RQ1**: What is the effect of major U.S. macroeconomic announcements on returns, volatility, and trading volume of major cryptocurrencies?
2. **RQ2**: How do these effects compare to their impacts on the U.S. stock market?
3. **RQ3**: Are there asymmetric effects depending on surprise direction, magnitude, or market regime?
4. **RQ4**: What is the timing and persistence of responses in both asset classes?

## 🏗️ Project Structure

```
macro-announcement-effect/
├── src/                           # Source code
│   ├── data_collection/          # Data collection modules
│   │   ├── base_collector.py     # Base data collector class
│   │   ├── yahoo_finance_collector.py  # Yahoo Finance data (free)
│   │   ├── crypto_collector.py   # Cryptocurrency data (CoinGecko free API)
│   │   └── economic_data_collector.py  # Economic indicators
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

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

**Windows Users:**
```batch
# Double-click run_analysis.bat or run in PowerShell:
.\run_analysis.ps1
```

**Linux/Mac Users:**
```bash
python run_analysis.py
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

```bash
# Copy environment template (optional)
cp .env.template .env

# Edit configuration if needed
# Note: All data sources are free, no API keys required for basic functionality
```

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

- **Stock Market Data**: Yahoo Finance (S&P 500, VIX, Treasury rates)
- **Cryptocurrency Data**: CoinGecko public API (Bitcoin, Ethereum)
- **Economic Data**: FRED via pandas-datareader (unemployment, inflation, GDP)
- **Announcement Dates**: Web scraping from Federal Reserve and BLS websites

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

Key configuration sections:
```yaml
data_sources:
  yahoo_finance:     # Free stock market data
  coingecko:         # Free crypto data
  economic_calendar: # Free announcement dates

analysis:
  event_windows:     # Event study windows
  returns:           # Return calculation methods
  volatility:        # Volatility estimation
  
statistics:
  significance_level: 0.05
  bootstrap_iterations: 1000
```

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

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Federal Reserve Economic Data (FRED)
- Yahoo Finance for market data
- CoinGecko for cryptocurrency data
- Research methodology based on established event study and regression techniques

## 📞 Contact

For questions or collaboration opportunities, please open an issue or contact the maintainers.

---

*This project implements a comprehensive empirical framework for studying macro announcement effects on financial markets, with a focus on comparing traditional and digital assets.*
Finding behavourial pattern of macro announcement effect to crypto, with stock market as control variable
