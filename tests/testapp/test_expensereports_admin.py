from datetime import date
from decimal import Decimal

from django.test import TestCase

from testapp import factories
from testapp.utils import admin_login, get_messages, model_to_postable_dict

from zivinetz.models import Assignment, CompensationSet, ExpenseReport


class ExpenseReportsAdminViewsTestCase(TestCase):
    def test_expensereport_list(self):
        admin_login(self)

        cf = factories.CompensationSetFactory.create()
        # for_date should not fail
        self.assertEqual(CompensationSet.objects.for_date(), cf)

        for i in range(10):
            factories.AssignmentFactory.create(
                status=Assignment.MOBILIZED,
                arranged_on=date.today(),
                mobilized_on=date.today(),
            ).generate_expensereports()

        self.assertContains(
            self.client.get(ExpenseReport().urls.url("list")), 'class="batch"', 50
        )

        response = self.client.get(ExpenseReport().urls.url("pdf"))
        self.assertEqual(response["content-type"], "application/pdf")
        self.assertEqual(
            response["content-disposition"],
            'attachment; filename="expense-statistics.pdf"',
        )

    def _create_report(self):
        factories.CompensationSetFactory.create()
        factories.AssignmentFactory.create(
            status=Assignment.MOBILIZED,
            date_from=date(2014, 9, 1),
            date_until=date(2014, 9, 26),
            arranged_on=date(2014, 9, 1),
            mobilized_on=date(2014, 9, 1),
        ).generate_expensereports()
        return ExpenseReport.objects.get()

    def test_expensereport_editing_allowed(self):
        report = self._create_report()
        admin_login(self)
        self.assertEqual(self.client.get(report.urls.url("detail")).status_code, 200)
        self.assertEqual(self.client.get(report.urls.url("edit")).status_code, 200)

        report.status = report.PAID
        report.save()

        response = self.client.get(report.urls.url("edit"), follow=True)

        self.assertRedirects(response, report.urls.url("detail"))

        self.assertEqual(
            get_messages(response), ["Paid expense reports cannot be edited."]
        )

        response = self.client.get(report.urls.url("delete"), follow=True)

        self.assertRedirects(response, report.urls.url("detail"))

        self.assertEqual(
            get_messages(response), ["Paid expense reports cannot be deleted."]
        )

    def test_expensereport_editing(self):
        report = self._create_report()
        self.assertAlmostEqual(report.total, Decimal("130.00"))

        state = {
            "working_days": 20,
            "free_days": 6,
            "sick_days": 0,
            "holi_days": 0,
            "forced_leave_days": 0,
        }
        for type, days in state.items():
            self.assertEqual(getattr(report, type), days)
        self.assertEqual(report.calculated_total_days, 26)

        base_data = {
            "date_from": report.date_from,
            "date_until": report.date_until,
            "report_no": report.report_no,
            "status": report.status,
            "specification": report.specification.id,
            "clothing_expenses": report.clothing_expenses,
            "transport_expenses": report.transport_expenses,
            "miscellaneous": report.miscellaneous,
        }

        data = {}
        data.update(base_data)
        data.update(state)

        admin_login(self)
        response = self.client.post(report.urls.url("edit"), data)
        self.assertRedirects(response, report.urls.url("detail"))

        del data["holi_days"]
        response = self.client.post(report.urls.url("edit"), data)
        self.assertEqual(response.status_code, 200)

        state["holi_days"] = 2
        data.update(state)
        response = self.client.post(report.urls.url("edit"), data)
        self.assertContains(response, 'id="id_ignore_warnings"', 1)

        state["working_days"] -= 2
        data.update(state)
        response = self.client.post(report.urls.url("edit"), data)
        self.assertRedirects(response, report.urls.url("detail"))

        report = ExpenseReport.objects.get()
        for type, days in state.items():
            self.assertEqual(getattr(report, type), days)
        self.assertEqual(report.calculated_total_days, 26)

    def test_transport_expenses_copying(self):
        factories.CompensationSetFactory.create()
        factories.AssignmentFactory.create(
            status=Assignment.MOBILIZED,
            date_from=date(2014, 9, 1),
            date_until=date(2014, 11, 26),
            arranged_on=date(2014, 9, 1),
            mobilized_on=date(2014, 9, 1),
        ).generate_expensereports()

        self.assertEqual(
            [r.transport_expenses for r in ExpenseReport.objects.all()], [0, 0, 0]
        )

        report = ExpenseReport.objects.all()[1]
        admin_login(self)
        data = model_to_postable_dict(report)
        data["transport_expenses"] = 10

        response = self.client.post(report.urls.url("edit"), data)
        self.assertRedirects(response, report.urls.url("detail"))

        self.assertEqual(
            [r.transport_expenses for r in ExpenseReport.objects.all()], [0, 10, 0]
        )

        data["transport_expenses"] = 20
        data["transport_expenses_notes"] = "Auto-Dumm"
        data["transport_expenses_copy"] = "1"

        response = self.client.post(report.urls.url("edit"), data)
        self.assertRedirects(response, report.urls.url("detail"))

        self.assertEqual(
            [r.transport_expenses for r in ExpenseReport.objects.all()], [0, 20, 20]
        )
        self.assertEqual(
            [r.transport_expenses_notes for r in ExpenseReport.objects.all()],
            ["", "Auto-Dumm", "Auto-Dumm"],
        )
