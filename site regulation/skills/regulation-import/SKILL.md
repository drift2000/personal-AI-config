---
name: regulation-import
description: Імпорт регулювань у Chem Regulations (Django management commands import_<country>_<source>) — новий імпорт для джерела, зміна чи рев'ю наявного (DEA CSA, CA Prop 65), версіонування RegulationDocument, зв'язок речовин через SubstanceImportService/PubChem, dry-run і перевірка повторного імпорту. Use for regulation import, parser-to-DB, enrichment, import review.
---

# Імпорт регулювань

Факти про код звірено 2026-10-29 (див. «Розбіжності»); перед роботою переконатися, що вони ще чинні. Вимоги продукту — `briefs/2026-05-25-chem-regulations.md` у приватному каталозі проєкту; для PDF-джерел додатково — skill `pdf-table-parsing`.

## Де що лежить

- Команда імпорту: `src/regulations/management/commands/import_<country>_<source>.py` — один файл на джерело (`import_us_dea_csa`, `import_us_ca_oehha_prop65`). Взірці: Prop 65 — CSV, чисті функції парсингу на рівні модуля; DEA CSA — PDF за координатами слів (`pdfplumber`), методи класу.
- Речовини: `src/core/substance_service.py` — `SubstanceImportService`:
  - `import_from_identifier(name|CAS)` → PubChem → upsert `Substance` за InChIKey + синоніми + структура;
  - `import_minimal(name, synonyms)` — без PubChem: `inchikey=None`, пошук наявної речовини за `SubstanceSynonym.name__iexact`.
- PubChem: `src/core/pubchem.py` — `PubChemClient` (timeout 10 c, retries з backoff, `VERIFY_SSL = False`).
- Моделі (поля звіряти з кодом перед використанням):
  - `regulations.Regulation` — `country_code`, `document_number`, `regulation_type` (TextChoices), `comments`;
  - `regulations.RegulationDocument` — `version`, `is_current`, `file_path`, `file_format`, `source_url`, `valid_from/valid_until`, `uploaded_by`, `notes`;
  - `regulations.RegulationEntry` — `substance`, `regulation_document`, `structure`, `restriction_type`, `status` (`EntryStatus`: active/removed/suspended), `removed_at`, `removal_notes`, `details`, `extra_data` (JSON для полів, специфічних для джерела);
  - `substances.Substance` (`inchikey`, `parent_substance`), `SubstanceSynonym` (`name`, `type`, `language`, `source`), `SubstanceStructure` (`smiles`, `structure_type`, `status`, `verified_by`).
  - `src/core/models_regulations.py` — старий паралельний набір моделей без міграцій; не використовувати й не розширювати.
- Дані: `docker_data/import` → `/app/import` (вхідні файли), `docker_data/catalog` → `/app/catalog` (збережені версії документів). `src/` змонтовано в `/app` (WORKDIR).

## Контракт команди (як у наявних)

1. Константи джерела вгорі файлу: `SOURCE_URL`, `COUNTRY_CODE`, `REGULATION_NAME`, `DOCUMENT_NUMBER`, `REGULATION_TYPE`.
2. Аргументи: `--dry-run` обов'язково; `--file` для локального файлу і/або `--skip-download` для завантажуваного.
3. Парсинг відокремлений від запису в БД і не пише в БД.
4. `--dry-run` — лише парсинг і зведення (кількості, перші N рядків), без змін у БД.
5. Запис — у `transaction.atomic()`: `Regulation.get_or_create` за стабільним ключем → `RegulationDocument` → речовини через `SubstanceImportService` → `RegulationEntry`.
6. Повторний запуск не створює дублікатів `RegulationEntry`: `get_or_create` за ключем, що враховує специфіку джерела (у Prop 65 — `doc + substance + extra_data.toxicity_flags`).
7. Історію не видаляти: зняті з регулювання речовини → `status=removed`, `removed_at`, `removal_notes`.
8. Наприкінці — зведення в stdout: нові/наявні/пропущені речовини, без PubChem, помилки.

## Вимоги брифу, яких код поки не виконує

Якщо задача їх зачіпає — реалізовувати за брифом. Якщо ні — не розширювати задачу, а згадати у звіті.

- SHA256 файлу і пропуск імпорту, якщо хеш не змінився (у DEA `hashlib` імпортовано, але не використано: кожен запуск створює нову версію; Prop 65 завжди пише `version=1`).
- Зняття `is_current` з попередніх версій документа.
- Позначення `removed` для речовин, яких немає в новій версії (DEA цього не робить).
- Enrichment як окремий модуль, який можна вимкнути (зараз PubChem викликається всередині імпорту).
- Автотестів немає (`tests.py` — заглушки).

## Перед новим джерелом з'ясувати

URL і формат джерела; 2–5 реальних прикладів рядків, включно з проблемними; які ідентифікатори є (CAS, InChIKey, лише назва); формат дат; як джерело позначає вилучення речовини; одна чи кілька записів на речовину; частоту оновлень. Чого немає — запитати, не вигадувати.

## Запуск і перевірка

- Лише dev-оточення: `./run.sh dev exec backend python manage.py import_<...> --dry-run`, далі без `--dry-run`. На `prod` — тільки за явним дорученням.
- Перед реальним імпортом переконатися, що backend дивиться на dev-БД (`.env`, `docker-compose.dev.yml`); вміст `.env` не виводити.
- Definition of Done:
  1. dry-run на реальному файлі дає очікувану кількість записів і правильні приклади;
  2. імпорт у dev;
  3. повторний імпорт не дає дублікатів `RegulationEntry`/`SubstanceSynonym`; поведінку версій описати чесно;
  4. вибірково перевірити записи в Django admin;
  5. записи без PubChem отримують статус, що потребує перевірки.
- Тести (якщо додаються): Django `TestCase` через `python manage.py test` (pytest у залежностях немає — без погодження не додавати); парсер тестувати як чисту функцію на фрагментах реальних рядків; мережу PubChem мокати.

## Рев'ю

Ідемпотентність; транзакції; дедуплікація (InChIKey → синонім); статуси замість видалення; обробка неповних рядків з логуванням сирого рядка; таймаути мережі; без жорстко прописаних шляхів поза змонтованими томами; зведення.
