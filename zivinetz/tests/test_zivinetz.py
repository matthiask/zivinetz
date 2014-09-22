from django.test import TestCase

from zivinetz.tests import factories


class ZivinetzTestCase(TestCase):
    def test_assignment_factory(self):
        assignment = factories.AssignmentFactory.create()

        self.assertEqual(
            assignment.regional_office, assignment.drudge.regional_office)

        print(assignment.__dict__)
