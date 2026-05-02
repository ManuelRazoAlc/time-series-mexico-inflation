from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# 03_exploratory_analysis.py
# Purpose:
# Create exploratory tables and figures for headline, core
# and non-core annual inflation in Mexico.
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

PROCESSED_PATH = BASE_DIR / "data" / "processed" / "inflation_monthly_processed.csv"
FIGURES_DIR = BASE_DIR / "outputs" / "figures"
TABLES_DIR = BASE_DIR / "outputs" / "tables"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)
TABLES_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(PROCESSED_PATH, parse_dates=["date"])

# ---------------------------------------------------------
# Visual configuration
# ---------------------------------------------------------

COLORS = {
    "headline": "#1f77b4",   # blue
    "core": "#ff7f0e",       # orange
    "non_core": "#2ca02c",   # green
    "gray": "#555555",
    "light_gray": "#d9d9d9",
    "red": "#d62728",
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
    """
    Apply a consistent clean visual style to matplotlib axes.
    """
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.25, linewidth=0.8)
    ax.set_axisbelow(True)


def save_figure(fig, path):
    """
    Save figure with consistent spacing and high resolution.
    """
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)

# ---------------------------------------------------------
# Descriptive statistics
# ---------------------------------------------------------

main_vars = ["headline", "core", "non_core"]

descriptive_stats = (
    df[main_vars]
    .describe()
    .T
    .reset_index()
    .rename(columns={"index": "variable"})
)

descriptive_stats_path = TABLES_DIR / "descriptive_statistics.csv"
descriptive_stats.to_csv(descriptive_stats_path, index=False, encoding="utf-8-sig")

# ---------------------------------------------------------
# Correlation table
# ---------------------------------------------------------

correlation_matrix = df[main_vars].corr()

correlation_path = TABLES_DIR / "inflation_correlation_matrix.csv"
correlation_matrix.to_csv(correlation_path, encoding="utf-8-sig")

# ---------------------------------------------------------
# Volatility table
# Standard deviation is used as a simple measure of volatility.
# ---------------------------------------------------------

volatility = pd.DataFrame(
    {
        "variable": main_vars,
        "standard_deviation": [df[var].std() for var in main_vars],
        "minimum": [df[var].min() for var in main_vars],
        "maximum": [df[var].max() for var in main_vars],
        "range": [df[var].max() - df[var].min() for var in main_vars],
    }
)

volatility_path = TABLES_DIR / "inflation_volatility_summary.csv"
volatility.to_csv(volatility_path, index=False, encoding="utf-8-sig")

# ---------------------------------------------------------
# Figure 1: Headline, core and non-core inflation
# ---------------------------------------------------------

fig, ax = plt.subplots(figsize=(12.5, 6.5))

ax.plot(
    df["date"],
    df["headline"],
    label="Headline inflation",
    linewidth=2.2,
    color=COLORS["headline"],
)

ax.plot(
    df["date"],
    df["core"],
    label="Core inflation",
    linewidth=2.2,
    color=COLORS["core"],
)

ax.plot(
    df["date"],
    df["non_core"],
    label="Non-core inflation",
    linewidth=2.0,
    color=COLORS["non_core"],
    alpha=0.9,
)

ax.set_title("Annual inflation components in Mexico")
ax.set_xlabel("Date")
ax.set_ylabel("Annual inflation rate (%)")
ax.legend(frameon=False, loc="upper right")
clean_plot(ax)

figure_path = FIGURES_DIR / "inflation_components_time_series.png"
save_figure(fig, figure_path)

# ---------------------------------------------------------
# Figure 2: Headline inflation and moving averages
# ---------------------------------------------------------

fig, ax = plt.subplots(figsize=(12.5, 6.5))

ax.plot(
    df["date"],
    df["headline"],
    label="Headline inflation",
    linewidth=1.6,
    color=COLORS["headline"],
    alpha=0.75,
)

ax.plot(
    df["date"],
    df["headline_ma_3"],
    label="3-month moving average",
    linewidth=2.1,
    color=COLORS["core"],
)

ax.plot(
    df["date"],
    df["headline_ma_12"],
    label="12-month moving average",
    linewidth=2.4,
    color=COLORS["non_core"],
)

ax.set_title("Headline inflation and moving averages")
ax.set_xlabel("Date")
ax.set_ylabel("Annual inflation rate (%)")
ax.legend(frameon=False, loc="upper right")
clean_plot(ax)

figure_path = FIGURES_DIR / "headline_inflation_moving_averages.png"
save_figure(fig, figure_path)

# ---------------------------------------------------------
# Figure 3: Monthly changes in annual inflation
# ---------------------------------------------------------

fig, ax = plt.subplots(figsize=(12.5, 6.5))

ax.plot(
    df["date"],
    df["headline_change"],
    label="Monthly change",
    linewidth=1.7,
    color=COLORS["headline"],
)

ax.axhline(
    0,
    linestyle="--",
    linewidth=1.2,
    color=COLORS["gray"],
)

ax.set_title("Monthly change in annual headline inflation")
ax.set_xlabel("Date")
ax.set_ylabel("Change in annual inflation rate, percentage points")
ax.legend(frameon=False, loc="upper left")
clean_plot(ax)

figure_path = FIGURES_DIR / "headline_inflation_monthly_changes.png"
save_figure(fig, figure_path)

# ---------------------------------------------------------
# Figure 4: Boxplot comparing distributions
# ---------------------------------------------------------

fig, ax = plt.subplots(figsize=(9.5, 6.5))

data_to_plot = [df["headline"], df["core"], df["non_core"]]

box = ax.boxplot(
    data_to_plot,
    tick_labels=["Headline", "Core", "Non-core"],
    showmeans=True,
    patch_artist=True,
    medianprops={"color": "#222222", "linewidth": 2},
    meanprops={
        "marker": "D",
        "markerfacecolor": "#222222",
        "markeredgecolor": "#222222",
        "markersize": 6,
    },
    boxprops={"linewidth": 1.3},
    whiskerprops={"linewidth": 1.3},
    capprops={"linewidth": 1.3},
)

box_colors = [COLORS["headline"], COLORS["core"], COLORS["non_core"]]

for patch, color in zip(box["boxes"], box_colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.35)

ax.set_title("Distribution of annual inflation components")
ax.set_ylabel("Annual inflation rate (%)")
ax.grid(axis="y", alpha=0.25)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

figure_path = FIGURES_DIR / "inflation_components_boxplot.png"
save_figure(fig, figure_path)

# ---------------------------------------------------------
# Figure 5: Gap between headline and components
# ---------------------------------------------------------

df["headline_core_gap"] = df["headline"] - df["core"]
df["headline_non_core_gap"] = df["headline"] - df["non_core"]

gap_summary = pd.DataFrame(
    {
        "variable": ["headline_minus_core", "headline_minus_non_core"],
        "mean": [
            df["headline_core_gap"].mean(),
            df["headline_non_core_gap"].mean(),
        ],
        "standard_deviation": [
            df["headline_core_gap"].std(),
            df["headline_non_core_gap"].std(),
        ],
        "minimum": [
            df["headline_core_gap"].min(),
            df["headline_non_core_gap"].min(),
        ],
        "maximum": [
            df["headline_core_gap"].max(),
            df["headline_non_core_gap"].max(),
        ],
    }
)

gap_summary_path = TABLES_DIR / "inflation_component_gaps_summary.csv"
gap_summary.to_csv(gap_summary_path, index=False, encoding="utf-8-sig")

fig, ax = plt.subplots(figsize=(12.5, 7.2))

ax.plot(
    df["date"],
    df["headline_core_gap"],
    label="Headline minus core",
    linewidth=2,
    color=COLORS["core"],
)

ax.plot(
    df["date"],
    df["headline_non_core_gap"],
    label="Headline minus non-core",
    linewidth=2,
    color=COLORS["non_core"],
)

ax.axhline(
    0,
    linestyle="--",
    linewidth=1.2,
    color=COLORS["gray"],
)

ax.set_title("Gap between headline inflation and its components")
ax.set_xlabel("Date")
ax.set_ylabel("Difference in percentage points")

ax.legend(
    frameon=False,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.14),
    ncol=2,
)

clean_plot(ax)

figure_path = FIGURES_DIR / "inflation_component_gaps.png"
save_figure(fig, figure_path)

# ---------------------------------------------------------
# Console output
# ---------------------------------------------------------

print("Exploratory analysis completed.")
print(f"Descriptive statistics saved to: {descriptive_stats_path}")
print(f"Correlation matrix saved to: {correlation_path}")
print(f"Volatility summary saved to: {volatility_path}")
print(f"Gap summary saved to: {gap_summary_path}")
print(f"Figures saved to: {FIGURES_DIR}")

print("\nDescriptive statistics:")
print(descriptive_stats.to_string(index=False))

print("\nCorrelation matrix:")
print(correlation_matrix)

print("\nVolatility summary:")
print(volatility.to_string(index=False))

print("\nGap summary:")
print(gap_summary.to_string(index=False))