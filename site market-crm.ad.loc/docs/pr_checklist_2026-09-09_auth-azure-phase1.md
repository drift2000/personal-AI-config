# PR Checklist — Azure AD SSO, Phase 1 (auth_azure app, backend only)

**Branch:** feature/OAuth2
**App(s) touched:** auth_azure (new), accounts (logging only), project (settings/urls)
**Date:** 2026-09-09

---

## Type of change

- [x] New feature
- [ ] Bug fix
- [ ] Refactor / cleanup
- [ ] Data migration / one-shot script
- [ ] Documentation only
- [ ] Frontend only

---

## Pre-merge checklist

### General
- [x] Locally tested against the running dev container (not "real data" —
      no real Azure tenant exists yet): `manage.py check`, `makemigrations`,
      `migrate` all clean; `GET /api/auth/azure/login/` verified to build a
      correct Azure v2 authorize redirect end-to-end; `manage.py test
      auth_azure` now passes 17/17 from a fresh database (see Notes — this
      needed the separate `ftp` migration fix,
      `docs/pr_checklist_2026-09-09_ftp-migration-0016-fix.md`).
- [x] No `print()` statements left in backend code (uses `common/command_logger.py`)
- [x] No hardcoded IDs, emails, or company names in production code
- [ ] Docker build still passes (`docker compose build`) — dependency installed
      live in the running container for this pass; not yet rebuilt from the
      updated `requirements.txt`

### Backend
- [x] New management commands have logging — n/a, no management commands added
      this phase (`link_existing_users_to_azure` backfill is Phase 2)
- [x] New models have `__str__` defined (`AzureProfile`, `ADGroupRoleMapping`)
- [x] ForeignKeys use explicit `on_delete` (`CASCADE` for `AzureProfile.user`,
      `PROTECT` for `ADGroupRoleMapping.internal_role` — deliberately not
      `CASCADE`, so deleting a `Group` in admin can't silently orphan mappings)
- [x] No new `save()` overrides added
- [x] Migrations generated and committed (`auth_azure/migrations/0001_initial.py`)
- [x] Migration reviewed for reversibility — pure `CreateModel`, both new
      fields on other models are none (no existing models altered); additive,
      nullable-safe, no backfill in the migration

### client app
- [x] Not touched. Azure identity fields deliberately live on a new
      `AzureProfile` model (`auth_azure`), not on `client.models.User` — see
      `docs/auth_azure/README.md` § "Two deviations". Regression checklist
      (`.github/agents/client.agent.md`) therefore not required — its trigger
      is `client` model/relation changes, and there are none.

### ftp / download
- [x] Not touched by this change. Separately: discovered a pre-existing,
      unrelated migration defect in `ftp/migrations/0016_usersonedrive_...py`
      (duplicate `db_table="users_onedrive"` vs. `0014_usersod.py`) that
      breaks fresh test-database creation for the whole repo. Reported to
      the user; not fixed here.

### Frontend
- [x] Not touched this phase (Phase 4).

### Documentation
- [x] `docs/auth_azure/README.md` created — models, login flow, settings,
      permission classes, explicit list of what's deferred to later phases
- [x] `.env.example` updated with the `AZURE_*` block
- [ ] `once` script documented — n/a

---

## Risk level

- [x] 🟡 Medium — new app, new settings (`INSTALLED_APPS`,
      `AUTHENTICATION_BACKENDS`, `MIDDLEWARE`, `OIDC_*`), and a new
      `OneToOne` on `auth.User`. No existing model/endpoint behavior changes
      while `AZURE_AUTH_ENFORCED=False` (verified: `IsAuthenticated` was
      already the global DRF default before this phase, unrelated to this
      change — see `ExistingApiUnauthenticatedBehaviorUnchangedTests` in
      `auth_azure/tests.py`). Not 🔴 High: no `client` app changes, no
      migration touches existing tables/columns.

---

## Notes for reviewer

Scope for this pass was deliberately limited to Phase 1 backend only
(confirmed before starting): the `auth_azure` app, its two models +
migration, OIDC login/callback endpoints, role-sync-from-Graph logic,
permission-class scaffolding, and settings/env wiring — all behind
`AZURE_AUTH_ENFORCED=False`. No real Azure AD tenant exists yet, so the
login/callback flow has not been exercised end-to-end; it's `pip install`ed
and Django-`check`ed clean, and unit-tested against mocked Graph responses.

Two things surfaced while doing the required pre-coding reading
(`.github/agents/client.agent.md`, current `accounts`/`project` state) that
changed the design from the original brief — both flagged and confirmed with
the user before writing code, both documented in `docs/auth_azure/README.md`:
password login + `/api/auth/me|login|logout/` already existed
(`c15c33a`, the commit immediately prior on this branch), and the "User
model" in the brief meant `client.User` (a CRM contact entity), not the
actual login account.

Initially could not run `python manage.py test auth_azure` — a pre-existing,
repo-wide test-database bootstrap bug (unrelated `ftp` migration ordering
defect, reproduced on `python manage.py test client` too) prevented building
a fresh test DB at all. Fixed separately (own PR checklist:
`docs/pr_checklist_2026-09-09_ftp-migration-0016-fix.md`,
writeup: `docs/ftp/migration_0016_fix_2026-09-09.md`) — tests now run and
pass. See `docs/auth_azure/README.md` § Testing.
