"""The sales forecast uses eight training years and two unseen test years."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.forecasting.sales_forecast import (
    FEATURE_COLUMNS,
    add_causal_features,
    fit_scaler,
    load_consolidated_sales,
    modeling_frames,
    split_by_year,
)

CSV = ROOT / "data" / "raw" / "brasaland_sales.csv"


def test_split_is_eight_training_years_and_two_test_years():
    sales = load_consolidated_sales(CSV)
    train, test = split_by_year(sales)

    assert len(train) == 96
    assert len(test) == 24
    assert set(train["month"].dt.year.unique()) == set(range(2016, 2024))
    assert set(test["month"].dt.year.unique()) == {2024, 2025}
    assert train["month"].max() < test["month"].min()
    assert set(train["month"]).isdisjoint(set(test["month"]))


def test_model_rows_do_not_leak_test_months_or_the_current_revenue():
    featured = add_causal_features(load_consolidated_sales(CSV))
    train, test = modeling_frames(featured)

    assert train["month"].max() < pd.Timestamp("2024-01-01")
    assert test["month"].min() == pd.Timestamp("2024-01-01")
    assert test["month"].max() == pd.Timestamp("2025-12-01")
    assert len(test) == 24
    assert set(train["month"]).isdisjoint(set(test["month"]))

    previous_revenue = featured["revenue_usd"].shift(1)
    rolling = previous_revenue.rolling(3, min_periods=3).mean()
    pd.testing.assert_series_equal(
        featured["revenue_lag_1"],
        previous_revenue,
        check_names=False,
    )
    pd.testing.assert_series_equal(
        featured["revenue_roll_3"],
        rolling,
        check_names=False,
    )
    assert featured.loc[featured["month"] == "2016-06-01", "revenue_lag_1"].iloc[0] != (
        featured.loc[featured["month"] == "2016-06-01", "revenue_usd"].iloc[0]
    )
    assert not test[list(FEATURE_COLUMNS)].isna().any().any()

    scaler = fit_scaler(train)
    assert scaler.n_samples_seen_ == len(train)
