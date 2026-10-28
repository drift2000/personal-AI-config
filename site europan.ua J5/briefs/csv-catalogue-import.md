# CSV catalogue import

## Goal and scope
- Import the supplied configurator CSV into com_cables tables while preserving Catalog → Product → Variant → Specifications relationships.

## Verified findings
- Source: data/configurator/Конфігуратор для каталога - Аркуш1.csv; 21,128 logical source records after two header rows and 49 columns.
- Existing schema uses #__cables_catalogs, #__cables_products, #__cables_product_variants, and #__cables_product_specifications.
- The source repeats title + type-size for distinct configurations (e.g., AAsXS / 1х25 at 20 and 35 kV); title + type-size is not a valid variant identity.

## Decision
- The CLI importer only writes with explicit --apply and a caller-supplied approved --family-key. It has no HTTP endpoint.
- It uses a single transaction, Joomla database API, and reports validation errors before any DML.

## Work status / next step
- Review a dry-run report after confirming the ProductFamily discriminator; no production import has been performed.
