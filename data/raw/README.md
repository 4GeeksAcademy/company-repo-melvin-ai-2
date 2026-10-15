# `data/raw` folder

This folder is intended for **raw data** related to the company: dumps, exports, sample files, event samples, or untransformed datasets.

- **Main purpose**: serve as a landing zone or reference for original data before pipelines process it.
- **Recommendation**: document each dataset’s origin, format, expected size, privacy/PII considerations, and how it is versioned (ideally avoiding sensitive data in the repository).

For the Company File Analyzer assignment, the graded sample CSV lives at [`scripts/incidents-brasaland.csv`](../../scripts/incidents-brasaland.csv) (submission layout). A copy may also exist under `data/`.

`telemetry_YYYY-MM-DD.csv` is the nightly backup of one UTC day from `telemetry_events`. `scripts/nightly_export.py` writes it only when the file is absent. It is gitignored because rows can include `user_id`. The weekly location pipeline does not read it.

> _Spanish version: [README.es.md](./README.es.md)._
