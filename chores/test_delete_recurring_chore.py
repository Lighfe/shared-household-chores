from django.test import Client, TestCase
from django.urls import reverse

from chores.dates import get_today
from chores.models import RecurringChore


def delete_url(chore_id):
    return reverse("delete_recurring_chore", args=[chore_id])


class DeleteRecurringChoreControlPresenceTests(TestCase):
    """Each row has a visible, confirming delete control (#13)."""

    def setUp(self):
        self.client = Client()
        self.today = get_today()
        self.chore = RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=self.today,
        )

    def test_home_page_row_has_delete_control(self):
        response = self.client.get("/")

        self.assertContains(response, "hx-post")
        self.assertContains(response, delete_url(self.chore.id))

    def test_delete_control_requires_confirmation(self):
        response = self.client.get("/")

        self.assertContains(response, "hx-confirm")


class DeleteRecurringChoreTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = get_today()
        self.chore = RecurringChore.objects.create(
            name="Take out trash",
            interval_days=7,
            next_due_date=self.today,
        )

    def test_post_hard_deletes_the_chore(self):
        response = self.client.post(delete_url(self.chore.id))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(RecurringChore.objects.filter(pk=self.chore.id).exists())

    def test_response_is_the_updated_section_partial(self):
        response = self.client.post(delete_url(self.chore.id))

        self.assertTemplateUsed(response, "chores/_recurring_chores_section.html")
        self.assertNotContains(response, "Take out trash")

    def test_deleting_only_remaining_chore_shows_empty_state(self):
        response = self.client.post(delete_url(self.chore.id))

        self.assertContains(response, "No recurring chores yet")

    def test_deleting_one_of_several_leaves_the_others(self):
        other = RecurringChore.objects.create(
            name="Water plants",
            interval_days=3,
            next_due_date=self.today,
        )

        response = self.client.post(delete_url(self.chore.id))

        self.assertNotContains(response, "Take out trash")
        self.assertContains(response, "Water plants")
        self.assertTrue(RecurringChore.objects.filter(pk=other.id).exists())

    def test_delete_of_missing_id_returns_404_and_deletes_nothing(self):
        response = self.client.post(delete_url(999999))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(RecurringChore.objects.count(), 1)

    def test_double_submit_of_same_id_returns_404_on_second_request(self):
        first_response = self.client.post(delete_url(self.chore.id))
        second_response = self.client.post(delete_url(self.chore.id))

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 404)

    def test_get_does_not_delete_and_returns_405(self):
        response = self.client.get(delete_url(self.chore.id))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(RecurringChore.objects.filter(pk=self.chore.id).exists())

    def test_post_without_csrf_token_is_rejected(self):
        csrf_client = Client(enforce_csrf_checks=True)

        response = csrf_client.post(delete_url(self.chore.id))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(RecurringChore.objects.filter(pk=self.chore.id).exists())

    def test_deleted_chore_leaves_no_orphaned_row_id_on_the_page(self):
        response = self.client.post(delete_url(self.chore.id))

        self.assertNotContains(response, f'id="chore-row-{self.chore.id}"')
