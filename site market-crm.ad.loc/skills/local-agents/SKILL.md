---
name: local-agents
description: >
  Skill bundle for local development agents of the CRM system.
  Covers: client, ftp, download, once, frontend apps.
  Priority: regression checks → documentation → scaffolding → PR checklists.
---

## Overview

This skill groups all local agent behaviors for the CRM project.
Agents run **locally only** — no CI integration by default.

### Project at a glance

| Layer     | Tech                          | Notes                                |
|-----------|-------------------------------|--------------------------------------|
| Frontend  | React.js                      | API-driven, session login required   |
| Backend   | Django 4.x                    | 5 apps: client, ftp, download, once, static pages |
| API docs  | Swagger                       | used by frontend                     |
| DB        | PostgreSQL                    | via Docker                           |
| Deploy    | Docker + git-based releases   | local → repo → server                |

### Apps and their roles

- **client** — core data: Company, Email, User, Domain, IsoCountry, CompanyCandidate. Most inter-model relations are here. Highest risk of regressions.
- **download** — import pipeline: downloaded stats linked back to `client` entities.
- **ftp** — integrations inventory + monthly auth/download logs per integration.
- **once** — one-shot import/migration scripts. Scripts are kept for archival, never re-run.
- **static pages** — monitoring views; read-only, no input.

---

## Agent files

| Agent                    | Scope                        |
|--------------------------|------------------------------|
| `agents/client.md`        | `backend/client/**`          |
| `agents/ftp.md`           | `backend/ftp/**`             |
| `agents/download.md`      | `backend/download/**`        |
| `agents/once.md`          | `backend/once/**`            |
| `agents/frontend.md`      | `frontend/src/**`            |

---

## Templates included

| Template file                            | Purpose                                  |
|------------------------------------------|------------------------------------------|
| `templates/model_doc.md.tpl`             | Model documentation skeleton             |
| `templates/regression_checklist.md.tpl` | Regression checklist for risky changes   |
| `templates/once_registry_entry.md.tpl`  | Archive entry for a one-shot script      |
| `templates/pr_checklist.md.tpl`         | PR risk checklist                        |
| `templates/frontend_table.component.tpl`| React table with sort + pagination       |
| `templates/frontend_table.react.tpl`    | Minimal React table stub                 |
| `templates/example_table_page.tpl`      | Page that uses the table component       |
| `templates/logging_backend.tpl`         | Django logging boilerplate               |
| `templates/logging_frontend.tpl`        | Frontend console logger helper           |

---

## Recommended workflow (local)

1. Before changing anything in `client`, run the regression checklist mentally (or generate one with `agents/client.md`).
2. Make changes and invoke the relevant agent to update docs.
3. Review generated Markdown under `docs/<app>/` (private project memory — never commit it to the repo).
4. For new components, copy scaffolding templates and adapt imports.
5. For `once` scripts: after running, fill in `docs/once/registry.md` via `agents/once.md`.

---

## Output conventions

- All documentation → `docs/<app>/`
- Scaffolded components → `frontend/src/components/` or `frontend/src/pages/`
- One-shot script archive → `docs/once/registry.md`
- Never write generated docs into `backend/` source directories.
