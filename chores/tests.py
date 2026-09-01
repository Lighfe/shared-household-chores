import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import Client, TestCase

from chores.dates import get_today
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


class MarkRecurringChoreDoneTests(TestCase):
    """Mark-done endpoint for a RecurringChore (#10)."""

    def setUp(self):
        self.client = Client()
        self.today = get_today()

    def _mark_done_url(self, chore_id):
        return f"/recurring-chores/{chore_id}/mark-done/"

    def test_get_request_does_not_change_anything(self):
        chore = RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=self.today,
        )

        response = self.client.get(self._mark_done_url(chore.pk))

        self.assertNotEqual(response.status_code, 200)
        chore.refresh_from_db()
        self.assertEqual(chore.next_due_date, self.today)
        self.assertIsNone(chore.last_done_date)

    def test_marking_nonexistent_chore_returns_404_and_does_not_error(self):
        response = self.client.post(self._mark_done_url(999999))

        self.assertEqual(response.status_code, 404)

    def test_valid_post_sets_last_done_date_to_today(self):
        chore = RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=self.today,
        )

        self.client.post(self._mark_done_url(chore.pk))

        chore.refresh_from_db()
        self.assertEqual(chore.last_done_date, self.today)

    def test_next_due_date_advances_by_interval_from_its_previous_value(self):
        old_next_due_date = self.today - datetime.timedelta(days=1)
        chore = RecurringChore.objects.create(
            name="Overdue chore",
            interval_days=7,
            next_due_date=old_next_due_date,
        )

        self.client.post(self._mark_done_url(chore.pk))

        chore.refresh_from_db()
        self.assertEqual(
            chore.next_due_date,
            old_next_due_date + datetime.timedelta(days=7),
        )
        # A late completion does not snap to "today + interval_days".
        self.assertNotEqual(
            chore.next_due_date, self.today + datetime.timedelta(days=7)
        )

    def test_far_overdue_chore_advances_by_exactly_one_interval_not_caught_up(self):
        old_next_due_date = self.today - datetime.timedelta(days=100)
        chore = RecurringChore.objects.create(
            name="Very overdue chore",
            interval_days=7,
            next_due_date=old_next_due_date,
        )

        self.client.post(self._mark_done_url(chore.pk))

        chore.refresh_from_db()
        # Exactly one interval added from the previous next_due_date --
        # not looped forward to catch up to today or beyond.
        self.assertEqual(
            chore.next_due_date,
            old_next_due_date + datetime.timedelta(days=7),
        )
        self.assertLess(chore.next_due_date, self.today)

    def test_marking_done_twice_in_a_row_advances_next_due_date_only_once(self):
        # Same-day no-op guard (#17): two back-to-back same-day POSTs
        # (double-tap/retry) are treated as one completion event, since
        # interval_days is always a whole number of days and a chore can
        # only meaningfully complete once per calendar day. This supersedes
        # #10's original test, which asserted the due date advanced twice.
        old_next_due_date = self.today - datetime.timedelta(days=1)
        chore = RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=old_next_due_date,
        )

        self.client.post(self._mark_done_url(chore.pk))
        chore.refresh_from_db()
        after_first = chore.next_due_date
        self.assertEqual(after_first, old_next_due_date + datetime.timedelta(days=7))

        self.client.post(self._mark_done_url(chore.pk))
        chore.refresh_from_db()

        self.assertEqual(chore.next_due_date, after_first)
        self.assertEqual(chore.last_done_date, self.today)

    def test_second_same_day_post_returns_the_current_row_unchanged(self):
        old_next_due_date = self.today - datetime.timedelta(days=1)
        chore = RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=old_next_due_date,
        )

        self.client.post(self._mark_done_url(chore.pk))
        chore.refresh_from_db()
        after_first = chore.next_due_date

        response = self.client.post(self._mark_done_url(chore.pk))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chores/_recurring_chore_row.html")
        content = response.content.decode()
        self.assertIn(after_first.isoformat(), content)

    def test_mark_done_on_a_later_day_advances_normally_after_a_same_day_noop(self):
        # A genuine new completion on a later day (last_done_date is not
        # today) must not be blocked by the same-day guard.
        old_next_due_date = self.today - datetime.timedelta(days=1)
        chore = RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=old_next_due_date,
        )

        self.client.post(self._mark_done_url(chore.pk))
        chore.refresh_from_db()
        after_first = chore.next_due_date

        # Simulate the next calendar day: last_done_date is no longer today.
        chore.last_done_date = self.today - datetime.timedelta(days=1)
        chore.save()

        self.client.post(self._mark_done_url(chore.pk))
        chore.refresh_from_db()

        self.assertEqual(
            chore.next_due_date, after_first + datetime.timedelta(days=7)
        )
        self.assertEqual(chore.last_done_date, self.today)

    def test_response_is_the_row_partial_with_updated_fields(self):
        chore = RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=self.today,
        )

        response = self.client.post(self._mark_done_url(chore.pk))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chores/_recurring_chore_row.html")
        self.assertTemplateNotUsed(response, "chores/home.html")
        self.assertTemplateNotUsed(response, "chores/_recurring_chores_section.html")
        content = response.content.decode()
        self.assertIn("Take out trash", content)
        self.assertIn(self.today.isoformat(), content)
        self.assertIn(
            (self.today + datetime.timedelta(days=7)).isoformat(), content
        )
        self.assertIn("chore--upcoming", content)

    def test_response_reflects_status_of_the_new_next_due_date(self):
        # interval_days=1 and next_due_date already today -> after marking
        # done, the new next_due_date is tomorrow -> status "upcoming".
        chore = RecurringChore.objects.create(
            name="Water plants",
            interval_days=1,
            next_due_date=self.today,
        )

        response = self.client.post(self._mark_done_url(chore.pk))

        self.assertContains(response, "chore--upcoming")
        self.assertNotContains(response, "chore--overdue")
        self.assertNotContains(response, "chore--due_today")


class MarkOneOffTaskDoneTests(TestCase):
    """Mark-done (hard delete) endpoint for a OneOffTask (#11)."""

    def setUp(self):
        self.client = Client()
        self.today = get_today()

    def _done_url(self, task_id):
        return f"/one-off-tasks/{task_id}/done/"

    def test_get_request_does_not_delete_anything(self):
        task = OneOffTask.objects.create(
            name="Return library book", due_date=self.today
        )

        response = self.client.get(self._done_url(task.pk))

        self.assertNotEqual(response.status_code, 200)
        self.assertTrue(OneOffTask.objects.filter(pk=task.pk).exists())

    def test_valid_post_deletes_the_task(self):
        task = OneOffTask.objects.create(
            name="Return library book", due_date=self.today
        )

        response = self.client.post(self._done_url(task.pk))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(OneOffTask.objects.filter(pk=task.pk).exists())

    def test_response_is_the_section_partial_without_the_deleted_task(self):
        task = OneOffTask.objects.create(
            name="Return library book", due_date=self.today
        )
        OneOffTask.objects.create(name="Renew passport", due_date=None)

        response = self.client.post(self._done_url(task.pk))

        self.assertTemplateUsed(response, "chores/_one_off_tasks_section.html")
        self.assertTemplateNotUsed(response, "chores/home.html")
        content = response.content.decode()
        self.assertNotIn("Return library book", content)
        self.assertIn("Renew passport", content)

    def test_recurring_chore_section_is_unaffected(self):
        RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=self.today,
        )
        task = OneOffTask.objects.create(
            name="Return library book", due_date=self.today
        )

        self.client.post(self._done_url(task.pk))
        response = self.client.get("/")

        self.assertContains(response, "Take out trash")

    def test_posting_twice_for_the_same_task_does_not_error(self):
        task = OneOffTask.objects.create(
            name="Return library book", due_date=self.today
        )

        first_response = self.client.post(self._done_url(task.pk))
        second_response = self.client.post(self._done_url(task.pk))

        self.assertEqual(first_response.status_code, 200)
        self.assertIn(second_response.status_code, (200, 404))
        self.assertFalse(OneOffTask.objects.filter(pk=task.pk).exists())

    def test_posting_for_a_never_existed_id_does_not_error(self):
        response = self.client.post(self._done_url(999999))

        self.assertIn(response.status_code, (200, 404))


class CancelOneOffTaskTests(TestCase):
    """Cancel/remove (hard delete) endpoint for a OneOffTask (#18).

    Split out from #11: same idempotent hard-delete data behavior as
    mark-done, but a distinct endpoint/control -- see
    `_docs/decisions.md` ("Cancelling a one-off task is a distinct action
    from completing it").
    """

    def setUp(self):
        self.client = Client()
        self.today = get_today()

    def _cancel_url(self, task_id):
        return f"/one-off-tasks/{task_id}/cancel/"

    def _done_url(self, task_id):
        return f"/one-off-tasks/{task_id}/done/"

    def test_get_request_does_not_delete_anything(self):
        task = OneOffTask.objects.create(
            name="Return library book", due_date=self.today
        )

        response = self.client.get(self._cancel_url(task.pk))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(OneOffTask.objects.filter(pk=task.pk).exists())

    def test_valid_post_deletes_the_task(self):
        task = OneOffTask.objects.create(
            name="Return library book", due_date=self.today
        )

        response = self.client.post(self._cancel_url(task.pk))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(OneOffTask.objects.filter(pk=task.pk).exists())

    def test_response_is_the_section_partial_without_the_cancelled_task(self):
        task = OneOffTask.objects.create(
            name="Return library book", due_date=self.today
        )
        OneOffTask.objects.create(name="Renew passport", due_date=None)

        response = self.client.post(self._cancel_url(task.pk))

        self.assertTemplateUsed(response, "chores/_one_off_tasks_section.html")
        self.assertTemplateNotUsed(response, "chores/home.html")
        content = response.content.decode()
        self.assertNotIn("Return library book", content)
        self.assertIn("Renew passport", content)

    def test_recurring_chore_section_is_unaffected(self):
        RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=self.today,
        )
        task = OneOffTask.objects.create(
            name="Return library book", due_date=self.today
        )

        self.client.post(self._cancel_url(task.pk))
        response = self.client.get("/")

        self.assertContains(response, "Take out trash")

    def test_cancelling_one_task_does_not_affect_marking_another_done(self):
        cancel_task = OneOffTask.objects.create(
            name="Return library book", due_date=self.today
        )
        done_task = OneOffTask.objects.create(
            name="Renew passport", due_date=self.today
        )

        self.client.post(self._cancel_url(cancel_task.pk))
        response = self.client.post(self._done_url(done_task.pk))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(OneOffTask.objects.filter(pk=cancel_task.pk).exists())
        self.assertFalse(OneOffTask.objects.filter(pk=done_task.pk).exists())

    def test_cancelling_the_only_task_shows_empty_state(self):
        task = OneOffTask.objects.create(
            name="Return library book", due_date=self.today
        )

        response = self.client.post(self._cancel_url(task.pk))

        self.assertContains(response, "No one-off tasks yet.")
        self.assertNotContains(response, "<ul class=\"task-list\">")

    def test_posting_twice_for_the_same_task_does_not_error(self):
        task = OneOffTask.objects.create(
            name="Return library book", due_date=self.today
        )

        first_response = self.client.post(self._cancel_url(task.pk))
        second_response = self.client.post(self._cancel_url(task.pk))

        self.assertEqual(first_response.status_code, 200)
        self.assertIn(second_response.status_code, (200, 404))
        self.assertFalse(OneOffTask.objects.filter(pk=task.pk).exists())

    def test_posting_for_a_never_existed_id_does_not_error(self):
        response = self.client.post(self._cancel_url(999999))

        self.assertIn(response.status_code, (200, 404))

    def test_csrf_protection_is_enforced(self):
        task = OneOffTask.objects.create(
            name="Return library book", due_date=self.today
        )
        csrf_client = Client(enforce_csrf_checks=True)

        response = csrf_client.post(self._cancel_url(task.pk))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(OneOffTask.objects.filter(pk=task.pk).exists())


class SmokeTest(TestCase):
    def test_admin_path_does_not_error(self):
        response = Client().get("/admin/")
        self.assertIn(response.status_code, (200, 302))


class SettingsTest(TestCase):
    def test_time_zone_is_berlin(self):
        self.assertEqual(settings.TIME_ZONE, "Europe/Berlin")

    def test_use_tz_is_disabled(self):
        self.assertFalse(settings.USE_TZ)
