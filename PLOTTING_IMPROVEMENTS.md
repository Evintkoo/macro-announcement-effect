# Plotting System Improvements

## Overview

The plotting system has been completely refactored to ensure clean, readable visualizations with no text overlap. Each image file now contains exactly one plot for better clarity and usability.

## Key Improvements Made

### 1. **One Plot Per Image File**
- **Before**: Multiple subplots combined in single images (2x2, 3x2 grids)
- **After**: Each visualization is saved as a separate, focused image file
- **Benefit**: Easier to view, share, and include in reports

### 2. **Text Overlap Prevention**
- **Enhanced rcParams**: Improved spacing, padding, and font sizes
- **Better Layout**: `plt.tight_layout(pad=2.0)` with extra padding
- **Optimized Saving**: `bbox_inches='tight'` prevents text clipping
- **Readable Labels**: Shortened and cleaned asset/variable names

### 3. **Improved Visual Quality**
- **Higher DPI**: 300 DPI for crisp, publication-ready images
- **Better Colors**: Consistent color schemes (orange for crypto, blue for stocks)
- **Enhanced Legends**: Better positioned legends with proper spacing
- **Grid Lines**: Subtle grid lines for better readability

### 4. **Smart Asset Name Cleaning**
- **BTC-USD_price** → **BTC**
- **^GSPC** → **S&P500**
- **economic_UNRATE** → **Unemployment Rate**
- **crypto_** and **stocks_** prefixes automatically cleaned

## Generated Plot Categories

### Overview Plots (`results/figures/overview/`)

#### Price Analysis (4 plots per asset category):
1. **Raw Prices**: Actual price levels over time
2. **Normalized Prices**: Base-100 normalized for comparison
3. **Daily Returns**: Percentage daily returns
4. **Rolling Volatility**: 30-day rolling volatility (annualized)

#### Data Quality:
1. **Data Availability Heatmap**: Shows data completeness over time
2. **Summary Statistics Table**: Clean, formatted statistics table

#### Economic Indicators:
- **Individual plots** for each economic indicator with trend lines

### Event Study Plots (`results/figures/event_study/`)

#### Cumulative Abnormal Returns:
1. **Crypto CARs**: Cryptocurrency-specific cumulative abnormal returns
2. **Stock CARs**: Traditional asset cumulative abnormal returns  
3. **Comparison Plot**: Crypto vs Stock averages
4. **All Assets**: Combined overview
5. **Final CARs**: Bar chart of final CAR values

#### Statistical Analysis:
1. **Mean CARs by Asset**: Average cumulative abnormal returns
2. **CAR Volatility**: Standard deviation of CARs
3. **Positive vs Negative Events**: Event reaction analysis
4. **CAR Range**: Min vs Max scatter plot

### Regression Plots (`results/figures/regression/`)

1. **Surprise Coefficients**: Response to economic surprises
2. **Statistical Significance**: P-values of coefficients
3. **Return Regression R-squared**: Model fit for returns
4. **Volatility Regression R-squared**: Model fit for volatility

## Technical Specifications

### Matplotlib Configuration:
```python
plt.rcParams.update({
    'figure.figsize': (12, 8),           # Standard figure size
    'font.size': 11,                     # Base font size
    'axes.titlesize': 16,               # Title font size
    'axes.labelsize': 13,               # Axis label size
    'savefig.dpi': 300,                 # High resolution
    'savefig.bbox': 'tight',            # Prevent clipping
    'figure.subplot.bottom': 0.15,      # Extra space for labels
    'axes.titlepad': 15,                # Title padding
    'legend.borderpad': 0.5             # Legend spacing
})
```

### File Naming Convention:
- **Descriptive names**: `crypto_cumulative_abnormal_returns.png`
- **Category prefixes**: `all_price_series_`, `economic_indicator_`
- **No spaces**: Underscores for compatibility
- **PNG format**: High quality, widely compatible

## Benefits for Analysis

1. **Better Presentations**: Individual plots easy to include in slides/reports
2. **Focused Analysis**: Each plot tells one clear story
3. **Professional Quality**: Publication-ready visualizations
4. **No Manual Editing**: No need to fix overlapping text in image editors
5. **Consistent Branding**: Uniform color schemes and styling
6. **Accessibility**: Larger fonts and better contrast

## Usage

The improved plotting system is automatically used when running:
```python
# Generate all overview plots
plot_generator.plot_data_overview(aligned_data)

# Generate event study plots  
plot_generator.plot_event_study_results(event_results)

# Generate regression plots
plot_generator.plot_regression_results(regression_results)
```

All plots are automatically saved to `results/figures/` with appropriate subdirectories.