# Local Agents — Usage Guide

Location (private project memory): agents in `agents/<role>.md`, templates in `skills/local-agents/templates/`.
Paths `agents/`, `skills/`, `docs/` are relative to the private project dir; `src/`, `run.sh` — to the repo.

---

## Quick reference — when to use which agent

| I'm working on...               | Use agent           | First step                                |
|---------------------------------|---------------------|-------------------------------------------|
| `src/backend/client/**`         | `agents/client.md`   | Generate regression checklist             |
| `src/backend/ftp/**`            | `agents/ftp.md`      | Check import idempotency                  |
| `src/backend/download/**`       | `agents/download.md` | Check client model cross-references       |
| `src/backend/once/**`           | `agents/once.md`     | Document in `docs/once/registry.md`       |
| `src/frontend/src/**`           | `agents/frontend.md` | Verify column keys vs. API response       |
| Opening a PR with risk          | any                 | Fill `pr_checklist.md.tpl`                |

For backend logging scaffolds, reuse the shared `src/backend/common/command_logger.py` helpers and start from `skills/local-agents/templates/logging_backend.tpl` instead of creating custom logging logic.

---

## Execution environment

- This project runs in Docker containers.
- Run tests and other verification commands inside the containerized environment only.
- Use `./run.sh` as the entry point for container operations and in-container command execution.
- Do not run test commands directly on the host unless a task explicitly says otherwise.

---

## Templates

| Template                              | Use for                                         |
|---------------------------------------|-------------------------------------------------|
| `model_doc.md.tpl`                    | New model documentation block                   |
| `regression_checklist.md.tpl`         | Pre-change regression check (especially client) |
| `pr_checklist.md.tpl`                 | Every PR that touches backend or shared models  |
| `once_registry_entry.md.tpl`          | Archiving a one-shot script after it runs       |
| `frontend_table.component.tpl`        | Full table with sort + pagination               |
| `frontend_table.react.tpl`            | Minimal table stub                              |
| `example_table_page.tpl`             | Page that wires columns + data into the table   |
| `logging_backend.tpl`                 | Django management command logging boilerplate   |
| `logging_frontend.tpl`                | Frontend dev-time logger helper                 |

---

## How to scaffold a template (manual)

```bash
# 1. Copy the template to the target path
cp <private>/skills/local-agents/templates/regression_checklist.md.tpl docs/client/regression_2024-11-10.md
cp <private>/skills/local-agents/templates/frontend_table.component.tpl src/frontend/src/components/IntegrationsTable.jsx
cp <private>/skills/local-agents/templates/example_table_page.tpl src/frontend/src/pages/IntegrationsPage.jsx

# 2. Fill in placeholders ({{ChangeDescription}}, columns, imports…)
# 3. Run checks inside the container via ./run.sh
# 4. Commit with a descriptive message
```

---

## Regression checklist workflow

This is the most important habit. Before touching anything in `client`:

1. Copy `regression_checklist.md.tpl` to `docs/client/regression_<date>.md`
2. Fill in the affected models section
3. Work through the checklist as you develop
4. Keep the completed checklist file — it's useful context for code review

---

## once script workflow

After running a one-off script:

1. Add docstring to the script file: purpose, run date, author.
2. Copy `once_registry_entry.md.tpl` → append to `docs/once/registry.md`.
3. Fill in the entry (rows affected, follow-up tasks).
4. Commit script + registry entry together.

**Never delete scripts from `src/backend/once/` — they are archival.**

---

## Output directories

| Content type             | Directory                        |
|--------------------------|----------------------------------|
| App documentation        | `docs/<app>/README.md`           |
| Regression checklists    | `docs/<app>/`                    |
| Once script registry     | `docs/once/registry.md`          |
| Frontend components      | `src/frontend/src/components/`   |
| Frontend pages           | `src/frontend/src/pages/`        |
