# auth_azure — Azure AD (Microsoft Entra ID) SSO

Backend-driven OIDC login: Django owns the redirect → Azure AD → callback →
token exchange flow. React never sees `id_token`/`access_token` — only the
same httpOnly Django session cookie the existing password login already uses.

**Status: Phase 1, 2, 4 done; Phase 3 scaffolded, not runnable yet.**
`AZURE_AUTH_ENFORCED=False`. Login works, existing users can be pre-linked
by email (Phase 2), and the frontend has a "Sign in with Microsoft" option
plus role-gated UI (Phase 4) — but none of it is mandatory yet. Phase 3's
tooling (baseline role Groups, `discover_azure_ad_groups`) is ready to run
the moment a real Azure AD tenant exists — see "Phase 3" below.

## Two deviations from the original design doc

The design doc that kicked this off assumed the frontend had no
authentication at all yet, and that "the client app's User model" was the
login account. Both were true when the doc was written but are stale as of
`c15c33a` ("added login for all crm pages"), the commit immediately before
this work started. Concretely:

1. **`accounts` app already serves `/api/auth/login/`, `/api/auth/logout/`,
   `/api/auth/me/`** (password-based, `django.contrib.auth`). Azure endpoints
   live at `/api/auth/azure/login/` and `/api/auth/azure/callback/` instead —
   `me`/`logout` are *not* duplicated here, because a Django session works
   identically regardless of which backend authenticated it (see
   `AUTHENTICATION_BACKENDS` in `project/settings.py`): `accounts.me_view`
   and `accounts.logout_view` already work for an Azure-authenticated session
   with no changes.
2. **`client.models.User` is a CRM contact/business-card entity** (name,
   company, social links — see `client/models.py:9`), unrelated to login.
   The real login account is `settings.AUTH_USER_MODEL`
   (`django.contrib.auth.models.User`, no custom user model configured). The
   Azure identity fields therefore live on a new `AzureProfile` model here,
   `OneToOne` to that user — not on `client.User`. This also means **no
   `client` app files were touched**, so the CLAUDE.md/`client.agent.md`
   regression-checklist requirement (only triggered by `client` model/relation
   changes) doesn't apply to this phase.

Also worth knowing: `REST_FRAMEWORK.DEFAULT_PERMISSION_CLASSES` already
defaults to `IsAuthenticated` globally (added in the same commit that added
password login) — the API is *already* not open by default, contrary to
CLAUDE.md's "DRF API has no auth enforcement" note, which predates that
commit. See `auth_azure/middleware.py`'s docstring for what this means for
`AZURE_AUTH_ENFORCED`.

## Models

- **`AzureProfile`** — `OneToOne` to `auth.User`. `azure_oid` (nullable
  unique UUID), `azure_tenant_id`, `last_login_via_azure`, `is_active_ad`
  (default `True`; flips to `False` by a future "still in AD?" check —
  never cascade-deletes related data). Upserted on every successful Azure
  login by `auth_azure/backends.py::AzureADOIDCBackend`.
- **`ADGroupRoleMapping`** — bridges an Azure AD group id to an existing
  `auth.Group` (`internal_role`, FK, `on_delete=PROTECT`, **nullable**).
  Reuses the group-based role system already in the codebase
  (`common/access.py`, `client/permissions.py`) instead of introducing a
  second role concept. `internal_role` is nullable because rows aren't only
  created manually — see "Unmapped AD groups" below.

Migrations: `0001_initial.py` (additive, nullable-safe, no backfill), plus
`0002_alter_adgrouprolemapping_internal_role.py` (made `internal_role`
nullable — see below).

### Unmapped AD groups: recorded automatically, granted nothing

An admin doesn't have to look up `azure_group_id`s by hand before they can
map anything. `AzureADOIDCBackend._record_unmapped_groups` runs on every
login and, for every AD group in the user's claims that isn't already a row
in `ADGroupRoleMapping`, creates one with `internal_role=None` (and refreshes
`azure_group_name` on rows that already exist, in case the group was renamed
in Azure AD). The admin's job (rollout phase 3) becomes: open
`ADGroupRoleMapping` in Django admin, see which rows already exist from real
logins, and pick a Django Group for the ones that should grant access.

A user whose AD group(s) are all unmapped (`internal_role` still `None`, or
no AD group at all) is not treated as "give them default/basic access" —
they get **no role**: `_sync_profile_and_roles` never adds them to any
Group, and (once `AZURE_AUTH_ENFORCED=True`) `HasAssignedRole` rejects them
at the API level — see below. The frontend (Phase 4) is expected to show
"your group doesn't have access yet" rather than a broken/empty page for
this case, driven by `GET /api/auth/me/` returning an empty role list.

## Login flow

1. `GET /api/auth/azure/login/` (`auth_azure.views.AzureLoginView`, a thin
   `mozilla_django_oidc` `OIDCAuthenticationRequestView`) redirects to Azure
   AD's `/oauth2/v2.0/authorize`.
2. User authenticates with Azure AD.
3. `GET /api/auth/azure/callback/` (`AzureCallbackView`) exchanges the code
   for tokens. `AzureADOIDCBackend.get_userinfo` additionally calls
   `graph_client.GraphClient.get_member_of()` with the access token to fetch
   the user's AD group memberships (`GroupMember.Read.All` scope).
4. `AzureADOIDCBackend.filter_users_by_claims` links to an existing
   `auth.User`: first by `AzureProfile.azure_oid`, falling back to
   case-insensitive email match (parallel-rollout support — no user is
   force-linked or force-created without an email match on first login).
   No match → `mozilla_django_oidc` creates a new `auth.User`.
5. `create_user`/`update_user` both call `_sync_profile_and_roles`, which
   upserts `AzureProfile` and re-syncs Django Groups from
   `ADGroupRoleMapping` **on every login** — but only ever touches groups
   this mapping table is authoritative for, so groups assigned outside
   Azure AD (e.g. `staff`) are never removed.
6. Django sets the session cookie; redirects to `settings.LOGIN_REDIRECT_URL`
   (`AZURE_POST_LOGIN_REDIRECT_URL` env, default `/`) or
   `LOGIN_REDIRECT_URL_FAILURE` on failure.

Login/callback success and failure are logged to `auth_azure.log` via
`common/command_logger.py::init_file_logger` (see `backends.py`, `views.py`).
Password-login success/failure was also instrumented (`accounts/views.py`)
to the same standard, in `accounts_auth.log` — it had none before this phase.

## Settings / environment variables

All in `.env` (see `.env.example`), read via `django-environ` in
`project/settings.py`. Never hardcoded, never sent to the frontend.

| Variable | Purpose |
|---|---|
| `AZURE_TENANT_ID` | Tenant ID; also used to derive the v2 authorize/token/jwks endpoints |
| `AZURE_CLIENT_ID` / `AZURE_CLIENT_SECRET` | App Registration credentials (`Web` platform, confidential client) |
| `AZURE_REDIRECT_URI` | Documents what to register in the Azure Portal App Registration. The actual value sent to Azure AD is computed by `mozilla_django_oidc` from `request.build_absolute_uri(reverse(OIDC_AUTHENTICATION_CALLBACK_URL))` (`OIDC_AUTHENTICATION_CALLBACK_URL = "auth_azure_api:azure_callback"`, set in `project/settings.py` — the library's unnamespaced default doesn't resolve against this app's namespaced URL and was verified to raise `NoReverseMatch` before this was added), respecting `USE_X_FORWARDED_HOST`/`SECURE_PROXY_SSL_HEADER` already configured for this deployment. Keep the registered URI and this deployment's actual host in sync manually — there's no code-level link between them. |
| `AZURE_GRAPH_SCOPES` | Space-separated OIDC + Graph scopes requested at login; default `openid profile email User.Read GroupMember.Read.All` |
| `AZURE_AUTH_ENFORCED` | Default `False`. See `middleware.py` — reserved for a later phase, currently a no-op even when `True` |
| `AZURE_POST_LOGIN_REDIRECT_URL` / `AZURE_POST_LOGIN_FAILURE_REDIRECT_URL` | Where to send the browser after login succeeds/fails; default `/` |

`AZURE_POST_LOGIN_REDIRECT_URL` sets Django's own `LOGIN_REDIRECT_URL`
setting (that's the name `mozilla_django_oidc` reads it under) — that
setting was previously unset in this project, so it also changes the
post-login redirect for the existing `django.contrib.auth.views.LoginView`
at `/login/` (Django admin / `common/access.py`-gated pages) from Django's
built-in default (`/accounts/profile/`, which doesn't exist here) to `/`
(the home page). This is a side effect of the two flows sharing one Django
setting name, not something specific to this app; flagging it since it
wasn't an explicit ask.

## Permission classes (`auth_azure/permissions.py`)

`IsAdmin`, `IsHubspotSyncOperator`, `IsViewer` — DRF `BasePermission`
subclasses checking group membership (`admin`/`hubspot_sync_operator`/`viewer`
groups respectively; superusers always pass), mirroring the existing
`client/permissions.py::IsNewsletterManager`/`IsStaffToolsUser` pattern. Not
wired into any view yet — that's Phase 4 (frontend gating), e.g. the HubSpot
sync button. This is the intended seam for later row-level permissions: add
`.filter()` logic inside one of these classes (or an adjacent queryset mixin)
without touching call sites.

`HasAssignedRole` is different from the three above: it's **global**, added
to `REST_FRAMEWORK.DEFAULT_PERMISSION_CLASSES` in `project/settings.py`
alongside `IsAuthenticated`, so it runs on every DRF view without being
opted into per-viewset. No-op (always passes) while
`AZURE_AUTH_ENFORCED=False` — same switch as everything else gated by that
flag. Once `True`: authenticated-but-role-less users (no membership in any
Group that's the `internal_role` of an `ADGroupRoleMapping` row) get
rejected; superusers still always pass. This is the backend half of "empty
role → no access", decided explicitly (not the default before this) because
the plain Django views under `/api/auth/` (`accounts`' login/logout/me,
`auth_azure`'s login/callback) aren't DRF views and so are unaffected by
this — a role-less user can always still see their own state and log out.

## Giving one person extra rights beyond their AD-mapped role

Example: an AD group is mapped to Django Group `manager`, but one specific
manager needs an additional capability that shouldn't apply to every
manager. Group membership is additive — a user can be in as many Django
Groups as needed — so the answer is: add that person to another Group (an
existing one like `hubspot_sync_operator`, or a new one) manually in Django
admin, same as before any of this Azure work existed.

This survives every future Azure login **as long as that Group is never
made the `internal_role` of any `ADGroupRoleMapping` row**.
`AzureADOIDCBackend._sync_profile_and_roles` only ever adds/removes Groups
that appear as an `internal_role` somewhere in that table (system-wide, not
just for this user) — everything else is left completely alone on every
sync. So a manually-assigned, AD-unmapped Group is a permanent manual
override; nothing here will silently touch it.

**The catch**: this protection is per-*Group*, not per-*user*. If that same
Group later becomes AD-mapped (someone links an AD group to it), it becomes
"managed" from that point on — the next login for every holder of that
Group re-evaluates it against their actual AD membership, including this
person's manual grant, which would be dropped if their AD groups don't
include the newly-linked one. Pick a Group name you don't intend to ever
map from AD if you want it to stay a pure manual switch — or accept that
mapping it later turns it into an AD-driven role for everyone who has it.

For gating actual API views on "has role X or role Y" (Phase 4, not started
— see `IsAdmin`/`IsHubspotSyncOperator`/`IsViewer` above), DRF combines
`permission_classes` list entries with AND by default; use its `|`/`&`
operators between classes (e.g. `IsManager | IsHubspotSyncOperator`) for OR.

## Phase 2 — linking existing users ahead of their first Azure login

`python manage.py link_existing_users_to_azure` (management command, not a
`once` script — expected to be re-run during rollout as new users are added
or emails get fixed). Purpose: this is about **users**, not roles/groups —
pre-populating `AzureProfile.azure_oid` for existing `auth.User` accounts by
matching email against Azure AD, so a user's *first* Azure login resolves
instantly by `azure_oid` (`AzureADOIDCBackend.filter_users_by_claims`)
instead of relying on the email fallback at that moment. Running it is
optional — the email fallback at login time means linking still works
without ever running this — but it lets IT review mismatches (no email,
ambiguous match, no AD match) before anyone's first real login.

- `--dry-run` — report without writing.
- `--force` — re-check users that already have an `azure_oid` (default:
  skip them, so re-running is cheap/idempotent).
- Skips users with no email (can never match) and reports Graph lookups that
  are ambiguous (`GraphAmbiguousMatchError` — more than one AD user shares a
  `mail`/`userPrincipalName`) separately from "not found", since ambiguous
  needs manual review rather than being treated the same as a clean miss.
- Logged via `common/command_logger.py::CommandLogger`, same as every other
  management command in this codebase.

This needed a second Graph capability distinct from what login uses:
`AppOnlyGraphClient` in `graph_client.py` fetches its own token via the
OAuth2 **client-credentials** grant (`get_app_only_access_token`, cached
in-process until near expiry) — the delegated `GraphClient` used during
login only has a token because a user just signed in, which isn't the case
here. Requires an **Application** permission (e.g. `User.Read.All`),
admin-consented in the Azure Portal separately from the **Delegated**
`GroupMember.Read.All` login uses — same App Registration and client
secret, different consent type. Not exercisable against a real tenant yet
(same as everything else in this app); tested against mocked Graph
responses.

## Phase 3 (scaffold only — no real Azure AD tenant/groups exist yet)

Phase 3 is populating `ADGroupRoleMapping` with real rows — this depends on
IT having created/identified the AD groups, which hasn't happened yet. What
*is* ready, so this can start the moment that access exists:

- **Baseline role Groups are seeded**: `admin`, `hubspot_sync_operator`,
  `viewer` (migration `0003_seed_role_groups.py`, same convention as
  `accounts/migrations/0001_create_staff_group.py`) — so they already exist
  as autocomplete options in `ADGroupRoleMapping`'s admin form.
  `ADGroupRoleMapping.internal_role` still accepts *any* Django Group, not
  only these three; more can be created in admin at any time.
- **`python manage.py discover_azure_ad_groups`** — lists every group in
  the whole Azure AD tenant via Microsoft Graph and auto-records each one
  in `ADGroupRoleMapping` (unmapped, via the same
  `ADGroupRoleMapping.record_seen` classmethod `AzureADOIDCBackend` uses at
  login time — refactored out to one place so both stay in sync). Point of
  this: without it, rows only appear reactively as real people log in one
  at a time; this sweeps the whole org in one run, so IT can start mapping
  immediately instead of waiting. `--dry-run` lists without writing. Never
  overwrites an already-set `internal_role`, so it's safe to re-run anytime
  (e.g. after new groups are created in AD).
- Needs its own Graph capability: `AppOnlyGraphClient.list_groups()`
  (`graph_client.py`), requiring a third distinct Application permission —
  `Group.Read.All` (or `Directory.Read.All`), admin-consented — on top of
  the two from Phase 1 (Delegated `GroupMember.Read.All`) and Phase 2
  (Application `User.Read.All`).

Once IT provides tenant access: run `discover_azure_ad_groups`, then open
`ADGroupRoleMapping` in Django admin and assign a Django Group to each row
that should grant access. Rows nobody has mapped simply grant nothing (see
"Unmapped AD groups" above) — there's no rush to map every row on day one.

## Phase 4 — frontend: sign-in option + role-gated UI

`AuthProvider`/`useAuth`/the `RequireAuth` route guard already existed
(shipped with password login in `c15c33a`, before this whole effort) —
Phase 4 didn't need to build an auth context from scratch, only extend what
was there:

- **`pages/auth/LoginPage.jsx`**: added a "Sign in with Microsoft" button
  below the existing password form — a plain `<a href="/api/auth/azure/login/">`
  (via MUI's `Button href=`), not an axios call, since Django needs a real
  browser navigation to redirect on to Azure AD. Password login is
  untouched and still works exactly as before.
- **`common/useHasRole.js`**: new hook, deliberately mirroring the existing
  `common/useStaffToolsAccess.js` pattern exactly (reads `groups` from
  `useAuth()`, checks by name, superuser bypass) rather than inventing a
  separate "roles" concept — `/api/auth/me/` already returns `groups` and
  that's what the one existing role-style hook already used. Role names
  passed in must match the group-name constants in
  `auth_azure/permissions.py` (`admin`/`hubspot_sync_operator`/`viewer`).
- **HubSpot sync button** (`pages/management/company/CompanyDetail.jsx`):
  now shown for `hasStaffToolsAccess OR useHasRole('hubspot_sync_operator')`
  — someone can be granted just this one capability via an AD-mapped role
  without needing the broader "Internal tools" `staff` group.
- **Backend enforcement, not just a hidden button**: `CompanyViewSet`
  (`client/api_views.py`) had *no* `permission_classes` on its `hubspot_sync`/
  `hubspot_sync_select` actions before this — any authenticated user could
  already call them directly regardless of what the frontend showed. Added
  `get_permissions()` override requiring `IsStaffToolsUser | IsHubspotSyncOperator`
  for just those two actions (every other action on that ViewSet is
  unchanged). This is `IsHubspotSyncOperator`'s first real use since it was
  written in Phase 1 — see `client/tests.py::CompanyHubspotSyncViewTests`
  for the new coverage (role-alone is sufficient; neither role → 403;
  existing `staff`-based tests updated to explicitly grant that group in
  `setUp`, since the endpoint no longer implicitly allows everyone).

Not done in this pass: no global "your role isn't mapped yet" landing page
(that's the `HasAssignedRole`/`AZURE_AUTH_ENFORCED` global gate from
"Giving one person extra rights" above — still off, and nothing in the
frontend renders a dedicated empty-role screen for it yet). Only exercised
via `manage.py check`, the full test suite, and `docker logs frontend_crm_dev`
showing a clean compile — no real Azure AD tenant exists yet, so the actual
Azure login button hasn't been clicked against a live tenant, and no
browser-based visual check was done (no headless browser tool available in
this environment).

## What's NOT in Phase 1

Per the rollout plan, deliberately not done yet:

- **`ADGroupRoleMapping` rows** (Phase 3) — table, admin UI, and the
  `discover_azure_ad_groups` sweep are all ready (see "Phase 3" above), but
  the table is empty until IT provides real tenant access.
- **`AZURE_AUTH_ENFORCED=True` behavior** — `middleware.py`'s
  `AzureAuthEnforcementMiddleware` is scaffolded but intentionally still a
  no-op; see its docstring. `HasAssignedRole` (permissions.py) is the one
  exception: it's fully implemented and does take effect the moment the flag
  flips — see "Permission classes" above. Flipping the flag today would
  reject every authenticated user from the whole API, since
  `ADGroupRoleMapping` has no mapped rows yet (phase 3 hasn't started) —
  don't flip it before phases 2–3 are done.
- Real Azure AD tenant/App Registration values — none exist yet, so none of
  this has been exercised against a live login (per explicit confirmation
  before starting this phase).

## Testing

`src/backend/auth_azure/tests.py` (47 tests) covers `GraphClient`
pagination/error handling, `AzureADOIDCBackend` user linking (by
`azure_oid`, by email fallback, no-match), role sync (add mapped groups,
preserve unmanaged groups, drop no-longer-present mapped groups), unmapped
AD group auto-recording (creates a row with `internal_role=None`, grants no
access, refreshes the cached name on rediscovery), the permission classes
including `HasAssignedRole` (no-op when not enforced; denies role-less,
unmapped-group-only, and unauthenticated; grants mapped-role and superuser),
the middleware no-op in both flag states, `AppOnlyGraphClient`/
`get_app_only_access_token` (client-credentials token fetch + caching,
single/none/ambiguous email matches, `list_groups` pagination), the
`link_existing_users_to_azure` command (links on match, `--dry-run` writes
nothing, skips no-email and already-linked-unless-`--force`, doesn't link
on ambiguous/no-match), `ADGroupRoleMapping.record_seen` (create-unmapped,
idempotent re-call, name refresh without touching an existing role), the
`discover_azure_ad_groups` command (records every discovered group,
preserves already-mapped rows, `--dry-run` writes nothing, surfaces Graph
failures as `CommandError`), and that unauthenticated behavior on an
existing endpoint (`/api/auth/me/`) is unchanged.

`src/backend/client/tests.py::CompanyHubspotSyncViewTests` (Phase 4) gained
two cases for the new `get_permissions()` gate on `CompanyViewSet`:
`hubspot_sync_operator` role alone is sufficient (no `staff` needed), and a
user with neither role gets 403. Existing cases in that class now grant
`setUp`'s user the `staff` group explicitly, since the endpoint no longer
implicitly allows every authenticated user. Full backend suite: 77 tests,
only the 2 pre-existing, unrelated `client` Mailchimp-timeout failures.

Fixed (2026-09-09): a pre-existing, unrelated `ftp` migration ordering bug
(`ftp/migrations/0016_usersonedrive_...py`) previously broke *any* fresh
database build, which meant `python manage.py test` could never get past
setup — see `docs/ftp/migration_0016_fix_2026-09-09.md`. With that fixed,
`python manage.py test auth_azure` runs cleanly (17/17 passing). Also
verified via a manual `GET /api/auth/azure/login/` against the running dev
container, confirming the full redirect-URL construction (correct authorize
endpoint, scopes, namespaced `redirect_uri`, `state`/`nonce`) end to end —
this is also how the `OIDC_AUTHENTICATION_CALLBACK_URL` `NoReverseMatch`
mentioned above was caught, before the `ftp` fix existed. Flagging this
separately; not fixed here (out of scope, touches already-applied `ftp`
migration history).
