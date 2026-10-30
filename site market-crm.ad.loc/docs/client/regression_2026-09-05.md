# Regression Checklist — HubSpot Full Property Compare + Cached Logo

**App:** client
**Date:** 2026-09-05
**Developer:** Denis
**PR / branch:** develop (feature: hubspot-company-sync, follow-up)

---

## What is changing?

Extends the existing manual HubSpot ↔ Company compare feature (see
`regression_2026-09-04.md` / `pr_hubspot_company_sync.md`):

- The comparison form now shows **every non-hidden HubSpot company property** (grouped by
  HubSpot's own property group), instead of the previously curated ~26-field allowlist.
  Fetched via HubSpot's property-metadata endpoint (`/crm/v3/properties/companies`, cached)
  and the batch-read endpoint (`/crm/v3/objects/companies/batch/read`, avoids the GET
  query-string length limit that requesting hundreds of properties would hit).
- If HubSpot returns a populated `logo_url` property for the matched company, the logo is
  downloaded once and cached locally under `media_shared/company/` (served at
  `/media/company/...`), so the frontend never re-fetches it from HubSpot on every page load.
  Skipped entirely if the company already has a cached logo.
- New nullable `Company.logo` `FileField` (plain `FileField`, not `ImageField` — no Pillow
  dependency added for what is just an opaque cached blob).
- `CompanySerializer` gains a read-only `logo_url` (absolute media URL, or null).
- `HubspotSync.jsx` renders the dynamic `groups` structure instead of the static
  `HUBSPOT_DISPLAY_FIELDS` array; unused per-field UI dictionary strings removed.

---

## Affected models / serializers / views

- [x] `client.models.Company` — new field `logo` (`FileField`, `upload_to="company/"`)
- [x] `client.serializers.CompanySerializer` — new read-only `logo_url`
- [x] `client.api_views.py` — `_extract_hubspot_data` reshaped to grouped/dynamic output;
      new `_maybe_cache_hubspot_logo` helper; doc-only `HubspotCompanyDataSerializer` reshaped
- [x] `client.services.hubspot_client.HubSpotClient` — new `list_company_properties()`
      (cached) and `get_company_with_all_properties()` (batch read)
- [x] `client.tests` — HubSpot view tests updated for the new call pattern / response shape

---

## client app — cross-reference checks

### Email
- [ ] N/A — not touched

### Domain
- [ ] N/A — not touched (domain lookup for HubSpot search unchanged)

### Company
- [x] `Company.marked_for_del` — untouched, new field/logic doesn't interact with it
- [x] `Company.corporation` (self-FK) — untouched
- [x] `Company.country` (PROTECT FK) — untouched; country matching logic (`_match_iso_country`)
      unchanged, still read-only display + explicit user copy
- [x] New `logo` field is nullable/blank — existing companies unaffected, no backfill needed

### CompanyCandidate
- [ ] N/A

### IsoCountry
- [ ] N/A

---

## ftp / download cross-checks

- [ ] N/A — this change does not touch `ftp` or `download` models/imports

---

## Migration checklist

- [x] Migration file generated and reviewed (`AddField logo`, nullable FileField, no default)
- [x] Migration is reversible (plain `AddField`, `RemoveField` on reverse — no data migration)
- [x] No `RunPython`
- [x] No raw SQL

---

## Smoke tests (manual, local)

- [ ] Django admin — Company still loads/saves (`logo` not added to admin form; cache-only field)
- [ ] `POST /api/client/companies/{id}/hubspot-sync/` — response now returns `hubspot_data.groups`
      instead of flat known fields (check Swagger / `schema_check.yaml` regenerated)
- [ ] `GET /api/client/companies/{id}/` — new `logo_url` field present, null when no logo cached
- [ ] Frontend — HubspotSync page renders all returned groups/fields for a real matched company;
      "Заповнити все з HubSpot" still only copies name/city/country
- [x] First sync of a company whose HubSpot record has `logo_url` populated creates a file under
      `media_shared/company/`; a second sync does not re-download it — verified manually via
      `manage.py shell` (mocked `requests.get`, confirmed file written once, skipped on retry,
      `CompanySerializer.logo_url` resolves it, no leftover file after cleanup)
- [ ] `python manage.py test client` — **blocked**, see Notes below (pre-existing, unrelated to
      this change); verified the new/changed code paths manually instead (see above) plus
      `manage.py check` and `manage.py spectacular` (schema regenerates with 0 errors)

---

## Notes / known risks

- "All available fields" is scoped to HubSpot properties with `hidden: false` in the portal's
  property metadata — this mirrors the previous curator's intent (exclude `hs_`-prefixed
  calculated/analytics noise) but is now driven by HubSpot's own metadata instead of a
  hand-maintained list, so it will include any custom properties the portal defines without
  a code change.
- Property metadata and the (unused) group-label overrides are cached process-wide via
  Django's cache backend for 1 hour — a brand-new custom property in HubSpot may take up to an
  hour to appear on the comparison form.
- Logo caching is best-effort: download failures are logged and swallowed, they never fail the
  sync request. There is no manual "refresh logo" action yet — clearing `Company.logo` (e.g. via
  Django admin/shell) is currently the only way to force a re-download.
- `HubSpotClient.get_company_by_id` (single-property GET) is kept as-is for backward
  compatibility / existing tests of that low-level method; the new `hubspot_sync` /
  `hubspot_sync/select` view code paths now call `get_company_with_all_properties` instead.
- **Pre-existing, unrelated bug found while testing**: `python manage.py test` (any app) fails
  building the test database — `ftp/migrations/0016_usersonedrive_...py` runs `CreateModel`
  for `UsersOneDrive` (`db_table="users_onedrive"`) before `DeleteModel("UsersOD")`, but
  `UsersOD` (`ftp/migrations/0014_usersod.py`) already owns that same `db_table`, so the
  `CreateModel` collides (`relation "users_onedrive" already exists"`) on a from-scratch test
  database. This predates today's change (migration committed in `5415e3b`, untouched here) and
  is unrelated to `client`/HubSpot — flagging for the `ftp` app owner since it currently blocks
  `manage.py test` for the whole project, not just `client`. Also found (and cleaned up) an
  orphaned `test_enamine_db` left over from a prior interrupted run on the shared dev Postgres
  container.
- `schema_check.yaml` regenerated (`manage.py spectacular`) — it was already stale before this
  change (missing the earlier session's `hubspot_id`/`logo_url` additions), now current.
