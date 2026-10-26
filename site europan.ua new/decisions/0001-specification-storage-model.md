# 0001 — Specification storage model

Status: proposed
Date: 2026-10-24

## Context

The working cable catalogue contains 57 heterogeneous technical fields. A
fixed schema column for each field would make later additions expensive and
cannot model family inheritance plus Variant exceptions. The existing page
already has a ProductFamily/Variant presentation boundary.

## Decision

Keep Joomla Category → ProductFamily → Variant as the catalogue hierarchy.
Store technical properties through:

- `SpecificationDefinition`: stable code, Ukrainian label, presentation group,
  value type, unit, allowed scope and filtering/visibility metadata.
- separate `ProductFamilySpecificationValue` and `VariantSpecificationValue`
  assignment tables. Each preserves raw imported text and one validated,
  normalised typed representation.
- Variant values override a same-definition family value. A missing value does
  not mean zero or a negative assertion.
- a separate import-run/raw-row evidence store; source rows are not discarded
  after normalisation.

Standards, certificates/documents and media remain related entities, rather
than generic specifications. `isPrimary` belongs to the relation between a
ProductFamily and a standard.

## Consequences

- New catalogue fields normally require a definition and mapping, not DDL.
- Family summaries can be generated from common values; changing values stay
  visible at Variant level.
- Filtering uses indexes over normalised values, not a JSON blob. JSON is
  reserved for raw import payloads and intrinsically structured values.
- Exact MariaDB tables, Joomla installer SQL and source-column mapping remain
  unapproved and must be designed only after a schema review and business
  validation of duplicates/CPR data.

## Interim ProductFamily-page JSON shape

The product owner accepted this as an interim discussion outcome for the
ProductFamily presentation record, not as approved database DDL:

```text
main_parameters
construction
electrical_parameters
thermal_parameters
documents
standards
```

- `construction` is one JSON document with nested `conductor`, `insulation`,
  `sheath`, and later construction groups. No database column is created per
  nested group.
- `electrical_parameters` holds only family-wide electrical values and
  explanatory text. Per-size currents and conductor resistance are not copied
  there, because Variant data is the source of truth for those values.
- `thermal_parameters` groups both `thermal` and `fire_safety` data, with an
  optional `references` list of standard/certificate codes.
- `standards` remains the single JSON list for `standard`, `certificate`, and
  later declaration records. `isPrimary` is valid only for a `standard` entry;
  certificate codes are referenced by code from `thermal_parameters` and are
  not duplicated there.
- `documents` lists presentation-ready document metadata and a normalised
  local URL. Certification verification status belongs to the related
  standards/certificate entry.

This shape intentionally mirrors the existing PHP demonstration fixture so a
future provider can return the same presentation contract after JSON decoding
and validation.

## Evidence

- `briefs/2026-10-24-cable-catalogue-source-audit.md`
- `src/components/com_cables/src/Service/ProductFamilyProviderInterface.php`
