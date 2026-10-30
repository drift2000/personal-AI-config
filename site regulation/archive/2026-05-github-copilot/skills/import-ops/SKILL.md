Import Ops Skill
----------------

Purpose
-------
Операційні норми для зберігання скачаних файлів, доступів, логування та метрик.

Storage
-------
- Dev: зберігати скачані файли у `catalog/<source_name>/v{n}/` на volume, не додавати до git.
- Prod: зберігати артефакти у S3/об'ємі з політикою зберігання і обмеженим доступом.

Access
------
- Хто має доступ до `catalog/` у dev — команда розробки; у prod — лише сервісні акаунти та адміністратори.

Logging & Metrics
-----------------
- Писати машино-зчитуваний JSON summary для кожного імпорту у `logs/imports/`.
- Метрики: `imports_total`, `imports_skipped_no_changes`, `imports_failed`, `enrichment_failures`, `created_substances_count`.

Security
--------
- Не зберігати особисті дані у логах; маскувати конфіденційні поля при необхідності.
