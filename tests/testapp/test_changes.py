from datetime import date

from django.test import TestCase

from testapp import factories

from zivinetz.models import AssignmentChange


class ChangesTestCase(TestCase):
    def test_change_tracking(self):
        assignment = factories.AssignmentFactory.create()

        self.assertEqual(AssignmentChange.objects.count(), 1)

        assignment.status = assignment.ARRANGED
        assignment.arranged_on = date.today()
        assignment.save()

        self.assertEqual(AssignmentChange.objects.count(), 2)

        assignment.status = assignment.MOBILIZED
        assignment.mobilized_on = date.today()
        assignment.save()

        self.assertEqual(AssignmentChange.objects.count(), 3)

        assignment.delete()

        self.assertEqual(AssignmentChange.objects.count(), 4)

        # Test the listing view.
        admin = factories.UserFactory.create(is_staff=True, is_superuser=True)
        self.client.login(username=admin.username, password="test")

        self.assertContains(
            self.client.get("/zivinetz/reporting/assignmentchanges/"), "by unknown", 4
        )
