
# Enhanced Analysis Summary Report
Generated: 2025-09-30 13:07:43

## 1. Statistical Significance Overview
- Total series analyzed: 564
- Series significant at 5% level: 62 (11.0%)
- Series significant at 1% level: 22 (3.9%)

### Most Statistically Significant Effects
                                                  mean_car  t_statistic  p_value    category
volatility_VIX_ETN_skewness_5d                    0.179750          inf      0.0  volatility
volatility_VIX_ETN_cumret_5d                      0.213576          inf      0.0  volatility
fixed_income_Treasury_10Y_Yield_cumret_5d         0.024620          inf      0.0       fixed
fixed_income_Treasury_30Y_Yield_cumret_5d         0.138141          inf      0.0       fixed
fixed_income_Investment_Grade_Bonds_skewness_10d  0.022275          inf      0.0       fixed

## 2. Event Asymmetry Insights
- Series with high asymmetry (>60%): 213
- Average positive/negative event ratio: 1.00

### Most Asymmetric Series
                                  positive_events  negative_events  asymmetry_score  mean_car
stocks_RUSSELL2000_kurtosis_10d               4.0              0.0              1.0  0.040031
stocks_VIX_skewness_5d                        0.0              2.0              1.0 -0.078508
stocks_OIL_kurtosis_5d                        0.0              5.0              1.0 -0.047886
crypto_Binance_Coin_cumret_10d                3.0              0.0              1.0  0.252961
crypto_Binance_Coin_kurtosis_20d              5.0              0.0              1.0  0.095074

## 3. Cross-Category Performance
### Category Rankings by Mean CAR
category
economic      0.0715
high          0.0440
crypto        0.0274
stocks        0.0273
fixed         0.0166
volatility    0.0117
bull          0.0000
low           0.0000
bear         -0.0041
trend        -0.0122
vix          -0.0474

## 4. Risk-Adjusted Performance
### Top Performers by Sharpe Ratio
                                           sharpe_ratio  sortino_ratio  max_drawdown
series                                                                              
fixed_income_Treasury_10Y_Yield_cumret_1d      0.780692       1.002875     -0.396911
crypto_Bitcoin_cumret_1d                       0.618951       0.843951     -1.453912
stocks_SP500_cumret_1d                         0.601301       0.673564     -0.293366
stocks_VIX_cumret_10d                         -0.252004      -0.405059    -10.885366

## 5. Regime Analysis
### Regime Distribution for stocks_SP500_cumret_1d
normal             1429
high_volatility     379
low_volatility       46

### Regime-Conditional Statistics
         regime  observations      mean      std       min      max  skewness  kurtosis
         normal          1429  0.000387 0.007268 -0.035926 0.024981 -0.483976  2.640256
high_volatility           379  0.000256 0.014033 -0.061609 0.090895  0.257214  6.297816
 low_volatility            46 -0.000358 0.004576 -0.014025 0.010734 -0.197258  1.344948

## 6. Risk Metrics Summary
### Value at Risk (95% confidence)
                                   series    VaR_95   CVaR_95  max_drawdown
                   stocks_SP500_cumret_1d -0.014613 -0.022603     -0.293366
                    stocks_VIX_cumret_10d -0.263527 -0.362303    -10.885366
                 crypto_Bitcoin_cumret_1d -0.048109 -0.073204     -1.453912
fixed_income_Treasury_10Y_Yield_cumret_1d -0.029613 -0.045180     -0.396911

## 7. Data Quality Metrics
- Sample size analyzed: 1854 observations
- Date range: 2020-09-01 00:00:00 to 2025-09-28 00:00:00
- Series completeness: 99.9%

## Key Takeaways
1. **Statistical Robustness**: 11.0% of event studies show statistically significant effects
2. **Asymmetry**: Notable asymmetry in positive vs negative event responses across categories
3. **Risk Characteristics**: Diverse risk profiles across asset classes with varying tail risk exposure
4. **Regime Dependency**: Evidence of regime-dependent behavior in volatility and correlation patterns

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
14. Cross-Correlation (SP500 vs VIX)
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
