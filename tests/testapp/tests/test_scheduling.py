from django.test import TestCase

from testapp.tests import factories


class SchedulingTestCase(TestCase):
    def test_scheduling(self):
        for i in range(20):
            factories.AssignmentFactory.create()
            factories.WaitListFactory.create()

        admin = factories.UserFactory.create(is_staff=True, is_superuser=True)
        self.client.login(username=admin.username, password='test')

        self.client.get('/zivinetz/admin/scheduling/')
