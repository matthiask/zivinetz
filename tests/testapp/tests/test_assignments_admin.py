# coding=utf-8

from __future__ import unicode_literals

from datetime import date, timedelta

from django.test import TestCase

from zivinetz.models import Assignment, Drudge, ExpenseReport

from testapp.tests import factories
from testapp.tests.utils import (
    admin_login, get_messages, model_to_postable_dict)


class AssignmentsAdminViewsTestCase(TestCase):
    admin = None

    def test_assignment_list(self):
        admin_login(self)

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
        admin_login(self)

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

    def test_assignment_detail_with_courses(self):
        admin_login(self)

        assignment = factories.AssignmentFactory.create()
        data = model_to_postable_dict(assignment)
        response = self.client.post(
            assignment.urls.url('edit'),
            data)
        self.assertRedirects(response, assignment.urls.url('detail'))

        drudge = Drudge.objects.get(id=assignment.drudge_id)
        self.assertFalse(drudge.environment_course)

        data = model_to_postable_dict(assignment)
        data['environment_course_date'] = '2014-09-01'
        response = self.client.post(
            assignment.urls.url('edit'),
            data,
            follow=True)

        self.assertEqual(
            get_messages(response),
            [
                'The assignment has been successfully saved.',
                'The drudge is now registered as having visited'
                ' the environment course.'
            ])

        drudge = Drudge.objects.get(id=assignment.drudge_id)
        self.assertTrue(drudge.environment_course)

        data = model_to_postable_dict(assignment)
        data['environment_course_date'] = '2014-10-01'
        response = self.client.post(
            assignment.urls.url('edit'),
            data)
        self.assertContains(
            response,
            '<li>Drudge already visited an environment course.</li>')
        self.assertContains(
            response,
            'id="id_ignore_warnings"')