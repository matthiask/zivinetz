# coding=utf-8

from __future__ import unicode_literals

from datetime import date, timedelta
import os

from django.conf import settings
from django.core.files.base import ContentFile
from django.test import TestCase

from zivinetz.models import Assignment, AssignmentChange, WaitList

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
