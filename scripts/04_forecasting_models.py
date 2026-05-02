from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.metrics import mean_absolute_error, mean_squared_error


# ---------------------------------------------------------
# 04_forecasting_models.py
# Purpose:
# Compare simple forecasting models for annual headline
# inflation in Mexico using a time-based train/test split.
# ---------------------------------------------------------

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
    "moving_average": "#2ca02c",
    "exp_smoothing": "#d62728",
    "gray": "#555555",
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
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def calculate_metrics(y_true, y_pred):
    """
    Calculate common forecast accuracy metrics.

    MAE:
    Average absolute error.

    RMSE:
    Square root of average squared error. Penalizes large errors more.

    MAPE:
    Average absolute percentage error.
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))

    # Avoid division by zero in MAPE.
    mask = y_true != 0
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

    return mae, rmse, mape


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

df = pd.read_csv(PROCESSED_PATH, parse_dates=["date"])
df = df.sort_values("date").reset_index(drop=True)

series = df[["date", "headline"]].copy()
series = series.dropna(subset=["headline"])

# ---------------------------------------------------------
# Train/test split
# ---------------------------------------------------------
# Here we use data up to 2020-12 as training data,
# and data from 2021-01 onward as test data.
# ---------------------------------------------------------

split_date = "2021-01-01"

train = series[series["date"] < split_date].copy()
test = series[series["date"] >= split_date].copy()

if train.empty or test.empty:
    raise ValueError("Train or test set is empty. Check the split_date.")

# ---------------------------------------------------------
# Model 1: Naive forecast
# ---------------------------------------------------------
# Forecast each test month using the previous observed value.
# ---------------------------------------------------------

full_series = series.copy()
full_series["naive_forecast"] = full_series["headline"].shift(1)

test_forecasts = test.copy()
test_forecasts = test_forecasts.merge(
    full_series[["date", "naive_forecast"]],
    on="date",
    how="left",
)

# ---------------------------------------------------------
# Model 2: Moving average forecast
# ---------------------------------------------------------
# Forecast each test month using the average of the previous
# 12 months.
# ---------------------------------------------------------

full_series["moving_average_12_forecast"] = (
    full_series["headline"]
    .rolling(window=12)
    .mean()
    .shift(1)
)

test_forecasts = test_forecasts.merge(
    full_series[["date", "moving_average_12_forecast"]],
    on="date",
    how="left",
)

# ---------------------------------------------------------
# Model 3: Simple exponential smoothing
# ---------------------------------------------------------
# forecast_t = alpha * observed_{t-1} + (1-alpha) * forecast_{t-1}
# ---------------------------------------------------------

alpha = 0.35

values = full_series["headline"].values
exp_forecast = [np.nan] * len(values)

# Initialize forecast with first observed value.
exp_forecast[1] = values[0]

for i in range(2, len(values)):
    exp_forecast[i] = alpha * values[i - 1] + (1 - alpha) * exp_forecast[i - 1]

full_series["exp_smoothing_forecast"] = exp_forecast

test_forecasts = test_forecasts.merge(
    full_series[["date", "exp_smoothing_forecast"]],
    on="date",
    how="left",
)

# Drop rows where at least one forecast is missing.
test_forecasts = test_forecasts.dropna(
    subset=[
        "naive_forecast",
        "moving_average_12_forecast",
        "exp_smoothing_forecast",
    ]
).reset_index(drop=True)

# ---------------------------------------------------------
# Evaluation metrics
# ---------------------------------------------------------

models = {
    "Naive forecast": "naive_forecast",
    "12-month moving average": "moving_average_12_forecast",
    "Exponential smoothing": "exp_smoothing_forecast",
}

metrics = []

for model_name, forecast_col in models.items():
    mae, rmse, mape = calculate_metrics(
        test_forecasts["headline"],
        test_forecasts[forecast_col],
    )

    metrics.append(
        {
            "model": model_name,
            "mae": mae,
            "rmse": rmse,
            "mape": mape,
        }
    )

metrics_df = pd.DataFrame(metrics)
metrics_df = metrics_df.sort_values("rmse").reset_index(drop=True)

metrics_path = TABLES_DIR / "forecast_model_comparison.csv"
metrics_df.to_csv(metrics_path, index=False, encoding="utf-8-sig")

forecast_values_path = TABLES_DIR / "forecast_values_test_period.csv"
test_forecasts.to_csv(forecast_values_path, index=False, encoding="utf-8-sig")

# ---------------------------------------------------------
# Figure 1: Actual vs forecasts
# ---------------------------------------------------------

fig, ax = plt.subplots(figsize=(12.5, 6.8))

ax.plot(
    test_forecasts["date"],
    test_forecasts["headline"],
    label="Actual headline inflation",
    linewidth=2.4,
    color=COLORS["actual"],
)

ax.plot(
    test_forecasts["date"],
    test_forecasts["naive_forecast"],
    label="Naive forecast",
    linewidth=1.8,
    color=COLORS["naive"],
    alpha=0.9,
)

ax.plot(
    test_forecasts["date"],
    test_forecasts["moving_average_12_forecast"],
    label="12-month moving average",
    linewidth=1.8,
    color=COLORS["moving_average"],
    alpha=0.9,
)

ax.plot(
    test_forecasts["date"],
    test_forecasts["exp_smoothing_forecast"],
    label="Exponential smoothing",
    linewidth=1.8,
    color=COLORS["exp_smoothing"],
    alpha=0.9,
)

ax.set_title("Headline inflation forecasts in the test period")
ax.set_xlabel("Date")
ax.set_ylabel("Annual inflation rate (%)")

ax.legend(
    frameon=False,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.14),
    ncol=2,
)

clean_plot(ax)

figure_path = FIGURES_DIR / "headline_inflation_forecasts_test_period.png"
save_figure(fig, figure_path)

# ---------------------------------------------------------
# Figure 2: Model comparison by RMSE and MAE
# ---------------------------------------------------------

plot_df = metrics_df.sort_values("rmse", ascending=True)

x = np.arange(len(plot_df))
bar_width = 0.35

fig, ax = plt.subplots(figsize=(10.5, 7.0))

bars_mae = ax.bar(
    x - bar_width / 2,
    plot_df["mae"],
    width=bar_width,
    label="MAE",
    color=COLORS["actual"],
)

bars_rmse = ax.bar(
    x + bar_width / 2,
    plot_df["rmse"],
    width=bar_width,
    label="RMSE",
    color=COLORS["exp_smoothing"],
)

ax.set_title("Forecast error comparison by model")
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

figure_path = FIGURES_DIR / "forecast_error_comparison.png"
save_figure(fig, figure_path)

# ---------------------------------------------------------
# Summary text file
# ---------------------------------------------------------

best_model = metrics_df.iloc[0]

summary_path = BASE_DIR / "outputs" / "forecast_model_summary.txt"

with open(summary_path, "w", encoding="utf-8") as file:
    file.write("Forecast Model Comparison Summary\n")
    file.write("=================================\n\n")

    file.write("Objective:\n")
    file.write(
        "Compare simple forecasting models for annual headline inflation in Mexico "
        "using Banxico monthly inflation data.\n\n"
    )

    file.write("Train/test split:\n")
    file.write(f"- Training period: {train['date'].min().date()} to {train['date'].max().date()}\n")
    file.write(f"- Test period: {test_forecasts['date'].min().date()} to {test_forecasts['date'].max().date()}\n\n")

    file.write("Models compared:\n")
    file.write("- Naive forecast: uses the previous month as the forecast.\n")
    file.write("- 12-month moving average: uses the average of the previous 12 months.\n")
    file.write("- Exponential smoothing: gives more weight to recent observations.\n\n")

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
        "Lower MAE and RMSE values indicate better forecast accuracy. "
        "RMSE penalizes larger errors more strongly than MAE, so it is useful "
        "when large forecast mistakes are especially important.\n"
    )

# ---------------------------------------------------------
# Console output
# ---------------------------------------------------------

print("Forecasting analysis completed.")
print(f"Rows in training set: {len(train)}")
print(f"Rows in test set: {len(test_forecasts)}")
print(f"Forecast values saved to: {forecast_values_path}")
print(f"Model comparison saved to: {metrics_path}")
print(f"Summary saved to: {summary_path}")
print(f"Figures saved to: {FIGURES_DIR}")

print("\nModel comparison:")
print(metrics_df.to_string(index=False))