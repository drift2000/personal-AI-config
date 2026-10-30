# Download app — API overview

`src/backend/download` exposes reporting endpoints over product download logs, enriched
by matching each download back to `client` entities (Company/Email/Domain). Full schema is
available via Swagger UI at `/api/schema/swagger/` (tags below match the Swagger groupings).

## API endpoints

| Route                                              | View                              | Tag             | Purpose                                                    |
| --------------------------------------------------- | --------------------------------- | --------------- | ------------------------------------------------------------ |
| `GET /api/download/root/`                            | `download_api_root_view`          | Download        | Root/health response for this API namespace                 |
| `GET /api/download/report/`                          | `DownloadReportViewSet`           | Download Report | Paginated list of download reports; rich filters via `ReportFilter` (region, new-users-only, `email_id`, `company_id`, date year/month) |
| `GET /api/download/report/{id}/`                     | `DownloadReportViewSet`           | Download Report | Single download report detail                                |
| `GET /api/download/product/monthly/{product_ids}/`   | `product_monthly_downloads_view`  | Download        | Monthly download counts for one or more products (comma-separated ids) |
| `GET /api/download/monthly/`                         | `monthly_downloads_view`          | Download        | Monthly download counts across all products, optional product-field filters |
| `GET /api/download/fields/{field}/`                  | `product_field_values_view`       | Download        | Distinct values for a product field (category/class/group/name) |
| `GET /api/download/reports/unknown-region-domains/`  | `unknown_region_domains_view`     | Download        | Domains with no resolved company region (staff-only)          |
| `GET /api/download/reports/free-host/`               | `free_host_view`                  | Download        | Free-host email downloads for company id=4 (staff-only)       |
| `POST /api/download/reports/add/`                    | `report_add`                      | Download        | Ingests a single download event in real time (see below)      |

## Notes

- `DownloadReportViewSet` maps frontend-friendly ordering keys (e.g. `company__region`) to the
  actual DB path (`email__company__country__region`) via `ORDERING_MAP` — region always comes
  from the email's *current* company, not the historical `Report.company`.
- Pagination uses the shared `common.pagination.DefaultPagination` (also used by `ftp`).

## Import pipeline: source → parse → match → store

Both `python manage.py import_download_stat <csv>` (batch) and
`POST /api/download/reports/add/` (single event, real time) funnel into the
same matching/creation logic: `download.tasks.process_download_event(data)`.
`data` is a dict with keys `id, cid, dtime, ip, action_stat, email, fullname`
— from `csv.DictReader` for the batch command (all raw strings) or from
`DownloadEventSerializer.validated_data` for the API (already-typed: `id` is
`int`, `dtime` is an aware `datetime`, `ip`/`email`/`fullname` are validated
strings).

Matching rules, in order:
1. Skip immediately (no error) if `Report.id` already exists — this is what
   makes both entry points idempotent for the same event/row.
2. If `Email` exists for the address, reuse its linked `Company`/`User`.
3. Else if a `Domain` matches the address's domain part, reuse its `Company`.
4. Else create a new `Company` (region guessed from the domain's TLD via
   `IsoCountry.tld`), a new `Domain` (`role="client"`), a new `User` (name
   split from `fullname`), and a new `Email` — then the `Report` row.

Known edge cases: unmatched TLD → `Company.country` stays `None`; blank
`ip`/`fullname` are only tolerated on the CSV path today (the API's
`DownloadEventSerializer` requires both — see the "Open items" section of
`docs/pr_checklist_2026-09-09_download-event.md`).

## Verification history

See `docs/pr_checklist_2026-09-09_download-event.md` for the manual
verification of `reports/add/` (a `dtime`-type bug that made every request to
this endpoint fail with `400` was found and fixed during that review) and for
open follow-ups (auth on the new endpoint, error-message detail, missing test
coverage in `download/tests.py`).

## Next steps (suggested)

- Add example QA queries for monthly import validation.
- Add real `TestCase`s for `process_download_event` (new email, existing
  email, existing domain/new email, duplicate `id`) once the unrelated `ftp`
  migration-history issue blocking `manage.py test` in this environment is
  merged in from `feature/OAuth2`.
