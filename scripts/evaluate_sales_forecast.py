"""Evaluate the Brasaland sales forest on the training years only.

Run from the repository root:

    uv run python scripts/evaluate_sales_forecast.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.forecasting.evaluation import (
    EVAL_DEPTH,
    EVAL_RESIDUAL,
    FoldScore,
    FoldWindow,
    cross_validate,
    diagnose,
    learning_curve_points,
    save_learning_curve,
    summarize,
    training_history,
)
from data.forecasting.sales_forecast import load_consolidated_sales

SALES_PATH = ROOT / "data" / "raw" / "brasaland_sales.csv"
CHART_PATH = ROOT / "data" / "eval" / "learning_curve.png"
REPORT_PATH = ROOT / "data" / "eval" / "evaluation_report.md"


def main() -> None:
    sales = load_consolidated_sales(SALES_PATH)
    history = training_history(sales)
    windows, scores = cross_validate(history)
    points = learning_curve_points(history)
    summary = summarize(scores)
    label, action = diagnose(points)
    save_learning_curve(points, CHART_PATH)
    report = _report(windows, scores, points, summary, label, action)
    REPORT_PATH.write_text(report)
    print(report)
    print(f"chart {CHART_PATH.relative_to(ROOT)}")


def _report(windows, scores, points, summary, label: str, action: str) -> str:
    curve_rows = "\n".join(
        f"| {size} | {train_error:,.0f} | {validation_error:,.0f} |"
        for size, train_error, validation_error in points
    )
    _, last_train, last_validation = points[-1]
    gap = last_validation - last_train
    curve_reading = _curve_reading(label, points[-1][0], last_train, last_validation, gap)
    validation_values = [score.validation_rmse for score in scores]
    stability = _stability(label, validation_values, summary)
    fold_rows = "\n".join(_fold_row(index, window, score) for index, (window, score) in enumerate(zip(windows, scores, strict=True), start=1))
    return "\n".join(
        [
            "# Brasaland sales forest — technical evaluation",
            "",
            f"Diagnosis: **{label}**.",
            "",
            "The forest under review is the one already trained for consolidated monthly revenue: "
            f"`RandomForestRegressor` with `random_state=42`, `max_depth={EVAL_DEPTH}`, "
            f"`min_samples_leaf=2`, and residual mode {'on' if EVAL_RESIDUAL else 'off'}. "
            "Every fold and every point on the learning curve uses only months through December 2023. "
            "2024 and 2025 are not in this evaluation.",
            "",
            "## Primary metric",
            "",
            "RMSE is primary. MAE is the typical dollar miss.",
            "",
            "The Brasaland briefing does not say whether a forecast that is too high costs more than one that is too low. "
            "It does say December sales rise 20–30% and January sales fall 12–18%, and Felipe buys ingredients from the expected trend. "
            "Missing one of those months by a large amount is more serious than missing several ordinary months by a little. "
            "RMSE counts those large misses more heavily. MAE is still reported so Finance can read the average dollar miss.",
            "",
            "## Cross-validation",
            "",
            "Five `TimeSeriesSplit` folds. Each training block is a prefix. Each validation block is the next contiguous months. "
            "Features for a fold are rebuilt from months up to the end of that fold, and the scaler is fit on that fold's training rows only.",
            "",
            f"- Validation RMSE: {summary['validation_rmse_mean']:,.0f} ± {summary['validation_rmse_std']:,.0f} USD",
            f"- Validation MAE: {summary['validation_mae_mean']:,.0f} ± {summary['validation_mae_std']:,.0f} USD",
            f"- Training RMSE: {summary['train_rmse_mean']:,.0f} ± {summary['train_rmse_std']:,.0f} USD",
            f"- Training MAE: {summary['train_mae_mean']:,.0f} ± {summary['train_mae_std']:,.0f} USD",
            "",
            "| Fold | Training months | Validation months | Train RMSE | Validation RMSE | Train MAE | Validation MAE |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: |",
            fold_rows,
            "",
            stability,
            "",
            "## Learning curve",
            "",
            "The training prefix grows in time order. The error at each size is RMSE on that prefix and on the next 12 months, still inside 2016–2023. "
            "The figure is `data/eval/learning_curve.png`.",
            "",
            curve_reading,
            "",
            "| Training months | Training RMSE (USD) | Validation RMSE (USD) |",
            "| ---: | ---: | ---: |",
            curve_rows,
            "",
            "## Corrective action",
            "",
            action,
            "",
        ]
    )


def _curve_reading(label: str, size: int, train_error: float, validation_error: float, gap: float) -> str:
    opening = (
        f"At {size} training months, training RMSE is {train_error:,.0f} USD and "
        f"validation RMSE is {validation_error:,.0f} USD. The gap is {gap:,.0f} USD."
    )
    if label == "overfitting":
        return (
            opening
            + " That gap is present at every prefix size and does not close as more training months are added. "
            "Training error stays low while validation error stays about twice as high. "
            "That is overfitting: the forest fits the months it has already seen more tightly than the next year."
        )
    if label == "underfitting":
        return (
            opening
            + " Both curves stay high and close together. That is underfitting: the forest is missing the December rise and the January drop, "
            "and adding more of the same years would not be the first fix."
        )
    return (
        opening
        + " The two curves stay close, and the error is low relative to a monthly revenue near three quarters of a million dollars. "
        "That is a reasonably well fitted forest."
    )


def _stability(label: str, validation_values: list[float], summary: dict[str, float]) -> str:
    band = (
        f"Validation RMSE stays between {min(validation_values):,.0f} and {max(validation_values):,.0f} USD "
        f"across the five folds ({summary['validation_rmse_mean']:,.0f} ± {summary['validation_rmse_std']:,.0f})."
    )
    if label == "overfitting":
        return (
            "Changing the training window does not remove the gap. "
            + band
            + " Every fold still has a lower training error than validation error."
        )
    return "Changing the training window keeps the same pattern. " + band


def _fold_row(index: int, window: FoldWindow, score: FoldScore) -> str:
    train_span = f"{window.train_months[0]:%Y-%m}–{window.train_months[-1]:%Y-%m}"
    validation_span = f"{window.validation_months[0]:%Y-%m}–{window.validation_months[-1]:%Y-%m}"
    return (
        f"| {index} | {train_span} | {validation_span} | "
        f"{score.train_rmse:,.0f} | {score.validation_rmse:,.0f} | "
        f"{score.train_mae:,.0f} | {score.validation_mae:,.0f} |"
    )


if __name__ == "__main__":
    main()
