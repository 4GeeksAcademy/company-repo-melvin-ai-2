"""Train the Brasaland sales forest and score the two held-out years.

Run from the repository root:

    uv run python scripts/train_sales_forecast.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.forecasting.sales_forecast import (
    RANDOM_STATE,
    add_causal_features,
    design_matrix,
    evaluate_test,
    load_consolidated_sales,
    modeling_frames,
    psi_label,
    save_forecast_chart,
    train_sales_model,
    tree_prediction_band,
    year_over_year,
)

SALES_PATH = ROOT / "data" / "raw" / "brasaland_sales.csv"
CHART_PATH = ROOT / "data" / "eval" / "sales_forecast_test.png"
REPORT_PATH = ROOT / "data" / "eval" / "sales_forecast_report.md"


def main() -> None:
    sales = load_consolidated_sales(SALES_PATH)
    train, test = modeling_frames(add_causal_features(sales))
    scaler, model, residual = train_sales_model(train)
    predicted, low, high = tree_prediction_band(
        model,
        design_matrix(test, scaler),
        test["seasonal_projection"].to_numpy(dtype=float),
        residual,
    )
    metrics = evaluate_test(test, predicted, year_over_year(train))
    save_forecast_chart(
        test["month"],
        test["revenue_usd"].to_numpy(dtype=float),
        predicted,
        low,
        high,
        CHART_PATH,
    )
    report = _report(train, test, metrics, model)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report)
    print(report)
    print(f"chart {CHART_PATH.relative_to(ROOT)}")
    print(f"random_state {RANDOM_STATE}")


def _report(train, test, metrics: dict[str, float], model) -> str:
    return "\n".join(
        [
            "# Brasaland sales forecast — test years 2024–2025",
            "",
            "Random Forest (`random_state=42`). "
            f"Trees predict {'the gap versus the seasonal projection' if getattr(model, 'brasaland_residual_', False) else 'revenue directly'}"
            f" at max depth {getattr(model, 'brasaland_max_depth_', 'default')}, "
            "chosen on 2022–2023 inside the training years. Training months are "
            f"{train['month'].min():%Y-%m} through {train['month'].max():%Y-%m} "
            f"({len(train)} rows after the first year of lag history). "
            f"Test months are {test['month'].min():%Y-%m} through {test['month'].max():%Y-%m} "
            f"({len(test)} rows). The forest did not see 2024 or 2025 during training.",
            "",
            f"- MSE: {metrics['mse']:.0f} USD²",
            f"- Average percentage error: {metrics['mape_percent']:.1f}% of that month's sales",
            f"- PSI: {metrics['psi']:.3f} ({psi_label(metrics['psi'])})",
            f"- Gini: {metrics['gini']:.3f}",
            f"- K2 Score: {metrics['k2_score']:.3f}",
            "",
            "PSI compares the year-over-year revenue ratio in the test years with the same ratio in the training years. "
            "A value above 0.25 means the growth behavior changed enough that the forest should be retrained. "
            "The dollar level itself is expected to rise because the series grows about 3% to 7% a year.",
            "",
            "The chart is `data/eval/sales_forecast_test.png`.",
            "",
        ]
    )


if __name__ == "__main__":
    main()
