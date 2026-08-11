---
scope: file-pattern
files:
  - "src/**/*.ts"
  - "uis/application/**/*.ts"
  - "uis/application/**/*.tsx"
description: Canonical operations logic conventions
---

# Business Logic Rule

- Treat `src` as the canonical Milestone 2 module and import it into consumers.
- Keep calculations pure, explicitly typed, non-mutating, and independent of UI frameworks.
- Preserve Brasaland entity names, validation rules, USD/COP behavior, and clear date boundaries.
- Keep sample data separate from reusable calculations.
- Never paste a calculation into `uis/application`; add or fix it in `src` and import it.
- Show meaningful calculation output in the interface, not only in console logs.
