---
name: client-agent
description: >
  Local agent for the `client` Django app.
  Generates documentation, regression checklists, and logging scaffolds
  for models, serializers, views, and management commands.
  Use whenever touching `src/backend/client/**`.
applyTo: "src/backend/client/**"
priority: highest   # most inter-model relations; highest regression risk
---

## Responsibilities

### 1. Regression checks (run BEFORE making changes)

Before touching any model or relation in `client`, ask the agent to produce a
regression checklist. The `client` app has dense cross-references:

```
Company ←→ Domain ←→ Email ←→ User
Company → IsoCountry
Company → Company (self, corporation)
CompanyCandidate → Company
```

Critical invariants to verify after any change:

- `Email.domain` is auto-populated on save from the email string — do not break `Email.save()`.
- `Email.md5_hash` is computed on save — verify hash logic is untouched.
- `Domain.date_created` is auto-set on save if blank — check after Domain model changes.
- `Company.marked_for_del` is a soft-delete flag — ensure no hard-delete queries bypass it.
- `CompanyCandidate → Company` link is nullable — imports must handle `None` gracefully.
- `IsoCountry.alpha2` is the primary key — any migration touching it is high risk.

**How to ask:**
> "Generate regression checklist for adding field X to Company"
> "What breaks if I change Email.status choices?"

### 2. Documentation

Generate or update `docs/client/README.md` covering:
- Model field tables with types, constraints, and business-logic notes.
- Serializer examples (request + response JSON).
- Important `save()` overrides and signals.
- Management command inventory with purpose and last-run date.
- Common queryset patterns used in views/reporting.

**How to ask:**
> "Document `Company` model: fields, relations, example serialized output"
> "Generate README section for client API endpoints"
> "Add serializer example for EmailSerializer"

### 3. Scaffolding

Produce ready-to-use boilerplate for:
- Management commands with logging (use `logging_backend.tpl`).
- New model documentation block (use `model_doc.md.tpl`).
- API endpoint documentation stub.

**How to ask:**
> "Scaffold management command `sync_companies` with logging"
> "Create model doc stub for new model `ContactNote`"

### 4. PR risk checklist

For PRs touching `client`, generate a short checklist covering:
- Which models/serializers are affected.
- Which auto-computed fields may be impacted.
- Migrations required and their reversibility.
- Related views or management commands to smoke-test.

---

## Logging conventions

For backend/client code that needs logging, reuse the shared helpers in `src/backend/common/command_logger.py`.
New files that require logging should start from `skills/local-agents/templates/logging_backend.tpl` and avoid custom logging setup unless the shared helper cannot cover the case.

```python
import logging
logger = logging.getLogger(__name__)

# Structured extra keys used in this app:
# company_id, user_id, user_email, domain, matrix_id, source_file, row_id
```

See `skills/local-agents/templates/logging_backend.tpl` for full management command example.

---

## Output conventions

- Documentation → `docs/client/`
- Use `model_doc.md.tpl` for each new model's doc block.
- Keep example JSON payloads realistic (use field choices defined in models).
