Tests Prompts
=============

1) Parser unit tests (pytest)
--
Prompt: "Згенеруй набір `pytest` unit-тестів для `parse()` з прикладами: повний запис, неповний запис (missing inchikey), дубльований запис. Перевір нормалізацію і те, що `raw` зберігається для проблемних рядків."

2) Importer dry-run summary
--
Prompt: "Запусти dry-run імпорту для `{{file_path}}` і поверни JSON summary з полями: `created_regulations`, `created_versions`, `created_substances`, `updated_substances`, `skipped_no_changes`, `errors` — не записуючи нічого в БД. Якщо неможливо виконати dry-run — опиши чому."

CI notes
--------
- Додати тести у CI; використовувати disposable Postgres для integration tests.
