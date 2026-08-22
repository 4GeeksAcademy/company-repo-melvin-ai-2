# Architecture Proposal — Brasaland Backend

**Audience:** CTO / Brasaland Digital  
**Author role:** Junior Developer, Brasaland Digital  
**Status:** Proposal only — no implementation code in this document  
**Company:** Brasaland (14 locations · Colombia & Florida · USD/COP)

---

## 1. Why this document exists

Before the team stands up the environment and first endpoints, we need a shared answer to:

- What architectural pattern we will use, and why it fits Brasaland.
- How the backend project folders and modules should be organized.
- How FastAPI routers and domains should be grouped.
- How frontend and backend stay separate but coordinated in this monorepo.
- What can go wrong if we ignore the structure.

This is documented technical reasoning, not a technology shopping list.

---

## 2. Company constraints that drive the design

Brasaland is not a generic SaaS product. The backend must reflect:

- **Multi-location operations** across 14 restaurants in two countries.
- **Dual currency** (USD and COP) on every financial metric Felipe Guerrero trusts.
- **Fragmented today-state:** WhatsApp orders, weak inventory visibility, incomplete loyalty data, manual reporting, and hiring coordination.
- **Two distinct UI audiences already in the monorepo:**
  - Public customers → `uis/website` (brand + Brasa Points).
  - Internal operators → `uis/backoffice` (operations metrics).
- **Existing Milestone 2 TypeScript domain logic** under root `src/` (menu, sales, locations, waste, margins, rankings). That logic must stay the behavioral reference; it must not be rewritten inside React components.
- **Monorepo rule:** all APIs live under `services/`. UI apps must not become the company API.

**v1 product focus:** Restaurant Operations (locations, sales, waste, performance).  
**Sketched later:** Brasa Points and People & Talent — named as domains, not fully designed in this sprint.

---

## 3. Chosen architectural pattern

### Pattern: Modular layered architecture (API / domain / shared contracts), organized by business domain

Concretely:

1. **Presentation / interface layer** — FastAPI routers and Pydantic request/response schemas.
2. **Domain / application layer** — pure Python services that port Milestone 2 formulas and validations.
3. **Shared contract layer** — versioned shapes and naming that keep TypeScript `src/` and Python services aligned.
4. **Composition root** — a single FastAPI application factory that mounts domain routers.

We organize packages **by Brasaland domain** (operations, loyalty, talent), not by dumping every route into one file.

### Why this fits Brasaland (not a generic preference)

| Brasaland reality | Why layered + domain modules fit |
| --- | --- |
| Felipe needs consistent margin, waste, and location scores | Domain services hold the formulas once; routers stay thin |
| Two UIs already exist and must call one company API | A clear interface layer + CORS/env boundary between Next.js and FastAPI |
| Colombia/Florida + USD/COP | Domain rules and currency handling live in services, not in UI copy-paste |
| Team will grow across milestones (loyalty, hiring, inventory AI) | Domains can expand without collapsing into one mega-router |
| CTO asked for one centralized backend early | One FastAPI app with multiple routers — not microservices yet |

### Patterns we are not choosing for v1

- **Classic MVC as the primary story:** Fine for teaching, but FastAPI’s natural unit is the **router + schema + service**, and Brasaland’s complexity is domain-driven (operations vs loyalty vs talent).
- **Serverless-first:** Premature for a learning monorepo that already standardizes on `services/` and local composition.
- **Many microservices:** Conflicts with the monorepo guidance to keep one centralized API until complexity forces a split.

---

## 4. Research: typical FastAPI project structure

Common production guidance converges on domain-oriented packages rather than a flat dump of all routes and models. This proposal draws especially on:

- [zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices) — domain folders with `router.py`, `schemas.py`, `service.py`, `dependencies.py`, plus shared app-level config.
- [FastAPI for production: Building scalable APIs beyond the tutorial (DSi Blog)](https://www.dsinnovators.com/blog/python/fastapi-production-scalable-apis-2024/) — organize by business domain; keep a `core` package for shared config/middleware; register routers from an application factory.
- Official FastAPI docs on [Bigger Applications - Multiple Files](https://fastapi.tiangolo.com/tutorial/bigger-applications/) — `APIRouter` and `include_router` for splitting endpoints by module.

Those sources agree on:

- Prefer **domain packages** (`auth/`, `orders/`, …) over a flat `routers/` + `models/` dump once there are multiple business areas.
- Inside each domain: `router.py`, `schemas.py` (Pydantic), `service.py` (business logic), `dependencies.py`, `exceptions.py`.
- A **`main.py` (or app factory)** that creates the FastAPI instance, registers middleware (including CORS), and `include_router`s each domain.
- Shared cross-cutting config in a `core/` (or equivalent) package: settings from environment variables, logging, shared exceptions.
- Keep routers thin; put rules in services so endpoints stay readable and testable.

### How that research shaped this proposal

| FastAPI convention | Brasaland application | Source influence |
| --- | --- | --- |
| Domain packages | `operations` first; light packages for `loyalty` and `talent` | zhanymkanov; DSi Blog |
| `router.py` + `service.py` | Routers expose HTTP; services port Milestone 2 calculations | zhanymkanov |
| Pydantic `schemas.py` | Request/response contracts for locations, sales, waste, metrics | zhanymkanov; FastAPI docs |
| App factory + `include_router` | Single app under `services/api` with CORS for website and backoffice | FastAPI bigger apps; DSi Blog |
| Shared `core/config` | Env-based API settings without scattering secrets in UIs | zhanymkanov; DSi Blog |
| Avoid one giant routes file | Prevents mixing public loyalty routes with internal operations routes | All three |

**Note:** Persistence technology is intentionally **out of scope** for this document. Services are described as pure domain logic + HTTP surface. Storage choices come in a later decision.

---

## 5. Proposed backend folder and module structure

Place the API as **one service** under the monorepo:

```text
services/
└── api/
    ├── README.md
    ├── pyproject.toml / requirements.txt
    ├── .env.example
    ├── app/
    │   ├── main.py                 # FastAPI factory, middleware, router includes
    │   ├── core/
    │   │   ├── config.py           # Settings from environment variables
    │   │   ├── cors.py             # Allowed origins for website + backoffice
    │   │   └── exceptions.py       # Shared HTTP error mapping
    │   ├── contracts/              # Shared naming/shapes aligned with root src/
    │   │   └── operations.py       # Field names mirroring MenuItem, Location, etc.
    │   ├── operations/             # PRIMARY domain (v1)
    │   │   ├── router.py
    │   │   ├── schemas.py
    │   │   ├── service.py          # Ported Milestone 2 formulas
    │   │   ├── dependencies.py
    │   │   └── exceptions.py
    │   ├── loyalty/                # Sketch only for later
    │   │   ├── router.py
    │   │   ├── schemas.py
    │   │   └── service.py
    │   └── talent/                 # Sketch only for later
    │       ├── router.py
    │       ├── schemas.py
    │       └── service.py
    └── tests/
        └── operations/
```

### Criteria for domain / responsibility separation

Split a module when **the business owner, vocabulary, or access audience changes**:

| Domain | Business owner / audience | Separation reason |
| --- | --- | --- |
| `operations` | Felipe Guerrero / location managers | Sales, waste, margins, rankings — internal metrics |
| `loyalty` | Camila Ospina / customers | Brasa Points registration — public marketing flow |
| `talent` | People & Talent | Candidates, stages, notes — HR-sensitive later |

Do **not** split by technical type alone (all schemas in one folder forever). That is what FastAPI research says stops scaling once domains multiply.

### Relationship to root `src/` (Milestone 2)

| Concern | Decision |
| --- | --- |
| TypeScript `src/` | Remains the **canonical reference** for pure formulas and entity names used by `uis/backoffice` today |
| FastAPI `app/operations/service.py` | **Reimplements/ports** the same formulas in Python for the API |
| Shared contract | `app/contracts/` documents matching field names and metric meanings so TS and Python do not drift |
| What we forbid | Copying formulas into React; calling Node from Python; inventing new field names per language |

---

## 6. FastAPI routers and endpoint organization

Mount one application, multiple routers, with clear prefixes and tags.

### Access posture (auth out of scope for v1, but designed now)

| Surface | Audience | v1 auth | Notes |
| --- | --- | --- | --- |
| Public | Website / health checks | None | Keep minimal |
| Internal | Backoffice operations | **Not implemented in v1**, but routes are grouped so auth middleware can wrap `/api/v1/operations/*` later |

### Router grouping

#### A. System (public)

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness for local/dev and future deploy checks |
| `GET` | `/api/v1/meta` | Optional: API version / company label (`Brasaland`) |

#### B. Operations (internal-intended) — **v1 priority**

Router: `app.operations.router`  
Prefix: `/api/v1/operations`  
Tag: `operations`

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/locations` | List locations (id, city, country, status, capacity…) |
| `GET` | `/locations/{location_id}` | Single location |
| `GET` | `/locations/{location_id}/margin` | Margin % for a location (ported `calculateLocationMargin`) |
| `GET` | `/locations/{location_id}/waste-cost` | Waste cost in USD or COP |
| `GET` | `/locations/rankings` | Ranked performance scores |
| `GET` | `/sales/summary` | Totals / average ticket / payment-method counts |
| `GET` | `/sales/top-items` | Top selling menu items |
| `GET` | `/countries/comparison` | Colombia vs USA metrics |
| `POST` | `/validate/menu-item` | Run menu validation rules |
| `POST` | `/validate/sale` | Run sale validation rules |
| `POST` | `/validate/location` | Run location validation rules |

Query parameters such as `currency=USD|COP` belong on financial endpoints so dual-currency rules stay explicit.

#### C. Loyalty (sketch — later)

Router prefix: `/api/v1/loyalty`  
Tag: `loyalty`

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/brasa-points/registrations` | Accept Brasa Points form payloads from `uis/website` |
| `GET` | `/brasa-points/registrations/{id}` | Optional lookup once persistence exists |

Public enough for marketing flows; still versioned under `/api/v1`.

#### D. Talent (sketch — later)

Router prefix: `/api/v1/talent`  
Tag: `talent`

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/candidates` | List / filter candidates |
| `POST` | `/candidates` | Register candidate |
| `GET` | `/candidates/{id}` | Detail |
| `PATCH` | `/candidates/{id}` | Status / stage updates |
| `POST` | `/candidates/{id}/notes` | Internal notes |

These routes are internal-sensitive; when auth lands, they share the same “internal” middleware bag as operations.

### Grouping criteria (summary)

1. **Domain vocabulary** (operations vs loyalty vs talent).  
2. **Audience** (public vs internal-intended).  
3. **Stability of Milestone 2 formulas** (operations owns the ported calculations).  
4. **Version prefix** `/api/v1` so breaking changes later do not surprise the UIs.

---

## 7. Frontend and backend as separate systems

### Monorepo vs separate repositories

**Decision: stay in the existing monorepo**, with clear folders:

- Frontends: `uis/website`, `uis/backoffice`
- Backend: `services/api`
- Shared company context: `CONTEXT.md`, `memory-bank/`
- TypeScript domain reference: root `src/`

**Why not separate repos for v1**

- The course and company template already enforce one monorepo with `uis/` + `services/`.
- CONTEXT, agents, and Milestone 2 logic must stay visible next to the UIs.
- One PR can still change a contract carefully across layers when needed.

**What “separate systems” still means inside the monorepo**

- Different runtimes (Node vs Python).
- Different install/start commands.
- Communication **only over HTTP JSON**, not by importing FastAPI into Next.js or vice versa.
- No Next.js Route Handlers as a substitute for `services/`.

### API communication

```text
uis/website  --HTTP JSON-->  services/api
uis/backoffice --HTTP JSON-->  services/api
                     ^
                     |
              ports formulas from
              root src/ (TS reference)
```

- Base URL comes from environment variables (never hardcode localhost in committed UI code without an env override).
- Backoffice should migrate from in-process TS imports toward API calls once endpoints exist — until then, TS `src/` remains valid for the Milestone 4 UI demonstration.

### Environment variables (examples — names only)

| Variable | Used by | Purpose |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | website, backoffice | Browser-visible API origin |
| `API_HOST` / `API_PORT` | FastAPI | Bind address for local run |
| `CORS_ORIGINS` | FastAPI | Comma-separated allowed frontend origins |
| `APP_ENV` | FastAPI | `development` / `production` toggles for docs exposure, logging |

Secrets (future auth tokens, etc.) never go into `NEXT_PUBLIC_*` variables.

### CORS

Because the UIs and API are different origins in local and deployed setups:

- Enable CORS middleware in FastAPI `main.py`.
- Allow only known origins from `CORS_ORIGINS` (e.g. `http://localhost:3100`, `http://localhost:3101` in development).
- Allow required methods (`GET`, `POST`, `PATCH`, `OPTIONS`) and headers (`Content-Type`, later `Authorization`).
- Do **not** use `allow_origins=["*"]` with credentials in production.

Without explicit CORS, the backoffice and website will look “broken” in the browser even when the API is healthy — a common FE/BE separation failure mode.

---

## 8. Initial technical decisions (checklist)

| Decision | Choice |
| --- | --- |
| Architectural pattern | Modular layered API + domain services |
| API framework | FastAPI |
| Service layout | Single app `services/api` |
| Domain priority | Operations first; loyalty & talent sketched |
| Milestone 2 TS | Keep in root `src/`; port formulas to Python services |
| Shared contract | Explicit naming/shapes under `app/contracts/` |
| Auth | Out of scope for v1; route prefixes prepared for later internal protection |
| Persistence | Not specified in this proposal |
| FE/BE topology | Monorepo, separate processes, HTTP + env + CORS |

---

## 9. Risks and points of attention

At least the following must be watched; ignoring the proposed structure creates concrete failure modes.

### Risk 1 — Dual implementation drift (TypeScript `src/` vs Python services)

If the team ports formulas carelessly, backoffice numbers (still using TS) and API numbers (Python) will disagree. Felipe will not trust either.

**Mitigation:** Shared contract document in `app/contracts/`; mirror function names (`calculate_location_margin`, etc.); add comparison tests later against known sample fixtures from Milestone 2.

### Risk 2 — Putting API logic inside Next.js

If developers add Route Handlers under `uis/*` “just for speed,” we violate monorepo boundaries, duplicate business rules, and break the CTO’s centralized-backend intent.

**Mitigation:** Enforce `services/` as the only API home in `AGENTS.md` / `.agents/rules`; reject PRs that introduce company APIs in UI apps.

### Risk 3 — CORS and env misconfiguration look like application bugs

Separate FE/BE means blank screens or blocked fetches when origins or `NEXT_PUBLIC_API_BASE_URL` are wrong.

**Mitigation:** Document `.env.example` for API and both UIs; keep `CORS_ORIGINS` explicit; verify `/health` from the browser network panel before debugging React.

### Risk 4 — Treating all routes as public forever

Operations and future talent data are internal. Shipping without a clear internal prefix plan invites accidental exposure when the API is deployed.

**Mitigation:** Keep `/api/v1/operations` and `/api/v1/talent` grouped so auth middleware can wrap them in a later sprint without rewriting the URL map.

### Risk 5 — Premature microservice split

Spinning `operations-api`, `loyalty-api`, and `talent-api` too early multiplies deploy and CORS complexity while the team is still learning FastAPI.

**Mitigation:** One FastAPI app, multiple domain routers, until operational load or team topology forces a split.

---

## 10. What “good” looks like for the next sprint kickoff

Any Brasaland engineer should be able to read this file and know:

1. We use a **modular layered** FastAPI backend under `services/api`.  
2. **Operations** is the first domain; loyalty and talent are placeholders.  
3. Routers are thin; **Python services** own ported Milestone 2 rules.  
4. Root **TypeScript `src/`** remains the reference implementation for pure logic.  
5. Frontends talk to the API over **HTTP**, configured by **env vars**, protected by **CORS**.  
6. **Auth and persistence** are deferred, but route grouping anticipates internal protection.

No code is required to accept this proposal — only agreement on the reasoning above before endpoints are created.

---

## 11. References

### Company and monorepo context

- `CONTEXT.md` — Brasaland company facts and constraints
- `memory-bank/projectbrief.md` — business objectives
- `memory-bank/techContext.md` — monorepo technical decisions
- `AGENTS.md` — agent delivery workflow and folder boundaries
- Root `README.md` — `uis/` vs `services/` placement rules

### FastAPI structure research (explicit sources)

- zhanymkanov, *FastAPI Best Practices* (project structure by domain): https://github.com/zhanymkanov/fastapi-best-practices
- DSi Innovators, *FastAPI for production: Building scalable APIs beyond the tutorial*: https://www.dsinnovators.com/blog/python/fastapi-production-scalable-apis-2024/
- FastAPI documentation, *Bigger Applications - Multiple Files* (`APIRouter`, `include_router`): https://fastapi.tiangolo.com/tutorial/bigger-applications/
- FastAPI documentation, *CORS (Cross-Origin Resource Sharing)*: https://fastapi.tiangolo.com/tutorial/cors/
