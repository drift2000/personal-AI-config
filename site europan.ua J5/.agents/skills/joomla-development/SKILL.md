---
name: joomla-development
description: Implement or maintain Europan's Joomla 5 `com_cables` component when Joomla-specific architecture, extension integration, or compatibility decisions are required. Do not use for generic PHP unrelated to Joomla.
metadata:
  short-description: Joomla 5 component workflow for Europan
---

# Joomla development

Use this skill for work in a custom Joomla extension, especially `com_cables`. Preserve Joomla 5.4 and PHP 8.3 compatibility; do not modify Joomla core.

## Workflow

1. Inspect the affected extension structure and its manifest before choosing an API. Identify whether the work belongs to the site, administrator, or shared namespace.
2. Prefer Joomla-native namespace/autoloading, service provider and dependency injection, MVCFactory, controllers/models/views, Table and Database APIs, Form XML, ACL, Router, and Web Asset Manager.
3. For an installable component, keep the manifest, service provider, language files, site/admin entry points, SQL install/update scripts, and assets consistent with the intended extension boundary.
4. Make the smallest compatible change. Use Joomla Database API rather than interpolated SQL, and preserve PHP 8.3 type compatibility.
5. Verify PHP syntax and the relevant Joomla integration surface: manifest discovery, namespace resolution, view route, form, ACL action, migration, or asset registration.

## Guardrails

- Do not copy Joomla 3/4 legacy patterns unless the current Joomla 5 code or a compatibility need justifies them.
- Do not bypass ACL, direct-request protection, CSRF checks, or Web Asset Manager merely to simplify a feature.
- Do not put domain or persistence logic in template files.
- Report unavailable Joomla runtime checks rather than claiming installation or routing was verified.
