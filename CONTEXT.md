# Brasaland Context

## Company
Brasaland is a family-founded grilled food restaurant chain established in Medellín in 2008. It operates 14 company-owned restaurants: 10 in Medellín, Bogotá, and Cali, and 4 in Miami and Orlando. About 115 employees support restaurant operations and corporate teams in Medellín and Miami.

## Business
Brasaland promises consistent product quality, warm service, and speed. It operates in a bilingual Colombia–Florida environment, uses COP and USD, and is improving fragmented processes such as WhatsApp orders, inventory visibility, loyalty data, restaurant reporting, and hiring.

## What We Are Building
- An improved public website and Brasa Points registration experience in `uis/website`.
- An internal operations entry point in `uis/backoffice`.
- Reusable TypeScript business logic for sales, margins, waste, and location performance.
- Persistent memory, rules, and skills that keep future agent work aligned with Brasaland.

## Constraints
- Treat this file and `memory-bank/` as the business source of truth.
- Keep business terms, data, prompts, and interfaces consistent.
- Keep reusable business logic outside UI components; place any APIs under `services/`.
