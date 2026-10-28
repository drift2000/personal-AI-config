---
name: database-change
description: Plan, implement, or verify safe MariaDB schema and data changes for Europan Joomla extensions, including install/update SQL and migration effects. Do not use for unrelated infrastructure changes.
metadata:
  short-description: Safe Joomla MariaDB change workflow
---

# Database change

Use this skill for any schema, index, constraint, migration, bulk-data, or installer-SQL change.

## Workflow

1. Inspect the active schema, existing data volume, Joomla table prefix use, extension manifest, and related queries before proposing a change.
2. Describe the target state, dependencies, data-compatibility risk, indexes and uniqueness rules, and whether foreign keys are appropriate for this installation model.
3. Prepare idempotent Joomla install/update SQL with MariaDB-compatible types. Define a backup or recovery path before destructive or bulk transformations.
4. Obtain architectural review for material schema decisions and explicit approval before a destructive, irreversible, or production-impacting operation.
5. Apply only authorized changes. Then verify migration discovery/execution, expected tables or indexes, data preservation, and repeat-run behavior.

## Guardrails

- Never assume a table prefix or use hard-coded production table names where Joomla prefix handling is required.
- Do not run destructive DDL/DML, mass deletion, or production changes without explicit authorization and a recovery plan.
- Do not claim rollback is available unless it was designed and tested.
- Report unavailable database access, schema evidence, and untested migration paths explicitly.
