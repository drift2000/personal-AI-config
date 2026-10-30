"""
Backend logging snippets for Django management commands and scripts.

Use the shared backend logging implementation from `src/backend/common/command_logger.py`.
When creating new backend files that need logging, start from this template and
reuse the common logger helpers instead of introducing custom logging logic.

Usage:
  - Add `logger = logging.getLogger(__name__)` at module level.
  - Use structured `extra` keys: `company_id`, `user_id`, `user_email`, `source_file`, `row_id`, `matrix_id`.

Example management command pattern:

```py
import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync companies from external source'

    def handle(self, *args, **options):
        logger.info('sync_companies.started', extra={'task': 'sync_companies'})
        try:
            # perform work
            processed = 0
            # on success
            logger.info('sync_companies.completed', extra={'processed': processed})
        except Exception as e:
            logger.exception('sync_companies.failed', extra={'error': str(e)})
            raise
```

Minimal logging configuration (for `settings.py`) to enable JSON output with `python-json-logger`:

```py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'fmt': '%(asctime)s %(levelname)s %(name)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    }
}
```

Notes:
- Prefer `logger.info()` / `logger.warning()` / `logger.exception()` over `print()` in scripts.
- Keep log messages short and use `extra` for structured metadata used by log aggregators.
"""
