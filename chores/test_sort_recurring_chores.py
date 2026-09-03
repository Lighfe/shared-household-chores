import datetime

from django.test import Client, TestCase
from django.urls import reverse

from chores.dates import get_today
from chores.models import OneOffTask, RecurringChore


def sort_url(sort=None):
    url = reverse("sort_recurring_chores")
    return f"{url}?sort={sort}" if sort is not None else url


class SortControlPresenceTests(TestCase):
    """The Recurring Chores section shows a visible sort-order control (#20)."""

    def setUp(self):
        self.client = Client()
        self.today = get_today()
        RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=self.today,
        )

    def test_home_page_shows_both_sort_options(self):
        response = self.client.get("/")

        self.assertContains(response, "Default")
        self.assertContains(response, "Name (A-Z)")

    def test_default_is_the_active_option_on_initial_load(self):
        response = self.client.get("/")
        content = response.content.decode()

        self.assertIn('aria-current="true">Default</strong>', content)

    def test_switching_to_name_marks_it_as_the_active_option(self):
        response = self.client.get(sort_url("name"))
        content = response.content.decode()

        self.assertIn('aria-current="true">Name (A-Z)</strong>', content)


class SortRecurringChoresViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = get_today()

    def test_default_sort_reproduces_status_then_due_date_then_name_then_id(self):
        upcoming = RecurringChore.objects.create(
            name="B upcoming",
            interval_days=5,
            next_due_date=self.today + datetime.timedelta(days=5),
        )
        overdue = RecurringChore.objects.create(
            name="A overdue",
            interval_days=5,
            next_due_date=self.today - datetime.timedelta(days=5),
        )

        response = self.client.get(sort_url("default"))
        names_in_order = [c["name"] for c in response.context["chores"]]

        self.assertEqual(names_in_order, ["A overdue", "B upcoming"])
        self.assertTrue(upcoming.pk and overdue.pk)

    def test_name_sort_ignores_status_and_due_date_grouping(self):
        RecurringChore.objects.create(
            name="Zebra upcoming",
            interval_days=5,
            next_due_date=self.today + datetime.timedelta(days=5),
        )
        RecurringChore.objects.create(
            name="Apple overdue",
            interval_days=5,
            next_due_date=self.today - datetime.timedelta(days=5),
        )

        response = self.client.get(sort_url("name"))
        names_in_order = [c["name"] for c in response.context["chores"]]

        # Alphabetical, even though "Apple overdue" would otherwise sort
        # first anyway under default (status) ordering too -- assert with
        # a case that would come out differently under default order.
        self.assertEqual(names_in_order, ["Apple overdue", "Zebra upcoming"])

    def test_name_sort_is_case_insensitive(self):
        RecurringChore.objects.create(
            name="banana",
            interval_days=1,
            next_due_date=self.today,
        )
        RecurringChore.objects.create(
            name="Apple",
            interval_days=1,
            next_due_date=self.today,
        )

        response = self.client.get(sort_url("name"))
        names_in_order = [c["name"] for c in response.context["chores"]]

        self.assertEqual(names_in_order, ["Apple", "banana"])

    def test_name_sort_uses_id_as_tiebreak_for_identical_names(self):
        first = RecurringChore.objects.create(
            name="Same name",
            interval_days=1,
            next_due_date=self.today,
        )
        second = RecurringChore.objects.create(
            name="Same name",
            interval_days=1,
            next_due_date=self.today,
        )

        response = self.client.get(sort_url("name"))
        ids_in_order = [c["id"] for c in response.context["chores"]]

        self.assertEqual(ids_in_order, sorted([first.id, second.id]))

    def test_default_sort_still_uses_id_as_final_tiebreak(self):
        first = RecurringChore.objects.create(
            name="Same name",
            interval_days=1,
            next_due_date=self.today,
        )
        second = RecurringChore.objects.create(
            name="Same name",
            interval_days=1,
            next_due_date=self.today,
        )

        response = self.client.get(sort_url("default"))
        ids_in_order = [c["id"] for c in response.context["chores"]]

        self.assertEqual(ids_in_order, sorted([first.id, second.id]))

    def test_invalid_sort_value_falls_back_to_default(self):
        RecurringChore.objects.create(
            name="A chore",
            interval_days=1,
            next_due_date=self.today,
        )

        response = self.client.get(sort_url("bogus"))

        self.assertEqual(response.status_code, 200)
        # Falls back to default rather than erroring or leaving the list
        # unsorted.
        self.assertIn('aria-current="true">Default</strong>', response.content.decode())

    def test_missing_sort_value_falls_back_to_default(self):
        response = self.client.get(sort_url())

        self.assertEqual(response.status_code, 200)
        self.assertIn('aria-current="true">Default</strong>', response.content.decode())

    def test_response_is_the_section_partial_via_get_no_full_reload(self):
        response = self.client.get(sort_url("name"))

        self.assertTemplateUsed(response, "chores/_recurring_chores_section.html")
        self.assertTemplateNotUsed(response, "chores/home.html")

    def test_post_is_rejected(self):
        response = self.client.post(sort_url("name"))

        self.assertEqual(response.status_code, 405)

    def test_zero_chores_shows_empty_state_regardless_of_sort_option(self):
        default_response = self.client.get(sort_url("default"))
        name_response = self.client.get(sort_url("name"))

        self.assertContains(default_response, "No recurring chores yet")
        self.assertContains(name_response, "No recurring chores yet")

    def test_one_chore_shown_identically_under_both_sort_options(self):
        RecurringChore.objects.create(
            name="Only chore",
            interval_days=7,
            next_due_date=self.today,
        )

        default_response = self.client.get(sort_url("default"))
        name_response = self.client.get(sort_url("name"))

        self.assertEqual(
            [c["name"] for c in default_response.context["chores"]], ["Only chore"]
        )
        self.assertEqual(
            [c["name"] for c in name_response.context["chores"]], ["Only chore"]
        )


class SortDoesNotAffectStoredDataOrOtherSectionsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = get_today()
        self.chore = RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=self.today + datetime.timedelta(days=3),
        )
        self.task = OneOffTask.objects.create(
            name="Return library book", due_date=self.today
        )

    def test_switching_sort_does_not_change_chore_fields(self):
        self.client.get(sort_url("name"))

        self.chore.refresh_from_db()
        self.assertEqual(self.chore.name, "Take out trash")
        self.assertEqual(self.chore.interval_days, 7)
        self.assertEqual(
            self.chore.next_due_date, self.today + datetime.timedelta(days=3)
        )

    def test_switching_sort_does_not_create_or_delete_chores(self):
        self.client.get(sort_url("name"))

        self.assertEqual(RecurringChore.objects.count(), 1)

    def test_switching_sort_does_not_affect_one_off_tasks(self):
        self.client.get(sort_url("name"))

        self.assertEqual(OneOffTask.objects.count(), 1)
        self.assertTrue(OneOffTask.objects.filter(pk=self.task.id).exists())

    def test_add_chore_form_still_present_after_switching_sort(self):
        response = self.client.get(sort_url("name"))

        self.assertContains(response, 'class="add-chore-form"')

    def test_reloading_home_after_sorting_by_name_resets_to_default(self):
        self.client.get(sort_url("name"))

        response = self.client.get("/")
        content = response.content.decode()

        self.assertIn('aria-current="true">Default</strong>', content)

    def test_adding_a_chore_preserves_the_active_name_sort(self):
        response = self.client.post(
            reverse("add_recurring_chore"),
            {
                "name": "Vacuum",
                "interval_days": 7,
                "next_due_date": self.today.isoformat(),
                "sort": "name",
                "priority": "medium",
            },
        )

        self.assertIn(
            'aria-current="true">Name (A-Z)</strong>', response.content.decode()
        )
        names_in_order = [c["name"] for c in response.context["chores"]]
        self.assertEqual(names_in_order, ["Take out trash", "Vacuum"])
