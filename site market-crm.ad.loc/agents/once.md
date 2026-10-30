---
name: once-agent
description: >
  Local agent for the `once` Django app.
  Scripts here run exactly once and are never re-run.
  The agent's job is to document what was done, when, and why —
  so future developers understand the state of the data without re-reading old scripts.
applyTo: "src/backend/once/**"
---

## Philosophy

The `once` app is an **archival directory**, not a feature app.
Scripts live there because they shaped the data at a specific point in time.
Deleting or re-running them would be wrong.

**Rule:** every script in `src/backend/once/` must have a corresponding entry in `docs/once/registry.md`.

---

## Responsibilities

### 1. Archive documentation (primary job)

After a script is written and run, use this agent to generate a registry entry.
Each entry must answer:
- What did this script do?
- When was it run (date + environment)?
- What data did it affect (model, approximate row count)?
- Are there any dependencies or follow-up tasks?
- Who ran it?

**How to ask:**
> "Document once script `import_legacy_companies.py`: migrated 3200 rows from old DB on 2024-11-10"
> "Add registry entry for `fix_email_hashes.py`"

### 2. Regression check (before touching existing scripts)

`once` scripts are never re-run, but they sometimes need small fixes (e.g., a comment update,
a logging addition for debugging). Before touching any file here:

- Confirm the script has NOT been run in production yet (check registry).
- If it has been run, treat the file as read-only. Add a comment only if absolutely necessary.
- Never change logic in a script that has already been executed — create a new one instead.

### 3. Suggest alternatives to `once` (when appropriate)

If a new task could be done via a proper management command in `client`, `ftp`, or `download`,
recommend that instead of adding to `once`. Use `once` only for truly one-off data migrations
with no repeating pattern.

**Decision guide:**
| Situation                                      | Recommended location          |
|------------------------------------------------|-------------------------------|
| Monthly import (repeatable)                    | `ftp` or `download` management command |
| One-time data fix on a specific date           | `once`                        |
| Data migration tied to a Django migration      | Django `RunPython` in migration |
| Scheduled task                                 | Management command + cron     |

---

## Output conventions

- Registry → `docs/once/registry.md` (append-only, newest entries at top).
- Use `skills/local-agents/templates/once_registry_entry.md.tpl` for consistent format.
- Script files in `src/backend/once/` should have a docstring at the top with: purpose, run date, author.
