Import Runner Skill
-------------------

Purpose
-------
Опис транзакційного імпортного процесу: перевірка checksum, версіонування документів, створення/оновлення моделей у БД.

Key steps
---------
1. Compute checksum (SHA256) for source file.
2. If checksum exists for `RegulationDocumentVersion` — skip import (metric `no_changes`).
3. Begin DB transaction:
   - Create or update `Regulation`.
   - Create `RegulationDocumentVersion` with `path`, `hash`, `is_current`.
   - For each `NormalizedRecord`: find or create `Substance` by `InChIKey`; if missing — create with `status=needs_review`.
   - Upsert `SubstanceInRegulation` records and set appropriate statuses.
4. Commit transaction; produce JSON summary of counts and errors.

Idempotence rules
-----------------
- Use deterministic keys (InChIKey) and `ON CONFLICT`/upsert semantics.
- Never delete historical versions; toggle `is_current` flags.

Failure handling
----------------
- If enrichment fails, do not rollback the import; record enrichment_failures in summary and continue.
- For DB errors, roll back transaction and surface error for investigation.

CLI/Runner
----------
- Provide `scripts/import_runner.py --source <name> --file <path> [--dry-run]` that runs parse→import and emits JSON summary.
