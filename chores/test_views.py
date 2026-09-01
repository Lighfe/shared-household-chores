import datetime

from django.test import Client, TestCase

from chores.dates import get_today
from chores.models import RecurringChore


class HomeViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = get_today()

    def test_returns_200_and_renders_home_template(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chores/home.html")

    def test_empty_state_message_when_no_chores(self):
        response = self.client.get("/")

        self.assertContains(response, "No recurring chores yet")

    def test_each_chore_appears_exactly_once(self):
        RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=self.today,
        )
        RecurringChore.objects.create(
            name="Water plants",
            interval_days=3,
            next_due_date=self.today + datetime.timedelta(days=2),
        )

        response = self.client.get("/")

        self.assertEqual(response.content.decode().count("Take out trash"), 1)
        self.assertEqual(response.content.decode().count("Water plants"), 1)

    def test_shows_name_next_due_last_done_and_status(self):
        RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=self.today - datetime.timedelta(days=1),
            last_done_date=self.today - datetime.timedelta(days=8),
        )

        response = self.client.get("/")
        content = response.content.decode()

        self.assertIn("Take out trash", content)
        self.assertIn((self.today - datetime.timedelta(days=1)).isoformat(), content)
        self.assertIn((self.today - datetime.timedelta(days=8)).isoformat(), content)
        self.assertIn("overdue", content)

    def test_never_done_chore_shows_never_placeholder(self):
        RecurringChore.objects.create(
            name="Deep clean fridge",
            interval_days=30,
            next_due_date=self.today + datetime.timedelta(days=10),
        )

        response = self.client.get("/")

        self.assertContains(response, "Never")
        self.assertNotContains(response, ">None<")

    def test_ordering_overdue_before_due_today_before_upcoming(self):
        upcoming = RecurringChore.objects.create(
            name="Upcoming chore",
            interval_days=5,
            next_due_date=self.today + datetime.timedelta(days=5),
        )
        overdue = RecurringChore.objects.create(
            name="Overdue chore",
            interval_days=5,
            next_due_date=self.today - datetime.timedelta(days=5),
        )
        due_today = RecurringChore.objects.create(
            name="Due today chore",
            interval_days=5,
            next_due_date=self.today,
        )

        response = self.client.get("/")
        chores = list(response.context["chores"])

        names_in_order = [c["name"] for c in chores]
        self.assertEqual(
            names_in_order,
            ["Overdue chore", "Due today chore", "Upcoming chore"],
        )
        # sanity: created objects are used (avoid unused-variable lint noise)
        self.assertTrue(upcoming.pk and overdue.pk and due_today.pk)

    def test_ordering_within_status_group_by_next_due_date_ascending(self):
        RecurringChore.objects.create(
            name="Overdue far",
            interval_days=1,
            next_due_date=self.today - datetime.timedelta(days=10),
        )
        RecurringChore.objects.create(
            name="Overdue near",
            interval_days=1,
            next_due_date=self.today - datetime.timedelta(days=1),
        )

        response = self.client.get("/")
        names_in_order = [c["name"] for c in response.context["chores"]]

        self.assertEqual(names_in_order, ["Overdue far", "Overdue near"])

    def test_same_status_and_due_date_renders_without_error_deterministically(self):
        RecurringChore.objects.create(
            name="Tie B",
            interval_days=1,
            next_due_date=self.today,
        )
        RecurringChore.objects.create(
            name="Tie A",
            interval_days=1,
            next_due_date=self.today,
        )

        first_response = self.client.get("/")
        second_response = self.client.get("/")

        self.assertEqual(first_response.status_code, 200)
        first_names = [c["name"] for c in first_response.context["chores"]]
        second_names = [c["name"] for c in second_response.context["chores"]]
        self.assertEqual(first_names, second_names)
        # Deterministic tie-break: alphabetical by name since due dates match.
        self.assertEqual(first_names, ["Tie A", "Tie B"])

    def test_page_has_no_add_edit_delete_or_mark_done_controls(self):
        RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=self.today,
        )

        response = self.client.get("/")
        content = response.content.decode().lower()

        self.assertNotIn("<form", content)
        self.assertNotIn("<button", content)
        for forbidden in ("add", "edit", "delete", "mark done", "mark as done"):
            self.assertNotIn(forbidden, content)

    def test_no_fixed_width_table_markup(self):
        RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=self.today,
        )

        response = self.client.get("/")

        self.assertNotContains(response, "<table")
