from datetime import date, timedelta

from django.test import TestCase

from testapp import factories
from testapp.utils import admin_login, get_messages, model_to_postable_dict
from zivinetz.models import Assignment, Drudge, ExpenseReport


class AssignmentsAdminViewsTestCase(TestCase):
    def test_assignment_list(self):
        admin_login(self)

        for i in range(10):
            factories.AssignmentFactory.create()

        response = self.client.get("/zivinetz/admin/assignments/")
        self.assertContains(response, 'class="batch"', 10)

        for i in range(0, 300, 50):
            day = date.today() - timedelta(days=i)

            self.assertContains(
                self.client.get(
                    "/zivinetz/admin/assignments/?active_on=%s"
                    % day.strftime("%Y-%m-%d")
                ),
                'class="batch"',
                Assignment.objects.for_date(day).count(),
            )

        response = self.client.get("/zivinetz/admin/assignments/pdf/?q=test")
        self.assertEqual(response["content-type"], "application/pdf")
        self.assertEqual(
            response["content-disposition"], 'attachment; filename="phones.pdf"'
        )

        self.assertContains(
            self.client.get(
                "/zivinetz/admin/assignments/"
                "?service_between=%s&service_and=%s" % ("2000-01-01", "2040-01-01")
            ),
            'class="batch"',
            10,
        )

    def test_assignment_detail(self):
        admin_login(self)

        drudge = factories.DrudgeFactory.create()

        response = self.client.post(
            Assignment().urls.url("add"),
            {
                "specification": factories.SpecificationFactory.create().id,
                "drudge": drudge.id,
                "regional_office": drudge.regional_office.id,
                "date_from": "2014-01-15",
                "date_until": "2014-04-20",
                "status": Assignment.ARRANGED,
                "arranged_on": "2014-01-03",
            },
        )

        assignment = Assignment.objects.get()
        self.assertRedirects(response, assignment.urls.url("detail"))

        self.assertEqual(ExpenseReport.objects.count(), 0)

        factories.CompensationSetFactory.create()

        self.assertRedirects(
            self.client.get(assignment.urls.url("create_expensereports")),
            assignment.urls.url("detail"),
        )
        self.assertEqual(ExpenseReport.objects.count(), 4)

        self.assertRedirects(
            self.client.get(assignment.urls.url("create_expensereports")),
            assignment.urls.url("detail"),
        )
        self.assertEqual(ExpenseReport.objects.count(), 4)

        self.assertRedirects(
            self.client.get(assignment.urls.url("remove_expensereports")),
            assignment.urls.url("detail"),
        )
        self.assertEqual(ExpenseReport.objects.count(), 0)

    def test_mobilized_on(self):
        admin_login(self)

        assignment = factories.AssignmentFactory.create()

        data = model_to_postable_dict(assignment)
        data["status"] = assignment.MOBILIZED
        response = self.client.post(assignment.urls.url("edit"), data)

        self.assertContains(
            response,
            "Mobilized on date must be set when status is mobilized.",
            status_code=200,
        )

    def test_assignment_editing_with_environment_course(self):
        admin_login(self)

        assignment = factories.AssignmentFactory.create()
        data = model_to_postable_dict(assignment)
        response = self.client.post(assignment.urls.url("edit"), data)
        self.assertRedirects(response, assignment.urls.url("detail"))

        drudge = Drudge.objects.get(id=assignment.drudge_id)
        self.assertFalse(drudge.environment_course)

        data = model_to_postable_dict(assignment)
        data["environment_course_date"] = "2014-09-01"
        response = self.client.post(assignment.urls.url("edit"), data, follow=True)

        self.assertEqual(
            get_messages(response),
            [
                "The assignment has been successfully saved.",
                "The drudge is now registered as having visited"
                " the environment course.",
            ],
        )

        drudge = Drudge.objects.get(id=assignment.drudge_id)
        self.assertTrue(drudge.environment_course)

        data = model_to_postable_dict(assignment)
        data["environment_course_date"] = "2014-10-01"
        response = self.client.post(assignment.urls.url("edit"), data)
        self.assertContains(
            response, "<li>Drudge already visited an environment course.</li>"
        )
        self.assertContains(response, 'id="id_ignore_warnings"')

    def test_assignment_editing_with_motor_saw_course(self):
        admin_login(self)

        assignment = factories.AssignmentFactory.create()
        data = model_to_postable_dict(assignment)
        response = self.client.post(assignment.urls.url("edit"), data)
        self.assertRedirects(response, assignment.urls.url("detail"))

        drudge = Drudge.objects.get(id=assignment.drudge_id)
        self.assertFalse(drudge.motor_saw_course)

        data = model_to_postable_dict(assignment)
        data["motor_saw_course_date"] = "2014-09-01"
        response = self.client.post(assignment.urls.url("edit"), data)

        self.assertContains(
            response,
            "Please also provide a value in the motor saw course"
            " selector when entering a starting date.",
        )

        data["motor_saw_course"] = "2-day"
        response = self.client.post(assignment.urls.url("edit"), data, follow=True)

        self.assertEqual(
            get_messages(response),
            [
                "The assignment has been successfully saved.",
                "The drudge is now registered as having visited the motor saw course.",
            ],
        )

        drudge = Drudge.objects.get(id=assignment.drudge_id)
        self.assertEqual(drudge.motor_saw_course, "2-day")

        data = model_to_postable_dict(assignment)
        data["motor_saw_course_date"] = "2014-10-01"
        response = self.client.post(assignment.urls.url("edit"), data)
        self.assertContains(
            response, "<li>Drudge already visited a motor saw course.</li>"
        )
        self.assertContains(response, 'id="id_ignore_warnings"')

    def test_warning_message_about_reports(self):
        admin_login(self)

        assignment = factories.AssignmentFactory.create()
        data = model_to_postable_dict(assignment)
        data["date_until_extension"] = assignment.date_until + timedelta(days=14)
        response = self.client.post(assignment.urls.url("edit"), data, follow=True)

        self.assertEqual(
            get_messages(response), ["The assignment has been successfully saved."]
        )

        assignment.date_until_extension = None
        assignment.mobilized_on = date.today()
        assignment.arranged_on = date.today()
        assignment.save()

        factories.CompensationSetFactory.create()
        assignment.generate_expensereports()

        data = model_to_postable_dict(assignment)
        data["date_until_extension"] = assignment.date_until + timedelta(days=60)
        response = self.client.post(assignment.urls.url("edit"), data, follow=True)

        self.assertEqual(
            get_messages(response),
            [
                "The assignment has been successfully saved.",
                "The extended until date has been changed. Please check"
                " whether you need to generate additional expense"
                " reports.",
            ],
        )

        assignment = assignment.__class__.objects.get(pk=assignment.id)
        previous = assignment.reports.count()
        assignment.generate_expensereports()
        new = assignment.reports.count()
        self.assertTrue(new in (previous + 2, previous + 3))
