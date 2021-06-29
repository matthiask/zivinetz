# coding=utf-8

from __future__ import unicode_literals

import io
from datetime import date, timedelta

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from testapp import factories
from testapp.utils import admin_login

from zivinetz.models import Assignment, Drudge, JobReference


class AdminViewsTestCase(TestCase):
    def test_admin_views(self):
        self.assertRedirects(
            self.client.get("/zivinetz/admin/"), "/admin/login/?next=/zivinetz/admin/"
        )
        self.assertRedirects(
            self.client.get("/zivinetz/admin/scheduling/"),
            "/admin/login/?next=/zivinetz/admin/scheduling/",
        )

        admin_login(self)
        self.assertRedirects(
            self.client.get("/zivinetz/"),
            "/zivinetz/admin/",
            fetch_redirect_response=False,
        )

    def test_deletion(self):
        admin_login(self)
        assignment = factories.AssignmentFactory.create()
        drudge = assignment.drudge
        regional_office = assignment.regional_office

        self.assertRedirects(
            self.client.get(drudge.urls.url("delete")), drudge.urls.url("detail")
        )

        self.assertEqual(
            self.client.get(assignment.urls.url("delete")).status_code, 200
        )

        self.assertRedirects(
            self.client.post(assignment.urls.url("delete")), assignment.urls.url("list")
        )

        self.assertEqual(Assignment.objects.count(), 0)

        self.assertRedirects(
            self.client.post(drudge.urls.url("delete")), drudge.urls.url("list")
        )

        self.assertEqual(Drudge.objects.count(), 0)

        self.assertRedirects(
            self.client.post(regional_office.urls.url("delete")),
            regional_office.urls.url("list"),
        )

        self.admin.is_superuser = False
        self.admin.save()

        regional_office = factories.RegionalOfficeFactory.create()

        # Deletion is not allowed. (Editing neither, but that is not what
        # we care about right now.)
        response = self.client.get(regional_office.urls.url("delete"), follow=False)

        self.assertEqual(response["location"], regional_office.urls.url("edit"))

    def test_drudge_list(self):
        admin_login(self)

        for i in range(5):
            factories.DrudgeFactory.create()

        response = self.client.get("/zivinetz/admin/drudges/")
        self.assertContains(response, 'class="batch"', 5)

        self.assertContains(
            self.client.get("/zivinetz/admin/drudges/?only_active=1"),
            'class="batch"',
            0,
        )

        assignment = factories.AssignmentFactory.create(
            date_from=date.today() - timedelta(days=20),
            date_until=date.today() + timedelta(days=20),
            arranged_on=date.today(),
            mobilized_on=date.today(),
            status=Assignment.MOBILIZED,
        )
        assignment.drudge.assessments.create(mark=3)
        assignment.drudge.assessments.create(mark=4)

        self.assertContains(
            self.client.get("/zivinetz/admin/drudges/?only_active=1"),
            'class="batch"',
            1,
        )
        response = self.client.get("/zivinetz/admin/drudges/")
        self.assertContains(response, 'class="batch"', 6)

        # Internal assessments
        self.assertContains(response, "<td>&ndash;</td>", 5)
        self.assertContains(response, "<td>3.50</td>", 1)

        # Batch mailing
        data = {"batchform": 1, "batch-action": "send_emails"}
        for drudge in Drudge.objects.all():
            data["batch_%d" % drudge.id] = drudge.id

        response = self.client.post("/zivinetz/admin/drudges/", data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'div class="action-objects"', 1)

        with io.BytesIO(b"Django\n") as fp:
            fp.name = "requirements.txt"
            data.update(
                {
                    "confirm": 1,
                    "subject": "Hello and welcome",
                    "body": "Whatever\nYes.",
                    "attachment": fp,
                }
            )

            response = self.client.post("/zivinetz/admin/drudges/", data)

        self.assertEqual(len(mail.outbox), 1)  # Bcc:
        self.assertEqual(
            set(mail.outbox[0].bcc),
            set(Drudge.objects.values_list("user__email", flat=True)),
        )

        attachment = mail.outbox[0].attachments[0]
        self.assertEqual(attachment[0], "requirements.txt")
        self.assertIn("Django", attachment[1])

    def test_drudge_detail(self):
        admin_login(self)
        drudge = factories.DrudgeFactory.create()

        self.assertContains(self.client.get(drudge.urls.url("detail")), "<form", 1)

        response = self.client.post(
            drudge.urls.url("detail"),
            {"mark": "5", "comment": "Viel schaffe, viel rauche, viel trinke"},
        )

        self.assertEqual(drudge.assessments.count(), 1)

        assessment = drudge.assessments.get()

        response = self.client.post(
            assessment.urls.url("edit"), {"mark": "3", "comment": "Blaaa"}
        )
        self.assertRedirects(response, drudge.urls.url("detail"))

        response = self.client.post(assessment.urls.url("delete"))
        self.assertRedirects(response, drudge.urls.url("detail"))

        self.assertFalse(drudge.assessments.exists())

    def test_drudge_picker(self):
        drudge = factories.DrudgeFactory.create()
        for i in range(60):
            factories.DrudgeFactory.create(regional_office=drudge.regional_office)

        url = drudge.urls.url("picker")
        self.assertRedirects(
            self.client.get(url),
            "/admin/login/" "?next=/zivinetz/admin/drudges/picker/",
        )

        admin_login(self)

        response = self.client.get(url)
        self.assertContains(response, "<tr data-value=", 50)

    def test_jobreferences(self):
        template = factories.JobReferenceTemplateFactory.create()
        assignment = factories.AssignmentFactory.create()

        admin_login(self)

        response = self.client.get(
            reverse(
                "zivinetz_jobreference_from_template", args=(template.id, assignment.id)
            )
        )

        reference = JobReference.objects.get()
        self.assertRedirects(response, reference.urls.url("edit"))

        response = self.client.get(reference.pdf_url())
        self.assertEqual(response["content-type"], "application/pdf")
        self.assertEqual(
            response["content-disposition"],
            'attachment; filename="reference-%d.pdf"' % reference.id,
        )
