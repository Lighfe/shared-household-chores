import datetime

from django.test import Client, TestCase
from django.urls import reverse

from chores.dates import get_today
from chores.models import OneOffTask, Priority, RecurringChore

CREATE_URL = "/items/add/"


class AddItemFormPresenceTests(TestCase):
    """The home page carries a single merged "Add" form (#23), replacing
    the separate add-chore and add-task forms/disclosures (#21)."""

    def setUp(self):
        self.client = Client()

    def test_home_page_includes_exactly_one_add_item_disclosure(self):
        response = self.client.get("/")
        content = response.content.decode()

        self.assertContains(response, "+ Add")
        # Only one merged disclosure -- not the old "+ Add chore"/"+ Add
        # task" pair.
        self.assertNotContains(response, "+ Add chore")
        self.assertNotContains(response, "+ Add task")
        self.assertEqual(content.count('<details class="add-item-disclosure"'), 1)

    def test_add_item_form_has_all_five_fields_and_submit(self):
        response = self.client.get("/")

        self.assertContains(response, "<form")
        self.assertContains(response, 'name="name"')
        self.assertContains(response, 'name="recurring"')
        self.assertContains(response, 'name="interval_days"')
        self.assertContains(response, 'name="due_date"')
        self.assertContains(response, 'name="priority"')
        self.assertContains(response, 'type="submit"')

    def test_form_posts_via_htmx_to_add_item_endpoint(self):
        response = self.client.get("/")

        self.assertContains(response, "hx-post")
        self.assertContains(response, reverse("add_item"))

    def test_disclosure_collapsed_by_default(self):
        response = self.client.get("/")
        content = response.content.decode()

        details_start = content.index('<details class="add-item-disclosure"')
        details_tag_end = content.index(">", details_start)
        details_tag = content[details_start:details_tag_end]
        self.assertNotIn("open", details_tag)

    def test_interval_field_is_marked_recurring_only_for_css_toggling(self):
        """Interval (days) is only relevant when "Recurring" is checked;
        it's hidden/shown purely via CSS (base.css's `:has()` rule)
        reacting to the checkbox, per #23's "no full page reload, no JS
        if possible" constraint -- verified here structurally (the field
        sits in a `.recurring-only` row) rather than via a browser, which
        `manage.py test` can't drive.
        """
        response = self.client.get("/")
        content = response.content.decode()

        recurring_only_start = content.index('class="form-row recurring-only"')
        interval_field_pos = content.index('name="interval_days"')
        due_date_field_pos = content.index('name="due_date"')

        # interval_days sits inside the recurring-only row...
        self.assertTrue(recurring_only_start < interval_field_pos < due_date_field_pos)
        # ...but due_date does not (it's always visible/optional-hinted).
        self.assertNotIn('class="form-row recurring-only"', content[interval_field_pos:due_date_field_pos])


class AddItemUncheckedCreatesOneOffTaskTests(TestCase):
    """"Recurring" unchecked creates a OneOffTask (#23)."""

    def setUp(self):
        self.client = Client()
        self.today = get_today()

    def test_unchecked_with_due_date_creates_one_off_task(self):
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
        self.assertEqual(RecurringChore.objects.count(), 0)

    def test_unchecked_without_due_date_creates_one_off_task_with_no_due_date(self):
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

    def test_unchecked_with_interval_entered_creates_task_and_ignores_interval(self):
        """A stray interval_days value with "Recurring" unchecked is not
        an error and is not stored anywhere -- it matches today's
        OneOffTaskForm behavior, which has no interval concept at all.
        """
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Return library book",
                "interval_days": "7",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(OneOffTask.objects.filter(name="Return library book").exists())
        self.assertEqual(RecurringChore.objects.count(), 0)

    def test_new_task_appears_in_the_one_off_tasks_list(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Return library book",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        self.assertContains(response, "Return library book")
        self.assertContains(response, 'id="one-off-tasks"')

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
        self.assertNotIn('value="Return library book"', content)

    def test_successful_submission_recollapses_the_disclosure(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Return library book",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        content = response.content.decode()
        details_start = content.index('<details class="add-item-disclosure"')
        details_tag_end = content.index(">", details_start)
        details_tag = content[details_start:details_tag_end]
        self.assertNotIn("open", details_tag)


class AddItemCheckedCreatesRecurringChoreTests(TestCase):
    """"Recurring" checked creates a RecurringChore (#23)."""

    def setUp(self):
        self.client = Client()
        self.today = get_today()

    def test_checked_with_interval_and_due_date_creates_recurring_chore(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Take out trash",
                "recurring": "on",
                "interval_days": "7",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        self.assertEqual(response.status_code, 200)
        chore = RecurringChore.objects.get(name="Take out trash")
        self.assertEqual(chore.interval_days, 7)
        self.assertEqual(chore.next_due_date, self.today)
        self.assertIsNone(chore.last_done_date)
        self.assertEqual(OneOffTask.objects.count(), 0)

    def test_new_chore_appears_in_the_recurring_chores_list(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Take out trash",
                "recurring": "on",
                "interval_days": "7",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        self.assertContains(response, "Take out trash")
        self.assertContains(response, 'id="recurring-chores"')

    def test_creates_chore_with_the_submitted_priority(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Take out trash",
                "recurring": "on",
                "interval_days": "7",
                "due_date": self.today.isoformat(),
                "priority": Priority.HIGH,
            },
        )

        self.assertEqual(response.status_code, 200)
        chore = RecurringChore.objects.get(name="Take out trash")
        self.assertEqual(chore.priority, Priority.HIGH)

    def test_successful_submission_recollapses_the_disclosure(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Take out trash",
                "recurring": "on",
                "interval_days": "7",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        content = response.content.decode()
        details_start = content.index('<details class="add-item-disclosure"')
        details_tag_end = content.index(">", details_start)
        details_tag = content[details_start:details_tag_end]
        self.assertNotIn("open", details_tag)


class AddItemCheckedValidationTests(TestCase):
    """Server-side enforcement of the checked-state requiredness (#23):
    a broken/bypassed client that submits "recurring" checked but omits
    interval_days or due_date is rejected, and creates nothing -- this
    doesn't rely on the client-side CSS/HTML toggle at all.
    """

    def setUp(self):
        self.client = Client()
        self.today = get_today()

    def test_checked_with_missing_interval_is_rejected_and_creates_nothing(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Take out trash",
                "recurring": "on",
                "interval_days": "",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
        self.assertFalse(RecurringChore.objects.exists())
        self.assertFalse(OneOffTask.objects.exists())

    def test_checked_with_missing_due_date_is_rejected_and_creates_nothing(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Take out trash",
                "recurring": "on",
                "interval_days": "7",
                "due_date": "",
                "priority": "medium",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
        self.assertFalse(RecurringChore.objects.exists())
        self.assertFalse(OneOffTask.objects.exists())

    def test_checked_with_both_interval_and_due_date_missing_is_rejected(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Take out trash",
                "recurring": "on",
                "interval_days": "",
                "due_date": "",
                "priority": "medium",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(RecurringChore.objects.exists())
        self.assertFalse(OneOffTask.objects.exists())

    def test_checked_with_zero_interval_is_rejected(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Take out trash",
                "recurring": "on",
                "interval_days": "0",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(RecurringChore.objects.exists())

    def test_empty_name_is_rejected_regardless_of_recurring_state(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
        self.assertEqual(OneOffTask.objects.count(), 0)

    def test_validation_failure_preserves_the_checked_recurring_state(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Take out trash",
                "recurring": "on",
                "interval_days": "",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        content = response.content.decode()
        # The checkbox re-renders checked, not reset to unchecked.
        checkbox_start = content.index('name="recurring"')
        checkbox_tag_end = content.index(">", checkbox_start)
        checkbox_tag = content[checkbox_start:checkbox_tag_end]
        self.assertIn("checked", checkbox_tag)

    def test_validation_failure_preserves_entered_name_and_due_date(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "Take out trash",
                "recurring": "on",
                "interval_days": "",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        self.assertContains(response, 'value="Take out trash"')
        self.assertContains(response, f'value="{self.today.isoformat()}"')

    def test_validation_failure_reopens_the_disclosure(self):
        response = self.client.post(
            CREATE_URL,
            {
                "name": "",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        content = response.content.decode()
        details_start = content.index('<details class="add-item-disclosure"')
        details_tag_end = content.index(">", details_start)
        details_tag = content[details_start:details_tag_end]
        self.assertIn("open", details_tag)

    def test_get_to_create_url_does_not_create_anything(self):
        response = self.client.get(CREATE_URL)

        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(RecurringChore.objects.count(), 0)
        self.assertEqual(OneOffTask.objects.count(), 0)


class AddItemDoesNotAffectExistingListsOrControlsTests(TestCase):
    """Only creation is merged (#23) -- the two lists, their sort order,
    and their per-item controls are otherwise unaffected."""

    def setUp(self):
        self.client = Client()
        self.today = get_today()

    def test_existing_chores_and_tasks_survive_a_new_task_submission(self):
        RecurringChore.objects.create(
            name="Existing chore", interval_days=7, next_due_date=self.today
        )
        OneOffTask.objects.create(name="Existing task", due_date=self.today)

        response = self.client.post(
            CREATE_URL,
            {
                "name": "New task",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        self.assertContains(response, "Existing chore")
        self.assertContains(response, "Existing task")

    def test_recurring_chore_row_still_has_its_mark_done_edit_delete_controls(self):
        chore = RecurringChore.objects.create(
            name="Existing chore", interval_days=7, next_due_date=self.today
        )

        response = self.client.post(
            CREATE_URL,
            {
                "name": "New task",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        self.assertContains(response, reverse("mark_recurring_chore_done", args=[chore.id]))
        self.assertContains(response, reverse("edit_recurring_chore", args=[chore.id]))
        self.assertContains(response, reverse("delete_recurring_chore", args=[chore.id]))

    def test_one_off_task_row_still_has_its_done_and_cancel_controls(self):
        task = OneOffTask.objects.create(name="Existing task", due_date=self.today)

        response = self.client.post(
            CREATE_URL,
            {
                "name": "Take out trash",
                "recurring": "on",
                "interval_days": "7",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        self.assertContains(response, reverse("mark_one_off_task_done", args=[task.id]))
        self.assertContains(response, reverse("cancel_one_off_task", args=[task.id]))

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
                "recurring": "on",
                "interval_days": "7",
                "due_date": self.today.isoformat(),
                "priority": "medium",
            },
        )

        content = response.content.decode()
        overdue_pos = content.index("Overdue chore")
        due_today_pos = content.index("Due today chore")
        upcoming_pos = content.index("Upcoming chore")
        self.assertTrue(overdue_pos < due_today_pos < upcoming_pos)
