# Client app — Models overview

This document is an auto-generated skeleton describing the main models in `src/backend/client`.
Fill missing business logic notes and example payloads after reviewing the code.

## Models

### User

- Description: Person record for email ownership / contact name.

Fields:

| Field           |                      Type | Notes                |
| --------------- | ------------------------: | -------------------- |
| first_name      | CharField(max_length=100) | required             |
| last_name       | CharField(max_length=100) | blank/null allowed   |
| soc_net         |                 JSONField | social networks JSON |
| additional_info |             RichTextField | rich text            |
| comment         |             RichTextField | rich text            |

Relations:

- `emails` related_name from `Email` (one-to-many)

Example serialized output:

```json
{
  "id": 1,
  "first_name": "Olena",
  "last_name": "Ivanova",
  "soc_net": {},
  "additional_info": "",
  "comment": ""
}
```

---

### IsoCountry

- Description: ISO3166 country reference table.

Fields:

| Field        |                    Type | Notes            |
| ------------ | ----------------------: | ---------------- |
| alpha2       | CharField(max_length=2) | primary key      |
| alpha3       | CharField(max_length=3) | optional         |
| numeric_code |            IntegerField | optional         |
| iso_name     |               CharField | optional         |
| tld          |               CharField | top-level domain |

Relations:

- `companies` related_name from `Company`

Example serialized output:

```json
{
  "alpha2": "UA",
  "iso_name": "Ukraine",
  "tld": ".ua"
}
```

---

### Company

- Description: Main company entity with metadata and hierarchical parent (`corporation`).

Fields:

| Field           |                      Type | Notes            |
| --------------- | ------------------------: | ---------------- |
| name            | CharField(max_length=200) | optional         |
| country         |    ForeignKey(IsoCountry) | PROTECT          |
| city            |                 CharField | optional         |
| segment         |        CharField(choices) | business segment |
| url             |                  URLField | optional         |
| soc_net         |                 JSONField | social networks  |
| corporation     |          ForeignKey(self) | parent company   |
| matrix_id       |              IntegerField | non-negative id  |
| additional_info |             RichTextField | optional         |
| marked_for_del  |              BooleanField | soft-delete flag |
| hubspot_id      |                 CharField | unique, nullable — linked HubSpot company id (see [HubSpot integration](#hubspot-integration)) |
| logo            |                  FileField | nullable — locally cached HubSpot logo, served from `/media/company/...` |

Relations:

- `domains` (Domain.related_name)
- `emails` (Email.related_name)
- `subsidiaries` via `corporation.related_name`

Example serialized output:

```json
{
  "id": 123,
  "name": "Example Corp",
  "country": "US",
  "city": "Boston",
  "segment": "research-dev",
  "url": "https://example.com"
}
```

---

### Domain

- Description: Domains owned/related to companies; used to infer `Email.domain`.

Fields:

| Field        |                      Type | Notes                     |
| ------------ | ------------------------: | ------------------------- |
| domain       | CharField(max_length=200) | unique                    |
| type         |        CharField(choices) | domain classification     |
| company      |       ForeignKey(Company) | optional                  |
| role         |        CharField(choices) | e.g. client/manager       |
| date_created |                 DateField | auto-set on save if empty |
| comment      |             RichTextField | optional                  |

Relations:

- `emails` related_name from `Email`

Example serialized output:

```json
{
  "id": 10,
  "domain": "example.com",
  "type": "business",
  "company": 123
}
```

---

### Email

- Description: Email addresses linked to `User`, `Company`, and `Domain` with status and hashes.

Fields:

| Field        |                Type | Notes                      |
| ------------ | ------------------: | -------------------------- |
| email        |          EmailField | unique, lowercased on save |
| status       |  CharField(choices) | active/inactive            |
| type         |           CharField | uses Domain.TYPE_CHOICES   |
| user         |    ForeignKey(User) | owner                      |
| company      | ForeignKey(Company) | optional                   |
| domain       |  ForeignKey(Domain) | populated on save          |
| md5_hash     |           CharField | computed from email        |
| date_created |           DateField | optional                   |

Example serialized output:

```json
{
  "id": 42,
  "email": "john.doe@example.com",
  "status": "active",
  "user": 5,
  "company": 123,
  "domain": 10,
  "md5_hash": "..."
}
```

---

### CompanyCandidate

- Description: Staging/candidate records used during import and matching flows.

Fields:

| Field       |                Type | Notes                            |
| ----------- | ------------------: | -------------------------------- |
| name        |           CharField | copy of Company.name             |
| domain      |           CharField | original domain string (indexed) |
| is_valid    |        BooleanField | candidate validity               |
| is_verified |        BooleanField | verification flag                |
| company     | ForeignKey(Company) | nullable target after sync       |
| checked_at  |       DateTimeField | auto_now                         |
| created_at  |       DateTimeField | auto_now_add                     |

Example serialized output:

```json
{
  "id": 9001,
  "name": "Candidate Ltd",
  "domain": "candidate.example",
  "is_valid": true,
  "is_synced": false
}
```

---

## API endpoints

All endpoints are documented via `drf-spectacular` — see Swagger UI at `/api/schema/swagger/`
(tag names below match the Swagger groupings). This table is a quick human-readable index.

| Route                                     | View                                  | Tag        | Purpose                                              |
| ------------------------------------------ | ------------------------------------- | ---------- | ----------------------------------------------------- |
| `GET /api/client/companies/`               | `CompanyViewSet`                      | Company    | List/search companies (by name or domain)              |
| `GET /api/client/companies/{id}/`          | `CompanyViewSet`                      | Company    | Company detail incl. domains                          |
| `GET /api/client/emails/`                  | `EmailViewSet`                        | Email      | List/search emails, filter by `company`/`user_id`       |
| `GET /api/client/emails/{id}/`             | `EmailViewSet`                        | Email      | Email detail                                          |
| `GET /api/client/emails/by-email/{email}/` | `EmailViewSet.by_email`               | Email      | Look up an email record by its address                |
| `GET /api/client/users/`                   | `UserViewSet`                         | User       | List/search users by name                              |
| `GET /api/client/users/{id}/`              | `UserViewSet`                         | User       | User detail                                            |
| `GET /api/client/new-users-per-month/`     | `new_users_per_month_view`            | Client     | Aggregated new-client-user counts per year/month        |
| `GET/POST /api/client/newsletter/subscribers/` | `NewsletterSubscriberListView`     | Newsletter | List Mailchimp subscribers / add a new subscriber       |
| `GET /api/client/newsletter/subscribers/{hash}/` | `NewsletterSubscriberDetailView` | Newsletter | Mailchimp subscriber detail + local CRM match           |
| `GET /api/client/newsletter/managers/`     | `newsletter_managers_view`            | Newsletter | Managers eligible for the subscription form             |
| `POST /api/client/companies/{id}/hubspot-sync/` | `CompanyViewSet.hubspot_sync`    | Company    | Manual read-only sync/compare vs. HubSpot (see below)   |
| `POST /api/client/companies/{id}/hubspot-sync/select/` | `CompanyViewSet.hubspot_sync_select` | Company | Link a specific HubSpot candidate after `multiple_matches` |

## HubSpot integration

Manual, button-triggered, read-only (HubSpot → CRM) comparison — no cron/background sync, no
writes back to HubSpot. Frontend page: `HubspotSync.jsx` (`/tools/hubspot-sync?company_id=`).

- **Matching**: if `Company.hubspot_id` is already set, fetches that HubSpot company directly;
  otherwise searches HubSpot by the company's first domain (`HubSpotClient.search_company_by_domain`)
  and links `hubspot_id` on a single unambiguous match.
- **Fields shown**: every HubSpot company property with `hidden: false` in the portal's own
  property metadata (`GET /crm/v3/properties/companies`, cached 1h) — not a hand-picked
  allowlist. Fetched via the batch-read endpoint (`HubSpotClient.get_company_with_all_properties`)
  since the full property list is too long for a GET query string. Grouped in the API response
  (`hubspot_data.groups`) the same way HubSpot groups them in its own UI.
- **Copy to CRM**: only `name`, `city`, and `country` (best-effort matched to `IsoCountry` via
  `_match_iso_country`) have a real `Company` counterpart and an inline "copy" action; everything
  else is comparison-only.
- **Logo caching**: if the matched HubSpot company has a populated `logo_url` property, it is
  downloaded once (`_maybe_cache_hubspot_logo`) and stored as `Company.logo` under
  `media_shared/company/<company_id>.<ext>` (served at `/media/company/...`). Skipped if the
  company already has a cached logo — there is currently no "refresh" action; clearing
  `Company.logo` is the only way to force a re-download.

See `docs/client/regression_2026-09-04.md` and `docs/client/regression_2026-09-05.md` for the
full history/regression notes of this feature.

## Next steps (suggested)

- Review `src/backend/client/serializers.py` and add serializer examples under each model section.
- Add short examples of common queries used in reporting (e.g., top domains per country).
- Use `/.github/agents/templates/model_doc.md.tpl` to expand each model's documentation with real field notes.

File references:

- Model definitions: [src/backend/client/models.py](../../src/backend/client/models.py)
- Suggested docs output folder: `docs/client/`
