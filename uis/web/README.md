# Brasaland Web (`uis/web`)

Internal Next.js app for Brasaland operations tools. Phase 2 adds the **Incident analysis** page that uploads a CSV to `services/api` and shows CONTEXT-aligned metrics.

## Run

Requires the API on port 8000 (see `services/api/README.md`).

```bash
cd uis/web
npm install
npm run dev
```

Open http://localhost:3102/incidents

Optional: set `NEXT_PUBLIC_API_BASE_URL` if the API is not at `http://localhost:8000`.

## Features

- Main nav link to **Incident analysis**
- Drag-and-drop or file picker upload → `POST /api/incidents/analyze`
- On-screen summary: totals, invalid breakdown, category, status, satisfaction
- Download button → `GET /api/incidents/results/export`
