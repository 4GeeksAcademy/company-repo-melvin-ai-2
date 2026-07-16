# CONTEXT.md — Brasaland

> This document describes your company and the domain context for project work. Everything you build should reflect this context: labels, terminology, and framing.

---

## Your company

**Brasaland** is a grilled food restaurant chain founded in 2008 in Medellín, Colombia. What began as a single family-run location has grown into a chain of **14 company-owned restaurants** operating in Colombia and the United States (Florida). The company employs approximately **115 people** between kitchen and floor staff, operations management, and the corporate team headquartered in Medellín with a commercial office in Miami. Annual revenue sits around 6 million dollars.

The brand is built on three pillars:

1. **Consistent product quality** across every location
2. **Warm and reliable customer experience**
3. **Speed of service**

---

## Company choice (project rationale)

Brasaland was selected as the company for this transversal project. The business operates across two countries, relies heavily on operational and customer data that is still incomplete today (for example, WhatsApp-driven orders with weak inventory visibility), and has clear room for digital tools that support Marketing, Restaurant Operations, and People & Talent.

Future AI work may focus on inventory needs by location using sales and customer signals. For this milestone, the priority deliverable in `uis/` is an internal **Talent Pipeline Tracker** for People & Talent—not a customer-facing core system.

See also `CONTEXT-SOLUTION.md` for the full personal justification, preferred departments, and agent ideas.

---

## Locations and language

- **Colombia:** 10 restaurants (Medellín, Bogotá, Cali)
- **United States (Florida):** 4 restaurants (Miami, Orlando)
- Bilingual environment (Spanish / English) is common; English UI labels are acceptable for internal tools when candidate data from shared APIs remains as returned (often Spanish).

---

## Milestone focus: Talent Pipeline Tracker

**Audience:** Brasaland People & Talent (internal auxiliary tool)

**Location in repo:** `uis/talent-pipeline-tracker`

**Problem:** Hiring for kitchen, floor, and operations roles across 14 locations needs a clear pipeline view—who applied, where they are in the process, and what recruiters noted—without losing list filters when opening a candidate.

**What the tool must support:**

- List candidates at a glance (name, position, status, stage)
- Filter by status and stage; search by name or email (URL query params, no full page reload)
- Open a candidate detail view; update status/stage with a single interaction (`PATCH`)
- Add and delete internal notes
- Register new candidates (`POST`) and edit existing ones (`PUT`)

**Terminology to use in the UI:** Candidate, Position, Status, Stage, Application date, Internal notes, People & Talent, Brasaland Talent Pipeline.

**Product framing:** Present the app as Brasaland’s internal hiring pipeline for staff across Colombia and Florida—not as a generic ATS or a public careers site.

---

## Related materials

- Public website / Brasa Points marketing milestone notes: `web-development-CONTEXT.md`
- Personal company selection notes: `CONTEXT-SOLUTION.md`
