# 0002 — Інструмент міграції: PHP CLI, прямий SQL, ідемпотентність

Status: accepted
Date: 2026-10-26

## Context

~10к товарів, багато полів JBZoo, кілька джерел (магазинів), потрібні повторні прогони (розробка на старому бекапі, фінал — на свіжому).

## Decision

- PHP 8.3 CLI-скрипт у контейнері `php-fpm`, каталог `migration/` поза `src/`.
- Джерело: бекап Akeeba, розпакований у `data/joomla`; SQL (`installation/sql/site.sNN`) → окрема БД `joomla_src` (лише читання).
- Запис у таблиці OC напряму через PDO з транзакціями; `migration_map(source, entity, src_id, oc_id, hash)` для ідемпотентності.
- Мапінг полів — конфіг, згенерований з аудиту й погоджений вручну.
- Клієнти й замовлення не переносяться (бекап старого сайту архівується).

## Consequences

- Етапи — окремі команди (`audit|categories|products|images|seo|content|reviews|verify`).
- Нові незмаплені поля на свіжому бекапі зупиняють імпорт зі списком полів.
- Редіректи — nginx `map` include.

## Evidence

- `briefs/2026-10-26-migration-joomla-jbzoo-to-ocstore.md`
