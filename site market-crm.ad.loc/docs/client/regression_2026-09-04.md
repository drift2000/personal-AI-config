# Regression Checklist — HubSpot Company Sync (manual, read-only)

**App:** client
**Date:** 2026-09-04
**Developer:** Denis
**PR / branch:** develop (feature: hubspot-company-sync)

---

## What is changing?

Add a manual, button-triggered, one-way (HubSpot → CRM) sync of company data from HubSpot.
No cron/background workers, no writes back to HubSpot.

- New nullable/unique/indexed field `Company.hubspot_id` (stores HubSpot's `hs_object_id` once matched).
- New service module `client/services/hubspot_client.py` (HubSpot Search API + direct GET by id).
- New DRF actions on the existing `CompanyViewSet`: `POST /api/client/companies/{id}/hubspot-sync/` and
  `POST /api/client/companies/{id}/hubspot-sync/select/`.
- `CompanyViewSet` changes from `ReadOnlyModelViewSet` to also support `PATCH` (partial_update), since the
  frontend needs to save edited/merged fields back to CRM and no such endpoint currently exists.
- Frontend: extend `CompanyDetail.jsx` with a HubSpot sync panel (CRM data / HubSpot data blocks, field copy,
  save).

---

## Affected models / serializers / views

- [x] `client.models.Company` — new field `hubspot_id`
- [x] `client.serializers.CompanySerializer` — expose `hubspot_id` (read-only)
- [x] `client.api_views.CompanyViewSet` — base class change (Read-only → Retrieve/List/Update), two new
      `@action` routes
- [x] `client.services.hubspot_client` — new module (HTTP client only, no DB access)

---

## client app — cross-reference checks

### Email
- [ ] N/A — not touched by this change (`Email.save()` / `md5_hash` untouched)

### Domain
- [x] `Company.domains` (related_name) is only *read* to pick the domain to search HubSpot by — no writes,
      no changes to `Domain.save()` / `date_created` behavior

### Company
- [x] `Company.marked_for_del` — sync/PATCH code paths do not bypass or touch this flag; PATCH only ever
      writes fields the frontend explicitly sends in the request body
- [x] `Company.corporation` (self-FK) — untouched; PATCH still accepts `corporation_id` like any other
      writable field already exposed by `CompanySerializer`, no new recursive logic added
- [x] `Company.country` (PROTECT FK to IsoCountry) — untouched; sync **reads** country info from HubSpot for
      display only, it is never auto-written to `Company.country` by the backend (the user chooses what to
      copy/save, mapping ISO code vs free text is an open question — see Notes)
- [x] New `hubspot_id` field does not interact with `marked_for_del`, `corporation`, or `country`

### CompanyCandidate
- [ ] N/A — this model/import flow is not touched

### IsoCountry
- [ ] N/A — `alpha2` PK not touched

---

## ftp / download cross-checks

- [ ] N/A — this change does not touch `ftp` or `download` models/imports

---

## Migration checklist

- [x] Migration file generated and reviewed (`AddField hubspot_id`, nullable + unique + db_index)
- [x] Migration is reversible (plain `AddField`, `RemoveField` on reverse — no data migration/backfill)
- [x] No `RunPython` — pure schema change
- [x] No raw SQL

---

## Smoke tests (manual, local)

- [ ] Django admin — Company still loads/saves (hubspot_id not added to admin form on purpose; read-only via
      API only for now)
- [ ] API endpoint — `GET/PATCH /api/client/companies/{id}/` response shape unchanged except new
      `hubspot_id` read-only field (check Swagger)
- [ ] New endpoints show up correctly in Swagger (`/api/schema/`)
- [ ] Frontend — CompanyDetail page loads for a company with no hubspot_id, one with a linked hubspot_id, and
      renders the multiple-matches picker

---

## Notes / known risks

- `CompanyViewSet` was previously `ReadOnlyModelViewSet` (no PATCH existed anywhere for Company). This PR
  adds `partial_update` capability. Risk: any other future caller could now PATCH company fields. Mitigated
  by only adding `Retrieve/List/Update` mixins (no `create`/`destroy`), so the blast radius is limited to
  editing existing companies, matching what this feature needs. No new permission class was added since the
  rest of the `client` API has no auth (per project conventions) — flagged here for reviewer awareness.
- `hubspot_id` uniqueness: Postgres allows multiple NULL values under a unique constraint, so companies
  without a HubSpot match are unaffected.
- Open question (per feature spec) not yet resolved: exact field mapping HubSpot → Company for "Заповнити
  все з HubSpot", and whether `country` should map ISO code or free text — deferred to the frontend copy
  step, backend does not auto-map/save these.
