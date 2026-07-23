---
scope: file-pattern
files:
  - "uis/**/*.{ts,tsx,css}"
description: Next.js interface conventions
---

# Frontend Rule

- Use Next.js App Router and strict TypeScript.
- Build mobile-first with semantic landmarks, keyboard access, visible focus, labels, useful alternative text, and adequate contrast.
- Extract repeated UI and content into typed components or data modules.
- Prefer server components; add `"use client"` only for browser state or events.
- Keep the public website and backoffice layouts separate.
- Never implement domain calculations or APIs inside a component.
- Verify responsive behavior, linting, and a production build before delivery.
