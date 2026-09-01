"""Single shared source of "today" for the whole app.

`USE_TZ = False` in `config/settings.py`, which means Django's own
`django.utils.timezone.now()` falls back to plain `datetime.datetime.now()`
-- a naive datetime in whatever timezone the host OS/container happens to be
configured with, not necessarily `settings.TIME_ZONE`. Likewise, raw
`datetime.date.today()` is host-timezone-dependent.

`get_today()` instead asks for "now" directly in `settings.TIME_ZONE`
(Europe/Berlin), so the resulting date is correct for Europe/Berlin no
matter what timezone the host process is running in.

Every call site that needs "today" for status checks, due-date defaults, or
recording a completion date should import and use `get_today()` from here
rather than computing its own date.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.conf import settings


def get_today() -> date:
    """Return today's date in the app's configured timezone.

    Correct for Europe/Berlin regardless of the host OS/container's local
    timezone setting.
    """
    tz = ZoneInfo(settings.TIME_ZONE)
    return datetime.now(tz).date()
