# com_cables — SEF routing and catalogue menu

## Goal and scope

Make the registered local `com_cables` ProductFamily demonstration reachable without the prior redirect to the home page, and provide a visible catalogue menu entry.

## Verified findings

- Before this change the component was enabled (`extension_id=249`), but no site menu item targeted it.
- Global Joomla `sef` and `sef_rewrite` settings were both `false`. A clean path was consequently parsed relative to `index.php` and returned a 404.
- The component had registered a router factory but no `Site\\Service\\Router` implementation.

## Implemented state

- `src/components/com_cables/src/Service/Router.php` builds and parses `product/<positive numeric id>` paths.
- A site menu-item metadata definition exists for the catalogue categories view.
- The local `mainmenu` now has published item `id=102`, title `Каталог кабелів`, alias `catalog-cables`, pointing to `com_cables` categories.
- The local Joomla configuration enables `sef` and `sef_rewrite`; Nginx already routes clean URLs to `index.php`.

## Verification

- `http://europan.localhost/catalog-cables` returned HTTP 200 and rendered the catalogue.
- `http://europan.localhost/catalog-cables/product/4` returned HTTP 200 and rendered `(N)HXH-J FE180/E30`.
- The legacy query URL canonicalized to `/component/cables/product/4` and returned HTTP 200.
- The product page now emits `/media/com_cables/css/product-family.css` and `/media/com_cables/js/product-family.js`; both returned HTTP 200.

## Asset-loading correction

- Product markup was rendering without its CSS or JavaScript because the asset registry URIs used `com_cables/css/...` and `com_cables/js/...`. Joomla's media resolver already selects the `css` or `js` folder, so it searched for non-existent double paths.
- The registry now declares `com_cables/product-family.css` and `com_cables/product-family.js`.
- `CablesComponent` attaches the product assets at `onBeforeCompileHead`, before Joomla locks the Web Asset Manager. This keeps the integration component-scoped and does not modify the active site template.

## Residual risk

- Menu item `102` is local database state rather than installer-provided data. A clean Joomla installation still requires an administrator to add the catalogue menu item (or future installer logic explicitly approved by the owner).
- Extension archive packaging remains unverified and was outside this routing change.
