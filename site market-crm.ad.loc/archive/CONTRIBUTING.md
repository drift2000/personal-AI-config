# Contributing — Local Agents and Development Workflow

---

## Core rules

- Agent assets live in `.github/agents/`, templates in `.github/agents/templates/`.
- Generated docs go in `docs/<app>/` — never in `src/backend/` source directories.
- Scaffolded frontend files go in `src/frontend/src/components/` or `src/frontend/src/pages/`.
- All agents run **locally only** — no CI integration.
- Prefer small, focused commits. Separate doc commits from code commits.

---

## Before making any change to `client`

The `client` app has the most inter-model dependencies and the highest regression risk.
**Always run a regression checklist before touching it.**

```bash
cp .github/agents/templates/regression_checklist.md.tpl docs/client/regression_$(date +%Y-%m-%d).md
# Fill it in, work through it while coding
```

The completed checklist stays in `docs/client/` — it's useful for PR reviews.

---

## Agent files

| Agent               | Scope                        | Key concern                              |
|---------------------|-------------------------------|------------------------------------------|
| `client.agent.md`   | `src/backend/client/**`      | Regressions on shared models             |
| `ftp.agent.md`      | `src/backend/ftp/**`         | Import idempotency + client linkage      |
| `download.agent.md` | `src/backend/download/**`    | Matching rules + client linkage          |
| `once.agent.md`     | `src/backend/once/**`        | Archive scripts, never re-run            |
| `frontend.agent.md` | `src/frontend/src/**`        | API contract consistency                 |

---

## PR checklist

For every PR that touches backend models, serializers, or import logic, fill in:

```bash
cp .github/agents/templates/pr_checklist.md.tpl /tmp/pr_checklist.md
# Fill it in, paste relevant parts into the PR description
```

---

## `once` scripts — rules

- Scripts in `src/backend/once/` run **exactly once** in production and are never re-run.
- Every script must have a docstring: purpose, run date, author.
- Every script must have an entry in `docs/once/registry.md` (use `once_registry_entry.md.tpl`).
- **Do not delete scripts** — they are archival documentation of data state.
- If a task is repeatable, put it in the correct app's `management/commands/` instead.

---

## Logging standards

**Backend** — `src/backend/` apps:
```python
import logging
logger = logging.getLogger(__name__)
# Use structured extra: company_id, user_id, user_email, domain,
#                       source_file, row_id, period, matrix_id
logger.info('task.started', extra={'task': 'sync_companies'})
logger.exception('task.failed', extra={'error': str(e)})
```
See `templates/logging_backend.tpl` for full management command example and `settings.py` config.

**Frontend** — `src/frontend/src/`:
```js
import { makeLogger } from './utils/logger'
const logger = makeLogger('ComponentName')
logger.info('mounted', { pageSize })
```
See `templates/logging_frontend.tpl` for implementation. Production logging/error-tracking can be added later.

---

## Commit message conventions

```
docs(client): scaffold Company model doc
feat(ftp): add monthly log import command
fix(download): handle unmatched domain rows gracefully
chore(once): archive import_legacy_companies script in registry
refactor(frontend): extract EmailsTable to shared component
```

---

## Documentation structure

```
docs/
  client/
    README.md          ← model/API overview, auto-generated + hand-edited
    regression_*.md    ← completed regression checklists
  ftp/
    README.md
  download/
    README.md
  frontend/
    README.md          ← page inventory, column mappings
  once/
    registry.md        ← append-only archive of all one-shot scripts
```
