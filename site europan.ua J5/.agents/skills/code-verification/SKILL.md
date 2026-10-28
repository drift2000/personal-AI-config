---
name: code-verification
description: Select and report proportionate verification for Europan Joomla, PHP, import, database, routing, ACL, and Docker changes. Do not use as permission to install dependencies or alter behavior just to pass checks.
metadata:
  short-description: Risk-based Europan verification workflow
---

# Code verification

Use this skill after implementation or when assessing readiness of a scoped change.

## Workflow

1. Inspect the diff and classify risk: isolated code, Joomla integration, schema/data, import, authorization/security, routing, or infrastructure.
2. Select only relevant available checks: PHP syntax, Composer validation, PHPUnit/unit/integration/regression tests, component installation, migrations, ACL, import consistency, routing, or Docker configuration.
3. Run the selected checks without installing dependencies or starting destructive workflows unless authorized.
4. Report each check as passed, failed, skipped, or unavailable, with the command/result and affected scope.
5. Identify residual risk and the next verification required before acceptance.

## Guardrails

- A check is not passed when it was not run, could not start, or lacks its required environment.
- Successful syntax validation does not establish Joomla integration, import correctness, permissions, or migration safety.
- Do not change business logic only to satisfy a test; explain the defect or disagreement first.
- Keep proposed tests distinct from executed tests and do not hide failures behind unrelated passing checks.
