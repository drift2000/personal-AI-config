# Once-scripts registry

Append-only. Every script in `src/backend/once/` must have an entry here.

---

## import_integration_from_ftp

| Field        | Value                        |
|--------------|------------------------------|
| File         | `src/backend/once/management/commands/import_integration_from_ftp.py` |
| Run date     | 2026-09-14                   |
| Environment  | dev                          |
| Run by       | Denis                        |
| Status       | ✅ Completed                 |

### What it did

Copied all rows from the four legacy `ftp` app tables (`Users`, `UsersS3`,
`UsersOneDrive`, `UsersOther`) into the new unified `integration.Integration`
table, tagging each with its `type`. Read-only against `ftp` — no legacy data
was modified or deleted. Idempotent by `login` (`update_or_create`), so it was
run twice in dev to confirm the second run is a no-op update rather than a
duplicate/error.

### Data affected

| Model                    | Rows affected | Notes                    |
|--------------------------|---------------|--------------------------|
| `integration.Integration`| 226 created (146 ftp, 65 s3, 14 onedrive, 1 other) | 0 skipped_invalid, 0 skipped_conflict |

Verified on a full pass over `ftp.Users` (146/146) that FK fields
(`company`/`manager_contact`/`client_contact`) and `collection`/`type_input`
arrays match the source rows exactly. All 65 `UsersS3.password` values were
already empty in the source table (pre-existing data state, not introduced by
this script).

### Dependencies

Requires `integration` app migrations applied first (`integration.0001_initial`).

### Follow-up tasks

- [ ] Run `python manage.py import_integration_from_ftp` manually on production, after review
- [ ] Add a second entry to this registry for the production run (date, row counts, any anomalies)
- [ ] Decide the fate of the legacy `ftp` app tables/admin/API once the new `integration` block is validated in production

### Can it be re-run?

Yes — it's an upsert keyed by `login`, so re-running is safe and just refreshes
`Integration` rows from the current state of the `ftp` tables. Re-running after
the `ftp` app is deprecated/removed would fail (source models gone), which is
expected and fine at that point.

---
