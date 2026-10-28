# 0002 — Four-table catalogue schema

Status: accepted
Date: 2026-10-28
Supersedes: 0001

## Context

The first normalized catalogue proposal introduced too many related tables for
the first delivery. The product owner explicitly approved a simpler first
approximation that follows the original four-entity model. The current product
page needs a ProductFamily, its Variant rows, nested component categories, and
structured technical sections. Global specification filtering, comparison,
multi-category assignment, reusable document/standard entities, and a second
language are outside v1.

## Decision

Use exactly four domain tables in v1:

1. component-owned nested categories compatible with Joomla `TableNested`;
2. ProductFamily products with one category, editorial fields, media paths,
   and small presentation JSON for marking, badges, and KPIs;
3. one specification row per Product with section JSON for construction,
   electrical, thermal, fire-safety, documents, standards, and additional
   parameters;
4. Variants with explicit display and nullable normalized columns for the
   stable mark-size, core, section, conductor, current, resistance, bend, and
   physical parameters.

Variant identity is `product_id + variant_key`; display mark size is not
unique. Variant count is derived. JSON is validated by the component and uses
stable machine codes. Missing numeric Variant values are `NULL`, never zero.

## Consequences

- The schema and administrator UI remain understandable for the first stage.
- New Product specifications can be added inside validated section JSON
  without DDL.
- New stable Variant dimensions require an additive schema migration.
- Products have one category in v1. Multi-category placement requires a fifth
  junction table later and will not be represented as JSON IDs.
- Specification JSON is not directly suitable for global relational filters;
  that trade-off is accepted because filtering/comparison is out of scope.
- Standards, documents, badges, KPI, translations, and import audit are not
  separate entities until a concrete workflow requires them.
- Existing installations require a separate audited update/backfill; the
  install SQL defines only a clean installation.

## Evidence

- Explicit product-owner approval in the 2026-10-28 schema discussion.
- `briefs/2026-10-28-catalog-database-schema-plan-v2.md`
- MariaDB 11.8.9 double-run verification of the install SQL on 2026-10-28.
