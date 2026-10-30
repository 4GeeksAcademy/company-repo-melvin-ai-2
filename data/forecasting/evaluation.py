"""Time-ordered evaluation of the Brasaland sales forest.

Cross-validation and the learning curve use only 2016–2023. The 2024–2025
check years are not read. Features for a fold are rebuilt from months up to
the end of that fold, so a later fold cannot enter an earlier lag or rolling
window.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from data.forecasting.sales_forecast import (
    FEATURE_COLUMNS,
    TARGET,
    TRAIN_END,
    add_causal_features,
    design_matrix,
    fit_forest,
    fit_scaler,
    tree_prediction_band,
)

# Frozen settings of the forest already trained for the sales forecast.
EVAL_DEPTH = 3
EVAL_RESIDUAL = True
N_SPLITS = 5


@dataclass(frozen=True)
class FoldWindow:
    """One chronological training prefix and the validation block after it."""

    train_months: tuple[pd.Timestamp, ...]
    validation_months: tuple[pd.Timestamp, ...]


@dataclass(frozen=True)
class FoldScore:
    train_mae: float
    train_rmse: float
    validation_mae: float
    validation_rmse: float


def training_history(sales: pd.DataFrame) -> pd.DataFrame:
    """Consolidated months through December 2023. The check years are excluded."""
    history = sales.loc[sales["month"] <= TRAIN_END].copy()
    history = history.sort_values("month").reset_index(drop=True)
    if history.empty or history["month"].max() > TRAIN_END:
        raise ValueError("Evaluation history must stop at December 2023.")
    return history


def chronological_folds(months: pd.Series, n_splits: int = N_SPLITS) -> list[FoldWindow]:
    """Return TimeSeriesSplit windows. Validation months always follow training months."""
    ordered = pd.to_datetime(pd.Series(months)).sort_values().reset_index(drop=True)
    if not ordered.is_monotonic_increasing:
        raise ValueError("Fold input months are not in chronological order.")
    splitter = TimeSeriesSplit(n_splits=n_splits)
    windows: list[FoldWindow] = []
    positions = np.arange(len(ordered))
    for train_pos, validation_pos in splitter.split(positions):
        train_months = tuple(pd.Timestamp(value) for value in ordered.iloc[train_pos])
        validation_months = tuple(pd.Timestamp(value) for value in ordered.iloc[validation_pos])
        if max(train_months) >= min(validation_months):
            raise ValueError("A validation month is not after the training months in its fold.")
        windows.append(FoldWindow(train_months, validation_months))
    return windows


def features_through(history: pd.DataFrame, last_month: pd.Timestamp) -> pd.DataFrame:
    """Rebuild causal features using only months up to ``last_month``."""
    clipped = history.loc[history["month"] <= last_month].copy()
    return add_causal_features(clipped)


def assert_fold_order(windows: list[FoldWindow]) -> None:
    """Every training month is earlier than every validation month in that fold."""
    previous_validation_end = None
    for window in windows:
        train_months = list(window.train_months)
        validation_months = list(window.validation_months)
        if train_months != sorted(train_months) or validation_months != sorted(validation_months):
            raise AssertionError("Months inside a fold are not chronological.")
        if max(train_months) >= min(validation_months):
            raise AssertionError("A validation month is earlier than a training month in the same fold.")
        if previous_validation_end is not None and min(validation_months) <= previous_validation_end:
            raise AssertionError("A later fold starts before the previous fold's validation block.")
        previous_validation_end = max(validation_months)


def cross_validate(history: pd.DataFrame) -> tuple[list[FoldWindow], list[FoldScore]]:
    """Five expanding prefixes inside the training years."""
    usable = _usable_months(history)
    windows = chronological_folds(usable)
    assert_fold_order(windows)
    scores = [score_fold(history, window) for window in windows]
    return windows, scores


def score_fold(history: pd.DataFrame, window: FoldWindow) -> FoldScore:
    """Fit the frozen forest on one prefix and score the following block."""
    featured = features_through(history, window.validation_months[-1])
    if featured["month"].max() > window.validation_months[-1]:
        raise ValueError("A fold was fit with months after its validation block.")
    train = _complete(featured, window.train_months)
    validation = _complete(featured, window.validation_months)
    if train.empty or len(validation) != len(window.validation_months):
        raise ValueError("A cross-validation fold lost a validation month to missing history.")
    _assert_training_lags_stay_before_validation(history, train, validation["month"].min())
    return _score_frames(train, validation)


def learning_curve_points(history: pd.DataFrame) -> list[tuple[int, float, float]]:
    """Grow the training prefix and score the next 12 months inside 2016–2023."""
    featured = features_through(history, history["month"].max()).dropna(subset=list(FEATURE_COLUMNS))
    featured = featured.sort_values("month").reset_index(drop=True)
    holdout_length = 12
    if len(featured) <= holdout_length + 18:
        raise ValueError("The training years are too short for a learning curve.")
    points: list[tuple[int, float, float]] = []
    last_train_size = len(featured) - holdout_length
    for size in _prefix_sizes(last_train_size):
        train = featured.iloc[:size]
        validation = featured.iloc[size : size + holdout_length]
        if train["month"].max() >= validation["month"].min():
            raise ValueError("The learning-curve validation block is not after its training prefix.")
        if validation["month"].max() > TRAIN_END:
            raise ValueError("The learning curve reached 2024.")
        score = _score_frames(train, validation)
        points.append((int(size), score.train_rmse, score.validation_rmse))
    return points


def summarize(scores: list[FoldScore]) -> dict[str, float]:
    validation_rmse = np.array([score.validation_rmse for score in scores], dtype=float)
    validation_mae = np.array([score.validation_mae for score in scores], dtype=float)
    train_rmse = np.array([score.train_rmse for score in scores], dtype=float)
    train_mae = np.array([score.train_mae for score in scores], dtype=float)
    return {
        "validation_rmse_mean": float(validation_rmse.mean()),
        "validation_rmse_std": float(validation_rmse.std(ddof=1)),
        "validation_mae_mean": float(validation_mae.mean()),
        "validation_mae_std": float(validation_mae.std(ddof=1)),
        "train_rmse_mean": float(train_rmse.mean()),
        "train_rmse_std": float(train_rmse.std(ddof=1)),
        "train_mae_mean": float(train_mae.mean()),
        "train_mae_std": float(train_mae.std(ddof=1)),
    }


def diagnose(points: list[tuple[int, float, float]]) -> tuple[str, str]:
    """Classify the end of the learning curve and name one matching change."""
    _, train_error, validation_error = points[-1]
    gap = validation_error - train_error
    relative_gap = gap / validation_error if validation_error else 0.0
    wide_gap = relative_gap > 0.25 and train_error < validation_error * 0.75
    high_error = min(train_error, validation_error) > 80_000
    if wide_gap and not high_error:
        return (
            "overfitting",
            "Raise `min_samples_leaf` from 2 to 4 on this RandomForestRegressor "
            "so each leaf needs more months, and do not increase `max_depth` above 3.",
        )
    if high_error and relative_gap <= 0.25:
        return (
            "underfitting",
            "Raise `max_depth` from 3 to 6 so the forest can follow the December rise "
            "and the January drop, and do not add more years of data as the first change.",
        )
    return (
        "well fitted",
        "Keep `max_depth=3`, `min_samples_leaf=2`, and the seasonal residual. "
        "Do not add features and do not deepen the forest.",
    )


def save_learning_curve(points: list[tuple[int, float, float]], path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    sizes = [point[0] for point in points]
    train_error = [point[1] for point in points]
    validation_error = [point[2] for point in points]
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.plot(sizes, train_error, color="#1f4d2a", linewidth=2, marker="o", label="Training RMSE")
    axis.plot(
        sizes,
        validation_error,
        color="#c47b2b",
        linewidth=2,
        marker="o",
        label="Validation RMSE",
    )
    axis.set_title("Brasaland sales forest learning curve, training years only")
    axis.set_xlabel("Training months")
    axis.set_ylabel("RMSE (USD)")
    axis.legend(loc="best")
    figure.tight_layout()
    figure.savefig(path, dpi=120)
    plt.close(figure)


def _usable_months(history: pd.DataFrame) -> pd.Series:
    featured = features_through(history, history["month"].max())
    complete = featured.dropna(subset=list(FEATURE_COLUMNS))
    return complete.sort_values("month")["month"].reset_index(drop=True)


def _complete(featured: pd.DataFrame, months: tuple[pd.Timestamp, ...]) -> pd.DataFrame:
    selected = featured.loc[featured["month"].isin(months)].copy()
    return selected.dropna(subset=list(FEATURE_COLUMNS)).sort_values("month")


def _assert_training_lags_stay_before_validation(
    history: pd.DataFrame, train: pd.DataFrame, validation_start: pd.Timestamp
) -> None:
    by_month = history.set_index("month")[TARGET]
    for month, lag in zip(train["month"], train["revenue_lag_1"], strict=True):
        source = month - pd.DateOffset(months=1)
        if source >= validation_start:
            raise ValueError("A training lag reaches into the validation window.")
        if not np.isclose(float(lag), float(by_month.loc[source])):
            raise ValueError("A training lag does not match the earlier month's revenue.")


def _score_frames(train: pd.DataFrame, validation: pd.DataFrame) -> FoldScore:
    scaler = fit_scaler(train)
    model = fit_forest(design_matrix(train, scaler), _target(train), EVAL_DEPTH)
    train_prediction = _predict(model, train, scaler)
    validation_prediction = _predict(model, validation, scaler)
    return FoldScore(
        train_mae=_mae(train[TARGET], train_prediction),
        train_rmse=_rmse(train[TARGET], train_prediction),
        validation_mae=_mae(validation[TARGET], validation_prediction),
        validation_rmse=_rmse(validation[TARGET], validation_prediction),
    )


def _target(frame: pd.DataFrame) -> np.ndarray:
    revenue = frame[TARGET].to_numpy(dtype=float)
    if not EVAL_RESIDUAL:
        return revenue
    return revenue - frame["seasonal_projection"].to_numpy(dtype=float)


def _predict(model, frame: pd.DataFrame, scaler) -> np.ndarray:
    midpoint, _, _ = tree_prediction_band(
        model,
        design_matrix(frame, scaler),
        frame["seasonal_projection"].to_numpy(dtype=float),
        EVAL_RESIDUAL,
    )
    return midpoint


def _mae(actual, predicted) -> float:
    return float(np.mean(np.abs(np.asarray(actual, dtype=float) - np.asarray(predicted, dtype=float))))


def _rmse(actual, predicted) -> float:
    error = np.asarray(actual, dtype=float) - np.asarray(predicted, dtype=float)
    return float(np.sqrt(np.mean(error**2)))


def _prefix_sizes(last_train_size: int) -> list[int]:
    raw = np.linspace(18, last_train_size, num=6)
    return sorted({int(size) for size in raw if 18 <= int(size) <= last_train_size})
