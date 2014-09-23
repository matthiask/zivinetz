# coding=utf-8

from __future__ import unicode_literals

from datetime import date, timedelta
from decimal import Decimal

from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from zivinetz.models import (
    Assignment, Drudge, ExpenseReport, JobReference)

from testapp.tests import factories


class AdminViewsTestCase(TestCase):
    admin = None

    def test_admin_views(self):
        self.client.get('/zivinetz/admin/')
        self.client.get('/zivinetz/admin/scheduling/')

    def _admin_login(self):
        if not self.admin:
            self.admin = factories.UserFactory.create(
                is_staff=True,
                is_superuser=True,
            )
        self.client.login(username=self.admin.username, password='test')

    def test_drudge_list(self):
        self._admin_login()

        for i in range(5):
            factories.DrudgeFactory.create()

        response = self.client.get('/zivinetz/admin/drudges/')
        self.assertContains(response, 'class="batch"', 5)

        self.assertContains(
            self.client.get('/zivinetz/admin/drudges/?only_active=1'),
            'class="batch"',
            0)

        assignment = factories.AssignmentFactory.create(
            date_from=date.today() - timedelta(days=20),
            date_until=date.today() + timedelta(days=20),
            arranged_on=date.today(),
            mobilized_on=date.today(),
            status=Assignment.MOBILIZED)
        assignment.drudge.assessments.create(
            mark=3,
        )
        assignment.drudge.assessments.create(
            mark=4,
        )

        self.assertContains(
            self.client.get('/zivinetz/admin/drudges/?only_active=1'),
            'class="batch"',
            1)
        response = self.client.get('/zivinetz/admin/drudges/')
        self.assertContains(
            response,
            'class="batch"',
            6)

        # Internal assessments
        self.assertContains(
            response,
            '<td>&ndash;</td>',
            5)
        self.assertContains(
            response,
            '<td>3.5</td>',
            1)

        # Batch mailing
        data = {
            'batchform': 1,
            'batch-action': 'send_emails',
        }
        for drudge in Drudge.objects.all():
            data['batch_%d' % drudge.id] = drudge.id

        response = self.client.post('/zivinetz/admin/drudges/', data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'div class="action-objects"', 1)

        data.update({
            'confirm': 1,
            'subject': 'Hello and welcome',
            'body': 'Whatever\nYes.',
            'attachment': '',
        })

        response = self.client.post('/zivinetz/admin/drudges/', data)
        self.assertEqual(len(mail.outbox), 1)  # Bcc:
        self.assertEqual(
            set(mail.outbox[0].bcc),
            set(Drudge.objects.values_list('user__email', flat=True)))

    def test_drudge_detail(self):
        self._admin_login()
        drudge = factories.DrudgeFactory.create()

        self.assertContains(
            self.client.get(drudge.urls.url('detail')),
            '<form', 1)

        response = self.client.post(drudge.urls.url('detail'), {
            'mark': '5',
            'comment': 'Viel schaffe, viel rauche, viel trinke',
        })

        self.assertEqual(drudge.assessments.count(), 1)

        assessment = drudge.assessments.get()

        response = self.client.post(assessment.urls.url('edit'), {
            'mark': '3',
            'comment': 'Blaaa',
        })
        self.assertRedirects(response, drudge.urls.url('detail'))

        response = self.client.post(assessment.urls.url('delete'))
        self.assertRedirects(response, drudge.urls.url('detail'))

        self.assertFalse(drudge.assessments.exists())

    def test_assignment_list(self):
        self._admin_login()

        for i in range(10):
            factories.AssignmentFactory.create()

        response = self.client.get('/zivinetz/admin/assignments/')
        self.assertContains(response, 'class="batch"', 10)

        for i in range(0, 300, 50):
            day = date.today() - timedelta(days=i)

            self.assertContains(
                self.client.get(
                    '/zivinetz/admin/assignments/?active_on=%s'
                    % day.strftime('%Y-%m-%d')),
                'class="batch"',
                Assignment.objects.for_date(day).count())

        response = self.client.get('/zivinetz/admin/assignments/pdf/?q=test')
        self.assertEqual(response['content-type'], 'application/pdf')
        self.assertEqual(
            response['content-disposition'],
            'attachment; filename="phones.pdf"')

        self.assertContains(
            self.client.get(
                '/zivinetz/admin/assignments/'
                '?service_between=%s&service_and=%s' % (
                    '2000-01-01',
                    '2020-01-01',
                )),
            'class="batch"',
            10)

    def test_assignment_detail(self):
        self._admin_login()

        drudge = factories.DrudgeFactory.create()

        response = self.client.post(Assignment().urls.url('add'), {
            'specification': factories.SpecificationFactory.create().id,
            'drudge': drudge.id,
            'regional_office': drudge.regional_office.id,
            'date_from': '2014-01-15',
            'date_until': '2014-04-20',
            'status': Assignment.ARRANGED,
            'arranged_on': '2014-01-03',
        })

        assignment = Assignment.objects.get()
        self.assertRedirects(response, assignment.urls.url('detail'))

        self.assertEqual(ExpenseReport.objects.count(), 0)

        factories.CompensationSetFactory.create()

        self.assertRedirects(
            self.client.get(assignment.urls.url('create_expensereports')),
            assignment.urls.url('detail'))
        self.assertEqual(ExpenseReport.objects.count(), 4)

        self.assertRedirects(
            self.client.get(assignment.urls.url('create_expensereports')),
            assignment.urls.url('detail'))
        self.assertEqual(ExpenseReport.objects.count(), 4)

        self.assertRedirects(
            self.client.get(assignment.urls.url('remove_expensereports')),
            assignment.urls.url('detail'))
        self.assertEqual(ExpenseReport.objects.count(), 0)

    def test_jobreferences(self):
        template = factories.JobReferenceTemplateFactory.create()
        assignment = factories.AssignmentFactory.create()

        self._admin_login()

        response = self.client.get(
            reverse(
                'zivinetz_jobreference_from_template',
                args=(template.id, assignment.id)))

        reference = JobReference.objects.get()
        self.assertRedirects(response, reference.urls.url('edit'))

        response = self.client.get(
            '/zivinetz/references/pdf/%d/' % reference.id)
        self.assertEqual(response['content-type'], 'application/pdf')
        self.assertEqual(
            response['content-disposition'],
            'attachment; filename="reference-%d.pdf"' % reference.id)

    def test_expensereport_list(self):
        self._admin_login()

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
        self._admin_login()

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

        state['holi_days'] += 2
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
