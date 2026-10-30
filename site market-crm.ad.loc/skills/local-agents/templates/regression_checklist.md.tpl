# Regression Checklist — {{ChangeDescription}}

**App:** {{AppName}}  
**Date:** {{Date}}  
**Developer:** {{Developer}}  
**PR / branch:** {{BranchName}}

---

## What is changing?

<!-- Briefly describe the change: new field, refactor, model rename, etc. -->

{{ChangeDetails}}

---

## Affected models / serializers / views

<!-- List everything that touches this change -->

- [ ] {{AffectedModel1}}
- [ ] {{AffectedSerializer1}}
- [ ] {{AffectedView1}}

---

## client app — cross-reference checks

> Skip items not relevant to your change.

### Email
- [ ] `Email.save()` still auto-populates `domain` from email string
- [ ] `Email.md5_hash` is still computed correctly on save
- [ ] `Email.status` choices are consistent with frontend display

### Domain
- [ ] `Domain.date_created` auto-set on save if blank — still works
- [ ] `Domain.company` FK — nullable correctly handled in queries

### Company
- [ ] `Company.marked_for_del` — soft-delete flag not bypassed by new queries
- [ ] `Company.corporation` (self-FK) — recursive queries still safe
- [ ] `Company.country` (PROTECT FK to IsoCountry) — no accidental cascade

### CompanyCandidate
- [ ] Nullable `company` FK handled in import flow — no crash on unresolved

### IsoCountry
- [ ] `alpha2` primary key — no migration touching it (high risk)

---

## ftp / download cross-checks

> Fill in if your change touches models used by ftp/download imports.

- [ ] ftp log import still resolves Company correctly after this change
- [ ] download matching still resolves Email / Domain correctly
- [ ] Idempotency of import commands preserved (re-run = no duplicates)

---

## Migration checklist

- [ ] Migration file generated and reviewed
- [ ] Migration is reversible (`./manage.py migrate <app> <prev>` tested locally)
- [ ] No `RunPython` that can't be undone (or documented in `docs/once/registry.md`)
- [ ] No raw SQL that assumes column order

---

## Smoke tests (manual, local)

- [ ] Django admin — affected model still loads and saves
- [ ] API endpoint — response shape unchanged (check Swagger)
- [ ] Frontend table — column keys still match API response fields
- [ ] Import command (if relevant) — runs without error on sample data

---

## Notes / known risks

<!-- Anything you want the reviewer to pay attention to -->

{{Notes}}
