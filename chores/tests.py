from django.conf import settings
from django.test import Client, TestCase


class SmokeTest(TestCase):
    def test_admin_path_does_not_error(self):
        response = Client().get("/admin/")
        self.assertIn(response.status_code, (200, 302))


class SettingsTest(TestCase):
    def test_time_zone_is_berlin(self):
        self.assertEqual(settings.TIME_ZONE, "Europe/Berlin")

    def test_use_tz_is_disabled(self):
        self.assertFalse(settings.USE_TZ)
