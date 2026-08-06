# `uis` folder

This folder contains **all projects with a user interface** for the cross-functional AI Engineering company project — for example: a public website, admin dashboard frontend, ecommerce UI, customer portals, Streamlit/Gradio app or other frontend-only tools.

The runnable applications are:

- **`website`** — the public corporate and Brasa Points experience. Run with `cd uis/website && npm run dev`.
- **`backoffice`** — the internal operations entry point that displays imported Milestone 2 business metrics. Run with `cd uis/backoffice && npm run dev`.
- **`web`** — internal web tools including **Incident analysis** (Phase 2 Company File Analyzer). Run with `cd uis/web && npm run dev` (API must be up; see `services/api`).

Organize `uis/` by **different concerns** — each subfolder covers a distinct area of the company (for example, public web vs internal operations) and includes its own technical and functional documentation.

- **Main purpose**: to centralize in a single place all frontend applications that support the company's use cases.
- **Recommendation**: document in this file (or in sub-READMEs) the applications you add, their objective, the technology used, and how to run them.

> _Estas instrucciones también están disponibles en [español](./README.es.md)._
