# `uis` folder

This folder contains **all projects with a user interface** for the cross-functional AI Engineering company project — for example: a public website, admin dashboard frontend, ecommerce UI, customer portals, Streamlit/Gradio app or other frontend-only tools.

The runnable applications are:

- **`website`** — the public corporate and Brasa Points experience. Run with `cd uis/website && npm run dev`.
- **`backoffice`** — internal operations overview plus **Supplier directory** at `/suppliers`. Run with `cd uis/backoffice && npm run dev` (port **3101**; API on **8000**). CONTEXT: [`memory-bank/supplier-directory.md`](../memory-bank/supplier-directory.md).
- **`web`** — internal web tools including **Incident analysis** (Phase 2 Company File Analyzer). Run with `cd uis/web && npm run dev` (API must be up; see `services/api`). Uses the **100-row** sample `scripts/incidents-brasaland.csv`; assignment context: [`memory-bank/company-file-analyzer.md`](../memory-bank/company-file-analyzer.md).

Organize `uis/` by **different concerns** — each subfolder covers a distinct area of the company (for example, public web vs internal operations) and includes its own technical and functional documentation.

- **Main purpose**: to centralize in a single place all frontend applications that support the company's use cases.
- **Recommendation**: document in this file (or in sub-READMEs) the applications you add, their objective, the technology used, and how to run them.

> _Estas instrucciones también están disponibles en [español](./README.es.md)._
