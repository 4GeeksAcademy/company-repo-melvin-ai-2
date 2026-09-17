# Production Lighthouse (next start)

Measured 17 September 2026 against `next build && next start` (not `npm run dev`).

- Public site: http://127.0.0.1:3005 (`next start -H 127.0.0.1 -p 3005`)
- Backoffice: http://127.0.0.1:3111 (`next start -H 127.0.0.1 -p 3111`)

Default `npm start` is :3000 / :3101 after you stop the webpack dev servers.

These reports are the production KPI check (Performance ≥ 90, LCP &lt; 2.5s, CLS &lt; 0.1).
