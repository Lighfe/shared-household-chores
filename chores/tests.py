import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import Client, TestCase

from chores.models import OneOffTask, RecurringChore


class RecurringChoreModelTest(TestCase):
    def test_create_with_all_fields_saves_and_reloads(self):
        chore = RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=datetime.date(2026, 9, 8),
            last_done_date=datetime.date(2026, 9, 1),
        )

        reloaded = RecurringChore.objects.get(pk=chore.pk)

        self.assertEqual(reloaded.name, "Take out trash")
        self.assertEqual(reloaded.interval_days, 7)
        self.assertEqual(reloaded.next_due_date, datetime.date(2026, 9, 8))
        self.assertEqual(reloaded.last_done_date, datetime.date(2026, 9, 1))

    def test_create_without_last_done_date_saves(self):
        chore = RecurringChore.objects.create(
            name="Water plants",
            interval_days=3,
            next_due_date=datetime.date(2026, 9, 4),
        )

        reloaded = RecurringChore.objects.get(pk=chore.pk)

        self.assertIsNone(reloaded.last_done_date)

    def test_interval_days_zero_is_rejected(self):
        chore = RecurringChore(
            name="Invalid interval",
            interval_days=0,
            next_due_date=datetime.date(2026, 9, 4),
        )

        with self.assertRaises(ValidationError):
            chore.full_clean()

    def test_interval_days_negative_is_rejected(self):
        chore = RecurringChore(
            name="Invalid interval",
            interval_days=-1,
            next_due_date=datetime.date(2026, 9, 4),
        )

        with self.assertRaises(ValidationError):
            chore.full_clean()

    def test_name_cannot_be_blank(self):
        chore = RecurringChore(
            name="",
            interval_days=1,
            next_due_date=datetime.date(2026, 9, 4),
        )

        with self.assertRaises(ValidationError):
            chore.full_clean()

    def test_str_returns_name(self):
        chore = RecurringChore(
            name="Take out trash",
            interval_days=7,
            next_due_date=datetime.date(2026, 9, 8),
        )

        self.assertEqual(str(chore), "Take out trash")


class OneOffTaskModelTest(TestCase):
    def test_create_with_due_date_saves_and_reloads(self):
        task = OneOffTask.objects.create(
            name="Return library books",
            due_date=datetime.date(2026, 9, 8),
        )

        reloaded = OneOffTask.objects.get(pk=task.pk)

        self.assertEqual(reloaded.name, "Return library books")
        self.assertEqual(reloaded.due_date, datetime.date(2026, 9, 8))

    def test_create_without_due_date_saves_as_none(self):
        task = OneOffTask.objects.create(name="Clean out the garage")

        reloaded = OneOffTask.objects.get(pk=task.pk)

        self.assertIsNone(reloaded.due_date)

    def test_delete_removes_it_from_the_database(self):
        task = OneOffTask.objects.create(
            name="Fix the leaky faucet",
            due_date=datetime.date(2026, 9, 8),
        )
        task_id = task.pk

        task.delete()

        self.assertFalse(OneOffTask.objects.filter(pk=task_id).exists())

    def test_str_returns_name(self):
        task = OneOffTask(name="Fix the leaky faucet")

        self.assertEqual(str(task), "Fix the leaky faucet")


class SmokeTest(TestCase):
    def test_admin_path_does_not_error(self):
        response = Client().get("/admin/")
        self.assertIn(response.status_code, (200, 302))


class SettingsTest(TestCase):
    def test_time_zone_is_berlin(self):
        self.assertEqual(settings.TIME_ZONE, "Europe/Berlin")

    def test_use_tz_is_disabled(self):
        self.assertFalse(settings.USE_TZ)
