# ProductFamily page — Stage 1 architecture brief

## Goal and scope

Assess integration of `data/nhxhj-product-page.html` as the frontend detail
page for a ProductFamily in Joomla 5 `com_cables`. This is research only; no
application, schema, asset, or Docker change was made.

## Verified findings

- The mock exists at `data/nhxhj-product-page.html`. It contains 125
  `VARIATIONS` records, despite hard-coded instances of 164 in the hero, KPI,
  tab, table heading, and counter.
- The site component is a minimal scaffold. Its only detail endpoint is
  `view=product&id=4`; `Site\\View\\Product\\HtmlView` checks that fixed id
  and builds a fixed Variant-like object itself. No ProductFamily or Variant
  model, table, database schema, CSS/JS, WAM registry, import, or custom
  router exists.
- Its manifest installs site/admin code but no component media. The service
  provider already registers Joomla MVCFactory, dispatcher, and RouterFactory.
  No custom site Router implementation is present.
- Cassiopeia renders the component inside
  `.site-grid > .container-component > main`; the header can be sticky.
- The mock uses Google-hosted IBM Plex fonts, inline SVGs, generic/global CSS,
  global JS selectors, `innerHTML`, an inline `onclick`, `href="#"` document
  cards, and incomplete tab ARIA/keyboard behavior. It contains no responsive
  media query.
- The local Joomla distribution is uninstalled and the host lacks `php`; no
  PHP, installation, routing, or browser-runtime verification was possible.

## Recommended approach

Adapt the existing `view=product` route and template rather than add a second
detail route. In Stage 2, treat the existing `id=4` as the identity of the
single demonstration ProductFamily; retain the `product` view/route name only
for backward compatibility. Introduce a site ProductModel and a separate,
namespaced demo-data provider that returns one ProductFamily page structure:
family metadata; badges/KPIs; textual/construction/electrical groups;
`variants`; documents; and standards. The provider is the only authority for
the demo data used by PHP rendering, filtering and counts. Each Variant must
retain every source field: `size`, `cores`, `section`, `conductor_d`,
`conductor_mat`, `current`, `bend_r`, `resistance`, and `resistance_pe`.
`resistance_pe` remains preserved even though the approved eight-column table
does not display it. The View retrieves the page structure, sets document
metadata and WAM assets, while the template only renders escaped values. This
preserves the presentation contract when a later model maps database-backed
Category → ProductFamily → published Variant data, including inherited family
values and Variant overrides.

Derive a single `count($variants)` value and reuse it at every total-count
location. Render the 125 initial table rows server-side or manipulate safe DOM
nodes only; component JS must not interpolate future catalog values through
`innerHTML`. Scope CSS and JS to one namespaced component root. Move CSS/JS to
`media/com_cables`, declare the manifest media destination, register WAM
assets in `joomla.asset.json`, then load with Joomla's extension asset
registry. Preserve the query route in this visual-only change; defer custom
SEF routing until actual stable family identity/slug and menu requirements are
known.

Implement ARIA-complete manual tabs: each tab/panel has linked IDs,
`aria-controls`/`aria-labelledby` and `aria-selected`; exactly one tab is in
the tab order; arrows/Home/End move focus; Enter/Space activates; active-panel
change manages focus when invoked by the electrical-table action. Build dynamic
filter options from variants, intersection filtering, normalisation of `х`,
`x`, and `×`, and announce the filtered count via an `aria-live` result. A
tab-jump link must go through this controller. There must be no inline event
handlers or active placeholder document URLs. Real documents require safe
Joomla URLs; missing documents should be visibly unavailable; the supplied
SVG can open in an accessible dialog.

The existing manifest declares site and administrator language paths that are
not present in this extension's current package layout. Since Stage 2 must add
component media to this manifest, it must first make the complete manifest
package layout consistent (including language files), or explicitly verify the
deployment mechanism does not use extension installation. Component discovery
or installation is not an acceptance gate until that pre-existing packaging
defect is resolved. No schema or database change is involved.

## Open decisions and risks

- Remote Google Fonts gives closest immediate visual fidelity but creates
  network, privacy, CSP, and availability dependence. Self-hosting
  license-verified IBM Plex assets is the production-stable alternative. This
  delivery decision needs explicit approval before Stage 2; the recommended
  default is self-hosting when licensed assets are supplied.
- The mock is fixed-width desktop design. Responsive breakpoints necessarily
  add an approved technical adaptation.
- `top: 0` sticky tabs may overlap a sticky template header; expose/define a
  component sticky-offset rather than modifying the template.
- Current `Product` naming is semantically weaker than ProductFamily but is
  the only existing endpoint; preserve it now to avoid a parallel frontend
  architecture.
- Technical claims, standards, certificates, and document URLs in the mock
  are demonstration content and require subject-matter confirmation before
  publication.

## Required later verification

Run PHP 8.3 syntax checks in the container; validate the manifest and WAM
registry; install/discover the component; test query and SEF route behavior;
and browser-test Cassiopeia (including sticky header), desktop/narrow layouts,
keyboard tabs, filter combinations/normalisation, safe document state, and
accessibility.
