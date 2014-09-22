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
    def test_admin_views(self):
        self.client.get('/zivinetz/admin/')
        self.client.get('/zivinetz/admin/scheduling/')
