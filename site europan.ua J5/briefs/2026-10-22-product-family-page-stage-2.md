# ProductFamily page — Stage 2 result

## Goal and scope

Implement the approved ProductFamily presentation for the existing frontend
`com_cables` product route, using only the supplied demonstration data. No
database, import, ACL, router, Docker, or Joomla-core change was made.

## Completed implementation

- Retained `view=product&id=4` and made it the stable demonstration
  ProductFamily identity. A missing identity still produces the Joomla 404.
- Added `ProductModel` and `DemoProductFamilyProvider`. The provider owns the
  shared page data; its 125 Variant records live once in
  `src/Service/data/nhxhj-variants.json` and retain all nine source fields,
  including `resistance_pe`.
- Replaced the placeholder template with the hero, five accessible tabs,
  description, full source construction SVG and six-item legend, electrical
  data, filterable variant table, document cards, standards and SVG dialog.
  The total derives once from `count($variants)` and is reused in every
  visible total.
- Added component-scoped WAM CSS/JS in `src/media/com_cables`; no remote font
  is loaded, so typography inherits the active Joomla template. The manifest
  now declares component media.
- Client code has no `innerHTML`, inline handlers, placeholder links, or
  external dependencies. It creates select options with DOM APIs, filters
  server-rendered rows, normalizes `х`/`x`/`×`, supports manual arrow/Home/End
  tab focus plus Enter/Space activation, announces filter counts, calculates
  the active Cassiopeia sticky-header offset, and opens the static SVG in a
  dialog.

## Verification

- JSON parse/contract check: passed — 125 Variant records and all nine fields.
- WAM manifest JSON and component XML: passed static parse.
- PHP 8.3 `php -l`: passed for ProductModel, provider, Product view and
  template, using a read-only bind mount in the local PHP container.
- Provider smoke test: passed — id 4 returns 125 variants; id 9 returns null.
- Security static scan: passed — no inline script/style/handler, `href="#"`,
  `innerHTML`, or Google Font dependency in the component files.

## Residual verification and risks

- Full Joomla installation/discovery, WAM browser delivery, menu/SEF routing,
  visual comparison and browser accessibility checks remain unavailable here.
  The base Compose file does not mount source; the dev override resolves
  `./src` relative to `docker/` and mounts the non-existent `docker/src`.
- The current extension manifest's historical `site`/`admin` package-folder
  layout still needs alignment before component installation can become a
  reliable acceptance gate.
- Technical/certification/standards statements remain demonstration content
  and require subject-matter validation before publication.
