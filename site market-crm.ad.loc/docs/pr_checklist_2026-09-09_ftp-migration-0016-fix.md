# PR Checklist — fix ftp.0016 migration ordering (broke fresh DB builds)

**Branch:** feature/OAuth2
**App(s) touched:** ftp (migration file only)
**Date:** 2026-09-09

---

## Type of change

- [x] Bug fix
- [ ] New feature
- [ ] Refactor / cleanup
- [ ] Data migration / one-shot script
- [ ] Documentation only
- [ ] Frontend only

---

## Pre-merge checklist

### General
- [x] Locally tested: dropped `test_enamine_db`, ran `python manage.py test`
      from scratch — all 20 `ftp` migrations apply cleanly, 45 tests run
      (only 2 pre-existing, unrelated `client` Mailchimp-timeout failures —
      see `docs/ftp/migration_0016_fix_2026-09-09.md`)
- [x] No `print()` statements left in backend code (none added)
- [x] No hardcoded IDs, emails, or company names in production code
- [ ] Docker build still passes (`docker compose build`) — not rebuilt from
      image this pass, tested against the running dev container instead

### Backend
- [x] No new management commands
- [x] No new models
- [x] No new ForeignKeys
- [x] No new `save()` overrides
- [x] No new migration — existing `0016` operations reordered, content
      byte-for-byte identical (see diff: only the position of `CreateModel`
      moved)
- [x] Reviewed for reversibility and for already-applied-database safety:
      Django only replays a migration when it isn't yet recorded in
      `django_migrations`, so this is a no-op for every database that
      already has `0016` applied (confirmed the real dev DB's
      `users_onedrive` table already matches the intended final shape,
      independently of this file)

### client app
- [x] Not touched.

### ftp / download (touched)
- [x] Import idempotency preserved — no import logic touched, migration
      operation order only
- [x] End schema unchanged — same models/fields/`db_table`, verified by
      diffing the operations list before/after (same 8 operations, same
      parameters, different order)

### Frontend
- [x] Not touched.

### Documentation
- [x] `docs/ftp/migration_0016_fix_2026-09-09.md` — root cause and fix
      writeup
- [x] `docs/auth_azure/README.md` updated to reflect the blocker being
      resolved (this was found while testing that app)

---

## Risk level

- [x] 🟡 Medium — touches a `client`-adjacent app's already-applied
      migration history. Not 🔴 High: no schema/content change (reorder
      only), no effect on databases where `0016` is already applied, and
      the fix was verified end-to-end against a from-scratch database build.

---

## Notes for reviewer

Found while trying to run tests for the new `auth_azure` app (Phase 1 of the
Azure AD SSO work — separate PR checklist:
`docs/pr_checklist_2026-09-09_auth-azure-phase1.md`). This bug is unrelated
to that work and pre-existing (dated 2025-09-18, reproduces on `develop`
today for any app's test run) — it just happened to block the first attempt
in this environment to build a database from scratch in a while. Root cause:
Django's migration autodetector generated `ftp.0016` with `CreateModel`
before the same-named old table was dropped, because it doesn't track
`db_table` reuse across a model rename-via-recreate. Fix is a pure
operation reorder; see the linked writeup for the full before/after.
