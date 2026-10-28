# Europan recovery audit

## Goal and scope

Establish the recoverable state of the Joomla 5 + `com_cables` project without changing repository code, database state, dependencies, or Docker configuration.

## Verified findings

- Project root: `/home/sined/Projects/site europan.ua new`; project name: `site europan.ua new`.
- Joomla source is version 5.4.10. The site is an uninstalled distribution: `configuration.php` is absent.
- No site or administrator `com_cables` directory, extension manifest, SQL schema/update file, import data file, custom product view, custom template, design source file, Composer project files, PHPUnit configuration, CI configuration, repository agent/skill, brief, ADR, README, or CONTRIBUTING file was found.
- `data/` contains no files, including database snapshots or import sources.
- Git branch `develop` points to the initial commit. An agent checkpoint ref preserves the same baseline source plus Docker files, but contains no catalog component. The only configured remote is `origin` for `drift2000/europan`.
- Docker Compose defines nginx, PHP-FPM, MariaDB, with profile-gated Adminer and MailHog. The PHP 8.3 image installs Composer. No containers are running.

## Work status / next step

Audit complete. Do not begin reconstruction until approval. First recovery phase should preserve the checkpoint, inspect remote history/backups with explicit authorization, and obtain the lost product-page layout and source catalog file before selecting final presentation or import behavior.

## References

- Repository `STRUCTURE.md`
- Repository `docker/docker-compose.yml`
- Repository `docker/php-fpm/Dockerfile.8.3`
- Repository `src/libraries/src/Version.php`
