# site europan.ua new — current context

## Current state
- The repository contains a Joomla 5.4.10 distribution and Docker configuration, restored as uncommitted working-tree files and duplicated in an agent checkpoint commit.
- `com_cables` now implements the demonstration ProductFamily page at `view=product&id=4`, using a model, a dedicated demo-data provider, 125 variants, component-scoped WAM CSS/JS, and a site router for `product/<id>` paths. Local menu item `mainmenu:102` (`catalog-cables`) exposes the catalogue and its product route.
- ProductFamily test content is isolated in the component's `Service/data/` fixtures. The page model consumes a `ProductFamilyProviderInterface` selected in the component service provider, so an approved catalogue-backed provider replaces that binding without View/template changes.
- `data/nhxhj-product-page.html` remains the visual reference. Its 125 Variant records have been retained in the component's single demo JSON source; visible totals derive from that data rather than the mock's stale 164 values.
- The supplied working ODS catalogue was audited on 2026-10-24. It has 16,023 valid Variant rows across 288 marks, while its `(N)HXH-J FE180/E30` family has 164 variants rather than the demo fixture's 125. Its mapping, duplicates, provisional CPR content, and source-data corrections require approval before any import work.

## Constraints and risks
- The local Docker Compose stack has no running containers; therefore the live database schema cannot be audited from this environment.
- The only Git remote is `origin` (`drift2000/europan`); local history contains only an initial commit plus a baseline checkpoint without the component history.
- The ProductFamily page inherits fonts from the active Joomla template; no external font provider is used. Its CSS and module JS are attached before the document head is compiled and were verified in the locally rendered HTML; extension-install packaging still needs verification. The local menu data is not installer-provided.

## References
- [Recovery audit brief](briefs/2026-10-21-recovery-audit.md)
- [ProductFamily page Stage 1 brief](briefs/2026-10-22-product-family-page-stage-1.md)
- [ProductFamily page Stage 1 security review](briefs/2026-10-22-product-family-page-security.md)
- [ProductFamily page Stage 2 result](briefs/2026-10-22-product-family-page-stage-2.md)
- [SEF routing and catalogue menu](briefs/2026-10-23-cables-sef-routing.md)
- [ProductFamily demo source boundary](briefs/2026-10-23-product-family-demo-source-boundary.md)
- [Cable catalogue source audit](briefs/2026-10-24-cable-catalogue-source-audit.md)
- [Proposed specification storage model](decisions/0001-specification-storage-model.md)
