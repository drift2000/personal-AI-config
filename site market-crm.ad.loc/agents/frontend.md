---
name: frontend-agent
description: >
  Local agent for the React.js frontend.
  Scaffolds table components, API hooks, and page stubs.
  Documents API contract expectations and component structure.
  Use whenever touching `src/frontend/src/**`.
applyTo: "src/frontend/src/**"
---

## Responsibilities

### 1. Regression checks (run BEFORE making changes)

The frontend is purely API-driven. Regressions usually come from:
- API response shape changes on the backend (Swagger is the source of truth).
- Column key mismatches between API response and table component `columns` config.
- Sorting/pagination state not reset when filters change.

**Questions to ask before changes:**
> "Which pages consume the /api/emails/ endpoint? Does my API change break any column mapping?"
> "If I rename a field in CompanySerializer, which frontend pages use that field?"

### 2. Scaffolding

Produce ready-to-use stubs for:
- New table page (use `frontend_table.component.tpl` + `example_table_page.tpl`).
- New API hook (`useFetch` or similar pattern consistent with existing code).
- New page route entry.

**How to ask:**
> "Scaffold table page for the ftp integrations list endpoint"
> "Create page stub for download stats with columns: company, domain, count, period"

### 3. Documentation

Produce or update `docs/frontend/README.md` covering:
- Page inventory: route → component → API endpoint consumed.
- Column definitions per table page.
- Any non-obvious rendering logic (e.g., status badges, conditional formatting).

**How to ask:**
> "Document the emails table page: columns, API endpoint, sort behavior"
> "Update frontend README with new integrations summary page"

---

## API contract conventions

- All data comes from Django REST via Swagger-documented endpoints.
- Frontend should never hardcode field names — always derive from a `columns` config array.
- If an API field is renamed, search for its `key` in all `columns` arrays before deploying.

## Component conventions

- Table components: use `frontend_table.component.tpl` (sort + pagination included).
- Logger: use `logging_frontend.tpl` wrapper during development (`makeLogger('ComponentName')`).
- API requires a logged-in session (DRF `IsAuthenticated` + role check); role-gated UI follows `auth_azure` roles — see `docs/auth_azure/README.md`.

---

## Output conventions

- Scaffolded components → `src/frontend/src/components/`
- Scaffolded pages → `src/frontend/src/pages/`
- Documentation → `docs/frontend/`
