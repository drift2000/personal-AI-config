Import Parser Skill
-------------------

Purpose
-------
Правила розробки парсерів для джерел регулювань. Описує normalized record, обробку неконсистентних даних і контракт `parse()`.

API contract
------------
- Файл: `src/import/<source>/parser.py`
- Функція: `def parse(file_path: str) -> Iterator[NormalizedRecord]`
- `NormalizedRecord` поля: `name`, `inchikey` (optional), `cas` (optional), `restriction_type`, `date_from`, `date_to`, `source_id`, `raw` (original row/json).

Normalization rules
-------------------
- Trim, Unicode NFC normalization, collapse whitespace.
- Case folding for comparisons (store canonical name separately).
- Extract InChIKey if present; якщо ні — залишити `None` і позначити `needs_review`.
- Parse dates to ISO 8601 (`YYYY-MM-DD`) when можливo, і логувати невідомі формати.

Edge cases
----------
- Повторювані записи у файлі: уникати дублювання за поєднанням (`inchikey` || normalized name + cas).
- Часткові рядки — повернути мінімальну структуру і помітити `raw` для діагностики.

Examples
--------
- Тестовий код у `src/import/<source>/tests/test_parser.py` повинен включати приклади повних/часткових/повторних записів.

Operational notes
-----------------
- Парсери мають бути pure functions — не модифікувати БД прямо.
- Документувати в README формат вхідних файлів і приклади.
