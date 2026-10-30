Parser Prompts
==============

1) Parse CSV → NormalizedRecords
--
Prompt: "Розпарси CSV-файл `{{file_path}}` у список NormalizedRecord з полями: `name`, `inchikey` (nullable), `cas` (nullable), `restriction_type`, `date_from`, `date_to`, `source_id`, `raw`. Поверни JSON-масив нормалізованих записів. Якщо рядок неповний — включи поле `raw` із сирим рядком."

Usage notes
-----------
- Підставляйте `{{file_path}}` перед викликом.
- Використовуйте для швидкої валідації форматів і створення тестових наборів даних.
