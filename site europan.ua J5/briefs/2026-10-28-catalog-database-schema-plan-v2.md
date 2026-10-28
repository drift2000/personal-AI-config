# Cable catalogue database schema plan v2

Status: proposed for final column review
Date: 2026-10-28

## Product-owner direction

The expanded normalized proposal was rejected as too large for the first
implementation. The first approximation must use exactly four domain tables,
following the owner's original model with only local refinements:

1. categories;
2. products/ProductFamily;
3. one Product specification record with section JSON;
4. Product variants with explicit stable columns.

No EAV definition/value tables, category junction, separate standards,
documents, media, badge, KPI, translation, or import-audit tables belong to
v1. Add a new table only after a concrete workflow proves it is needed.

## Table 1: `#__cables_categories`

Component-owned nested categories using Joomla nested-table conventions:

- identity/tree: `id`, `asset_id`, `parent_id`, `lft`, `rgt`, `level`, `path`;
- content: `title`, `alias`, `description`, `image`;
- Joomla: `state`, `access`, `language`, `ordering`, checkout and audit fields;
- extension: `params`, `metadata`.

Indexes: tree fields, `(parent_id, alias)`, `(state, access)`, language.

With the four-table limit, Product has one `category_id`. Multi-category
placement is deliberately deferred. If it becomes required, add a proper
fifth junction table; do not store category IDs in JSON.

## Table 2: `#__cables_products`

One row is one cable family/mark without core count and section:

- identity/navigation: `id`, `asset_id`, `category_id`, `code`, `title`,
  `alias`;
- editorial: `short_description`, `description`, `purpose`,
  `application_area`, `marking_decoding`, `warranty`, `service_life`,
  `additional_information`;
- presentation JSON: `badges`, `kpis`;
- media: `image`, `diagram`;
- Joomla/SEO: state, access, language, ordering, checkout/audit, `metakey`,
  `metadesc`, `metadata`, `params`.

`badges` and `kpis` are ordered JSON arrays because they are small
presentation structures and are not filtering/identity data. Variant count is
derived, not stored as a manual KPI.

## Table 3: `#__cables_product_specifications`

Exactly one row per Product (`UNIQUE(product_id)`):

- `construction` JSON;
- `electrical_parameters` JSON;
- `thermal_parameters` JSON;
- `fire_safety` JSON;
- `documents` JSON;
- `standards` JSON;
- `additional_parameters` JSON;
- `schema_version` and Joomla checkout/audit fields.

JSON uses stable machine codes, not Ukrainian labels as keys. A section has an
ordered `items` list; each item can contain `code`, `label`, `value`, `unit`,
`status`, and `note`. `status` distinguishes verified, draft, unknown, and not
applicable. Documents keep local media paths/URLs and metadata. Standards keep
type/code/title/isPrimary; `isPrimary` is meaningful inside this Product row.

The administrator can add or remove inner specification items without DDL.
Whole JSON documents are validated in the application before persistence.

## Table 4: `#__cables_product_variants`

One row is one concrete mark size/execution:

- identity: `id`, `product_id`, stable `variant_key`, `mark_size`;
- cores: `core_configuration`, nullable `core_count_total`;
- section: `section_display`, nullable `section_main_mm2`,
  `section_aux_mm2`;
- conductor: `conductor_class_code`, `conductor_class_text`,
  `conductor_diameter_display`, `conductor_diameter_main_mm`,
  `conductor_diameter_aux_mm`;
- current: `current_air_ac`, `current_air_dc`, `current_ground_ac`,
  `current_ground_dc`;
- resistance: `resistance_main_ohm_km`, `resistance_pe_ohm_km`,
  `resistance_aux_ohm_km`;
- bend: `bend_radius_display`, nullable `bend_radius_multiplier`;
- physical: `outer_diameter_mm`, `weight_kg_km`;
- Joomla: `state`, `ordering`, audit fields.

Use `UNIQUE(product_id, variant_key)`. `mark_size` is not a safe identity key.
Display fields preserve compound values such as `3+1` and `10+6`; nullable
numeric columns support validation and sorting. A missing numeric value is
`NULL`, never zero. Rare future Variant attributes require an explicit schema
migration only when a real field is known; v1 has no catch-all Variant JSON.

## Deliberate v1 trade-offs

- One category per Product. M:N requires a fifth table later.
- Product/Specification JSON is application-validated but not relationally
  queryable. This is accepted because v1 has no global specification filter or
  comparison.
- Joomla Finder reads and indexes visible JSON text plus Variant mark sizes;
  Variants have no separate URLs.
- Ukrainian only. Keep `language` fields, but choose the translation model only
  before adding a second language.
- ODS remains a development source. Conflicts are reported and resolved before
  persistence; unverified CPR is not published.
- Legacy/current JSON fixtures are reference data, not an approved migration
  baseline. Inspect the installed schema before implementation.

## Next step

Review exact columns and JSON contracts, then prepare MariaDB DDL and an
additive migration plan. No source/schema change is authorized by this brief.

