# ProductFamily page — Stage 1 security review

## Goal and scope

Read-only review of `data/nhxhj-product-page.html` and the planned Joomla 5
`com_cables` frontend integration. No component, configuration, or schema
files were changed.

## Verified findings

- The mock has one inline event handler at line 1145, an inline script at
  lines 1282–1360, inline CSS, and Google Fonts dependencies at lines 8–10.
  These conflict with a strict CSP and should not be transplanted directly.
- The table renderer assigns template strings containing `VARIATIONS` values
  to `tbody.innerHTML` (lines 1335 and 1341–1352). The bundled 125 records
  are static and contain no executable markup, so this is not exploitable in
  the mock; it would become stored XSS if future catalog/import values reach
  the same sink.
- All inline SVGs are static simple shapes/text. No `script`, `foreignObject`,
  external `use`/`image`, animation, or event attributes were found.
- Three document cards use `href="#"` (lines 1199, 1213, 1224). They have no
  current navigation target. Future document URLs must not be output as an
  unvalidated `href`.
- `com_cables` currently escapes every displayed product field and generates
  its local catalogue link with Joomla `Route`. It has no component media
  directory, WAM registry, or manifest media declaration. This is a clean
  baseline; do not use raw HTML as a data field or bypass the View escaping
  convention.
- The development Compose override publishes Adminer on all host interfaces
  when the `local` profile is enabled and `.env` contains example DB
  credentials. This is outside the page integration but is a local-network
  exposure risk; production Compose does not start Adminer by default.

## Stage 2 guardrails

- Register external CSS/JS using component-scoped WAM assets and put them
  under `media/com_cables`; use delegated event listeners and namespaced root
  queries. Do not retain inline scripts, handlers, or styles.
- Render product-family and variant strings using `$this->escape()` in PHP.
  For client-side generated filters/table rows, create DOM elements and set
  `textContent`; do not interpolate catalog values into `innerHTML`. Keep the
  material badge as a closed mapping from an enum, not a string returned by
  catalog data.
- Route only known internal component targets through `Route`. Model documents
  as approved local media/file IDs or validated HTTPS URLs; reject control
  characters and `javascript:`, `data:`, `vbscript:`, protocol-relative, and
  unapproved hosts. Render absent/unapproved documents as disabled text, not
  a link. Add `rel="noopener noreferrer"` for any approved external target
  that opens a new tab.
- Preserve the static inline SVG only as reviewed template markup. If SVGs
  later become uploads or data fields, sanitize server-side and serve uploaded
  SVG with a CSP that disables scripts, or convert to a safe raster/managed
  asset.
- Prefer self-hosted, license-verified IBM Plex fonts. If remote fonts remain
  approved, explicitly allow only `fonts.googleapis.com` in `style-src` and
  `fonts.gstatic.com` in `font-src`; use no broad CSP relaxations such as
  `'unsafe-inline'` for scripts. Enable/test Joomla HTTP Headers CSP in report
  only before enforcement.
- Bind Adminer to loopback for local development or do not use the `local`
  profile on shared networks; keep non-default credentials and `.env` ignored.

## Residual risks / required verification

- A later admin/import capability changes the threat model: review ACL,
  CSRF, XLSX/CSV validation, stored-XSS paths, document upload/download
  authorization, audit logging, and destructive bulk actions before it is
  introduced.
- Browser-test the WAM assets under the intended CSP and verify no other
  template/plugin policy requires unsafe inline script/style. Verify document
  endpoints enforce publication/access state and do not disclose private
  files.

## References

- `data/nhxhj-product-page.html:8-10,1145,1199-1232,1282-1360`
- `src/components/com_cables/tmpl/product/default.php`
- `src/components/com_cables/src/View/Product/HtmlView.php`
- `src/administrator/components/com_cables/cables.xml`
- `docker/docker-compose.dev.yml`, `docker/docker-compose.prod.yml`
