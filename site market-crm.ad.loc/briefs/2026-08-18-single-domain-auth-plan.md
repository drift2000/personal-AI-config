# Single-domain routing + session auth + permission-driven UI

Status: Phase 0 + Phase 1 + Phase 2 (partial) done — 2026-08-18
Owner: Denis

## Goal

Move from the current two-prefix routing (`/` React, `/backend/` Django) to a
clean single-domain layout (`/` React, `/api/` Django REST, `/admin/` Django
Admin), and add real authentication + Django-Groups-based permissions so the
React dashboard can conditionally render blocks (guest / user / manager)
while Django enforces access on every protected endpoint. UI hiding is a UX
convenience only — it is never the security boundary.

## Current state (surveyed 2026-08-17)

- Single host, path-based split via nginx: `/` → frontend, `/backend/` →
  Django (prefix stripped by nginx, restored via `FORCE_SCRIPT_NAME =
  "/backend"` in `backend/project/settings.py`).
- `/api/` already exists but lives under `/backend/api/` — DRF +
  drf-spectacular are already wired (`backend/project/api_urls.py`).
- No auth enforcement anywhere: DRF defaults (`AllowAny` + Session/Basic),
  zero `permission_classes` in the codebase. No CORS configured (not needed,
  same origin).
- Frontend: CRA + react-router-dom 6, axios `baseURL: "/backend/api/"`
  hardcoded in `frontend/src/api/axiosInstance.js`. Dead Bearer-token
  interceptor present (nothing sets the token). No route guards.
- **Naming gotcha:** `client.models.User` is a CRM business entity (contact),
  *not* the Django auth user. Auth will use the standard
  `django.contrib.auth.User` + `Group`/`Permission` — a separate thing.
- No existing Groups/permissions scaffolding — greenfield for Phase 3/4.

## Decisions made

- Auth mechanism: **session (cookie-based)**, via DRF `SessionAuthentication`
  — same origin makes this simpler and safer than JWT; no new dependency
  needed (`SessionMiddleware` already present). CSRF token handling required
  on login POST.
- URL migration: **full cutover at once** — drop `/backend/` entirely in
  favor of top-level `/api/` and `/admin/`, done in one pass (Phase 0)
  rather than staged behind the old prefix.
- Permission enforcement rollout: **gradual, per app** — `ftp` → `download`
  → `client` (highest regression risk last, per `CLAUDE.md` conventions:
  regression checklist required before touching `client` models/relations).
- `/report/` and `/ftp/` prefix collision (Django legacy read-only template
  pages — `ftp/import-logs/`, `report/unknown-domains/`, `report/free-host/`,
  `client/newsletter/`, `client/import-contacts/run/` — vs. React SPA routes
  already living at `/report/ftp*`, `/report/download*`): **drop nginx
  routing to the Django template pages**, let React's catch-all own those
  prefixes. Django code/urls.py for these views is left untouched (not
  deleted) — which of these pages are still actually needed is a separate
  review to do later, not decided as part of this migration.
- `STATIC_URL` / `/backend_static/` is **kept as-is**, not renamed to
  `/static/` (deviation from the original chat mockup) — CRA's own
  production build already puts its JS/CSS under `/static/js/`,
  `/static/css/`; reusing `/static/` for Django would collide with that in
  prod. `/backend_static/` was clearly chosen deliberately to dodge this.

## Phases

### Phase 0 — URL migration (`/backend/` → `/api/` + `/admin/`) — DONE

Config-only, no auth behavior change yet.

- [x] `docker_files/config/nginx/default.dev.conf` — replaced `/backend/`
      proxy rule with direct `location /api/` and `location /admin/` →
      `backend:8000` (kept `/backend_static/` and `/media/` as-is)
- [x] `docker_files/config/nginx/default.prod.conf` — same change
- [x] `backend/project/settings.py` — removed `FORCE_SCRIPT_NAME = "/backend"`
      and the drf-spectacular `SERVERS` override that depended on it; updated
      `LOGIN_URL` to `/login/`
- [x] `backend/project/urls.py` / `api_urls.py` — confirmed no hardcoded
      prefix (paths were always relative; `FORCE_SCRIPT_NAME` was the only
      thing adding the outer `/backend` layer)
- [x] `frontend/src/api/axiosInstance.js` — `baseURL` → `"/api/"`, removed
      dead Bearer-token interceptor (nothing ever set that token)
- [x] Found and fixed 11 more frontend files with `/backend/api/...`
      **hardcoded directly** (bypassing `axiosInstance`, via plain `axios`/
      `fetch` calls): `api/downloadReport.js`, `api/ftpReport.js`,
      `api/companies.js`, `api/emails.js`, `api/downloads.js`,
      `api/productDownloads.js`, `api/users.js`,
      `pages/graphs/DownloadGraph.jsx`, `pages/graphs/NewUsersGraph.jsx`,
      `pages/management/company/CompanyDetail.jsx`,
      `pages/management/users/UserDetail.jsx` — all now `/api/...`
- [x] `backend/templates/partials/navbar.html`, `footer.html` — fixed two
      leftover `/backend/` links (low-impact: these templates are only
      reachable through the now-unreachable `home()`/login views, see below)
- [ ] `frontend/.env` — `REACT_APP_API_URL` was searched for and found
      **unused nowhere** in the codebase (no `.env` file exists locally
      either) — nothing to do, left alone
- [ ] Fill `.github/agents/templates/pr_checklist.md.tpl` for this PR
      (touches backend + shared config) — still to do before merging

**Verified live on the dev stack** (`nginx_crm_dev`/`backend_crm_dev`/
`frontend_crm_dev`, port 8082) after reloading nginx and restarting the
backend: `/` → 200 (React), `/api/schema/swagger/` → 200, `/admin/` → 302 to
login, `/admin/login/` → 200, `/api/client/companies/` → 200 (still
`AllowAny`, as expected pre-Phase-1).

**Incident during Phase 0 (self-inflicted, resolved):** Django's dev
`StatReloader` picked up the `settings.py` edit mid-way — after the
`FORCE_SCRIPT_NAME` line was removed but before the `SPECTACULAR_SETTINGS`
`SERVERS` block that referenced it was — and crashed
(`NameError: FORCE_SCRIPT_NAME`), taking the container down. Fixed by
finishing the edit (removing the dependent block) and restarting
`backend_crm_dev`. Lesson: when live-editing settings files with volume-
mounted autoreload, expect a crash on the intermediate state if a variable
and its usage are removed in separate edits — not a bug in the end state.

**Side-effect noted, not acted on:** with nginx no longer routing anything
to bare Django root, `project/views.py`'s `home()` and `api_index_view()`,
plus the top-level `/login/`/`/logout/` and the `/ftp/`, `/report/`,
`/client/` template-view URLs, are now externally unreachable (only
`/api/`, `/admin/`, `/backend_static/`, `/media/`, and `/` (React) are
routed). The code is untouched — cleanup/removal is part of the "review
which pages are still needed" pass mentioned above, not this phase.

### Phase 1 — Backend auth foundation (additive, nothing breaks) — DONE

- [x] New Django app `backend/accounts/` (auth doesn't belong to client/ftp/
      download/once/frontend — it's cross-cutting). Plain Django views
      (`JsonResponse`), not DRF `APIView` — deliberate: DRF's
      `SessionAuthentication.enforce_csrf()` only runs once a session
      *already* resolves to a user, so an anonymous login POST through DRF
      would skip CSRF checking entirely (a known DRF gap — "login CSRF").
      Plain views stay under Django's global `CsrfViewMiddleware`, which
      checks every unsafe method regardless of auth state.
- [x] `POST /api/auth/login/` — session login (username/password JSON body)
- [x] `POST /api/auth/logout/`
- [x] `GET /api/auth/me/` — `{authenticated, user, groups, permissions}`;
      guest → `authenticated: false`, empty arrays. Decorated
      `@ensure_csrf_cookie` so an anonymous visit still hands out a
      `csrftoken` cookie for the subsequent login POST.
- [x] `frontend/src/api/axiosInstance.js` — `withCredentials: true`, request
      interceptor reads the `csrftoken` cookie and sets `X-CSRFToken` on any
      non-GET/HEAD/OPTIONS request
- [x] Kept default `permission_classes = AllowAny` on all *existing*
      endpoints untouched — this phase only adds new capability, enforces
      nothing yet
- [x] Verified live through the actual access path (`nginx_gateway` on
      `http://marketing-crm.local`, port 80 — **not** the direct dev port
      8082): anonymous `GET /api/auth/me/` → sets cookie + returns guest
      state; `POST /api/auth/login/` with bad creds → `400` (proves CSRF
      passed, reached view logic); `POST /api/auth/logout/` → `200`.
      Did **not** test a successful login (no test-account password
      available) — worth trying with a real account before relying on it.

**Bug found in production use (fixed):** bare `GET /api/` hit
`project.views.api_index_view`, which rendered a template `api.html` that
**never existed** in this repo — a pre-existing dead view, invisible before
because `/api/` only lived behind `/backend/` and nobody browsed it
directly. Now that `/api/` is a real top-level path, it 500'd
(`TemplateDoesNotExist`) as soon as someone visited it. Fixed by replacing
the broken render with a redirect to the Swagger UI
(`backend/project/views.py`); also dropped its `@login_required` since
Swagger itself is currently open (`AllowAny`, consistent with the rest of
Phase 1). Verified: `GET /api/` → `302` → `/api/schema/swagger/` → `200`.

**Gotcha found during verification:** `CSRF_TRUSTED_ORIGINS` lists
`http://marketing-crm.local` with **no port**. Testing directly against the
dev nginx's own exposed port (`localhost:8082`, `NGINX_PORT` in `.env`)
fails CSRF Origin checking — `nginx_crm_dev` is actually also attached to
`gateway_network` (the gateway overlay is active in this dev stack), so real
traffic goes through `nginx_gateway` on port 80 as `marketing-crm.local`,
which matches. Direct port-8082 access bypasses the gateway and will 403 on
any POST — that's expected, not a bug, but easy to misdiagnose.

### Phase 2 — Frontend integration (UX layer) — partial

- [x] `frontend/src/context/AuthContext.jsx` — `AuthProvider` + `useAuth()`
      hook; fetches `/api/auth/me/` on mount, exposes
      `{authenticated, user, groups, permissions, loading, login, logout}`
- [x] `frontend/src/api/auth.js` — `fetchMe`/`loginRequest`/`logoutRequest`
      thin wrappers over the shared `api` axios instance
- [x] `frontend/src/pages/auth/LoginPage.jsx` — username/password form,
      calls `login()`, shows a MUI `Alert` on failure, navigates to `/` on
      success. Routed at `/login` in `App.jsx`.
- [x] `Header.jsx` — shows a **Login** button (top-right of the AppBar) when
      logged out. When logged in: **admin users** (`user.is_staff`) see an
      **Admin** link to `/admin/` instead of their name (decision: gate on
      `is_staff` — the same flag Django itself requires to log into
      `/admin/` — rather than `is_superuser` or a dedicated Group, since no
      Group scheme exists yet pre-Phase-4); non-admin users still see their
      name. `Logout` button always shown when logged in.
      `accounts/views.py`'s `_serialize_auth_state()` now also returns
      `user.is_staff` / `user.is_superuser` in the `/api/auth/me/` payload
      for this.
- [x] `Footer.jsx` (previously an empty file, now wired into `App.jsx`) —
      "© 2026 Enamine" + an **API** link to `/api/schema/swagger/`, mirroring
      the old Django `templates/partials/footer.html`/`navbar.html`. Pinned
      to the bottom of the viewport on short pages: wrapped `Header` +
      `main` + `Footer` in a `flex-direction: column; min-height: 100vh` div
      in `App.jsx`, with `main { flex: 1 0 auto }` — same pattern the old
      Django `base.html` used (`d-flex flex-column min-vh-100` /
      `flex-grow-1`), just inline styles instead of Bootstrap classes (no
      Tailwind/Bootstrap present in the CRA app — the `container mx-auto
      px-4` classes on `<main>` were already inert, no framework provides
      them).
- [x] Brought back the 5 cards from the old Django home page
      (`backend/templates/index.html`) as an "Internal tools" section below
      the main grid on `pages/Home.jsx`: **Unknown company region**, **Free
      Host contacts**, **Newsletter subscribers JP + KR** link out with a
      plain `<a>` (full page nav to a Django-rendered page, not a React
      route); **Import ftp logs** and **Import contacts** stay disabled,
      matching the original — they trigger real import jobs
      (`ftp.views.import_ftp_logs_page`, `client.views.run_contact_import`),
      not just reports, so enabling them was deliberately deferred rather
      than assumed.
- [x] Re-routed the underlying Django views under a new **`/tools/`**
      prefix instead of restoring their old bare `/ftp/`, `/report/`,
      `/client/` paths or folding them into `/api/`: `backend/project/urls.py`
      now mounts `ftp.urls`/`download.urls`/`client.urls` at
      `tools/ftp/`, `tools/report/`, `tools/client/` (only the prefix
      changed — the apps' own `urls.py` files are untouched, and Django's
      `{% url %}` template tags resolve automatically, so no template
      edits were needed). Chosen over the two options discussed in Phase 0
      (passthrough of the old paths, or nesting under `/api/tools/`)
      because the user didn't want non-REST pages under `/api/` at all.
      Added a matching `location /tools/` proxy block to both nginx confs.
      Verified live: `/tools/report/unknown-domains/`,
      `/tools/report/free-host/`, `/tools/client/newsletter/`,
      `/tools/ftp/import-logs/` all resolve `200` through the gateway.
- [x] Verified live with Playwright driving the system-installed Chrome
      (`playwright-core` via npx cache, no browser download needed —
      corporate proxy blocked Playwright's own Chromium download with a
      self-signed-cert error; drove the already-installed
      `C:\Program Files\Google\Chrome\Application\chrome.exe` instead via
      `channel`-less `executablePath`): home page shows Header Login button
      + Footer copyright/API link; `/login` renders the form; submitting
      wrong credentials shows "Invalid credentials." via the `Alert`; no new
      console errors (pre-existing CRA HMR websocket-to-:3000 errors are
      unrelated noise, not caused by this change). **Did not verify a
      successful login** (no test-account password available) — try this
      with a real account before considering Phase 2 fully done. Same
      caveat applies to the new **Admin** link: logic is in place
      (`user.is_staff` check) but unverified against a real `is_staff=True`
      session — `admin` is `is_superuser=True` in the DB per an earlier
      read-only check, so should also satisfy `is_staff`, but worth
      confirming with an actual login.
- [ ] Capability-driven conditional rendering (`features.reports`, etc. —
      easier for React to consume than raw `app.codename` permission
      strings) — **not started**, this is Phase 4's `features` mapping
      consumed on the frontend; nothing to conditionally show/hide yet
      since no real Groups/permissions distinctions exist until Phase 4
- [ ] Home page block layout: guest / user / manager tiers (per the original
      chat mockup) — **not started**, depends on the capability mapping
      above
- [ ] Update `.github/agents/frontend.agent.md` — it currently states "No
      authentication logic needed — the app is internal and unprotected"
      under Component conventions; that's now stale and should describe the
      `AuthContext`/capability pattern instead — **not done yet**

#### Phase 2 follow-up round (UI polish, 2026-08-17)

- [x] **Admin link styling** — was a MUI `Button` (button chrome); changed
      to a MUI `Link` (`Header.jsx`) so it reads as a plain link, matching
      the "Login"-adjacent name/text next to it instead of looking like an
      action button.
- [x] **Bootstrap decision** — found Bootstrap was already half-wired: CSS
      loaded via a CDN `<link>` in `public/index.html`
      (`bootstrap@5.3.0`), and the `bootstrap` package was already in
      `package.json` (`^5.3.6`) but never actually imported anywhere.
      Meanwhile every real component (`Header`, `Footer`, `LoginPage`,
      pages) is MUI. Decision: **Bootstrap for layout utilities only**,
      MUI stays the component library. Switched the CDN link for a proper
      local import (`import "bootstrap/dist/css/bootstrap.min.css"` in
      `index.jsx`) — offline-safe, uses the dependency that was already
      declared. Verified no visual regression on the React side
      (screenshot comparison, no console errors).
- [x] **Visual parity between the React SPA and the Django `/tools/*`
      pages** — true component reuse isn't practical (separate documents:
      CRA SPA vs. Django server-rendered templates, would need a whole
      separate widget-bundle build pipeline). Went with matching-look/
      separate-code instead: rebuilt
      `backend/templates/partials/navbar.html` to mirror
      `frontend/src/components/layout/Header.jsx` — same logo
      (`/media/Logo.svg`), same nav structure (Reports/Management/
      Integrations/Graphs, dropdowns matching 1:1), same `bg-primary`
      blue, and the **same `is_staff`-gated Admin-link-vs-name logic** as
      the React header. The two implementations are hand-kept-in-sync, not
      shared code — a comment in `navbar.html` points back to `Header.jsx`
      and this doc as the pairing to update together.
      Verified live: screenshot of `/tools/report/free-host/` matches the
      React header's look, and the Bootstrap dropdown JS
      (`static/js/bootstrap.bundle.js`, already present) actually opens the
      "Reports" menu correctly.
- [x] **Fixed `/logout/` being dead** — an accidental side-effect of Phase
      0 dropping `/login/`/`/logout/` nginx routing: the navbar's Logout
      button posts to Django's built-in `LogoutView` at `/logout/`, which
      had no nginx route and would silently no-op. Added an exact-match
      `location = /logout/` proxy block to both nginx confs. (The React
      app doesn't need this — it uses the JSON `/api/auth/logout/` from
      Phase 1 instead. Both call the same `django.contrib.auth.logout()`
      under the hood, just with a different response shape suited to each
      caller: redirect for a plain HTML form, JSON for `fetch`/axios.)
      Verified: `GET /logout/` → `302` → `/`.
- [x] Login link in both navbars now points at `/login` (the React page) —
      Django's own `{% url 'login' %}`/`registration/login.html` is
      effectively superseded and no longer linked to from anywhere, though
      left in place (unreachable via nginx, harmless dead code, same
      "review later" bucket as the other Phase-0 leftovers).

#### Phase 2 follow-up round 2: React shell + Django content via iframe (2026-08-18)

User asked a better question than what round 1 shipped: instead of hand-
syncing two navbars (React `Header.jsx` + Django `navbar.html`), keep
**one** shell (React `Header`/`Footer`) and embed the Django-rendered
`/tools/*` pages as page *content* inside `<main>`. Chose **iframe** over
fetch-and-`dangerouslySetInnerHTML` (the other option on the table): forms,
filters and pagination on the Django side keep working natively since it's
a real document in its own browsing context, vs. fragment-injection which
would drop inline `<script>` execution and turn every in-page link/form
into a full-page escape from the SPA unless separately intercepted —
meaningfully worse for the newsletter page specifically, since it has a
real create/edit form.

- [x] `X_FRAME_OPTIONS = "SAMEORIGIN"` added to `settings.py` — Django's
      unset default is `DENY`, which would have silently blocked the
      iframe (blank frame, same-origin or not) via
      `XFrameOptionsMiddleware`. `SAMEORIGIN` still blocks framing by other
      sites; it only permits the app framing its own pages.
- [x] New `backend/templates/base_bare.html` — same bootstrap CSS/JS as
      `base.html`, but **no navbar/footer include**. Switched
      `free_host.html`, `unknown_domains.html`, and all three
      `client/mailchimp_*.html` templates to extend this instead of
      `base.html`, so the iframe shows only the actual page content — no
      duplicate header inside the frame.
- [x] `frontend/src/components/layout/DjangoFrame.jsx` — thin wrapper
      rendering `<iframe src=... style={{height: 'calc(100vh - 260px)'}}>`
      inside a MUI `Container`, reused for all three embedded pages.
- [x] New SPA routes in `App.jsx`: `/internal-tools/unknown-domains`,
      `/internal-tools/free-host`, `/internal-tools/newsletter` — deliberately
      named differently from the Django-side `/tools/*` prefix (which is
      what the iframe's `src` still points at) to avoid the two "tools"
      namespaces reading as the same thing in the URL bar.
- [x] `Home.jsx` tool cards now `<Link>` (SPA nav) to the `/internal-tools/*`
      routes instead of a plain `<a href="/tools/...">` full-page nav.
- [x] **Found and fixed a real bug this surfaced**: the newsletter page is
      gated by `common.access.authenticated_backend_required`, which
      redirects anonymous requests to Django's own `/login/?next=...`. That
      path had no nginx route (dropped in Phase 0) and fell through to
      React's catch-all — so an anonymous visit inside the iframe loaded
      the **entire React SPA, Header/Footer and all, nested inside the
      iframe** (visibly double header on screenshot). Fixed by: adding an
      exact-match `location = /login/` nginx proxy (both confs, mirroring
      the `/logout/` one from round 1) so this stays inside Django/iframe
      space, and switching `registration/login.html` to extend
      `base_bare.html` instead of `base.html` (it already had proper `next`
      handling — hidden `next` field, Django's `LoginView` reads it — that
      part needed no code change, just to actually be reachable and not
      double-render a header). Verified live: anonymous visit to
      `/internal-tools/newsletter` now shows one React header + a clean
      Django login card inside the iframe, no nesting.
- [x] Verified live end-to-end: clicking "Unknown company region" on the
      home page SPA-navigates (no full page reload) to
      `/internal-tools/unknown-domains`, which shows one Header/Footer with
      the Django "Unknown Region Domains" table rendered inside the iframe.
      Same for free-host. No console/page errors in any of these checks.

**Superseded by this round:** the hand-synced Django `navbar.html`/
`footer.html` work from round 1 is now moot for `free_host.html`,
`unknown_domains.html`, and the `client/mailchimp_*` templates specifically
— they no longer render `base.html`'s navbar/footer at all (they're inside
an iframe under the real React header now). `navbar.html`/`footer.html`
still exist and would still matter if `index.html`/`registration/login.html`
(pre-fix) were ever reachable directly outside an iframe — `index.html`
still isn't reachable (same as noted in Phase 0), so in practice
`navbar.html` is now fully dead code. Left in place rather than deleted
(same "review later" convention as the rest of Phase 0's leftovers) — worth
revisiting whether to delete it outright once nothing extends `base.html`
anymore.

#### Phase 2 follow-up round 3: reverted rounds 1–2's visual-parity work (2026-08-18)

Tried it, didn't like it: the iframe looked cramped (fixed-height box with
its own internal scrollbar — "виглядає скомкано, зжато, загнано в маленькі
рамки"). Reverted the visual-parity chase entirely, back to `/tools/*`
being independent full-page Django views with their own original look.
Kept the two things from rounds 1–2 that were genuine bug fixes rather than
part of the parity effort:

- **Reverted** (`git checkout --` back to the last commit, since each of
  these had no other unrelated changes mixed in):
  `backend/templates/partials/navbar.html` (back to the plain original —
  "Backend" text brand, unconditional Admin link, no Reports/Management/
  Integrations/Graphs mirroring), `free_host.html`, `unknown_domains.html`,
  all three `client/mailchimp_*.html`, `registration/login.html` (all six
  back to `{% extends "base.html" %}`).
- **Deleted**: `backend/templates/base_bare.html`,
  `frontend/src/components/layout/DjangoFrame.jsx` — no longer referenced
  by anything.
- **Reverted**: `X_FRAME_OPTIONS = "SAMEORIGIN"` in `settings.py` (back to
  Django's default `DENY` — nothing needs framing anymore).
- **Reverted**: `App.jsx`'s `/internal-tools/*` routes and the `DjangoFrame`
  import; `Home.jsx`'s tool cards go back to plain
  `<a href="/tools/...">` full-page links instead of `<Link>` SPA nav.
- **Kept** (explicitly, per the user — these fixed real bugs independent of
  the parity/iframe idea): the exact-match `location = /login/` and
  `location = /logout/` nginx blocks (both confs). Without these,
  `authenticated_backend_required`'s `/login/?next=...` redirect and the
  navbar's Logout POST both silently 404/no-op against React's catch-all —
  a real regression from Phase 0 dropping `/login/`/`/logout/` routing,
  unrelated to whether `/tools/*` is visited directly or embedded.
  `backend/project/urls.py`'s `/tools/` prefix mount (from the original
  Phase-0-era URL-collision discussion, predates rounds 1–2) also stays —
  that's just where these views live now, independent of how they're
  linked to.
- **Explicitly not touched**: `frontend/src/components/layout/Header.jsx` —
  user clarified "Header" in the revert request meant the *Django* navbar,
  not the React one. `Header.jsx`'s Login/Logout/`is_staff`-gated Admin
  link (from the original Phase 2 ask) stays exactly as shipped.
- Verified live: React home page unchanged (Header/Footer/Internal-tools
  cards all intact), clicking a tool card does a full-page navigation to
  `/tools/report/free-host/` which renders with its own original dark
  "Backend" navbar again, no nesting, no iframe.

**Bugs found while re-verifying `/tools/*`, not fixed (out of scope of this
UI-polish round, flagged for later):**
- `ftp.views.import_ftp_logs_page` (`/tools/ftp/import-logs/`) renders a
  template `import_ftp_logs.html` that **does not exist** — `500
  TemplateDoesNotExist`, same class of bug as the Phase-0 `api.html` one.
  No user-facing impact right now since its Home-page card is deliberately
  disabled, but it'll 500 the moment anything links to it for real.
- `client.mailchimp_views` (newsletter pages) are gated by a custom
  `authenticated_backend_required` decorator (`common/access.py`) that
  redirects unauthenticated requests to `/login/?next=...`. That now lands
  on the **React** login page (Django's own `/login/` is unreachable per
  above), and `LoginPage.jsx` ignores the `?next=` param entirely — always
  `navigate("/")` after login — so a guest bounced off `/tools/client/
  newsletter/` ends up back on the React home page, not the page they
  wanted. Not fixed here; would need `LoginPage.jsx` to read and honor
  `?next=`.

### Phase 3 — Real permission enforcement on API (gradual, per app)

Order: `ftp` → `download` → `client` (risk-ascending, per `CLAUDE.md`).

- [ ] `ftp`: add `permission_classes` to viewsets, verify frontend still
      hides/shows correctly
- [ ] `download`: same
- [ ] `client`: **produce
      `docs/client/regression_<date>.md`** from the regression checklist
      template *before* changing anything; use `client-agent` for the work
- [ ] `once/**` — not touched, archival only

### Phase 4 — Groups & capabilities mapping

- [ ] Define actual Django Groups (which roles exist — TBD with business
      input, not a technical decision)
- [ ] Map `Group`/`Permission` → `features` dict returned by
      `/api/auth/me/`

## Open questions / to revisit later

- Which Groups/roles actually exist in the org (Managers? others?) — needed
  before Phase 4, not before.
- Whether `REACT_APP_API_URL` env var should be wired up properly or removed
  outright (Phase 0 decision, currently dead code either way).
