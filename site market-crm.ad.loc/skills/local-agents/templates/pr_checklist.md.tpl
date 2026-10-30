# PR Checklist — {{PRTitle}}

**Branch:** {{BranchName}}  
**App(s) touched:** {{Apps}}  
**Date:** {{Date}}

---

## Type of change

- [ ] New feature
- [ ] Bug fix
- [ ] Refactor / cleanup
- [ ] Data migration / one-shot script
- [ ] Documentation only
- [ ] Frontend only

---

## Pre-merge checklist

### General
- [ ] Locally tested against real (or realistic) data
- [ ] No `print()` statements left in backend code (use logger)
- [ ] No hardcoded IDs, emails, or company names in production code
- [ ] Docker build still passes (`docker compose build`)

### Backend
- [ ] All new management commands have logging (`logger.info / warning / exception`)
- [ ] New models have `__str__` defined
- [ ] ForeignKeys use explicit `on_delete` (no accidental CASCADE on critical data)
- [ ] Any new `save()` override is idempotent
- [ ] Migrations generated and committed
- [ ] Migrations reviewed for reversibility

### client app (if touched)
- [ ] Regression checklist completed (see `templates/regression_checklist.md.tpl`)
- [ ] `Email.save()` / `Domain.save()` overrides unaffected
- [ ] Soft-delete (`marked_for_del`) logic preserved

### ftp / download (if touched)
- [ ] Import idempotency preserved
- [ ] Unmatched rows logged, not silently dropped

### Frontend
- [ ] Column `key` values match actual API response field names
- [ ] Pagination / sort state resets on filter change
- [ ] No hardcoded endpoint URLs (use config/constants)

### Documentation
- [ ] `docs/<app>/README.md` updated if models/API changed
- [ ] `once` script documented in `docs/once/registry.md` (if applicable)
- [ ] `skills/local-agents/AGENT_USAGE.md` updated if workflow changed

---

## Risk level

- [ ] 🟢 Low — isolated change, no shared models touched
- [ ] 🟡 Medium — touches shared models or serializers, regression checklist done
- [ ] 🔴 High — touches `client` core models, migrations, or import logic — needs extra review

---

## Notes for reviewer

{{ReviewerNotes}}
