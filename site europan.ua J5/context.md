# site europan.ua new — current context

## Current state
- Joomla 5 cable catalogue uses catalog → product → variant → product specifications tables.
- A CLI importer now exists at src/cli/import-cables.php; it is dry-run by default and requires both an approved family key and --apply.
- Product owner limited the proposed first catalogue schema to four domain tables: nested categories, ProductFamily products, one JSON specification row per Product, and explicit-column Variants. Expanded EAV/related-entity tables are deferred until a concrete workflow requires them (2026-10-28).
- Clean-install SQL for the accepted four-table schema is implemented and passed two consecutive executions on MariaDB 11.8.9 (2026-10-28). Existing installations still require a separately reviewed update/backfill.
- Local dev MariaDB was explicitly rebuilt from the old empty 0.2.1 catalogue tables to the accepted four-table schema on 2026-10-28. It contains only the nested root category; Joomla schema registry remains 0.2.1. Independent read-only QA confirmed tables, indexes, root shape, and HTTP 200 for `/` and `/catalog-cables/product/4`.

## Constraints and risks
- The source has duplicate title + variant combinations for distinct voltages. ProductFamily identity must be explicitly approved before a production import.
- The CSV contains malformed/ambiguous records; the importer reports them and performs no partial write.

## References
- [CSV catalogue import brief](briefs/csv-catalogue-import.md)
- [Current proposed four-table catalogue schema plan](briefs/2026-10-28-catalog-database-schema-plan-v2.md)
- [Accepted four-table catalogue schema ADR](decisions/0002-four-table-catalogue-schema.md)
