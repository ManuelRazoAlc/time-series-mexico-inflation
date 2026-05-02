# Mexico Inflation Time Series Forecasting Report

## Project objective

This project analyzes annual inflation in Mexico using monthly time series data obtained from Banco de México's SIE API.

The main objective is to compare the behavior of headline, core and non-core inflation, and evaluate different forecasting approaches for short-term annual headline inflation prediction.

The project combines exploratory time series analysis, moving averages, volatility comparison and rolling one-step-ahead forecasting models.

## Research question

How has annual inflation in Mexico evolved over time, and which time series forecasting approach performs better for short-term headline inflation prediction?

## Data source

The data were obtained from Banco de México's Sistema de Información Económica (SIE) API.

The project uses the following annual inflation series:

- `SP30578`: Headline annual inflation
- `SP74662`: Core annual inflation
- `SP74665`: Non-core annual inflation

The raw data are downloaded automatically using the script:

- `scripts/01_download_banxico_data.py`

The downloaded data are stored in:

- `data/raw/banxico_inflation_series_long.csv`
- `data/raw/banxico_inflation_metadata.csv`

## Unit of analysis

The unit of analysis is the monthly observation.

Each row in the processed dataset represents one month and contains annual inflation values for headline, core and non-core inflation.

The processed dataset is stored in:

- `data/processed/inflation_monthly_processed.csv`

## Variables used

The main variables are:

- `date`: monthly observation date
- `headline`: annual headline inflation rate
- `core`: annual core inflation rate
- `non_core`: annual non-core inflation rate
- `headline_change`: monthly change in annual headline inflation
- `core_change`: monthly change in annual core inflation
- `non_core_change`: monthly change in annual non-core inflation
- `headline_ma_3`: 3-month moving average of headline inflation
- `headline_ma_12`: 12-month moving average of headline inflation

## Exploratory analysis

The exploratory analysis compares headline, core and non-core annual inflation.

The main outputs are:

- `outputs/figures/inflation_components_time_series.png`
- `outputs/figures/headline_inflation_moving_averages.png`
- `outputs/figures/headline_inflation_monthly_changes.png`
- `outputs/figures/inflation_components_boxplot.png`
- `outputs/figures/inflation_component_gaps.png`

The analysis shows that non-core inflation is the most volatile component, while core inflation tends to be smoother and more persistent.

Headline inflation is strongly related to core inflation, but periods of large deviations are often associated with movements in the non-core component.

## Moving averages

The project calculates 3-month and 12-month moving averages of headline inflation.

The 3-month moving average captures short-term movements, while the 12-month moving average smooths temporary fluctuations and helps visualize the medium-term inflation trend.

This is useful because monthly inflation data may contain short-term noise, especially during periods of sudden shocks.

## Forecasting design

The forecasting exercise focuses on annual headline inflation.

The data are split into:

- Initial training period: January 2000 to December 2020
- Rolling test period: January 2021 to March 2026

The evaluation uses a rolling one-step-ahead forecasting scheme.

For each month in the test period, each model is fitted using all information available up to the previous month and then used to forecast the next month.

This design is more realistic than producing a static long-horizon forecast because the model is updated as new observations become available.

## Forecasting models compared

The project compares the following models:

### Naive forecast

The naive forecast uses the previous month's observed inflation rate as the forecast for the next month.

This model is simple but useful as a benchmark, especially when the series is highly persistent.

### ARIMA(1,1,1)

The ARIMA model captures autoregressive and moving-average dynamics after differencing the series.

It is used as a non-seasonal statistical forecasting model.

### SARIMA(1,1,1)(1,0,1,12)

The SARIMA model extends ARIMA by including seasonal components with a 12-month structure.

This model is useful when monthly data may contain recurring annual patterns.

### Holt-Winters

The Holt-Winters model uses exponential smoothing with trend and seasonality.

It gives more weight to recent observations while allowing for trend and seasonal movements.

## Evaluation metrics

The models are compared using three forecast error metrics:

### MAE

Mean Absolute Error measures the average absolute forecast error.

Lower MAE means that the model has smaller errors on average.

### RMSE

Root Mean Squared Error penalizes larger errors more strongly.

Lower RMSE means the model avoids large forecast mistakes better.

### MAPE

Mean Absolute Percentage Error expresses forecast error as a percentage of the actual observed value.

Lower MAPE means better relative forecast accuracy.

## Model comparison results

The rolling one-step-ahead evaluation produced the following results:

| Model | MAE | RMSE | MAPE |
|---|---:|---:|---:|
| SARIMA(1,1,1)(1,0,1,12) | 0.233 | 0.280 | 4.51% |
| ARIMA(1,1,1) | 0.314 | 0.397 | 6.11% |
| Naive forecast | 0.316 | 0.421 | 6.11% |
| Holt-Winters | 0.331 | 0.436 | 6.42% |

The SARIMA model achieved the lowest error across all three metrics.

This suggests that including seasonal structure improves short-term forecasting performance for annual headline inflation.

## Interpretation of results

The results show that SARIMA outperformed the naive forecast, ARIMA and Holt-Winters under a rolling one-step-ahead forecasting design.

This is important because the naive model was a strong benchmark: annual inflation is persistent, so using the previous month's value already provides a reasonable short-term forecast.

However, SARIMA reduced the forecast error further, indicating that the model captured additional time series structure beyond simple persistence.

The improvement is visible in the lower MAE, RMSE and MAPE values.

## Key findings

- Annual headline inflation in Mexico shows strong persistence over time.
- Core inflation is smoother than non-core inflation.
- Non-core inflation is more volatile and shows larger swings.
- The naive forecast is a competitive short-term benchmark.
- SARIMA produced the best forecasting performance in the rolling one-step-ahead evaluation.
- Rolling evaluation gives a more realistic assessment than a static long-horizon forecast.

## Limitations

This project focuses on univariate time series forecasting using inflation history only.

The models do not include external explanatory variables such as exchange rates, interest rates, energy prices, wages or monetary policy indicators.

The forecast exercise is designed for short-term comparison and should not be interpreted as a full macroeconomic forecasting system.

## Possible extensions

Future versions of this project could include:

- Forecasting with exogenous variables using SARIMAX
- Comparison with policy rate or exchange rate series
- Forecasting core and non-core inflation separately
- Automatic ARIMA order selection
- Forecast intervals
- Rolling forecast evaluation with different training windows
- Additional models such as Prophet, VAR or machine learning regressors

## Project outputs

The main outputs are stored in:

### Figures

- `outputs/figures/inflation_components_time_series.png`
- `outputs/figures/headline_inflation_moving_averages.png`
- `outputs/figures/headline_inflation_monthly_changes.png`
- `outputs/figures/inflation_components_boxplot.png`
- `outputs/figures/inflation_component_gaps.png`
- `outputs/figures/rolling_statistical_forecasts_test_period.png`
- `outputs/figures/rolling_statistical_forecast_error_comparison.png`
- `outputs/figures/rolling_statistical_forecast_errors_over_time.png`

### Tables

- `outputs/tables/inflation_series_summary.csv`
- `outputs/tables/descriptive_statistics.csv`
- `outputs/tables/inflation_correlation_matrix.csv`
- `outputs/tables/inflation_volatility_summary.csv`
- `outputs/tables/inflation_component_gaps_summary.csv`
- `outputs/tables/rolling_statistical_forecast_values_test_period.csv`
- `outputs/tables/rolling_statistical_forecast_model_comparison.csv`

## Conclusion

This project shows how public economic time series data can be downloaded, processed, analyzed and modeled in a reproducible Python workflow.

The final rolling forecasting comparison indicates that SARIMA provides the best short-term forecasting performance for annual headline inflation among the models evaluated.

The project demonstrates practical skills in data extraction from an API, time series preparation, exploratory analysis, statistical forecasting, model evaluation and communication of results.