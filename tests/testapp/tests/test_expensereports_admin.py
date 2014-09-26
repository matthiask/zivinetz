# coding=utf-8

from __future__ import unicode_literals

from datetime import date
from decimal import Decimal

from django.test import TestCase

from zivinetz.models import Assignment, ExpenseReport

from testapp.tests import factories
from testapp.tests.utils import admin_login


class ExpenseReportsAdminViewsTestCase(TestCase):
    def test_expensereport_list(self):
        admin_login(self)

        factories.CompensationSetFactory.create()
        for i in range(10):
            factories.AssignmentFactory.create(
                status=Assignment.MOBILIZED,
                arranged_on=date.today(),
                mobilized_on=date.today(),
            ).generate_expensereports()

        self.assertContains(
            self.client.get(ExpenseReport().urls.url('list')),
            'class="batch"',
            50)

        response = self.client.get(ExpenseReport().urls.url('pdf'))
        self.assertEqual(response['content-type'], 'application/pdf')
        self.assertEqual(
            response['content-disposition'],
            'attachment; filename="expense-statistics.pdf"')

    def test_expensereport_editing(self):
        admin_login(self)

        factories.CompensationSetFactory.create()
        factories.AssignmentFactory.create(
            status=Assignment.MOBILIZED,
            date_from=date(2014, 9, 1),
            date_until=date(2014, 9, 26),
            arranged_on=date(2014, 9, 1),
            mobilized_on=date(2014, 9, 1),
        ).generate_expensereports()

        report = ExpenseReport.objects.get()

        self.assertAlmostEqual(report.total, Decimal('130.00'))

        state = {
            'working_days': 20,
            'free_days': 6,
            'sick_days': 0,
            'holi_days': 0,
            'forced_leave_days': 0,
        }
        for type, days in state.items():
            self.assertEqual(getattr(report, type), days)
        self.assertEqual(report.calculated_total_days, 26)

        base_data = {
            'date_from': report.date_from,
            'date_until': report.date_until,
            'report_no': report.report_no,
            'status': report.status,
            'specification': report.specification.id,

            'clothing_expenses': report.clothing_expenses,
            'transport_expenses': report.transport_expenses,
            'miscellaneous': report.miscellaneous,
        }

        data = {}
        data.update(base_data)
        data.update(state)

        response = self.client.post(report.urls.url('edit'), data)
        self.assertRedirects(response, report.urls.url('detail'))

        del data['holi_days']
        response = self.client.post(report.urls.url('edit'), data)
        self.assertEqual(response.status_code, 200)

        state['holi_days'] = 2
        data.update(state)
        response = self.client.post(report.urls.url('edit'), data)
        self.assertContains(response, 'id="id_ignore_warnings"', 1)

        state['working_days'] -= 2
        data.update(state)
        response = self.client.post(report.urls.url('edit'), data)
        self.assertRedirects(response, report.urls.url('detail'))

        report = ExpenseReport.objects.get()
        for type, days in state.items():
            self.assertEqual(getattr(report, type), days)
        self.assertEqual(report.calculated_total_days, 26)
