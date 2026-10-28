---
name: catalog-domain
description: Design, implement, or review Europan `com_cables` catalog rules involving ProductFamily, Variant, Specifications, or idempotent import behavior. Do not use to invent missing source-column mappings or product-page design.
metadata:
  short-description: Europan cable catalogue domain workflow
---

# Catalog domain

Use this skill when a change affects the catalogue model or import semantics. The working model is `Joomla Category → ProductFamily → Variant → Specifications`.

## Domain invariants

- A ProductFamily represents a cable brand or series and owns common descriptions and values.
- A Variant represents a concrete size or execution and belongs to one ProductFamily.
- Specifications require definitions, typed or normalized values, assignments, and an explicit inheritance/override rule. A Variant value must have defined precedence over its inherited family value.
- Import is a pipeline: parse → validate → match → persist → report. Repeating unchanged input must not create duplicates.

## Workflow

1. Identify affected entities, business identity keys, relationships, and the source of truth for each value.
2. State validation, normalization, uniqueness, inheritance, conflict, and idempotency rules before changing persistence or import code.
3. Preserve raw import evidence and produce counts/errors in the report; do not silently discard invalid or conflicting records.
4. Test representative create, update, duplicate, inherited, overridden, malformed, and partially valid cases.
5. Record assumptions when the source mapping or business rule is missing.

## Guardrails

- The historical 16,023-row / 288-brand / 15,960-pair figures are planning context, not a current data contract.
- Do not infer the lost 49-column mapping or catalogue page layout.
- Do not add a database column per new specification without an approved storage rationale.
