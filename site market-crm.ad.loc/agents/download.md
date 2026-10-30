---
name: download-agent
description: >
  Local agent for the `download` Django app.
  Documents the import pipeline, data linkage to `client`,
  and scaffolds QA queries and test cases.
  Use whenever touching `src/backend/download/**`.
applyTo: "src/backend/download/**"
---

## Responsibilities

### 1. Regression checks (run BEFORE making changes)

The `download` app enriches import data by matching to `client` entities.
Critical invariants:

- Matching logic must tolerate unresolved rows (no hard crash on missing Company/Domain).
- If `client.Email`, `client.Domain`, or `client.Company` fields change, re-verify matching rules.
- Aggregation queries for the frontend summary must still return correct totals after schema changes.
- Import must be idempotent for the same source file.

**Questions to ask before changes:**
> "Which download queries join on client.Email? Does this break after Email status field change?"
> "Are there any raw SQL queries in download that reference client tables directly?"

### 2. Documentation

Generate or update `docs/download/README.md` covering:
- Import pipeline: source → parse → match → store.
- Matching rules: how downloads are linked to `Company`, `Email`, `Domain`.
- Known edge cases: unmatched rows, duplicate entries, partial matches.
- Common analytics queries (Django ORM + Postgres SQL equivalents).

**How to ask:**
> "Create README section explaining how downloads are matched to Company"
> "Document matching rules for Domain-based resolution"

### 3. Scaffolding

- Sample QA SQL queries for monthly import validation.
- Django queryset examples for common reporting tasks.
- Test case stubs for import pipeline.

**How to ask:**
> "Generate sample QA SQL for monthly import"
> "Scaffold Django queryset for top downloads per Company this month"

---

## Logging conventions

```python
logger = logging.getLogger(__name__)
# Extra keys: company_id, email, domain, source_file, row_id, period (YYYY-MM), match_method
```

---

## Output conventions

- Documentation → `docs/download/`
- Prefer small queries runnable on Postgres with Django ORM equivalents alongside.
- Log unmatched rows with enough context to diagnose later (domain, row_id, period).
