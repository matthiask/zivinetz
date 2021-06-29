from django.test import TestCase

from testapp import factories

from zivinetz.models import Assignment


class SchedulingTestCase(TestCase):
    def test_scheduling(self):
        for i in range(20):
            factories.AssignmentFactory.create()

        admin = factories.UserFactory.create(is_staff=True, is_superuser=True)
        self.client.login(username=admin.username, password="test")

        self.assertEqual(
            self.client.get("/zivinetz/admin/scheduling/").status_code, 200
        )

        Assignment.objects.all().delete()
        self.assertEqual(
            self.client.get("/zivinetz/admin/scheduling/").status_code, 200
        )
