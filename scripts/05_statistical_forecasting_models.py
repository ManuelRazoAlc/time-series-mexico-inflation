from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing


# ---------------------------------------------------------
# 05_statistical_forecasting_models.py
# Purpose:
# Compare formal time series forecasting models for annual
# headline inflation in Mexico using rolling one-step-ahead
# forecasts.
# ---------------------------------------------------------

warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parents[1]

PROCESSED_PATH = BASE_DIR / "data" / "processed" / "inflation_monthly_processed.csv"
FIGURES_DIR = BASE_DIR / "outputs" / "figures"
TABLES_DIR = BASE_DIR / "outputs" / "tables"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)
TABLES_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Visual configuration
# ---------------------------------------------------------

COLORS = {
    "actual": "#1f77b4",
    "naive": "#ff7f0e",
    "arima": "#2ca02c",
    "sarima": "#d62728",
    "holt_winters": "#9467bd",
    "mae": "#1f77b4",
    "rmse": "#d62728",
}

plt.rcParams.update(
    {
        "figure.figsize": (12, 6),
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "font.size": 12,
        "axes.titlesize": 18,
        "axes.labelsize": 13,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "legend.fontsize": 11,
        "axes.titlepad": 14,
    }
)


def clean_plot(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.25, linewidth=0.8)
    ax.set_axisbelow(True)


def save_figure(fig, path):
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def calculate_metrics(y_true, y_pred):
    """
    Calculate common forecast accuracy metrics.
    Lower values indicate better performance.
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))

    mask = y_true != 0
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

    return mae, rmse, mape


def safe_arima_forecast(history, order):
    """
    Fit an ARIMA model and produce a one-step-ahead forecast.
    If the model fails, return NaN instead of stopping the script.
    """
    try:
        model = ARIMA(history, order=order)
        fitted = model.fit()
        forecast = fitted.forecast(steps=1)
        return float(forecast.iloc[0])
    except Exception:
        return np.nan


def safe_sarima_forecast(history, order, seasonal_order):
    """
    Fit a SARIMA model and produce a one-step-ahead forecast.
    If the model fails, return NaN instead of stopping the script.
    """
    try:
        model = SARIMAX(
            history,
            order=order,
            seasonal_order=seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        fitted = model.fit(disp=False)
        forecast = fitted.forecast(steps=1)
        return float(forecast.iloc[0])
    except Exception:
        return np.nan


def safe_holt_winters_forecast(history):
    """
    Fit a Holt-Winters exponential smoothing model and produce
    a one-step-ahead forecast. If the model fails, return NaN.
    """
    try:
        model = ExponentialSmoothing(
            history,
            trend="add",
            seasonal="add",
            seasonal_periods=12,
            initialization_method="estimated",
        )
        fitted = model.fit(optimized=True)
        forecast = fitted.forecast(steps=1)
        return float(forecast.iloc[0])
    except Exception:
        return np.nan


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

df = pd.read_csv(PROCESSED_PATH, parse_dates=["date"])
df = df.sort_values("date").reset_index(drop=True)

series_df = df[["date", "headline"]].dropna().copy()
series_df = series_df.set_index("date")

# Monthly start frequency.
y = series_df["headline"].asfreq("MS")

# ---------------------------------------------------------
# Train/test split
# ---------------------------------------------------------

split_date = "2021-01-01"

train = y[y.index < split_date].copy()
test = y[y.index >= split_date].copy()

if train.empty or test.empty:
    raise ValueError("Train or test set is empty. Check split_date.")


# ---------------------------------------------------------
# Rolling one-step-ahead forecasts
# ---------------------------------------------------------
# For each month in the test period:
# 1. Fit each model using all data available up to the previous month.
# 2. Forecast only the next month.
# 3. Add the actual observed value to the history.
#
# This makes the comparison fairer than forecasting the whole
# test period from a single model fitted only once.
# ---------------------------------------------------------

history = train.copy()
forecast_rows = []

for forecast_date, actual_value in test.items():
    naive_pred = float(history.iloc[-1])

    arima_pred = safe_arima_forecast(
        history=history,
        order=(1, 1, 1),
    )

    sarima_pred = safe_sarima_forecast(
        history=history,
        order=(1, 1, 1),
        seasonal_order=(1, 0, 1, 12),
    )

    holt_winters_pred = safe_holt_winters_forecast(history)

    forecast_rows.append(
        {
            "date": forecast_date,
            "actual": actual_value,
            "naive_forecast": naive_pred,
            "arima_forecast": arima_pred,
            "sarima_forecast": sarima_pred,
            "holt_winters_forecast": holt_winters_pred,
        }
    )

    # Update history with the actual observed value.
    history.loc[forecast_date] = actual_value
    history = history.sort_index()


forecast_df = pd.DataFrame(forecast_rows)

# Remove rows where any model failed.
forecast_df = forecast_df.dropna().reset_index(drop=True)


# ---------------------------------------------------------
# Evaluation metrics
# ---------------------------------------------------------

models = {
    "Naive forecast": "naive_forecast",
    "ARIMA(1,1,1)": "arima_forecast",
    "SARIMA(1,1,1)(1,0,1,12)": "sarima_forecast",
    "Holt-Winters": "holt_winters_forecast",
}

metrics = []

for model_name, forecast_col in models.items():
    mae, rmse, mape = calculate_metrics(
        forecast_df["actual"],
        forecast_df[forecast_col],
    )

    metrics.append(
        {
            "model": model_name,
            "mae": mae,
            "rmse": rmse,
            "mape": mape,
        }
    )

metrics_df = pd.DataFrame(metrics).sort_values("rmse").reset_index(drop=True)

metrics_path = TABLES_DIR / "rolling_statistical_forecast_model_comparison.csv"
metrics_df.to_csv(metrics_path, index=False, encoding="utf-8-sig")

forecast_values_path = TABLES_DIR / "rolling_statistical_forecast_values_test_period.csv"
forecast_df.to_csv(forecast_values_path, index=False, encoding="utf-8-sig")


# ---------------------------------------------------------
# Figure 1: Actual vs rolling statistical forecasts
# ---------------------------------------------------------

fig, ax = plt.subplots(figsize=(12.5, 7.2))

ax.plot(
    forecast_df["date"],
    forecast_df["actual"],
    label="Actual headline inflation",
    linewidth=2.6,
    color=COLORS["actual"],
)

ax.plot(
    forecast_df["date"],
    forecast_df["naive_forecast"],
    label="Naive forecast",
    linewidth=1.8,
    color=COLORS["naive"],
    alpha=0.9,
)

ax.plot(
    forecast_df["date"],
    forecast_df["arima_forecast"],
    label="ARIMA(1,1,1)",
    linewidth=1.8,
    color=COLORS["arima"],
    alpha=0.9,
)

ax.plot(
    forecast_df["date"],
    forecast_df["sarima_forecast"],
    label="SARIMA",
    linewidth=1.8,
    color=COLORS["sarima"],
    alpha=0.9,
)

ax.plot(
    forecast_df["date"],
    forecast_df["holt_winters_forecast"],
    label="Holt-Winters",
    linewidth=1.8,
    color=COLORS["holt_winters"],
    alpha=0.9,
)

ax.set_title("Rolling one-step-ahead forecasts for headline inflation")
ax.set_xlabel("Date")
ax.set_ylabel("Annual inflation rate (%)")

ax.legend(
    frameon=False,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.14),
    ncol=3,
)

clean_plot(ax)

figure_path = FIGURES_DIR / "rolling_statistical_forecasts_test_period.png"
save_figure(fig, figure_path)


# ---------------------------------------------------------
# Figure 2: Forecast error comparison
# ---------------------------------------------------------

plot_df = metrics_df.sort_values("rmse", ascending=True)

x = np.arange(len(plot_df))
bar_width = 0.35

fig, ax = plt.subplots(figsize=(11.5, 7.0))

bars_mae = ax.bar(
    x - bar_width / 2,
    plot_df["mae"],
    width=bar_width,
    label="MAE",
    color=COLORS["mae"],
)

bars_rmse = ax.bar(
    x + bar_width / 2,
    plot_df["rmse"],
    width=bar_width,
    label="RMSE",
    color=COLORS["rmse"],
)

ax.set_title("Rolling forecast error comparison across statistical models")
ax.set_xlabel("Model")
ax.set_ylabel("Forecast error")
ax.set_xticks(x)
ax.set_xticklabels(plot_df["model"], rotation=15, ha="right")

ax.legend(
    frameon=False,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.22),
    ncol=2,
)

for bars in [bars_mae, bars_rmse]:
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{height:.2f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

clean_plot(ax)

figure_path = FIGURES_DIR / "rolling_statistical_forecast_error_comparison.png"
save_figure(fig, figure_path)


# ---------------------------------------------------------
# Figure 3: Forecast errors over time
# ---------------------------------------------------------

error_df = forecast_df.copy()
error_df["naive_error"] = error_df["actual"] - error_df["naive_forecast"]
error_df["arima_error"] = error_df["actual"] - error_df["arima_forecast"]
error_df["sarima_error"] = error_df["actual"] - error_df["sarima_forecast"]
error_df["holt_winters_error"] = error_df["actual"] - error_df["holt_winters_forecast"]

fig, ax = plt.subplots(figsize=(12.5, 7.0))

ax.plot(
    error_df["date"],
    error_df["naive_error"],
    label="Naive forecast error",
    linewidth=1.7,
    color=COLORS["naive"],
)

ax.plot(
    error_df["date"],
    error_df["arima_error"],
    label="ARIMA error",
    linewidth=1.7,
    color=COLORS["arima"],
)

ax.plot(
    error_df["date"],
    error_df["sarima_error"],
    label="SARIMA error",
    linewidth=1.7,
    color=COLORS["sarima"],
)

ax.plot(
    error_df["date"],
    error_df["holt_winters_error"],
    label="Holt-Winters error",
    linewidth=1.7,
    color=COLORS["holt_winters"],
)

ax.axhline(0, linestyle="--", linewidth=1.1, color="#555555")

ax.set_title("Rolling one-step-ahead forecast errors over time")
ax.set_xlabel("Date")
ax.set_ylabel("Actual minus forecast, percentage points")

ax.legend(
    frameon=False,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.14),
    ncol=2,
)

clean_plot(ax)

figure_path = FIGURES_DIR / "rolling_statistical_forecast_errors_over_time.png"
save_figure(fig, figure_path)


# ---------------------------------------------------------
# Summary text file
# ---------------------------------------------------------

best_model = metrics_df.iloc[0]

summary_path = BASE_DIR / "outputs" / "rolling_statistical_forecast_model_summary.txt"

with open(summary_path, "w", encoding="utf-8") as file:
    file.write("Rolling Statistical Forecast Model Comparison Summary\n")
    file.write("====================================================\n\n")

    file.write("Objective:\n")
    file.write(
        "Compare formal time series forecasting models for annual headline inflation "
        "in Mexico using Banxico monthly inflation data.\n\n"
    )

    file.write("Evaluation design:\n")
    file.write(
        "Models are evaluated using a rolling one-step-ahead forecasting scheme. "
        "For each month in the test period, each model is fitted using all information "
        "available up to the previous month and then used to forecast the next month.\n\n"
    )

    file.write("Train/test split:\n")
    file.write(f"- Initial training period: {train.index.min().date()} to {train.index.max().date()}\n")
    file.write(f"- Rolling test period: {forecast_df['date'].min().date()} to {forecast_df['date'].max().date()}\n\n")

    file.write("Models compared:\n")
    file.write("- Naive forecast: uses the previous month as the forecast benchmark.\n")
    file.write("- ARIMA(1,1,1): autoregressive integrated moving-average model.\n")
    file.write("- SARIMA(1,1,1)(1,0,1,12): ARIMA model with seasonal components.\n")
    file.write("- Holt-Winters: exponential smoothing with additive trend and seasonality.\n\n")

    file.write("Model performance:\n")
    for _, row in metrics_df.iterrows():
        file.write(
            f"- {row['model']}: MAE = {row['mae']:.3f}, "
            f"RMSE = {row['rmse']:.3f}, MAPE = {row['mape']:.2f}%\n"
        )

    file.write("\nBest model by RMSE:\n")
    file.write(
        f"- {best_model['model']} "
        f"(RMSE = {best_model['rmse']:.3f}, MAE = {best_model['mae']:.3f})\n\n"
    )

    file.write("Interpretation note:\n")
    file.write(
        "The rolling design makes the comparison fairer than a static long-horizon forecast, "
        "because each model is updated as new observations become available. If the naive "
        "benchmark remains competitive, this indicates strong short-term persistence in "
        "annual headline inflation.\n"
    )


# ---------------------------------------------------------
# Console output
# ---------------------------------------------------------

print("Rolling statistical forecasting analysis completed.")
print(f"Rows in initial training set: {len(train)}")
print(f"Rows in rolling test set: {len(forecast_df)}")
print(f"Forecast values saved to: {forecast_values_path}")
print(f"Model comparison saved to: {metrics_path}")
print(f"Summary saved to: {summary_path}")
print(f"Figures saved to: {FIGURES_DIR}")

print("\nModel comparison:")
print(metrics_df.to_string(index=False))