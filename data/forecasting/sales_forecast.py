"""Brasaland consolidated sales forecast.

The series is monthly revenue for all 14 locations. Training uses 2016–2023.
The check uses 2024–2025. Features at month t are known before that month's
revenue is known, so the test years never enter the training rows or the lags
that describe those training rows.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42
# Random Forest, not XGBoost. The series has 120 months, which is too small
# for a boosted model that needs a tuning pass. Mariana needs a ranking of
# good and bad months she can explain, and each tree is already one forecast,
# so the band across trees is the variability range.
TRAIN_START = pd.Timestamp("2016-01-01")
TRAIN_END = pd.Timestamp("2023-12-01")
TEST_START = pd.Timestamp("2024-01-01")
TEST_END = pd.Timestamp("2025-12-01")

COLUMNS = ("month", "revenue_usd", "covers_served", "avg_ticket_usd", "market")
MAGNITUDE_FEATURES = (
    "revenue_lag_1",
    "revenue_lag_12",
    "revenue_roll_3",
    "revenue_roll_12",
    "seasonal_projection",
    "covers_lag_1",
    "ticket_lag_1",
)
CALENDAR_FEATURES = ("month_sin", "month_cos")
FEATURE_COLUMNS = MAGNITUDE_FEATURES + CALENDAR_FEATURES
TARGET = "revenue_usd"


def load_consolidated_sales(path: Path) -> pd.DataFrame:
    """Read the Brasaland file and keep the consolidated month rows.

    Blank cells become missing values and those rows are dropped. A missing
    revenue is not replaced with a guess, because that would change the
    growth and seasonality already in the file.
    """
    frame = pd.read_csv(path)
    missing = [name for name in COLUMNS if name not in frame.columns]
    if missing:
        raise ValueError(f"Sales file is missing columns: {', '.join(missing)}")
    frame = frame.loc[:, list(COLUMNS)].copy()
    frame["month"] = pd.to_datetime(frame["month"], errors="coerce")
    for column in ("revenue_usd", "covers_served", "avg_ticket_usd"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    market = frame["market"].astype("string").str.strip()
    frame["market"] = market.mask(market == "", pd.NA)
    consolidated = frame.loc[frame["market"] == "consolidated"].copy()
    consolidated = consolidated.dropna(
        subset=["month", "revenue_usd", "covers_served", "avg_ticket_usd"]
    )
    consolidated = consolidated.loc[consolidated["revenue_usd"] > 0]
    consolidated = consolidated.sort_values("month").drop_duplicates("month")
    consolidated = consolidated.reset_index(drop=True)
    _require_complete_span(consolidated)
    return consolidated


def _require_complete_span(frame: pd.DataFrame) -> None:
    expected = pd.date_range(TRAIN_START, TEST_END, freq="MS")
    actual = pd.DatetimeIndex(frame["month"])
    if len(actual) != len(expected) or not actual.equals(expected):
        raise ValueError(
            "Brasaland sales must be one consolidated row for every month "
            "from 2016-01 through 2025-12."
        )


def add_causal_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Add lags, rolling history, and the calendar. Nothing reads future rows."""
    featured = frame.copy()
    revenue = featured[TARGET]
    featured["revenue_lag_1"] = revenue.shift(1)
    featured["revenue_lag_12"] = revenue.shift(12)
    featured["revenue_lag_13"] = revenue.shift(13)
    past = revenue.shift(1)
    featured["revenue_roll_3"] = past.rolling(3, min_periods=3).mean()
    featured["revenue_roll_12"] = past.rolling(12, min_periods=12).mean()
    # Last year, scaled by the latest completed year-over-year change.
    featured["seasonal_projection"] = featured["revenue_lag_12"] * (
        featured["revenue_lag_1"] / featured["revenue_lag_13"]
    )
    featured["covers_lag_1"] = featured["covers_served"].shift(1)
    featured["ticket_lag_1"] = featured["avg_ticket_usd"].shift(1)
    month_number = featured["month"].dt.month
    featured["month_sin"] = np.sin(2 * np.pi * month_number / 12)
    featured["month_cos"] = np.cos(2 * np.pi * month_number / 12)
    return featured


def split_by_year(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """First eight years for training, last two years for the check."""
    train = frame.loc[
        (frame["month"] >= TRAIN_START) & (frame["month"] <= TRAIN_END)
    ].copy()
    test = frame.loc[
        (frame["month"] >= TEST_START) & (frame["month"] <= TEST_END)
    ].copy()
    return train.reset_index(drop=True), test.reset_index(drop=True)


def modeling_frames(featured: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Year split, then drop training rows that do not yet have a full year of history."""
    train, test = split_by_year(featured)
    train = train.dropna(subset=list(FEATURE_COLUMNS)).reset_index(drop=True)
    if test[list(FEATURE_COLUMNS)].isna().any().any():
        raise ValueError("A test month is missing history. That would leak or skip a check year.")
    if train.empty or test.empty:
        raise ValueError("The year split produced an empty training or test set.")
    if train["month"].max() >= test["month"].min():
        raise ValueError("Training months overlap the test months.")
    return train, test


def fit_scaler(train: pd.DataFrame) -> StandardScaler:
    """Scale dollar and count features using training rows only."""
    scaler = StandardScaler()
    scaler.fit(train.loc[:, list(MAGNITUDE_FEATURES)])
    return scaler


def design_matrix(frame: pd.DataFrame, scaler: StandardScaler) -> np.ndarray:
    scaled = scaler.transform(frame.loc[:, list(MAGNITUDE_FEATURES)])
    calendar = frame.loc[:, list(CALENDAR_FEATURES)].to_numpy(dtype=float)
    return np.hstack([scaled, calendar])


def fit_forest(
    train_matrix: np.ndarray,
    train_target: np.ndarray,
    max_depth: int,
) -> RandomForestRegressor:
    model = RandomForestRegressor(
        n_estimators=400,
        max_depth=max_depth,
        max_features=1.0,
        min_samples_leaf=2,
        random_state=RANDOM_STATE,
        n_jobs=1,
    )
    model.fit(train_matrix, train_target)
    return model


def train_sales_model(train: pd.DataFrame) -> tuple[StandardScaler, RandomForestRegressor, bool]:
    """Fit the forest on 2016–2023.

    Depth, and whether the trees predict revenue or only the gap versus the
    seasonal projection, is chosen on 2022–2023. Those months are still inside
    the training years. 2024–2025 are not used.
    """
    cutoff = train["month"].max() - pd.DateOffset(months=23)
    earlier = train.loc[train["month"] < cutoff]
    holdout = train.loc[train["month"] >= cutoff]
    if earlier.empty or holdout.empty:
        raise ValueError("The training years do not leave a holdout for depth selection.")

    best: tuple[float, bool, int] | None = None
    for residual in (True, False):
        for depth in (2, 3, 4, 6):
            error = _holdout_error(earlier, holdout, residual, depth)
            if best is None or error < best[0]:
                best = (error, residual, depth)
    assert best is not None
    _, residual, depth = best
    scaler = fit_scaler(train)
    target = _model_target(train, residual)
    model = fit_forest(design_matrix(train, scaler), target, depth)
    model.brasaland_residual_ = residual
    model.brasaland_max_depth_ = depth
    return scaler, model, residual


def _holdout_error(
    earlier: pd.DataFrame,
    holdout: pd.DataFrame,
    residual: bool,
    depth: int,
) -> float:
    scaler = fit_scaler(earlier)
    model = fit_forest(
        design_matrix(earlier, scaler),
        _model_target(earlier, residual),
        depth,
    )
    predicted, _, _ = tree_prediction_band(
        model,
        design_matrix(holdout, scaler),
        holdout["seasonal_projection"].to_numpy(dtype=float),
        residual,
    )
    return mean_squared_error(holdout[TARGET], predicted)


def _model_target(frame: pd.DataFrame, residual: bool) -> np.ndarray:
    revenue = frame[TARGET].to_numpy(dtype=float)
    if not residual:
        return revenue
    return revenue - frame["seasonal_projection"].to_numpy(dtype=float)


def tree_prediction_band(
    model: RandomForestRegressor,
    matrix: np.ndarray,
    seasonal_projection: np.ndarray | None = None,
    residual: bool | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Point forecast plus the 10th and 90th percentile across trees."""
    per_tree = np.vstack([tree.predict(matrix) for tree in model.estimators_])
    if residual is None:
        residual = bool(getattr(model, "brasaland_residual_", False))
    if residual:
        if seasonal_projection is None:
            raise ValueError("A residual forest needs the seasonal projection.")
        per_tree = per_tree + np.asarray(seasonal_projection, dtype=float)
    low = np.percentile(per_tree, 10, axis=0)
    high = np.percentile(per_tree, 90, axis=0)
    midpoint = per_tree.mean(axis=0)
    return midpoint, low, high


def mean_squared_error(actual, predicted) -> float:
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    return float(np.mean((actual - predicted) ** 2))


def mean_absolute_percentage_error(actual, predicted) -> float:
    """Average miss as a percent of that month's sales."""
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    return float(np.mean(np.abs(actual - predicted) / actual) * 100)


def population_stability_index(expected, actual, bins: int = 5) -> float:
    """PSI of the test sample against the training sample.

    The values compared here are year-over-year revenue ratios, not the raw
    dollar level. The briefing's growth pattern moves the dollar level up
    every year, so a dollar-level PSI would call ordinary growth a break.
    """
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    edges = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        edges = np.linspace(
            min(expected.min(), actual.min()),
            max(expected.max(), actual.max()),
            4,
        )
    edges = edges.astype(float)
    edges[0] = -np.inf
    edges[-1] = np.inf
    expected_share = _share(np.histogram(expected, bins=edges)[0])
    actual_share = _share(np.histogram(actual, bins=edges)[0])
    return float(np.sum((actual_share - expected_share) * np.log(actual_share / expected_share)))


def _share(counts: np.ndarray) -> np.ndarray:
    share = counts.astype(float)
    share = np.clip(share / share.sum(), 1e-6, None)
    return share / share.sum()


def normalized_gini(actual, predicted) -> float:
    """1 ranks months in the same order as actual sales. 0 does not rank them."""
    perfect = _gini(actual, actual)
    if perfect == 0:
        return 0.0
    return float(_gini(actual, predicted) / perfect)


def _gini(actual, predicted) -> float:
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    order = np.argsort(predicted, kind="mergesort")
    sorted_actual = actual[order]
    total = sorted_actual.sum()
    if total == 0:
        return 0.0
    cumulative = np.cumsum(sorted_actual)
    n = len(actual)
    return float(cumulative.sum() / total - (n + 1) / 2) / n


def k2_score(actual, predicted, seasonal_naive) -> float:
    """Skill against repeating the same month last year.

    The briefing names K2 Score and does not give its algebra. This is the
    forecast skill score: 1 is a perfect test forecast, 0 ties last year's
    same month, and a negative value is worse than that repeat.
    """
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    seasonal_naive = np.asarray(seasonal_naive, dtype=float)
    model_error = np.sum((actual - predicted) ** 2)
    naive_error = np.sum((actual - seasonal_naive) ** 2)
    if naive_error == 0:
        return 1.0 if model_error == 0 else 0.0
    return float(1 - model_error / naive_error)


def psi_label(value: float) -> str:
    if value < 0.10:
        return "stable"
    if value <= 0.25:
        return "moderate shift"
    return "structural shift; the forest would need retraining"


def evaluate_test(
    test: pd.DataFrame, predicted: np.ndarray, train_yoy: np.ndarray
) -> dict[str, float]:
    """MSE, PSI, Gini, and K2 on the test years only."""
    actual = test[TARGET].to_numpy(dtype=float)
    naive = test["revenue_lag_12"].to_numpy(dtype=float)
    psi = population_stability_index(train_yoy, year_over_year(test))
    return {
        "mse": mean_squared_error(actual, predicted),
        "mape_percent": mean_absolute_percentage_error(actual, predicted),
        "psi": psi,
        "gini": normalized_gini(actual, predicted),
        "k2_score": k2_score(actual, predicted, naive),
    }


def year_over_year(frame: pd.DataFrame) -> np.ndarray:
    return (frame[TARGET] / frame["revenue_lag_12"]).to_numpy(dtype=float)


def save_forecast_chart(
    months: pd.Series,
    actual: np.ndarray,
    predicted: np.ndarray,
    low: np.ndarray,
    high: np.ndarray,
    path: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.fill_between(months, low, high, color="#c5d4c0", label="Variability (10th–90th percentile of trees)")
    axis.plot(months, actual, color="#1f4d2a", linewidth=2, label="Actual revenue")
    axis.plot(months, predicted, color="#c47b2b", linewidth=2, label="Predicted revenue")
    axis.set_title("Brasaland consolidated revenue, test years 2024–2025")
    axis.set_ylabel("Revenue (USD)")
    axis.set_xlabel("Month")
    axis.legend(loc="upper left")
    figure.autofmt_xdate()
    figure.tight_layout()
    figure.savefig(path, dpi=120)
    plt.close(figure)
