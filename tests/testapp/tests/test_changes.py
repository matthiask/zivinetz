from datetime import date

from django.test import TestCase

from testapp.tests import factories

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
