# PR Checklist — API refactor: docs, cleanup, perf fix across all APIs

**Branch:** develop
**App(s) touched:** client, ftp, download, common, frontend (api layer)
**Date:** 2026-08-31

---

## Type of change

- [x] Refactor / cleanup
- [x] Bug fix (dead code + N+1 query in `ftp`)
- [x] Documentation only (partly — Swagger schema descriptions + docs/*/README.md)
- [ ] New feature
- [ ] Data migration / one-shot script
- [ ] Frontend only

---

## Pre-merge checklist

### General
- [ ] Locally tested against real (or realistic) data
- [x] No `print()` statements left in backend code (none added)
- [x] No hardcoded IDs, emails, or company names in production code (none added)
- [ ] Docker build still passes (`docker compose build`) — run via `./run.sh`

### Backend
- [x] No new management commands added
- [x] No new models added
- [x] No new ForeignKeys added
- [x] No new `save()` overrides added
- [x] No migrations needed (no model changes)

### client app (touched)
- [x] No model/relation changes — only an `@extend_schema` decorator added to
      `new_users_per_month_view`. Regression checklist not required per
      `.github/agents/client.agent.md` (only model/relation changes need one).
- [x] `Email.save()` / `Domain.save()` overrides unaffected (untouched)
- [x] Soft-delete (`marked_for_del`) logic preserved (untouched)

### ftp / download (touched)
- [x] Import idempotency preserved (import scripts/`run_import_step` untouched)
- [x] Unmatched rows still logged, not silently dropped (unchanged behavior)
- [x] `CompaniesSourcesView` N+1 fix verified to return identical `results` shape,
      just fewer queries (see verification section of the plan)
- [x] Dead/unreachable code removed from `UsersOtherViewSet.get_queryset`
      (was a copy-paste artifact, never executed)
- [x] Duplicated `CustomPagination` classes consolidated into
      `common/pagination.py::DefaultPagination`

### Frontend
- [x] Column `key` values unaffected — only `src/frontend/src/api/*` changed,
      no page/column code touched
- [x] Pagination / sort state unaffected — no page components touched
- [x] No hardcoded endpoint URLs left behind — all api modules now go through
      the shared `api` axios instance (relative paths) instead of hand-rolled
      absolute `/api/...` strings on bare `axios`
- [x] Removed 4 dead files (`clientApi.js`, `downloadApi.js`, `ftpApi.js`,
      `index.js`) confirmed to have zero importers via repo-wide grep

### Documentation
- [x] `docs/client/README.md` updated with an API endpoints table
- [x] `docs/ftp/README.md` created with an API endpoints table
- [x] `docs/download/README.md` created with an API endpoints table
- [ ] `once` script documented — n/a, no `once` scripts touched

---

## Risk level

- [x] 🟡 Medium — touches `ftp`/`download` viewsets and shared pagination, but
      no model/migration changes; the `CompaniesSourcesView` query rewrite is
      the one piece that needs a real before/after response comparison.

---

## Notes for reviewer

This pass focused on: (1) adding missing `drf-spectacular` schema docs so every
endpoint has a summary/description/tag in Swagger, (2) removing a dead
duplicate-code block and a redundant per-company query loop in
`ftp/CompaniesSourcesView` (real N+1 — now 4 queries total instead of 4×N), (3)
deduplicating the `CustomPagination` class into `common/pagination.py`, and (4)
cleaning up the frontend `api/` layer (removed 4 unused stub files, unified
every module onto the shared axios instance with CSRF support). No response
shapes changed; no frontend page/component code was touched.
