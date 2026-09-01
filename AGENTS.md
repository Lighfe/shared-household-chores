Django app for household chores

Documents

- `_docs/process.md` - how work is organized
- `_docs/meta.md` - how these docs grow
- `_docs/manual_testing.md` - how a human testing session turns into groomed issues

Commands

- `uv sync` - install dependencies
- `uv run python manage.py test` - the whole suite
- `uv run python manage.py test chores` - one app's tests
- `uv run python manage.py runserver 0.0.0.0:8000` - run bound to all interfaces for LAN access (see README)

Rules

- Dependencies are added in `pyproject.toml`. Do not add one without asking
- Get "today" via `chores.dates.get_today()`, never `date.today()`/`timezone.now()` directly (host timezone isn't guaranteed to be Europe/Berlin)