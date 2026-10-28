# Cable catalogue database schema plan

Status: proposed for product-owner discussion
Date: 2026-10-28

## Goal and scope

Read-only comparison of `data/nhxhj-product-page.html`,
`data/configurator/Каталог кабелю.ods`, the current uncommitted `com_cables`
schema/fixtures, and proposed ADR 0001. The goal is a staged MariaDB schema
for Joomla 5 that supports a ProductFamily page and its Variants without
making JSON the primary store for searchable or validated catalogue facts.

No project source, database, Docker environment, or production state was
changed.

## Verified source facts

- ODS sheet `Аркуш1` has 56 data columns, 16,029 non-empty data rows, and
  16,023 valid rows with both product mark and type size. It contains 288
  marks and 59 non-empty product-group labels; 716 valid rows have no group.
- Five supplied columns have no usable values: two screen-resistance columns,
  the helper current column, the alternative section column, and all three
  media columns are empty (seven empty columns in total).
- The target `(N)HXH-J FE180/E30` has 164 source rows. The HTML embeds 125
  Variant records: 107 overlap, 57 are ODS-only, and 18 are HTML-only.
- Target field conflicts include two standards values, two purpose values,
  two application values, a provisional CPR statement, and the row
  `3х1,0(RE)` with section `300`, diameter `1,15`, and resistance `18,1`.
- `mark + type_size` is not globally unique: 63 pairs occur twice. Variant
  identity therefore needs an internal key and cannot rely on display size.
- Fields that vary inside at least some marks include conductor material,
  conductor construction, voltage, standards, purpose, fire/CPR data, and
  several electrical values. Product-level defaults need Variant overrides.

## Page-to-source mapping

- Direct ProductFamily candidates: mark, country, synonyms, marking text,
  purpose, application, key-feature prose, guarantee and service-life text.
- Direct/derived Variant candidates: type size, core configuration, section,
  conductor diameter/class, four current scenarios, conductor resistances,
  bend rule, outer diameter, and mass.
- Flexible specifications: construction materials, screening/armour, voltage,
  insulation resistances, thermal limits, testing voltage, ecological/CPR
  properties.
- Related entities: standards, certificates, declarations, documents/media.
- Missing editorial data: approved short description, badge/KPI selection and
  ordering, icons/styles, primary-standard designation, real document files,
  approved images/diagram, several detailed construction claims, and SEO
  metadata.
- Conflicts requiring explicit review include the category, `(N)` decoding,
  provisional CPR text, target assortment authority, and malformed numeric
  values. No automatic publication should resolve these silently.

## Recommended target model

Use a hybrid model:

1. `#__cables_categories`: component-owned nested set (`parent_id`, `lft`,
   `rgt`, `level`, `path`) plus Joomla publication, ACL, language, ordering,
   image, checkout, audit, params, and metadata fields.
2. `#__cables_products`: language-neutral ProductFamily identity and editorial
   page content (`family_key`, title, alias, short/full description, purpose,
   application, synonyms, marking text, extra information) plus Joomla fields.
3. `#__cables_product_category_map`: M:N placement. Products also keep one
   `primary_category_id` for canonical routing and breadcrumb.
4. `#__cables_product_variants`: explicit stable page/table attributes. Keep
   display/raw forms for compound values and nullable normalized values for
   validation/sorting. Use `UNIQUE(product_id, identity_key)`, not type size.
5. `#__cables_specification_groups` and
   `#__cables_specification_definitions`: stable codes, labels, group, type,
   unit, allowed scope, visibility/search/filter metadata, ordering/state.
6. Separate `#__cables_product_specification_values` and
   `#__cables_variant_specification_values`: raw value, normalized typed value,
   explicit value status, provenance/review state. Variant value overrides a
   ProductFamily value; a missing row means inherit/unknown, never zero.
7. `#__cables_highlight_definitions` and
   `#__cables_product_highlights`: ordered badge/KPI assignments. Values can
   be manual, derived from a specification, or derived from Variant count;
   do not duplicate the Variant count as stored Product data.
8. `#__cables_documents`: product-owned datasheets, certificates, and other
   files with role, title, description, local media path/URL, MIME type,
   language, ordering, and publication state. Keep one hero image and one
   diagram on Product in v1; add a media relation only when galleries or
   reusable media become real requirements.
9. `#__cables_standards` and `#__cables_product_standards`: shared standards,
   certificates, and declarations. `is_primary` belongs to the product
   relation; it can optionally reference a product asset.

Keep ordered marking parts as a separate table only if the administrator UI
edits each code/meaning pair. Otherwise keep one product marking text field in
v1 and split it when that workflow is implemented.

## Variant v1 fields

- Identity/display: `id`, `product_id`, `identity_key`, `mark_size`.
- Core/section: `core_configuration`, `core_count_total`, `section_display`,
  `section_main_mm2`, `section_aux_mm2`.
- Conductor: `conductor_class_code`, `conductor_class_text`,
  `conductor_diameter_display`, `conductor_diameter_main_mm`,
  `conductor_diameter_aux_mm`.
- Electrical: air AC/DC and ground AC/DC currents; main, PE, and auxiliary
  conductor resistance.
- Physical: bend display expression and optional multiplier, outer diameter,
  mass.
- Joomla/state: state, ordering, created/modified and actor fields.

Conductor material can remain an inherited Product specification in v1, with
a Variant specification override available for the 23 marks in which it
varies. `bend_radius_display` is required because values such as `7,5·Dз` are
formulas, not millimetres despite the source heading.

## Joomla integration

- Use component-owned categories with Joomla `TableNested` conventions and
  component ACL/assets. Remove the architectural dependency on Joomla core
  categories; current `catid` is legacy only.
- Joomla Smart Search/Finder integration should index family title/alias,
  editorial fields, synonyms, visible specifications, and Variant mark sizes.
  Variants do not receive separate URLs.
- Do not add a denormalized search JSON field or MariaDB full-text design in
  v1; the Finder plugin owns the search index.
- Keep stable technical codes and values language-neutral. Before the second
  language, add category/product/definition translation tables rather than
  duplicating all Variants. Translation tables are not required in Ukrainian
  v1.

## Alternatives rejected

- JSON-only Product and Variant records: fast fixture work, but weak validation,
  inheritance, administrator editing, indexing, and conflict handling.
- One column per all 56 source fields: simple queries but excessive sparse DDL
  and no clean extension to different cable types.
- Full EAV including core count and section: flexible but makes the primary
  Variant table, identity, validation, and page filtering unnecessarily hard.

## Migration and staging

The current worktree schema is not an approved baseline. Before implementation:

1. Inspect the installed local schema/version and row counts.
2. Add new tables and nullable columns without deleting JSON or `catid`.
3. Backfill and compare counts, identity collisions, inherited/overridden
   values, and rendered page output.
4. Switch the provider only after the relational source reproduces the page.
5. Remove legacy JSON/columns only in a separate approved destructive migration
   with a tested recovery path.

Raw import evidence belongs in optional import-run/import-row staging tables
when the import workflow is implemented. ODS parsing must follow
parse → validate → normalize → match → persist → report and remain idempotent.

## Product-owner decisions still open

1. Accept M:N categories with one primary category (recommended).
2. Formalize Variant `identity_key` discriminators when the same ProductFamily
   and mark size have different voltage/execution.
3. Decide which additional ODS fields appear in the first Variant table
   (outer diameter and mass are the strongest candidates).
4. Decide whether badge/KPI values may be derived from specifications
   (recommended) or are always manual.
5. Confirm unverified CPR remains draft and unpublished (recommended).
6. Choose the translation strategy only before adding the second language.

## References

- `data/nhxhj-product-page.html`
- `data/configurator/Каталог кабелю.ods`
- `src/administrator/components/com_cables/sql/install.mysql.utf8mb4.sql`
- `src/administrator/components/com_cables/sql/updates/mysql/0.2.1.sql`
- `decisions/0001-specification-storage-model.md`
- `briefs/2026-10-24-cable-catalogue-source-audit.md`
