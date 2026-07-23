# Brasaland Backoffice

Internal Next.js entry point for Brasaland operations. The dashboard renders sales, margin, waste, menu, country, and location-performance output by importing the canonical Milestone 2 TypeScript module from the monorepo root.

## Run

```bash
npm install
npm run dev
```

Open `http://localhost:3000`. Use a different port when the public website is already running:

```bash
npm run dev -- --port 3001
```

## Verify

```bash
npm run lint
npm run build
```

Do not copy operations calculations into this application. Extend the root `src` module and import the result. Any future API belongs under `services`.
