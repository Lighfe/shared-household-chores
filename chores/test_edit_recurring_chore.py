import datetime

from django.test import Client, TestCase
from django.urls import reverse

from chores.dates import get_today
from chores.models import RecurringChore


def edit_url(chore_id):
    return reverse("edit_recurring_chore", args=[chore_id])


def cancel_url(chore_id):
    return reverse("cancel_edit_recurring_chore", args=[chore_id])


class EditRecurringChoreFormPresenceTests(TestCase):
    """Each row has a visible control that reveals a pre-filled edit form."""

    def setUp(self):
        self.client = Client()
        self.today = get_today()
        self.chore = RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=self.today,
        )

    def test_home_page_row_has_edit_control(self):
        response = self.client.get("/")

        self.assertContains(response, "hx-get")
        self.assertContains(response, edit_url(self.chore.id))

    def test_get_edit_returns_form_prefilled_with_current_values(self):
        response = self.client.get(edit_url(self.chore.id))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chores/_recurring_chore_edit_row.html")
        self.assertContains(response, 'value="Take out trash"')
        self.assertContains(response, 'value="7"')
        self.assertContains(response, 'name="name"')
        self.assertContains(response, 'name="interval_days"')

    def test_get_edit_does_not_modify_the_chore(self):
        self.client.get(edit_url(self.chore.id))

        self.chore.refresh_from_db()
        self.assertEqual(self.chore.name, "Take out trash")
        self.assertEqual(self.chore.interval_days, 7)

    def test_edit_form_posts_via_htmx_to_the_edit_endpoint(self):
        response = self.client.get(edit_url(self.chore.id))

        self.assertContains(response, "hx-post")
        self.assertContains(response, edit_url(self.chore.id))

    def test_get_edit_of_missing_chore_returns_404(self):
        response = self.client.get(edit_url(999999))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(RecurringChore.objects.count(), 1)


class EditRecurringChoreSaveTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = get_today()
        self.chore = RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=self.today,
            last_done_date=self.today - datetime.timedelta(days=7),
        )

    def test_valid_submission_updates_name_and_interval(self):
        response = self.client.post(
            edit_url(self.chore.id),
            {"name": "Take out recycling", "interval_days": "14"},
        )

        self.assertEqual(response.status_code, 200)
        self.chore.refresh_from_db()
        self.assertEqual(self.chore.name, "Take out recycling")
        self.assertEqual(self.chore.interval_days, 14)

    def test_editing_interval_does_not_change_next_due_date_or_last_done_date(self):
        original_next_due = self.chore.next_due_date
        original_last_done = self.chore.last_done_date

        self.client.post(
            edit_url(self.chore.id),
            {"name": "Take out trash", "interval_days": "30"},
        )

        self.chore.refresh_from_db()
        self.assertEqual(self.chore.next_due_date, original_next_due)
        self.assertEqual(self.chore.last_done_date, original_last_done)

    def test_response_is_the_updated_row_partial_not_redirect(self):
        response = self.client.post(
            edit_url(self.chore.id),
            {"name": "Take out recycling", "interval_days": "14"},
        )

        self.assertTemplateUsed(response, "chores/_recurring_chore_row.html")
        self.assertContains(response, "Take out recycling")

    def test_successful_edit_keeps_sort_position_by_unchanged_next_due_date(self):
        RecurringChore.objects.create(
            name="Overdue chore",
            interval_days=5,
            next_due_date=self.today - datetime.timedelta(days=5),
        )
        RecurringChore.objects.create(
            name="Upcoming chore",
            interval_days=5,
            next_due_date=self.today + datetime.timedelta(days=5),
        )

        response = self.client.get("/")
        content = response.content.decode()
        overdue_pos = content.index("Overdue chore")
        due_today_pos = content.index("Take out trash")
        upcoming_pos = content.index("Upcoming chore")
        self.assertTrue(overdue_pos < due_today_pos < upcoming_pos)

    def test_duplicate_name_is_accepted(self):
        RecurringChore.objects.create(
            name="Existing chore",
            interval_days=3,
            next_due_date=self.today,
        )

        response = self.client.post(
            edit_url(self.chore.id),
            {"name": "Existing chore", "interval_days": "7"},
        )

        self.assertEqual(response.status_code, 200)
        self.chore.refresh_from_db()
        self.assertEqual(self.chore.name, "Existing chore")
        self.assertEqual(
            RecurringChore.objects.filter(name="Existing chore").count(), 2
        )

    def test_submitting_unchanged_values_succeeds_as_a_no_op(self):
        response = self.client.post(
            edit_url(self.chore.id),
            {"name": "Take out trash", "interval_days": "7"},
        )

        self.assertEqual(response.status_code, 200)
        self.chore.refresh_from_db()
        self.assertEqual(self.chore.name, "Take out trash")
        self.assertEqual(self.chore.interval_days, 7)

    def test_get_to_edit_url_does_not_modify_the_chore(self):
        response = self.client.get(edit_url(self.chore.id))

        self.assertNotEqual(response.status_code, 405)
        self.chore.refresh_from_db()
        self.assertEqual(self.chore.name, "Take out trash")
        self.assertEqual(self.chore.interval_days, 7)

    def test_post_to_missing_chore_returns_404_and_creates_nothing(self):
        response = self.client.post(
            edit_url(999999),
            {"name": "Ghost chore", "interval_days": "7"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(RecurringChore.objects.filter(name="Ghost chore").exists())
        self.assertEqual(RecurringChore.objects.count(), 1)

    def test_editing_twice_in_a_row_shows_fresh_values_second_time(self):
        self.client.post(
            edit_url(self.chore.id),
            {"name": "First edit", "interval_days": "10"},
        )

        response = self.client.get(edit_url(self.chore.id))

        self.assertContains(response, 'value="First edit"')
        self.assertContains(response, 'value="10"')
        self.assertNotContains(response, 'value="Take out trash"')


class EditRecurringChoreValidationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = get_today()
        self.chore = RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=self.today,
        )

    def test_empty_name_is_rejected_and_preserves_interval(self):
        response = self.client.post(
            edit_url(self.chore.id),
            {"name": "", "interval_days": "14"},
        )

        self.chore.refresh_from_db()
        self.assertEqual(self.chore.name, "Take out trash")
        self.assertEqual(self.chore.interval_days, 7)
        self.assertContains(response, "This field is required.")
        self.assertContains(response, 'value="14"')
        self.assertTemplateUsed(response, "chores/_recurring_chore_edit_row.html")

    def test_blank_interval_is_rejected_and_preserves_name(self):
        response = self.client.post(
            edit_url(self.chore.id),
            {"name": "New name", "interval_days": ""},
        )

        self.chore.refresh_from_db()
        self.assertEqual(self.chore.name, "Take out trash")
        self.assertEqual(self.chore.interval_days, 7)
        self.assertContains(response, "This field is required.")
        self.assertContains(response, 'value="New name"')

    def test_zero_interval_is_rejected(self):
        response = self.client.post(
            edit_url(self.chore.id),
            {"name": "New name", "interval_days": "0"},
        )

        self.chore.refresh_from_db()
        self.assertEqual(self.chore.interval_days, 7)
        self.assertEqual(response.status_code, 200)

    def test_negative_interval_is_rejected(self):
        response = self.client.post(
            edit_url(self.chore.id),
            {"name": "New name", "interval_days": "-3"},
        )

        self.chore.refresh_from_db()
        self.assertEqual(self.chore.interval_days, 7)
        self.assertEqual(response.status_code, 200)

    def test_non_numeric_interval_is_rejected(self):
        response = self.client.post(
            edit_url(self.chore.id),
            {"name": "New name", "interval_days": "abc"},
        )

        self.chore.refresh_from_db()
        self.assertEqual(self.chore.interval_days, 7)
        self.assertContains(response, "Enter a whole number.")


class CancelEditRecurringChoreTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = get_today()
        self.chore = RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=self.today,
        )

    def test_cancel_returns_the_view_mode_row_without_saving(self):
        response = self.client.get(cancel_url(self.chore.id))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chores/_recurring_chore_row.html")
        self.assertContains(response, "Take out trash")

    def test_cancel_discards_any_typed_changes(self):
        # Simulate the user having typed into the edit form (never posted).
        self.client.get(edit_url(self.chore.id))

        response = self.client.get(cancel_url(self.chore.id))

        self.chore.refresh_from_db()
        self.assertEqual(self.chore.name, "Take out trash")
        self.assertEqual(self.chore.interval_days, 7)
        self.assertContains(response, "Take out trash")

    def test_cancel_of_missing_chore_returns_404(self):
        response = self.client.get(cancel_url(999999))

        self.assertEqual(response.status_code, 404)

    def test_cancel_only_accepts_get(self):
        response = self.client.post(cancel_url(self.chore.id))

        self.assertEqual(response.status_code, 405)
