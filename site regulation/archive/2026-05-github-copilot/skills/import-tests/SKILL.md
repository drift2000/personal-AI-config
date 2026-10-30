Import Testing & CI Skill
-------------------------

Purpose
-------
Вимоги до тестування парсерів і імпорту; інтеграція з CI для запуску unit/integration тестів.

Tests
-----
- Unit tests for `parse()` та normalization (edge cases, malformed rows).
- Integration tests for full import flow into disposable Postgres (use `pytest` + `pytest-postgresql` or Docker test container).
- Idempotence test: run importer twice and assert no duplicate versions/records.

CI
--
- Add job to run parser unit tests on push/PR.
- Optional job: run integration tests using a disposable Postgres service or Docker Compose profile.

Dry-run
-------
- Implement `--dry-run` mode in runner to return JSON summary without writing to DB; write tests asserting dry-run leaves DB unchanged.
