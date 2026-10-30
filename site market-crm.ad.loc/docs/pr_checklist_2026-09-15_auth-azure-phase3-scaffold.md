# PR Checklist — Azure AD SSO, Phase 3 scaffold (no real AD access yet)

**Branch:** feature/OAuth2
**App(s) touched:** auth_azure only
**Date:** 2026-09-15

---

## Type of change

- [x] New feature
- [ ] Bug fix
- [x] Refactor / cleanup (`ADGroupRoleMapping.record_seen` extracted, reused
      by both the login path and the new command)
- [ ] Data migration / one-shot script
- [ ] Documentation only
- [ ] Frontend only

---

## Pre-merge checklist

### General
- [x] Locally tested against the running dev container: `manage.py check`
      clean, `migrate auth_azure` applied cleanly, full suite 75/75 (only
      the 2 pre-existing, unrelated `client` Mailchimp-timeout failures)
- [x] No `print()` (uses `CommandLogger`)
- [x] No hardcoded IDs, emails, or company names
- [ ] Docker build still passes — tested against the running dev container,
      not rebuilt from image this pass (same caveat as Phases 1–2)

### Backend
- [x] New management command (`discover_azure_ad_groups`) has logging
- [x] No new models — one data migration
      (`0003_seed_role_groups.py`, seeds `admin`/`hubspot_sync_operator`/`viewer`
      Groups, same convention as `accounts/migrations/0001_create_staff_group.py`)
- [x] No new ForeignKeys
- [x] No new `save()` overrides
- [x] Migration reviewed for reversibility: `RunPython` with both forwards
      and reverse functions, mirrors an existing precedent exactly
- [x] Command is idempotent and safe to re-run (never overwrites an
      already-set `internal_role`)

### client app
- [x] Not touched.

### ftp / download
- [x] Not touched.

### Frontend
- [x] Not touched.

### Documentation
- [x] `docs/auth_azure/README.md` — new "Phase 3" section, status line
      updated, testing section updated (47 tests)
- [x] `.env.example` — noted the third Application permission
      (`Group.Read.All`/`Directory.Read.All`) this needs, distinct from
      Phase 1's Delegated and Phase 2's Application permission

---

## Risk level

- [x] 🟢 Low — additive only (one seed migration, one new command, one new
      Graph method, one extracted-and-reused model method). No behavior
      change for any existing path — `AzureADOIDCBackend._record_unmapped_groups`
      now calls `ADGroupRoleMapping.record_seen` instead of inlining the
      same logic, verified identical via the existing backend tests still
      passing unchanged.

---

## Notes for reviewer

Requested explicitly as "prepare Phase 3 without real AD access yet" — so
this is scaffolding, not the actual rollout step. Nothing here can be
exercised against a real tenant (same caveat as every other phase);
`discover_azure_ad_groups` and `AppOnlyGraphClient.list_groups` are tested
only against mocked Graph responses. The three Graph capabilities built so
far (login-time delegated group fetch, Phase 2's app-only user lookup,
Phase 3's app-only group listing) each need a distinct Azure AD permission
consented — that's now spelled out end-to-end in `.env.example` and
`docs/auth_azure/README.md` so IT has the full list in one place instead of
discovering it phase by phase.
