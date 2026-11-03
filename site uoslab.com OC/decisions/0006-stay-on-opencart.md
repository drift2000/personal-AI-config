# 0006 — Лишаємось на OpenCart 3.0.5.1, не переходимо на ocStore 3.0.4.1

Status: accepted
Date: 2026-11-02

## Context

`src/` — ванільний OpenCart 3.0.5.1 (раніше в контексті помилково записано як ocStore). Оцінено перехід на ocStore 3.0.4.1 (`data/ocStore`).
Порівняння схем: у нашій БД немає колонок, яких бракує в ocStore; ocStore додає 8 колонок (`meta_h1`, `noindex`, `product_to_category.main_category`) і 25 таблиць (блог, `manufacturer_description`, `order_shipment`…). Переваги ocStore: SEO Pro (мультимовні ЧПУ), модуль курсів НБУ, meta_h1/noindex, головна категорія. Недоліки: ядро старіше (база 3.0.3.x, PHP 7.3+; сумісність із PHP 8.3 не перевірено), ~1000 змінених файлів ядра, повторна перевірка 6 наших розширень, дублювання з «Новинами» та `language_url`.

## Decision

Лишаємось на OpenCart 3.0.5.1 (рішення користувача). Потрібні можливості (курси НБУ, за потреби meta_h1/noindex/головна категорія) — власними розширеннями; код ocStore (напр. `extension/currency/nbu.php`, `seopro.php`) можна використовувати як довідку.

## Consequences

- Продовжуємо `language_url` (мовний префікс, hreflang).
- `data/ocStore` — лише довідка, у `src/` не переносити.
