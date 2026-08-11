# Technical Context

## Architecture
- `uis/website`: public Next.js App Router application.
- `uis/application`: internal Next.js App Router application with a distinct layout.
- `src`: canonical TypeScript domain models, sample data, and pure operations utilities.
- `services`: the only allowed location for APIs and background services.
- `packages` and `shared`: reusable libraries and non-code assets as the project grows.

## Decisions
- TypeScript is required for application and business code.
- UI code uses reusable components, semantic HTML, responsive CSS, and server rendering by default.
- Business calculations stay pure and are imported from `src`; they must not be copied into a UI.
- Financial data supports USD and COP. Dates must be handled explicitly to avoid timezone ambiguity.
- Each application owns its dependencies and can be run from its directory with `npm run dev`.

## Constraints
- Preserve the monorepo folder responsibilities documented in the root README.
- Keep public and internal layouts visually and structurally separate.
- Never place API route handlers inside a UI application; create them under `services`.
- Validate with linting and production builds before delivery.
- Do not commit generated files such as `node_modules` or `.next`.
