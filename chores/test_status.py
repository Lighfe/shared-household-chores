from datetime import date, timedelta

from django.test import SimpleTestCase

from chores.status import Status, get_status


class GetStatusTests(SimpleTestCase):
    def setUp(self):
        self.today = date(2026, 9, 1)

    def test_one_day_before_today_is_overdue(self):
        due_date = self.today - timedelta(days=1)
        self.assertEqual(get_status(due_date, self.today), Status.OVERDUE)

    def test_several_days_before_today_is_overdue(self):
        due_date = self.today - timedelta(days=10)
        self.assertEqual(get_status(due_date, self.today), Status.OVERDUE)

    def test_equal_to_today_is_due_today(self):
        self.assertEqual(get_status(self.today, self.today), Status.DUE_TODAY)

    def test_one_day_after_today_is_upcoming(self):
        due_date = self.today + timedelta(days=1)
        self.assertEqual(get_status(due_date, self.today), Status.UPCOMING)

    def test_several_days_after_today_is_upcoming(self):
        due_date = self.today + timedelta(days=10)
        self.assertEqual(get_status(due_date, self.today), Status.UPCOMING)

    def test_none_due_date_is_no_due_date(self):
        self.assertEqual(get_status(None, self.today), Status.NO_DUE_DATE)

    def test_none_due_date_is_no_due_date_regardless_of_today(self):
        other_today = date(1999, 12, 31)
        self.assertEqual(get_status(None, other_today), Status.NO_DUE_DATE)

    def test_status_values_are_distinct(self):
        values = {
            Status.OVERDUE,
            Status.DUE_TODAY,
            Status.UPCOMING,
            Status.NO_DUE_DATE,
        }
        self.assertEqual(len(values), 4)
