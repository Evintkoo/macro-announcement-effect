
# Enhanced Analysis Summary Report
Generated: 2025-10-16 15:03:32

## Project Configuration
- **Project**: Macro Announcement Effects on Crypto vs Stock Markets
- **Version**: 1.0.0
- **Data Period**: 2020-09-01 to present
- **Significance Level**: 0.05
- **Returns Method**: log
- **Volatility Method**: realized

## Data Coverage
- **Cryptocurrencies**: 10 symbols
- **Stocks/Indices**: 27 symbols
- **Economic Indicators**: 14 tracked

## 1. Statistical Significance Overview
- Total series analyzed: 241
- Series significant at 5% level: 14 (5.8%)
- Series significant at 1% level: 8 (3.3%)

### Most Statistically Significant Effects
                                                  mean_car  t_statistic   p_value category
fixed_income_Treasury_10Y_Yield_cumret_5d         0.024620          inf  0.000000    fixed
fixed_income_Treasury_30Y_Yield_cumret_5d         0.138141          inf  0.000000    fixed
fixed_income_Investment_Grade_Bonds_skewness_10d  0.022263          inf  0.000000    fixed
stocks_DJI_skewness_10d                           0.190486  1418.224876  0.000449   stocks
crypto_BNB_kurtosis_10d                           0.261147    77.584184  0.008205   crypto

## 2. Event Asymmetry Insights
- Series with high asymmetry (>60%): 121
- Average positive/negative event ratio: 2.00

### Most Asymmetric Series
                                 positive_events  negative_events  asymmetry_score  mean_car
stocks_RUSSELL2000_kurtosis_10d              4.0              0.0              1.0  0.040031
stocks_OIL_kurtosis_5d                       0.0              5.0              1.0 -0.047886
crypto_BNB_cumret_10d                        3.0              0.0              1.0  0.252961
crypto_XRP_skewness_20d                      0.0              5.0              1.0 -0.102663
crypto_BNB_kurtosis_20d                      5.0              0.0              1.0  0.095074

## 3. Cross-Category Performance
### Category Rankings by Mean CAR
category
stocks    0.0559
crypto    0.0412
fixed     0.0325

## 4. Risk-Adjusted Performance
### Top Performers by Sharpe Ratio
                        sharpe_ratio  sortino_ratio  max_drawdown
series                                                           
stocks_SP500_cumret_1d      0.600227       0.669974     -0.293366

## 5. Regime Analysis
### Regime Distribution for stocks_SP500_cumret_1d
normal             1433
high_volatility     383
low_volatility       55

### Regime-Conditional Statistics
         regime  observations      mean      std       min      max  skewness  kurtosis
         normal          1433  0.000407 0.007294 -0.035926 0.024981 -0.506577  2.695141
high_volatility           383  0.000184 0.013995 -0.061609 0.090895  0.266908  6.313507
 low_volatility            55 -0.000294 0.004141 -0.014025 0.010156 -0.526230  1.597953

## 6. Risk Metrics Summary
### Value at Risk (95% confidence)
                series    VaR_95   CVaR_95  max_drawdown
stocks_SP500_cumret_1d -0.014624 -0.022655     -0.293366

## 7. Data Quality Metrics
- Sample size analyzed: 1871 observations
- Date range: 2020-09-01 00:00:00 to 2025-10-15 00:00:00
- Series completeness: 99.9%

## Key Takeaways
1. **Statistical Robustness**: 5.8% of event studies show statistically significant effects
2. **Asymmetry**: Notable asymmetry in positive vs negative event responses across categories
3. **Risk Characteristics**: Diverse risk profiles across asset classes with varying tail risk exposure
4. **Regime Dependency**: Evidence of regime-dependent behavior in volatility and correlation patterns

## Configuration Details
- **Bootstrap Iterations**: 1000
- **VAR Max Lags**: 5
- **VAR IC Criterion**: aic
- **Annualization Factor**: 252

## Output Files
All results have been saved to `D:\Works\Researchs\macro-announcement-effect\notebooks\final_results/`

### Plots Generated:
1. Top Mean CAR Effects (bar chart)
2. Event Study Dispersion (scatter plot)
3. Mean CAR by Category (box plot)
4. Cumulative Returns Snapshot (line chart)
5. Correlation Matrix (heatmap)
6. Rolling Correlation vs SP500
7. Significance Rate by Category
8. Event Asymmetry (scatter plot)
9. Distribution Analysis (histograms)
10. Q-Q Plots
11. Category Violin Plot
12. Rolling Volatility
13. VaR Comparison
14. Cross-Correlation Analysis
15. Dynamic Correlation
16. CAR by Event Window (if available)
17. Regime Detection
18. Risk-Adjusted Performance

### Tables Generated:
1. Category Summary
2. Correlation Matrix
3. Rolling Correlation Data
4. Significance Summary
5. Top Significant Results
6. Significance by Category
7. Asymmetric Series
8. Normality Tests
9. Category Detailed Statistics
10. Rolling Volatility Data
11. Risk Metrics
12. Cross-Correlation Data
13. Event Window Analysis (if available)
14. Regime Distribution
15. Regime Statistics
16. Performance Metrics

---
*For detailed methodology and complete results, refer to the full analysis pipeline outputs.*
*Configuration file: D:\Works\Researchs\macro-announcement-effect\config\config.yaml*
