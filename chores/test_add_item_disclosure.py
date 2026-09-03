from django.test import Client, TestCase

from chores.dates import get_today
from chores.models import OneOffTask, RecurringChore

RECURRING_CREATE_URL = "/recurring-chores/add/"
ONE_OFF_CREATE_URL = "/one-off-tasks/add/"


class AddChoreDisclosureTests(TestCase):
    """The add-chore form is collapsed behind a native disclosure (#21)."""

    def setUp(self):
        self.client = Client()
        self.today = get_today()

    def test_home_page_wraps_add_chore_form_in_a_collapsed_details_disclosure(self):
        response = self.client.get("/")
        content = response.content.decode()

        self.assertContains(response, "<details")
        self.assertContains(response, "+ Add chore")
        # Collapsed by default: no `open` attribute on the <details> tag
        # that owns the add-chore form.
        details_start = content.index('<details class="add-item-disclosure"')
        details_tag_end = content.index(">", details_start)
        details_tag = content[details_start:details_tag_end]
        self.assertNotIn("open", details_tag)

    def test_chore_list_remains_visible_alongside_the_disclosure(self):
        RecurringChore.objects.create(
            name="Existing chore", interval_days=7, next_due_date=self.today
        )

        response = self.client.get("/")

        self.assertContains(response, "Existing chore")
        self.assertContains(response, "+ Add chore")

    def test_successful_submission_re_renders_with_the_disclosure_collapsed(self):
        response = self.client.post(
            RECURRING_CREATE_URL,
            {
                "name": "Take out trash",
                "interval_days": "7",
                "next_due_date": self.today.isoformat(),
            },
        )

        content = response.content.decode()
        self.assertContains(response, "Take out trash")
        details_start = content.index('<details class="add-item-disclosure"')
        details_tag_end = content.index(">", details_start)
        details_tag = content[details_start:details_tag_end]
        self.assertNotIn("open", details_tag)

    def test_failed_submission_re_renders_with_the_disclosure_open(self):
        response = self.client.post(
            RECURRING_CREATE_URL,
            {
                "name": "",
                "interval_days": "7",
                "next_due_date": self.today.isoformat(),
            },
        )

        content = response.content.decode()
        self.assertContains(response, "This field is required.")
        details_start = content.index('<details class="add-item-disclosure"')
        details_tag_end = content.index(">", details_start)
        details_tag = content[details_start:details_tag_end]
        self.assertIn("open", details_tag)
        # Entered values are preserved alongside the reopened form.
        self.assertContains(response, 'value="7"')

    def test_disclosure_uses_summary_element_for_native_semantics(self):
        response = self.client.get("/")

        self.assertContains(response, "<summary")
        self.assertContains(response, "</summary>")


class AddTaskDisclosureTests(TestCase):
    """Same collapsed-by-default treatment applies to the add-task form (#21)."""

    def setUp(self):
        self.client = Client()
        self.today = get_today()

    def test_home_page_wraps_add_task_form_in_a_collapsed_details_disclosure(self):
        response = self.client.get("/")
        content = response.content.decode()

        self.assertContains(response, "+ Add task")
        one_off_start = content.index('id="one-off-tasks"')
        details_start = content.index(
            '<details class="add-item-disclosure"', one_off_start
        )
        details_tag_end = content.index(">", details_start)
        details_tag = content[details_start:details_tag_end]
        self.assertNotIn("open", details_tag)

    def test_task_list_remains_visible_alongside_the_disclosure(self):
        OneOffTask.objects.create(name="Existing task", due_date=self.today)

        response = self.client.get("/")

        self.assertContains(response, "Existing task")
        self.assertContains(response, "+ Add task")

    def test_successful_submission_re_renders_with_the_disclosure_collapsed(self):
        response = self.client.post(
            ONE_OFF_CREATE_URL,
            {
                "name": "Return library book",
                "due_date": self.today.isoformat(),
            },
        )

        content = response.content.decode()
        self.assertContains(response, "Return library book")
        details_start = content.index('<details class="add-item-disclosure"')
        details_tag_end = content.index(">", details_start)
        details_tag = content[details_start:details_tag_end]
        self.assertNotIn("open", details_tag)

    def test_failed_submission_re_renders_with_the_disclosure_open(self):
        response = self.client.post(
            ONE_OFF_CREATE_URL,
            {
                "name": "",
                "due_date": self.today.isoformat(),
            },
        )

        content = response.content.decode()
        self.assertContains(response, "This field is required.")
        details_start = content.index('<details class="add-item-disclosure"')
        details_tag_end = content.index(">", details_start)
        details_tag = content[details_start:details_tag_end]
        self.assertIn("open", details_tag)
        self.assertContains(response, f'value="{self.today.isoformat()}"')
