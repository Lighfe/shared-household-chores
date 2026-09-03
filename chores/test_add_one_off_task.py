import datetime

from django.test import Client, TestCase
from django.urls import reverse

from chores.dates import get_today
from chores.models import OneOffTask

CREATE_URL = "/one-off-tasks/add/"


class AddOneOffTaskFormPresenceTests(TestCase):
    """The home page carries a visible add-task form (#9)."""

    def setUp(self):
        self.client = Client()

    def test_home_page_includes_add_task_form_with_two_inputs_and_submit(self):
        response = self.client.get("/")
        content = response.content.decode()

        self.assertContains(response, "<form")
        self.assertContains(response, 'name="name"')
        self.assertContains(response, 'name="due_date"')
        self.assertIn('type="submit"', content)

    def test_form_posts_via_htmx_to_create_endpoint(self):
        response = self.client.get("/")

        self.assertContains(response, "hx-post")
        self.assertContains(response, reverse("add_one_off_task"))

    def test_htmx_is_vendored_and_linked(self):
        response = self.client.get("/")

        self.assertContains(response, "chores/js/htmx.min.js")


class AddOneOffTaskCreationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = get_today()

    def test_valid_submission_with_due_date_creates_task(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Return library book",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        self.assertEqual(response.status_code, 200)
        task = OneOffTask.objects.get(name="Return library book")
        self.assertEqual(task.due_date, self.today)

    def test_valid_submission_without_due_date_creates_task_with_no_due_date(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Renew passport",
                "due_date": "",
                "priority": "medium",
            },
        )

        self.assertEqual(response.status_code, 200)
        task = OneOffTask.objects.get(name="Renew passport")
        self.assertIsNone(task.due_date)
        self.assertContains(response, "No due date")

    def test_response_is_the_updated_task_list_partial_not_redirect(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Return library book",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chores/_one_off_tasks_section.html")
        self.assertContains(response, "Return library book")

    def test_first_task_replaces_empty_state_message(self):
        response = self.client.get("/")
        self.assertContains(response, "No one-off tasks yet")

        response = self.client.post(
            CREATE_URL,
            {
                "name": "Return library book",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        self.assertNotContains(response, "No one-off tasks yet")
        self.assertContains(response, "Return library book")

    def test_new_task_appears_in_correctly_sorted_position(self):
        OneOffTask.objects.create(
            name="Overdue task",
            due_date=self.today - datetime.timedelta(days=5),
        )
        OneOffTask.objects.create(
            name="Upcoming task",
            due_date=self.today + datetime.timedelta(days=5),
        )

        response = self.client.post(
            CREATE_URL,
            {
                "name": "Due today task",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        content = response.content.decode()
        overdue_pos = content.index("Overdue task")
        due_today_pos = content.index("Due today task")
        upcoming_pos = content.index("Upcoming task")
        self.assertTrue(overdue_pos < due_today_pos < upcoming_pos)

    def test_successful_submission_returns_a_cleared_empty_form(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Return library book",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        content = response.content.decode()
        # A fresh, unbound form has no `value="..."` populated for the
        # text input -- the previously submitted name must not reappear
        # as the input's value.
        self.assertNotIn('value="Return library book"', content)

    def test_duplicate_name_is_accepted_and_creates_a_second_task(self):
        OneOffTask.objects.create(name="Return library book", due_date=self.today)

        self.client.post(
            CREATE_URL,
            {
                "name": "Return library book",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        self.assertEqual(
            OneOffTask.objects.filter(name="Return library book").count(), 2
        )

    def test_past_due_date_is_accepted_and_shows_as_overdue(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Overdue on creation",
                "due_date": (self.today - datetime.timedelta(days=3)).isoformat(),
                "priority": "medium",
            },
        )

        self.assertTrue(
            OneOffTask.objects.filter(name="Overdue on creation").exists()
        )
        self.assertContains(response, "task--overdue")

    def test_far_future_due_date_is_accepted(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Way out there",
                "due_date": (
                    self.today + datetime.timedelta(days=3650)
                ).isoformat(),
                "priority": "medium",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(OneOffTask.objects.filter(name="Way out there").exists())

    def test_get_to_create_url_does_not_create_a_task(self):
        response = self.client.get(CREATE_URL)

        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(OneOffTask.objects.count(), 0)

    def test_recurring_chore_section_and_form_unaffected(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Return library book",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        self.assertNotContains(response, "recurring-chores")
        self.assertNotContains(response, "add-chore-form")


class AddOneOffTaskValidationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = get_today()

    def test_empty_name_is_rejected_with_error(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        self.assertEqual(OneOffTask.objects.count(), 0)
        self.assertContains(response, "This field is required.")
        self.assertContains(response, f'value="{self.today.isoformat()}"')

    def test_whitespace_only_name_is_rejected(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "   ",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        self.assertEqual(OneOffTask.objects.count(), 0)
        self.assertContains(response, "This field is required.")

    def test_unparseable_due_date_is_rejected_and_preserves_name(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Return library book",
                "due_date": "not-a-date",
                "priority": "medium",
            },
        )

        self.assertEqual(OneOffTask.objects.count(), 0)
        self.assertContains(response, "Enter a valid date.")
        self.assertContains(response, 'value="Return library book"')

    def test_validation_failure_leaves_task_list_unchanged(self):
        OneOffTask.objects.create(name="Existing task", due_date=self.today)

        response = self.client.post(
            CREATE_URL,
            {
                "name": "",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        self.assertEqual(OneOffTask.objects.count(), 1)
        self.assertContains(response, "Existing task")
