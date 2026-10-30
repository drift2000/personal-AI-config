# Промт для Claude Code: HubSpot Company Sync

## Контекст задачі

Реалізувати фічу ручної одноразової/повторюваної синхронізації даних компанії з HubSpot CRM API у наш enamine.crm.

**Ключові рішення, які вже прийняті (не переглядати без потреби):**
- Напрямок: тільки HubSpot → CRM (read-only з боку HubSpot, ми нічого туди не пишемо)
- Тригер: виключно вручну, кнопкою на сторінці компанії — жодних cron/scheduled задач, жодних background-воркерів
- Матчинг компаній: по полю `domain`, через HubSpot Search API (`POST /crm/v3/objects/companies/search`, фільтр `domain`), НЕ через прямий GET за `idProperty=domain` (не працює, повертає 404)
- Після першого успішного матчингу зберігаємо `hs_object_id` компанії з HubSpot у нове поле `hubspot_id` моделі `Company` — для наступних синхронізацій вже робимо прямий `GET /crm/v3/objects/companies/{hubspot_id}`, без повторного пошуку
- Токен HubSpot (private app access token) зберігається ТІЛЬКИ на бекенді (env-змінна), фронтенд ніколи не звертається до HubSpot напряму і ніколи не бачить токен
- UI: розширення вже існуючої сторінки компанії на фронтенді (React), НЕ нова окрема сторінка, НЕ Django admin template
- Візуально: два блоки на сторінці компанії — "Дані CRM" і "Дані HubSpot", плюс кнопка "Заповнити все з HubSpot" (масове копіювання полів) і можливість перенести/відредагувати поля вручну перед збереженням
- Кешування/зберігання проміжних HubSpot-даних не потрібне — синхронізація завжди по запиту наживо

## ОБОВ'ЯЗКОВІ кроки перед написанням коду

1. Прочитай `.github/agents/client.agent.md` (або задиспатчи субагента `client-agent`) — модель `Company` в `client` app має найвищий ризик регресій у репо через щільні зв'язки з іншими моделями.
2. Прочитай `.github/agents/frontend.agent.md` (або задиспатчи `frontend-agent`) перед змінами в `src/frontend/src/**`.
3. Оскільки зміна торкається моделі `Company` (нове поле `hubspot_id` + міграція), згенеруй регресійний чек-лист із шаблону `.github/agents/templates/regression_checklist.md.tpl` і поклади в `docs/client/regression_<YYYY-MM-DD>.md` ДО того, як почнеш міняти модель.
4. Це PR, що торкається бекенду і спільних моделей — заповни `.github/agents/templates/pr_checklist.md.tpl` в кінці роботи.
5. Всі тести й запуск виключно через `./run.sh` (Docker) — не використовуй host-команди типу `python manage.py test` напряму.

## Backend (Django, app `client`)

### 1. Модель
- Додати поле `hubspot_id` (nullable, unique, indexed) до моделі `Company` в `client` app.
- Створити міграцію.

### 2. HubSpot клієнт
- Окремий сервісний модуль (наприклад `client/services/hubspot_client.py`), що інкапсулює:
  - `search_company_by_domain(domain: str) -> list[dict]` — виклик `POST /crm/v3/objects/companies/search` з фільтром `domain`, повертає список кандидатів (може бути 0, 1 або кілька)
  - `get_company_by_id(hubspot_id: str) -> dict | None` — `GET /crm/v3/objects/companies/{companyId}` з потрібним переліком `properties` (не `properties=all`, а явний список — визначити список разом з фронтендом, мінімум: `name, domain, country, city, industry, phone, address, numberofemployees`)
  - Токен читається з `settings.HUBSPOT_ACCESS_TOKEN` (env-змінна), ніде не хардкодиться
  - Обробка помилок: HTTP 404 (не знайдено), 429 (rate limit — з `Retry-After` header), 401/403 (проблема з токеном) — кожна має повертати зрозумілий статус на рівні API, не сирий traceback

### 3. API-ендпоінти (додати в Swagger — джерело правди для фронтенду)

**`POST /api/companies/{id}/hubspot-sync/`**
Логіка:
- якщо в `Company.hubspot_id` вже є значення → прямий `GET` по ньому
- якщо немає → `search_company_by_domain(company.domain)`
  - 1 результат → зберегти `hubspot_id`, повернути дані
  - 0 результатів → повернути статус `not_found`
  - >1 результатів → повернути статус `multiple_matches` зі списком кандидатів (id, name, domain кожного) для ручного вибору на фронтенді

Відповідь (приклад форми, узгодь фінальну схему в Swagger):
```json
{
  "status": "ok" | "not_found" | "multiple_matches" | "error",
  "hubspot_data": { "name": "...", "domain": "...", "country": "...", "...": "..." } | null,
  "candidates": [ { "hubspot_id": "...", "name": "...", "domain": "..." } ] | null,
  "error": "human readable message" | null
}
```

**`POST /api/companies/{id}/hubspot-sync/select/`** (потрібен тільки для кейсу `multiple_matches`)
- приймає обраний `hubspot_id` кандидата, зберігає його на компанії, повертає `hubspot_data` як в основному ендпоінті

**Збереження обраних полів у CRM** — використати наявний ендпоінт оновлення компанії (`PATCH /api/companies/{id}/`), окремий ендпоінт під це не потрібен: фронтенд просто шле туди фінальний набір полів, які користувач вирішив перенести/відредагувати.

### 4. Логування
- Кожен виклик до HubSpot (успіх, not_found, multiple_matches, error) логувати через `src/backend/common/command_logger.py`, побудований за шаблоном `.github/agents/templates/logging_backend.tpl`. Не створюй ad hoc логування в іншому місці.

### 5. Тести (запуск через `./run.sh`)
- Мок HubSpot API (не бити реальний API в тестах)
- Кейси: hubspot_id вже є / немає domain / 0 збігів / 1 збіг / кілька збігів / 429 від HubSpot / 401 (невалідний токен) / компанія архівована в HubSpot

## Frontend (React, `src/frontend/src`)

- Розширити існуючу сторінку/компонент картки компанії (не створювати нову сторінку/роут).
- Кнопка "Синхронізувати з HubSpot" → викликає `POST /api/companies/{id}/hubspot-sync/`.
- Стани UI:
  - `loading`
  - `ok` → показати два блоки поруч: CRM-дані (поточні, редаговані) і HubSpot-дані (read-only, довідкові)
  - `not_found` → повідомлення "Компанію не знайдено в HubSpot за доменом ..."
  - `multiple_matches` → список кандидатів з кнопкою вибору кожного → викликає `select/` ендпоінт
  - `error` → показати `error` з відповіді
- Кнопка "Заповнити все з HubSpot" — копіює всі значення з HubSpot-блоку в CRM-блок (як чернетку, ще не збережено)
- Опціонально: іконка/кнопка переносу окремого поля біля кожного рядка (per-field copy), а не тільки масова
- Кнопка "Зберегти" → `PATCH /api/companies/{id}/` з фінальним станом CRM-блоку
- Дотримуватись конвенцій із `.github/agents/frontend.agent.md`
- Нове логування на фронтенді (якщо буде потрібне, напр. клікові події) — через шаблон `.github/agents/templates/logging_frontend.tpl`

## Що НЕ робити
- Не звертатись до HubSpot API з фронтенду
- Не кешувати/зберігати HubSpot-дані в БД, окрім `hubspot_id`
- Не чіпати `once` app
- Не автоматизувати тригер синхронізації (ні webhook, ні cron) — тільки ручна кнопка
- Не використовувати `idProperty=domain` для прямого GET — тільки Search API для пошуку по домену

## Питання, які треба уточнити з людиною, якщо виникнуть під час розробки
- Точний фінальний перелік полів для мапінгу HubSpot → Company (зараз орієнтовний список вище)
- Формат зберігання multi-value полів (наприклад country — код ISO чи текст)
- UX для випадку, коли компанія в HubSpot архівована (`archived: true` в відповіді)
