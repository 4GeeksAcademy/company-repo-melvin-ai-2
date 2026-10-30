# Brasaland sales forest — technical evaluation

Diagnosis: **overfitting**.

The forest under review is the one already trained for consolidated monthly revenue: `RandomForestRegressor` with `random_state=42`, `max_depth=3`, `min_samples_leaf=2`, and residual mode on. Every fold and every point on the learning curve uses only months through December 2023. 2024 and 2025 are not in this evaluation.

## Primary metric

RMSE is primary. MAE is the typical dollar miss.

The Brasaland briefing does not say whether a forecast that is too high costs more than one that is too low. It does say December sales rise 20–30% and January sales fall 12–18%, and Felipe buys ingredients from the expected trend. Missing one of those months by a large amount is more serious than missing several ordinary months by a little. RMSE counts those large misses more heavily. MAE is still reported so Finance can read the average dollar miss.

## Cross-validation

Five `TimeSeriesSplit` folds. Each training block is a prefix. Each validation block is the next contiguous months. Features for a fold are rebuilt from months up to the end of that fold, and the scaler is fit on that fold's training rows only.

- Validation RMSE: 43,807 ± 7,923 USD
- Validation MAE: 35,800 ± 5,308 USD
- Training RMSE: 16,771 ± 3,741 USD
- Training MAE: 13,136 ± 2,545 USD

| Fold | Training months | Validation months | Train RMSE | Validation RMSE | Train MAE | Validation MAE |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 1 | 2017-02–2018-07 | 2018-08–2019-08 | 12,285 | 37,687 | 10,098 | 31,383 |
| 2 | 2017-02–2019-08 | 2019-09–2020-09 | 15,305 | 34,319 | 12,082 | 30,640 |
| 3 | 2017-02–2020-09 | 2020-10–2021-10 | 15,009 | 50,010 | 11,946 | 40,380 |
| 4 | 2017-02–2021-10 | 2021-11–2022-11 | 19,975 | 43,986 | 15,472 | 34,229 |
| 5 | 2017-02–2022-11 | 2022-12–2023-12 | 21,279 | 53,033 | 16,083 | 42,367 |

Changing the training window does not remove the gap. Validation RMSE stays between 34,319 and 53,033 USD across the five folds (43,807 ± 7,923). Every fold still has a lower training error than validation error.

## Learning curve

The training prefix grows in time order. The error at each size is RMSE on that prefix and on the next 12 months, still inside 2016–2023. The figure is `data/eval/learning_curve.png`.

At 71 training months, training RMSE is 21,127 USD and validation RMSE is 55,688 USD. The gap is 34,561 USD. That gap is present at every prefix size and does not close as more training months are added. Training error stays low while validation error stays about twice as high. That is overfitting: the forest fits the months it has already seen more tightly than the next year.

| Training months | Training RMSE (USD) | Validation RMSE (USD) |
| ---: | ---: | ---: |
| 18 | 12,285 | 32,319 |
| 28 | 14,796 | 40,129 |
| 39 | 15,150 | 37,743 |
| 49 | 18,010 | 46,641 |
| 60 | 19,768 | 43,058 |
| 71 | 21,127 | 55,688 |

## Corrective action

Raise `min_samples_leaf` from 2 to 4 on this RandomForestRegressor so each leaf needs more months, and do not increase `max_depth` above 3.
