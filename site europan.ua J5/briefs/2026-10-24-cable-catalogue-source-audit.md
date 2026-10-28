# Cable catalogue source audit

## Goal and scope

Read-only comparison of the supplied `data/configurator/Каталог кабелю.ods`
with the existing demonstration ProductFamily page and its `(N)HXH-J FE180/E30`
fixtures. No source, schema, import, or frontend files were changed.

## Verified findings

- The ODS has one populated sheet and 16,023 valid Variant rows. It contains
  288 product marks, 59 non-empty product-group labels, and 57 catalogue data
  fields. The sheet has trailing empty rows to the spreadsheet limit; an
  importer must not treat those as records.
- `Марка продукції` is the closest source field to the current ProductFamily
  concept; `Типорозмір продукції` is the candidate display/variant key. The
  product-group label belongs above the family (normally a Joomla category),
  but has missing values and spelling variants that require a controlled
  vocabulary.
- Product code cannot be an identity key: only 8 populated cells exist and
  their contents are notes/questions rather than product codes.
- There are 63 exact `(product group, mark, type size)` duplicate collisions.
  Imports must report them and preserve source-row provenance, rather than
  silently deduplicating them.
- For `(N)HXH-J FE180/E30`, the ODS contains 164 type sizes while the demo
  JSON has 125. Exactly 107 size labels overlap; the source has 57 labels
  absent from the demo and the demo has 18 labels absent from the source.
  The mismatch is material, including unequal-PE `3х…+1х…` sizes in the
  source versus same-section `3+1х…` demo sizes.
- Of the exact overlap, source electrical/core values agree with the demo
  except for `3х1,0(RE)`, whose source cross-section is `300` despite a
  `1.15 mm` conductor diameter and `RE` class. This is a likely source-data
  error requiring subject-matter confirmation. Source `-` versus demo blank
  for unavailable current/PE-resistance values is not a value contradiction.
- The source fields include construction, operating conditions, current
  loadings, resistances, diameters, mass, CPR and certification metadata. It
  has no populated cross-section drawing, image, or photo cells.
- CPR source content is not publication-ready: 7,411 records carry workflow
  or provisional wording (for example, certification pending/required) and
  7,077 are blank or not applicable. Only 1,535 are candidates for a
  publishable classification after validation.
- Family-level source values are often uniform but are not globally guaranteed:
  conductor construction varies inside 23 marks; standards, purpose,
  fire-safety, CPR, voltage and several construction fields also vary in some
  marks. The storage model needs explicit family inheritance plus Variant
  override, not one fixed set of columns copied to every page.
- The current page preserves several target-family facts (voltage, primary TU,
  fire certificate identifier, warranty/lifetime, sheath, temperatures), but
  it is still demo content. It omits `ДСТУ IEC 60502-1:2009` from its standards
  list; its `(N)` decoding claims VDE origin whereas the supplied source says
  local national/DSTU certification. The source product-group label for this
  mark is also semantically inconsistent with the cable construction and
  should not be published as the page category without review.

## Recommended direction

1. Keep the established `Joomla Category → ProductFamily → Variant` model,
   with an approved normalized product-group vocabulary as the category and
   `Марка продукції` as the initial family candidate. Require review for the
   six marks found under multiple product groups.
2. Introduce a data-driven SpecificationDefinition catalogue for the 57 source
   fields, including value type, unit, applicability and presentation group.
   Store raw source value and normalized typed value separately. Assign a
   specification at family level only when it is common; use a Variant
   override when source values differ.
3. Stage imports as parse → validate → normalize → match → persist → report.
   Use a source-record fingerprint/provenance as the temporary row identity;
   do not use product code. Treat conflicting variant identity and draft CPR
   text as reportable validation outcomes, not automatic publication data.
4. Retain the `ProductFamilyProviderInterface`, but replace only its data
   implementation after the schema/mapping is approved. The provider should
   calculate page summaries from verified inherited/overridden values instead
   of consuming static prose.
5. Make the page show family highlights, then a Variant comparison table with
   core/section, conductor class, current by installation condition,
   resistance, bend radius, outer diameter and mass where available. Provide
   progressive disclosure for all applicable specifications.
6. Treat CPR/certificates as a separately verified publication state. Do not
   show generic success checks for unverified source text. Do not label the
   existing fixed SVG as a source drawing; use it only as an explicitly
   schematic fallback until an approved diagram asset exists.

## Work status / next step

Await product-owner decisions on the source mapping, taxonomy normalisation,
duplicate policy, the `(N)HXH-J FE180/E30` assortment authority, and CPR
publication policy before any schema or importer implementation.

## References

- `data/configurator/Каталог кабелю.ods`
- `src/components/com_cables/src/Service/data/nhxhj-product-family.php`
- `src/components/com_cables/src/Service/data/nhxhj-variants.json`
- `src/components/com_cables/src/Service/DemoProductFamilyProvider.php`
- `src/components/com_cables/tmpl/product/default.php`
