# Brasaland sales forecast — test years 2024–2025

Random Forest (`random_state=42`). Trees predict the gap versus the seasonal projection at max depth 3, chosen on 2022–2023 inside the training years. Training months are 2017-02 through 2023-12 (83 rows after the first year of lag history). Test months are 2024-01 through 2025-12 (24 rows). The forest did not see 2024 or 2025 during training.

- MSE: 1705988660 USD²
- Average percentage error: 4.4% of that month's sales
- PSI: 0.204 (moderate shift)
- Gini: 0.790
- K2 Score: 0.132

PSI compares the year-over-year revenue ratio in the test years with the same ratio in the training years. A value above 0.25 means the growth behavior changed enough that the forest should be retrained. The dollar level itself is expected to rise because the series grows about 3% to 7% a year.

The chart is `data/eval/sales_forecast_test.png`.
