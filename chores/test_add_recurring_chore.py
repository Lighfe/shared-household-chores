import datetime

from django.test import Client, TestCase
from django.urls import reverse

from chores.dates import get_today
from chores.models import RecurringChore

CREATE_URL = "/recurring-chores/add/"


class AddRecurringChoreFormPresenceTests(TestCase):
    """The home page carries a visible add-chore form (#8)."""

    def setUp(self):
        self.client = Client()

    def test_home_page_includes_add_chore_form_with_three_inputs_and_submit(self):
        response = self.client.get("/")
        content = response.content.decode()

        self.assertContains(response, "<form")
        self.assertContains(response, 'name="name"')
        self.assertContains(response, 'name="interval_days"')
        self.assertContains(response, 'name="next_due_date"')
        self.assertIn('type="submit"', content)

    def test_form_posts_via_htmx_to_create_endpoint(self):
        response = self.client.get("/")

        self.assertContains(response, "hx-post")
        self.assertContains(response, reverse("add_recurring_chore"))

    def test_htmx_is_vendored_and_linked(self):
        response = self.client.get("/")

        self.assertContains(response, "chores/js/htmx.min.js")


class AddRecurringChoreCreationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = get_today()

    def test_valid_submission_creates_chore_with_next_due_date_and_no_last_done(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Take out trash",
                "interval_days": "7",
                "next_due_date": self.today.isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        chore = RecurringChore.objects.get(name="Take out trash")
        self.assertEqual(chore.interval_days, 7)
        self.assertEqual(chore.next_due_date, self.today)
        self.assertIsNone(chore.last_done_date)

    def test_response_is_the_updated_chore_list_partial_not_redirect(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Take out trash",
                "interval_days": "7",
                "next_due_date": self.today.isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chores/_recurring_chores_section.html")
        self.assertContains(response, "Take out trash")

    def test_new_chore_appears_in_correctly_sorted_position(self):
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

        response = self.client.post(
            CREATE_URL,
            {
                "name": "Due today chore",
                "interval_days": "7",
                "next_due_date": self.today.isoformat(),
            },
        )

        content = response.content.decode()
        overdue_pos = content.index("Overdue chore")
        due_today_pos = content.index("Due today chore")
        upcoming_pos = content.index("Upcoming chore")
        self.assertTrue(overdue_pos < due_today_pos < upcoming_pos)

    def test_successful_submission_returns_a_cleared_empty_form(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Take out trash",
                "interval_days": "7",
                "next_due_date": self.today.isoformat(),
            },
        )

        content = response.content.decode()
        # A fresh, unbound form has no `value="..."` populated for the
        # text input -- the previously submitted name must not reappear
        # as the input's value.
        self.assertNotIn('value="Take out trash"', content)

    def test_duplicate_name_is_accepted_and_creates_a_second_chore(self):
        RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=self.today,
        )

        self.client.post(
            CREATE_URL,
            {
                "name": "Take out trash",
                "interval_days": "3",
                "next_due_date": self.today.isoformat(),
            },
        )

        self.assertEqual(
            RecurringChore.objects.filter(name="Take out trash").count(), 2
        )

    def test_past_initial_due_date_is_accepted_and_shows_as_overdue(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Overdue on creation",
                "interval_days": "7",
                "next_due_date": (
                    self.today - datetime.timedelta(days=3)
                ).isoformat(),
            },
        )

        self.assertTrue(
            RecurringChore.objects.filter(name="Overdue on creation").exists()
        )
        self.assertContains(response, "chore--overdue")

    def test_far_future_initial_due_date_is_accepted(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Way out there",
                "interval_days": "7",
                "next_due_date": (
                    self.today + datetime.timedelta(days=3650)
                ).isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            RecurringChore.objects.filter(name="Way out there").exists()
        )

    def test_get_to_create_url_does_not_create_a_chore(self):
        response = self.client.get(CREATE_URL)

        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(RecurringChore.objects.count(), 0)


class AddRecurringChoreValidationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = get_today()

    def test_empty_name_is_rejected_with_error_and_preserves_other_fields(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "",
                "interval_days": "7",
                "next_due_date": self.today.isoformat(),
            },
        )

        self.assertEqual(RecurringChore.objects.count(), 0)
        self.assertContains(response, "This field is required.")
        self.assertContains(response, 'value="7"')
        self.assertContains(response, f'value="{self.today.isoformat()}"')

    def test_blank_interval_is_rejected_and_preserves_other_fields(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Take out trash",
                "interval_days": "",
                "next_due_date": self.today.isoformat(),
            },
        )

        self.assertEqual(RecurringChore.objects.count(), 0)
        self.assertContains(response, "This field is required.")
        self.assertContains(response, 'value="Take out trash"')

    def test_zero_interval_is_rejected(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Take out trash",
                "interval_days": "0",
                "next_due_date": self.today.isoformat(),
            },
        )

        self.assertEqual(RecurringChore.objects.count(), 0)
        self.assertEqual(response.status_code, 200)

    def test_negative_interval_is_rejected(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Take out trash",
                "interval_days": "-3",
                "next_due_date": self.today.isoformat(),
            },
        )

        self.assertEqual(RecurringChore.objects.count(), 0)
        self.assertEqual(response.status_code, 200)

    def test_non_numeric_interval_is_rejected(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Take out trash",
                "interval_days": "abc",
                "next_due_date": self.today.isoformat(),
            },
        )

        self.assertEqual(RecurringChore.objects.count(), 0)
        self.assertContains(response, "Enter a whole number.")

    def test_blank_due_date_is_rejected_and_preserves_other_fields(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Take out trash",
                "interval_days": "7",
                "next_due_date": "",
            },
        )

        self.assertEqual(RecurringChore.objects.count(), 0)
        self.assertContains(response, "This field is required.")
        self.assertContains(response, 'value="Take out trash"')
        self.assertContains(response, 'value="7"')

    def test_unparseable_due_date_is_rejected(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Take out trash",
                "interval_days": "7",
                "next_due_date": "not-a-date",
            },
        )

        self.assertEqual(RecurringChore.objects.count(), 0)
        self.assertContains(response, "Enter a valid date.")
