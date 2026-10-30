# site marker-crm.ad.loc — поточний контекст

## Поточний стан

- Продукт: enamine.crm — внутрішня CRM (компанії, контакти, домени, інтеграції ftp/s3/onedrive, імпорт завантажень, звіти, HubSpot sync).
- Стек: Django 4.x + DRF (drf-spectacular), React 19 (CRA, MUI), PostgreSQL; усе в Docker через `./run.sh`. Командні правила для агентів — у проєктному `AGENTS.md` (`CLAUDE.md` = `@AGENTS.md`, з 2026-10-29), запуск — `README.md`.
- Перед змінами в коді модуля прочитати відповідну роль: `src/backend/{client,ftp,download,once}/**` → `agents/<app>.md`, `src/frontend/src/**` → `agents/frontend.md` (для делегування — general-purpose субагент із тілом файлу ролі). Шаблони чеклистів і scaffold — `skills/local-agents/templates/`; заповнені чеклисти й згенеровані docs — у приватний `docs/<app>/`, не в репозиторій.
- Основна гілка — `develop`. Останні етапи за git log: HubSpot sync (`d2254ee`…`d4e2d08`), логін для всіх сторінок CRM (`c15c33a`), Azure AD SSO — app `auth_azure` (`bcc6e0f`), уніфікований Integration app (`8f68837`).
- Azure AD SSO: фази 1, 2, 4 зроблено, фаза 3 — лише scaffold (немає реального tenant/груп) — за `docs/auth_azure/README.md` станом на 2026-09-15, не перевірялось повторно.

## Структура цього каталогу

Перенесено 2026-10-29 з локальних gitignored каталогів репозиторію (`.github/`, `docs/`, `CONTRIBUTING.md`); вміст історичних файлів не змінювався.

- `agents/<role>.md` — ролі за модулями (client, ftp, download, once, frontend); раніше `.github/agents/*.agent.md`.
- `skills/local-agents/` — `SKILL.md`, `AGENT_USAGE.md`, `templates/*.tpl` (regression/PR чеклисти, logging, таблиці фронтенду); раніше `.github/skills/` і `.github/agents/templates/`.
- `docs/` — документація модулів (`<app>/README.md`), regression- і PR-чеклисти, `once/registry.md`. Структура збережена, тож посилання `docs/...` в історичних файлах валідні відносно цього каталогу; посилання `.github/agents/...` в них — старі шляхи (див. відповідність вище).
- `briefs/` — `2026-08-18-single-domain-auth-plan.md` (раніше `docs/architecture/`), `2026-09-04-hubspot-sync-prompt.md` (промпт задачі HubSpot sync).
- `archive/` — `CONTRIBUTING.md` (старий опис workflow агентів), `docs-tmp/` (старі нотатки з запуску; `README.local.md` перейменовано в `README.local-setup.md`, бо `*.local.md` ігнорується приватним репо).

## Обмеження та ризики

- `client` — найвищий ризик регресій (щільні зв'язки моделей): перед змінами — regression checklist (`agents/client.md`).
- `src/backend/once/**` — архівні скрипти, не редагувати й не перезапускати; реєстр — `docs/once/registry.md`.
- DRF API закрите за замовчуванням: `SessionAuthentication` + `IsAuthenticated` + `HasAssignedRole` (no-op, доки `AZURE_AUTH_ENFORCED` не True) — перевірено в `project/settings.py` 2026-10-29. Старі матеріали (агенти, `archive/`) ще кажуть «API без auth» — застаріло.

## Відкриті питання та наступні дії

- На момент перенесення в робочому дереві є незакомічені зміни (`client/api_views.py`, `serializers.py`, `tests.py`, frontend `PeriodFilteredReport.jsx`, `HubspotSync.jsx`, `run.sh`, `docker/scripts/*`, `.env.example`, db-seed) — чужа/поточна робота, не чіпалась.

## Посилання

- `docs/auth_azure/README.md`, `docs/client/README.md`, `docs/download/README.md`, `docs/ftp/README.md`
- `briefs/2026-09-04-hubspot-sync-prompt.md`, `briefs/2026-08-18-single-domain-auth-plan.md`
