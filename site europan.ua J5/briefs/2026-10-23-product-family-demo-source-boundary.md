# ProductFamily demo source boundary

## Goal and scope

Keep the frontend ProductFamily template independent of the temporary test
content, so a later catalogue-backed source can be selected without rewriting
the View or template. No database schema, data, import, or administrator UI
change is included.

## Verified implementation

- Family-level demonstration content is in
  `src/components/com_cables/src/Service/data/nhxhj-product-family.php`; the
  existing 125 Variant records remain in the adjacent JSON file.
- `DemoProductFamilyProvider` only reads and normalises those fixtures.
- `ProductFamilyProviderInterface` is the page-data contract. The component
  service provider binds it to the demonstration provider.
- The component receives that source from its extension container at boot, and
  `ProductModel` gets it from the booted `CablesComponent`. This is necessary
  because an extension's child DI container is not the global
  `Factory::getContainer()`.
- The template now obtains family-specific badge, diagram label, construction
  legend, temperature title and fire-safety note from the returned contract.

## Fixture contract refinements

- `standards` is a typed reference list; exactly one `isPrimary` record drives
  the hero and the normative-document value. The fire-safety certificate is a
  `type: certificate` record in that same list and is referenced by code.
- Construction and electrical rows can declare a reference instead of copying
  a value: `standardCode`, `primaryStandard`, `variantRange`,
  `variantBendRadius`, or `constructionField`. The provider resolves them for
  the presentation contract and fails fast when a reference is invalid.
- The provider derives the number-of-cores and section ranges from Variants,
  and bend radii from the actual single-core (`10·Dз`) and multi-core
  (`7,5·Dз`) Variant groups. This corrects the inverted explanatory comments
  in the initial fixture edit while retaining the displayed values.
- Presentation-neutral names are now `featureHighlights`,
  `safetyAndServiceDetails`, `constructionDetails`,
  `electricalParameters`, and `thermalAndSafetyParameters`; the static
  temperature section title remains in the template.

## Switch to persistence

Implement a database-backed `ProductFamilyProviderInterface` after the
ProductFamily/Variant schema and mapping are approved, then replace only the
binding in `administrator/components/com_cables/services/provider.php`. The
provider must supply the same page contract, including normalised document URLs
and all Variant fields; `ProductModel`, View and template do not change.

## Verification

- PHP 8.3 syntax checks passed for the new contract, fixture, provider, model,
  extension and template.
- Provider smoke check passed: id 4 returns 125 Variants.
- `GET /catalog-cables/product/4` returned HTTP 200 and rendered the family
  page with the expected 125-variant total.

## References

- `src/components/com_cables/src/Service/ProductFamilyProviderInterface.php`
- `src/administrator/components/com_cables/services/provider.php`
