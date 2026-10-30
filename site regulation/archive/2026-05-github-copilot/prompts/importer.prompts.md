Importer Prompts
================

1) Generate idempotent importer (Django)
--
Prompt: "Згенеруй Django-менеджмент команду `import_{{source_name}}` яка: 1) обчислює SHA256 для `{{file_path}}`; 2) якщо хеш новий — запускає парсер і транзакційно створює `Regulation`, `RegulationDocumentVersion`, `Substance` (upsert за InChIKey) та `SubstanceInRegulation`; 3) підтримує `--dry-run` режим і повертає JSON summary (created/updated/skipped). Надішли приклад коду і коротку інструкцію запуску."

2) SHA256 utility snippet
--
Prompt: "Напиши маленьку функцію `compute_sha256(file_path: str) -> str` на Python, яка читає файл ефективно (chunked) і повертає hex SHA256. Додай короткий приклад використання."

Usage notes
-----------
- Використовуйте `--dry-run` для безпечної перевірки перед реальним імпортом.
