---
name: catalog-domain
description: Design, implement, or review Europan `com_cables` catalog rules involving ProductFamily, Variant, Specifications, or idempotent import behavior. Do not use to invent missing source-column mappings or product-page design.
metadata:
  short-description: Europan cable catalogue domain workflow
---

# Catalog domain

Use this skill when a change affects the catalogue model or import semantics. The working model is the accepted four-table schema (ADR 0002): `nested Category → ProductFamily → Product specification JSON + Variants`.

## Domain invariants

- A ProductFamily represents a cable brand or series, belongs to one category in v1, and owns common descriptions and values.
- A Variant represents a concrete size or execution and belongs to one ProductFamily. Its identity is `product_id + variant_key`; display mark size is not unique. Missing numeric Variant values are `NULL`, never zero.
- Product-level specifications live in one specification row per Product as component-validated section JSON with stable machine codes. Stable Variant dimensions are explicit nullable columns.
- EAV definition/value tables, category junctions, and separate standards/documents entities are out of v1; introducing them requires a new accepted ADR.
- Import is a pipeline: parse → validate → match → persist → report. Repeating unchanged input must not create duplicates.

## Workflow

1. Identify affected entities, business identity keys, relationships, and the source of truth for each value.
2. State validation, normalization, uniqueness, conflict, and idempotency rules before changing persistence or import code.
3. Preserve raw import evidence and produce counts/errors in the report; do not silently discard invalid or conflicting records.
4. Test representative create, update, duplicate, missing-value (`NULL`), invalid-JSON-section, malformed, and partially valid cases.
5. Record assumptions when the source mapping or business rule is missing.

## Guardrails

- The historical 16,023-row / 288-brand / 15,960-pair figures are planning context, not a current data contract.
- Do not infer the lost 49-column mapping or catalogue page layout.
- New Product specifications go into validated section JSON, not new columns. A new stable Variant dimension requires an additive schema migration and an approved rationale.
