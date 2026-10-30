# PR Checklist — Azure AD SSO, Phase 2 (link existing users + unmapped-group recording + global role gate)

**Branch:** feature/OAuth2
**App(s) touched:** auth_azure only
**Date:** 2026-09-15

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
- [x] Locally tested against the running dev container: `manage.py check`,
      `makemigrations`/`migrate` clean; full suite 66/66 (only the 2
      pre-existing, unrelated `client` Mailchimp-timeout failures)
- [x] No `print()` (uses `CommandLogger`/`init_file_logger`)
- [x] No hardcoded IDs, emails, or company names
- [ ] Docker build still passes — tested against the running dev container,
      not rebuilt from image this pass (same caveat as Phase 1)

### Backend
- [x] New management command (`link_existing_users_to_azure`) has logging
      (`CommandLogger`, matches `ftp/management/commands/sync_ftp_users_and_roles.py`'s style)
- [x] No new models — `ADGroupRoleMapping.internal_role` made nullable
      (migration `0002_alter_adgrouprolemapping_internal_role`)
- [x] ForeignKeys: no change (`internal_role` stays `on_delete=PROTECT`, now
      also `null=True`)
- [x] No new `save()` overrides
- [x] Migration generated and committed, reviewed for reversibility: a
      single nullable-relaxation, no data loss, safe to reverse
- [x] Command is idempotent and safe to re-run (`--force` re-checks
      already-linked users; without it they're skipped) — required since
      this is explicitly not a `once` script

### client app
- [x] Not touched.

### ftp / download
- [x] Not touched.

### Frontend
- [x] Not touched.

### Documentation
- [x] `docs/auth_azure/README.md` — new "Phase 2" section (the command) and
      "Unmapped AD groups" section (auto-recording + the global role gate
      decided in conversation, not the original design doc)
- [x] `.env.example` — noted the additional Application permission
      (`User.Read.All` or similar, admin-consented) `link_existing_users_to_azure`
      needs, distinct from the Delegated scope login uses

---

## Risk level

- [x] 🟡 Medium — touches `auth_azure` only (not `client`), but adds a
      **global** DRF permission class (`HasAssignedRole`) to
      `REST_FRAMEWORK.DEFAULT_PERMISSION_CLASSES`. No-op today
      (`AZURE_AUTH_ENFORCED=False`, verified by the unchanged full test
      suite), but flipping that flag before `ADGroupRoleMapping` has mapped
      rows would 403 every authenticated user — flagged prominently in
      `docs/auth_azure/README.md` and to the user directly in this session.

---

## Notes for reviewer

Three things landed together because they came out of the same design
conversation with the user, not because they're one feature:

1. **Phase 2 proper** — `link_existing_users_to_azure`: pre-link existing
   `auth.User` accounts to Azure by email, using a new app-only
   (client-credentials) Graph capability distinct from the delegated one
   login uses.
2. **Unmapped AD group auto-recording** — `ADGroupRoleMapping.internal_role`
   is now nullable; `AzureADOIDCBackend` auto-creates an unmapped row for
   any never-seen AD group at login time, so an admin never has to look up
   `azure_group_id`s by hand — they just fill in rows that already exist.
3. **Global role gate** — `HasAssignedRole`, explicitly requested by the
   user as "the empty-role case should be a global API block, not just a
   frontend nicety." Ties to the same `AZURE_AUTH_ENFORCED` flag as
   everything else — see the risk note above before ever flipping it.
