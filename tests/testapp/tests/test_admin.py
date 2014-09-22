# coding=utf-8

from __future__ import unicode_literals

from datetime import date, timedelta

from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from zivinetz.models import (
    Assignment, Drudge, JobReference)

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
        print response.content
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
