Import Enrichment Skill
-----------------------

Purpose
-------
Опис підходу до доповнення метаданих (enrichment) — наприклад, інтеграція з PubChem для CAS, смайлсів, синонімів.

Principles
----------
- Enrichment — опціональний, викликається після базового імпорту або як окремий процес.
- Must be idempotent: повторний виклик не має створювати дублей.
- Повинні бути таймаути і retries для мережевих викликів; помилки мають логуватись але не відкатувати основний імпорт.

Implementation notes
--------------------
- Винести клієнт PubChem у `src/import/<source>/enrichment.py` з методом `enrich(substance: Substance) -> dict`.
- Використовувати `httpx` або `requests` з configurable timeout і backoff.
- Зберігати provenance у `Synonym` або `Structure` з полем `source`.

Rate limiting & cost
--------------------
- Повідомити про rate limits у README та використовувати кешування результатів (локальний cache або Redis) для зменшення запитів.
