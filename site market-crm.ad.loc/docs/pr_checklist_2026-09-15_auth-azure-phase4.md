# PR Checklist — Azure AD SSO, Phase 4 (frontend sign-in option + role-gated HubSpot sync)

**Branch:** feature/OAuth2
**App(s) touched:** auth_azure (none — reused as-is), client (backend permission wiring), frontend
**Date:** 2026-09-15

---

## Type of change

- [x] New feature
- [ ] Bug fix
- [ ] Refactor / cleanup
- [ ] Data migration / one-shot script
- [ ] Documentation only
- [x] Frontend only — mostly; one backend permission change alongside it (see below)

---

## Pre-merge checklist

### General
- [x] Locally tested against the running dev container: `manage.py check`
      clean, full backend suite 77/77 (only the 2 pre-existing, unrelated
      `client` Mailchimp-timeout failures), `docker logs frontend_crm_dev`
      shows a clean webpack compile (1 pre-existing, unrelated unused-import
      warning in `CompanyDetail.jsx`, not introduced by this change)
- [x] No `print()`/`console.log` left in
- [x] No hardcoded IDs, emails, or company names
- [ ] Docker build still passes — tested against the running dev containers,
      not rebuilt from image this pass (same caveat as Phases 1–3)
- [ ] **Not verified in an actual browser** — no headless-browser tool was
      available in this environment. Verified instead via: webpack compiling
      cleanly, HTTP reachability (`curl` 200s), and code review against the
      existing `useStaffToolsAccess`/`RequireAuth` patterns already proven
      in production. Please click through `/login` and a company detail
      page before merging.

### Backend
- [x] `client/api_views.py::CompanyViewSet.get_permissions()` — new
      override, only for `hubspot_sync`/`hubspot_sync_select` actions; every
      other action unchanged (still the global default)
- [x] No new models, no migrations
- [x] `client/tests.py::CompanyHubspotSyncViewTests` updated (existing
      `setUp` now grants `staff` explicitly) + 2 new cases (role-alone
      sufficient; neither role → 403)

### client app (touched — permission wiring only, no model/relation change)
- [x] Regression checklist not required per `.github/agents/client.agent.md`
      — its trigger is model/relation changes, and there are none here
- [x] `Email.save()` / `Domain.save()` overrides unaffected (untouched)
- [x] Soft-delete (`marked_for_del`) logic preserved (untouched)
- [x] **Behavior change, flagged explicitly**: `hubspot_sync`/`hubspot_sync_select`
      were previously reachable by *any* authenticated user (no
      `permission_classes` set at all) — the frontend button was hidden for
      non-staff, but the API itself wasn't gated. Now requires `staff` OR
      `hubspot_sync_operator`. This is an intentional fix, not a side
      effect — flagging per the PR template's instruction to call out
      anything touching `client`.

### ftp / download
- [x] Not touched.

### Frontend
- [x] Column `key` values — n/a, no table changed
- [x] Pagination / sort state — n/a
- [x] No hardcoded endpoint URLs — the one new hardcoded string
      (`/api/auth/azure/login/`) is a real browser-redirect target, not an
      API call through the shared `api` axios instance, so it's exempt from
      that convention (same reasoning as why it isn't in `api/auth.js`)

### Documentation
- [x] `docs/auth_azure/README.md` — new "Phase 4" section, status line,
      testing section updated

---

## Risk level

- [x] 🟡 Medium — touches `client`'s `CompanyViewSet` (permission_classes on
      two actions, not models/migrations) and adds a genuine access-control
      *change* (previously ungated actions now require a role) rather than
      pure UI polish. Everything else (frontend hook, login button) is
      additive and low-risk on its own.

---

## Notes for reviewer

The interesting part of this pass isn't the frontend (that was mostly
wiring `useHasRole` the same way `useStaffToolsAccess` already works) —
it's that `CompanyViewSet.hubspot_sync`/`hubspot_sync_select` had **no**
`permission_classes` at all before this, discovered while implementing the
button-gating the original design doc asked for. Fixed it in the same pass
since leaving the frontend gated while the API stayed open would have been
a misleading half-measure. `IsHubspotSyncOperator` (written in Phase 1,
unused until now) and the existing `IsStaffToolsUser` are combined with
DRF's `|` operator so `staff`'s existing access is preserved exactly, not
narrowed.
