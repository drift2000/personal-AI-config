# PR Checklist — HubSpot Company Sync (manual, read-only)

**Branch:** develop
**App(s) touched:** client (backend + frontend)
**Date:** 2026-09-04

---

## Type of change

- [x] New feature

---

## Pre-merge checklist

### General
- [x] Locally tested against real data (dev DB via the running `backend_crm_dev` / `postgres_crm_dev` containers, using `curl` against the live endpoints)
- [x] No `print()` statements left in backend code (uses `common.command_logger.init_file_logger`, same pattern as `client/services/mailchimp.py`)
- [x] No hardcoded IDs, emails, or company names in production code
- [ ] Docker build still passes (`docker compose build`) — not run this session; only the already-running dev containers were exercised (migrate/exec), image build itself wasn't rebuilt
- [ ] `npm run build` — not run; changes verified via the running dev webpack server (compiled with only a pre-existing unrelated warning)

### Backend
- [x] New logging via `client/services/hubspot_client.py` (`hubspot.log`) and reused in `client/api_views.py` — same convention as `mailchimp.log`
- [x] New model (`Company.hubspot_id`) has no custom `__str__` needed (existing `Company.__str__` unaffected)
- [x] No new ForeignKeys added
- [x] `Company.save(update_fields=["hubspot_id"])` calls are idempotent (re-running sync/select is safe)
- [x] Migration generated and committed: `client/migrations/0015_company_hubspot_id.py`
- [x] Migration reviewed for reversibility — plain `AddField`, trivially reversible, no data migration

### client app (touched)
- [x] Regression checklist completed: `docs/client/regression_2026-09-04.md`
- [x] `Email.save()` / `Domain.save()` overrides unaffected (not touched)
- [x] Soft-delete (`marked_for_del`) logic preserved (untouched by sync/PATCH code paths)

### ftp / download
- [x] Not touched by this feature.
- [!] **Unrelated pre-existing bug found while validating**: `ftp/migrations/0016_usersonedrive_remove_usersod_company_and_more.py` does `CreateModel("UsersOneDrive", db_table="users_onedrive")` instead of `RenameModel` from the `UsersOD` model created in `ftp/migrations/0014_usersod.py` (same `db_table`). This makes it impossible to build a fresh database purely from migrations (`relation "users_onedrive" already exists`) — confirmed by running `manage.py test` against a clean DB (see Notes). The live dev database currently has `users_onedrive` still on the **pre-0016 column layout** (still has `company_id`/`company_contact_id`/`customer_contact_id`, no `role` column), i.e. it doesn't actually match what migrations 0016–0020 claim to have done — it was presumably patched by hand at some point outside of Django's migration flow. Flagging for a dedicated `ftp`-scoped investigation; not fixed here (out of scope for this PR, needs `.github/agents/ftp.agent.md` review).

### Frontend
- [x] Column `key` values N/A (no table added)
- [x] No hardcoded endpoint URLs — added `syncCompanyWithHubspot`, `selectHubspotCandidate`, `updateCompany` to `src/frontend/src/api/companies.js`, following the existing `fetchCompanyById` pattern
- [x] New "HubSpot" tab on `CompanyDetail.jsx` (`src/frontend/src/pages/management/company/HubspotSyncPanel.jsx`), no new route/page created
- [x] Frontend never calls HubSpot directly; token stays backend-only (`settings.HUBSPOT_ACCESS_TOKEN`, env-only, never serialized to the frontend)

### Documentation
- [x] `docs/client/regression_2026-09-04.md` added
- [ ] `docs/client/README.md` — not updated with the new endpoints/model field in this pass (recommend a follow-up doc pass covering `hubspot_id`, the two new actions, and `client/services/hubspot_client.py`)

---

## Risk level

- [x] 🔴 High — touches `client` core model (`Company.hubspot_id`), adds a migration, and changes `CompanyViewSet` from read-only to allow `PATCH` (needed for the frontend save step; no such endpoint existed before) — needs extra review

---

## What was built

- `Company.hubspot_id` (nullable, unique, indexed `CharField`) + migration `0015_company_hubspot_id`.
- `client/services/hubspot_client.py`: `HubSpotClient` with `search_company_by_domain()` (Search API, domain filter) and `get_company_by_id()` (`archived=true` so archived companies come back instead of 404ing); typed errors for config/404/401-403/429 (with `Retry-After`).
- `CompanyViewSet` (in `client/api_views.py`) changed from `ReadOnlyModelViewSet` to `Retrieve/List/Update` only (no `create`/`destroy`), adding:
  - `POST /api/client/companies/{id}/hubspot-sync/` — direct GET if `hubspot_id` is already set, otherwise search-by-domain; handles 0/1/N matches, auto-links on a single match, unlinks if a previously-linked id 404s upstream.
  - `POST /api/client/companies/{id}/hubspot-sync/select/` — links a chosen candidate from the `multiple_matches` case.
  - Country matching: HubSpot's free-text `country` is resolved against `client.IsoCountry` (`iso_name`/`official_name`) server-side, returning `country_alpha2`/`country_match_name` so the frontend never has to (or risks) sending free text into the `country` PROTECT FK.
  - Saving edited/merged CRM fields reuses the now-PATCH-capable `PATCH /api/client/companies/{id}/` (no new endpoint, per spec).
- Frontend: `HubspotSyncPanel.jsx`, wired as a new "HubSpot" tab on the existing company detail page — sync button, not_found/multiple_matches/error states, side-by-side CRM/HubSpot blocks, "Заповнити все з HubSpot" + per-field copy (only for fields that actually exist on `Company`: name, city, country), Save via PATCH.
- Tests: `client/tests.py` — `HubSpotClientTests` (404/401/429 handling, request shape) and `CompanyHubspotSyncViewTests` (existing id / no domain / 0 / 1 / N matches / rate limit / auth error / archived / stale-id unlink / select / country match).

## Deliberately deferred (per spec's own open questions, resolved with the user during this session)

- HubSpot fields with no `Company` counterpart (`phone`, `industry`, `numberofemployees`, `address`) are **reference-only** in the HubSpot block — no copy target, no new `Company` columns added (user's explicit choice, to avoid extra migration risk on the highest-risk model).
- `country`: resolved server-side against `IsoCountry` (user's explicit choice) rather than copying HubSpot's raw text or leaving it unmapped.

## Notes for reviewer

- Tests could not be run via `./run.sh ... manage.py test` in this session: building a fresh test database hits the unrelated pre-existing `ftp` migration bug described above (affects *any* app's tests, not just `client`, since Django migrates all apps to build the test DB). The new endpoints were instead verified live against the running dev containers (`curl` against `/api/client/companies/2/hubspot-sync/`, `/select/`, and `PATCH /api/client/companies/2/`; migration applied and verified against the real dev DB; `country_alpha2` matching verified against the real `IsoCountry` table). The added test code was reviewed by hand for correctness against the implementation. Recommend re-running `client` tests once the `ftp` migration issue is fixed.
