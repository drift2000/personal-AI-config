# FTP app — API overview

`src/backend/ftp` exposes read-only reporting endpoints over the imported FTP/OneDrive/S3/Other
integration logs, plus one action endpoint that triggers the monthly import scripts. Full schema
is available via Swagger UI at `/api/schema/swagger/` (tags below match the Swagger groupings).

## API endpoints

| Route                              | View                       | Tag           | Purpose                                                        |
| ----------------------------------- | -------------------------- | ------------- | --------------------------------------------------------------- |
| `GET /api/ftp/auth/`                | `AuthViewSet`              | FTP Auth      | History of FTP login/authorization events, filter by `login`     |
| `GET /api/ftp/auth/{id}/`           | `AuthViewSet`              | FTP Auth      | Single authorization event detail                                |
| `GET /api/ftp/download/`            | `DownloadViewSet`          | FTP Download  | History of FTP downloads, filter by `login`                      |
| `GET /api/ftp/download/{id}/`       | `DownloadViewSet`          | FTP Download  | Single download event detail                                     |
| `GET /api/ftp/report/`              | `FTPUsersReportViewSet`    | FTP Report    | FTP users with activity stats; filters: `status`, `collection`, `type_input`, `source`, `company_new` |
| `GET /api/ftp/report/{id}/`         | `FTPUsersReportViewSet`    | FTP Report    | Single FTP user detail                                           |
| `GET /api/ftp/onedrive/`            | `UsersOneDriveViewSet`     | FTP OneDrive  | OneDrive integration users, filter by `company`                  |
| `GET /api/ftp/onedrive/{id}/`       | `UsersOneDriveViewSet`     | FTP OneDrive  | OneDrive user detail                                             |
| `GET /api/ftp/s3/`                  | `UsersS3ViewSet`           | FTP S3        | S3 integration users, filter by `company`                        |
| `GET /api/ftp/s3/{id}/`             | `UsersS3ViewSet`           | FTP S3        | S3 user detail                                                   |
| `GET /api/ftp/other/`               | `UsersOtherViewSet`        | FTP Other     | Other integration users, filter by `company`                     |
| `GET /api/ftp/other/{id}/`          | `UsersOtherViewSet`        | FTP Other     | Other-integration user detail                                    |
| `GET /api/ftp/companies-sources/`   | `CompaniesSourcesView`     | FTP Companies | Companies aggregated across all sources; filters: `source`, `collection`, `type_input` |
| `POST /api/ftp/run-import/{step}/`  | `run_import_step`          | —             | Triggers a monthly import management command (staff-only, see `common.access.staff_tools_required`) |

## Known perf/consistency notes

- `CompaniesSourcesView` aggregates `collection`/`type_input` across four tables. It batches
  one query per table (not per company) — see `_aggregate_collections_by_company` in
  `ftp/api_views.py`. If this view gets noticeably slower again as data grows, that's the
  first place to look.
- Pagination across this app's viewsets uses the shared `common.pagination.DefaultPagination`
  (also used by `download`), so page-size defaults/limits stay consistent across apps.

## Next steps (suggested)

- Document the monthly import flow (file naming, expected columns) per
  `.github/agents/ftp.agent.md`.
- Add a model field table similar to `docs/client/README.md`.
