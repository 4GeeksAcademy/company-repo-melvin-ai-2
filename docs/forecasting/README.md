# Brasaland sales forecast

Finance asked whether consolidated monthly sales for the 14 locations can be predicted before a full executive dashboard is built. The series is `data/raw/brasaland_sales.csv`. The business rules are in [`CONTEXT-company.md`](./CONTEXT-company.md).

Train and score it from the repository root:

```bash
uv run python scripts/train_sales_forecast.py
```

The check chart is written to `data/eval/sales_forecast_test.png`. The numbers are written to `data/eval/sales_forecast_report.md`.

## Why Random Forest

The model is `sklearn.ensemble.RandomForestRegressor` with `random_state=42`. Depth, and whether the trees predict revenue itself or only the gap versus last year's same month adjusted for the latest growth, is chosen on 2022–2023. Those months are inside the training window. The test years are not used to make that choice.

- The file has 120 months. A boosted model needs a tuning search this sample does not support.
- Mariana needs to tell a strong month from a weak month in advance. A forest is an average of simple seasonal rules, which is explainable in that meeting.
- Each tree is its own forecast. The chart band is the 10th to 90th percentile of those trees, so the result is a range rather than one optimistic number.

Same-month covers and average ticket are not features. Together they nearly equal revenue, so using them would report the month after it happened. Lags, rolling history, and the calendar are known before the month closes.

Dollar and count features are scaled with `StandardScaler` fit on the training rows only. Month sine and cosine are already on one scale, so they are not scaled. The forest does not use the scale to choose a split; the scaler is there so those columns are not compared in raw dollars versus guest counts.

One feature is last year's same month, adjusted by the latest completed year-over-year change. Both inputs are earlier months, so the adjustment does not see the month being scored.

## What the test metrics mean

All four graded metrics are computed on 2024–2025. The forest is not scored on the training years.

- **MSE** is the average squared miss, in USD². A single large miss dominates it, so a low MSE can hide a month that was badly ranked. The report also gives the average absolute miss as a percent of that month's sales, which is the figure Felipe and Mariana can read.
- **PSI** compares the year-over-year revenue ratio in the test years with the same ratio in the training years. Below 0.10, growth behavior is stable. From 0.10 to 0.25, watch it. Above 0.25, the pattern has shifted enough that the forest should be retrained. The raw dollar level is not the PSI input: the briefing's growth of about 3% to 7% a year would make every later year look like a new population.
- **Gini** says whether the forecast ranks months in the same order as actual sales. 1 is a perfect ordering. Near 0, the model does not separate good months from bad ones, even if the dollar error looks small.
- **K2 Score** is the skill against repeating the same month last year: `1 - (forest squared error / last-year squared error)`. The briefing names this score and does not give the algebra; this is the forecast skill score. 1 is a perfect test forecast. 0 ties "same month last year." A negative score is worse than that repeat.

## Split

2016–2023 is training (96 months). 2024–2025 is the check (24 months). The first 12 training months are dropped only because a 12-month lag does not exist yet. Those dropped months are still inside the training years, and no 2024 or 2025 row is used to build a training feature.
