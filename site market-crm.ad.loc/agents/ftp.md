---
name: ftp-agent
description: >
  Local agent for the `ftp` Django app.
  Documents integrations, scaffolds log-import templates,
  and checks that imported logs link correctly to `client` entities.
  Use whenever touching `src/backend/ftp/**`.
applyTo: "src/backend/ftp/**"
---

## Responsibilities

### 1. Regression checks (run BEFORE making changes)

The `ftp` app links to `client` during log import. Critical invariants:

- Imported auth/download logs must reference a valid `Company` or remain unlinked (never silently dropped).
- Monthly import is idempotent — re-running the same file must not duplicate records.
- If `client.Company` or `client.Domain` models change, verify the ftp matching logic still resolves correctly.
- Integration status fields must remain consistent with what the frontend summary table displays.

**Regression questions to ask before changes:**
> "What ftp queries depend on Company.marked_for_del?"
> "Does the monthly log importer handle duplicate rows?"

### 2. Documentation

Generate or update `docs/ftp/README.md` covering:
- Integration inventory: name, type, expected log format, field mapping to `client`.
- Monthly import checklist: file naming, expected columns, import command.
- Known edge cases and failure modes (e.g., missing company match).
- Example curl/wget invocations for manual log retrieval if applicable.

**How to ask:**
> "Document SFTP integration X: expected fields and mapping to Company"
> "Generate monthly import checklist for ftp logs"

### 3. Scaffolding

- Parser stub for a new log format.
- Management command with logging for a new import flow.

**How to ask:**
> "Scaffold parser for monthly log file format Y"
> "Create management command `import_ftp_logs_october` with logging"

---

## Logging conventions

```python
logger = logging.getLogger(__name__)
# Extra keys: company_id, integration_name, source_file, row_id, period (YYYY-MM)
```

---

## Output conventions

- Documentation → `docs/ftp/`
- Include sample transformed CSV/JSON to illustrate mapping.
- Note unresolved/skipped rows separately from matched rows in import logs.
