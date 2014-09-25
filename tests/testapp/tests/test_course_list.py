from datetime import date

from django.test import TestCase

from testapp.tests import factories


class CourseListTestCase(TestCase):
    def test_course_list(self):
        a1 = factories.AssignmentFactory.create(
            motor_saw_course_date=date.today(),
        )
        a2 = factories.AssignmentFactory.create(
            motor_saw_course_date=date.today(),
            environment_course_date=date.today(),
        )
        a3 = factories.AssignmentFactory.create(
            environment_course_date=date.today(),
        )
        factories.AssignmentFactory.create()
        factories.AssignmentFactory.create()
        factories.AssignmentFactory.create()

        # Test the listing view.
        admin = factories.UserFactory.create(is_staff=True, is_superuser=True)
        self.client.login(username=admin.username, password='test')

        response = self.client.get('/zivinetz/reporting/courses/')
        # Four entries for three assignments, one header row and one week row.
        self.assertContains(response, '<tr>', 4 + 1 + 1)
        self.assertContains(response, a1.get_absolute_url(), 2)
        self.assertContains(response, a2.get_absolute_url(), 4)
        self.assertContains(response, a3.get_absolute_url(), 2)
