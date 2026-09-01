from datetime import date, datetime, timezone
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase

from chores.dates import get_today


def _fixed_datetime(fixed_utc_instant):
    """Build a datetime subclass whose .now(tz) always reports the given
    fixed UTC instant, converted into whatever tz is requested -- exactly
    like the real `datetime.now(tz)`, but with a controlled "current
    moment" instead of the real host clock."""

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return fixed_utc_instant.replace(tzinfo=None)
            return fixed_utc_instant.astimezone(tz)

    return FixedDatetime


class GetTodayTests(SimpleTestCase):
    def test_berlin_date_ahead_of_utc_date_in_winter(self):
        # 23:30 UTC on Jan 15 is already 00:30 on Jan 16 in Europe/Berlin
        # (UTC+1 in winter). A host running in UTC would compute Jan 15 for
        # "today" -- the correct Europe/Berlin answer is Jan 16.
        fixed_utc_instant = datetime(2026, 1, 15, 23, 30, tzinfo=timezone.utc)

        with patch("chores.dates.datetime", _fixed_datetime(fixed_utc_instant)):
            result = get_today()

        self.assertEqual(result, date(2026, 1, 16))

    def test_berlin_date_ahead_of_utc_date_during_summer_dst(self):
        # 22:30 UTC on Jun 15 is 00:30 on Jun 16 in Europe/Berlin (UTC+2
        # during DST). A UTC-configured host would compute Jun 15.
        fixed_utc_instant = datetime(2026, 6, 15, 22, 30, tzinfo=timezone.utc)

        with patch("chores.dates.datetime", _fixed_datetime(fixed_utc_instant)):
            result = get_today()

        self.assertEqual(result, date(2026, 6, 16))

    def test_berlin_date_behind_a_host_far_east_of_utc(self):
        # 01:30 in a UTC+14 host timezone (e.g. Pacific/Kiritimati) on
        # Mar 2 is still Mar 1, 12:30 UTC, which is Mar 1, 13:30 in
        # Europe/Berlin (UTC+1). A host running in that far-eastern
        # timezone would already report Mar 2 -- the correct Europe/Berlin
        # answer is still Mar 1.
        fixed_utc_instant = datetime(2026, 3, 1, 12, 30, tzinfo=timezone.utc)
        host_local_date = fixed_utc_instant.astimezone(
            ZoneInfo("Pacific/Kiritimati")
        ).date()
        self.assertEqual(host_local_date, date(2026, 3, 2))

        with patch("chores.dates.datetime", _fixed_datetime(fixed_utc_instant)):
            result = get_today()

        self.assertEqual(result, date(2026, 3, 1))

    def test_matches_direct_zoneinfo_conversion(self):
        # Sanity check against an independent computation, without mocking.
        expected = datetime.now(ZoneInfo("Europe/Berlin")).date()
        self.assertEqual(get_today(), expected)

    def test_uses_configured_time_zone_setting(self):
        # get_today() must read settings.TIME_ZONE rather than hardcoding
        # "Europe/Berlin", so it stays correct if the setting ever changes.
        fixed_utc_instant = datetime(2026, 1, 1, 23, 0, tzinfo=timezone.utc)

        with patch("chores.dates.datetime", _fixed_datetime(fixed_utc_instant)):
            with self.settings(TIME_ZONE="Pacific/Kiritimati"):
                result = get_today()

        # UTC+14: 2026-01-01 23:00 UTC -> 2026-01-02 13:00.
        self.assertEqual(result, date(2026, 1, 2))
