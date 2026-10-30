"""Time-ordered folds for the Brasaland sales forest. No shuffled split."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.forecasting.evaluation import (
    assert_fold_order,
    chronological_folds,
    features_through,
    training_history,
)
from data.forecasting.sales_forecast import load_consolidated_sales

CSV = ROOT / "data" / "raw" / "brasaland_sales.csv"


def test_each_fold_keeps_chronological_order_and_stops_before_2024():
    sales = load_consolidated_sales(CSV)
    history = training_history(sales)
    usable = features_through(history, history["month"].max()).dropna()
    windows = chronological_folds(usable.sort_values("month")["month"])

    assert len(windows) == 5
    assert history["month"].max() < pd.Timestamp("2024-01-01")
    assert_fold_order(windows)
    for window in windows:
        assert list(window.train_months) == sorted(window.train_months)
        assert list(window.validation_months) == sorted(window.validation_months)
        assert max(window.train_months) < min(window.validation_months)


def test_a_fold_does_not_rebuild_features_from_a_later_fold():
    sales = load_consolidated_sales(CSV)
    history = training_history(sales)
    usable = features_through(history, history["month"].max()).dropna()
    windows = chronological_folds(usable.sort_values("month")["month"])
    first = windows[0]
    featured = features_through(history, first.validation_months[-1])

    assert featured["month"].max() == first.validation_months[-1]
    assert featured["month"].max() < windows[-1].validation_months[-1]
