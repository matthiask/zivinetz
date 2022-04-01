import os
from datetime import date, timedelta

from django.conf import settings
from django.core.files.base import ContentFile
from django.test import TestCase

from testapp import factories

from zivinetz.models import Assignment, AssignmentChange


class DrudgeViewsTestCase(TestCase):
    def test_create_profile_as_drudge(self):
        # Hit a few views, just for fun
        self.assertRedirects(
            self.client.get("/zivinetz/"), "/accounts/login/?next=/zivinetz/"
        )
        self.assertRedirects(
            self.client.get("/zivinetz/dashboard/"),
            "/accounts/login/?next=/zivinetz/dashboard/",
        )

        user = factories.UserFactory.create()
        self.client.login(username=user.username, password="test")

        self.assertRedirects(self.client.get("/zivinetz/"), "/zivinetz/profile/")
        self.assertRedirects(
            self.client.get("/zivinetz/dashboard/"), "/zivinetz/profile/"
        )

        data = {
            "first_name": "Hans",
            "last_name": "Muster",
            "zdp_no": "12345",
            "address": "Musterstrasse 42",
            "zip_code": "8000",
            "city": "Zürich",
            "date_of_birth": "1980-01-01",
            "place_of_citizenship_city": "Zürich",
            "place_of_citizenship_state": "ZH",
            "bank_account": "GB29 NWBK 6016 1331 9268 19",
            "regional_office": factories.RegionalOfficeFactory.create().id,
        }

        self.assertContains(
            self.client.post("/zivinetz/profile/", data),
            "Please select either yes or no.",
        )

        data["environment_course"] = "2"  # Yes.

        response = self.client.post("/zivinetz/profile/", data)
        self.assertRedirects(response, "/zivinetz/profile/")

        self.assertRedirects(
            self.client.get("/zivinetz/dashboard/"), "/zivinetz/profile/"
        )
        self.assertRedirects(
            self.client.get("/zivinetz/dashboard/"), "/zivinetz/profile/"
        )

        path = os.path.join(
            os.path.dirname(settings.BASE_DIR), "zivinetz", "data", "3-0.jpg"
        )

        with open(path, "rb") as image, ContentFile(image.read()) as cf:
            user.drudge.profile_image.save("profile.jpg", cf)

        response = self.client.get("/zivinetz/dashboard/")
        self.assertEqual(response.status_code, 200)

        self.assertRedirects(self.client.get("/zivinetz/"), "/zivinetz/dashboard/")

    def test_create_assignment_as_drudge(self):
        drudge = factories.DrudgeFactory.create()
        self.client.login(username=drudge.user.username, password="test")

        data = {
            "assignment": "1",
            "specification": factories.SpecificationFactory.create().id,
            "regional_office": drudge.regional_office.id,
            "date_from": date.today(),
            "date_until": date.today() - timedelta(days=60),
            "part_of_long_assignment": "",
            "codeword": "whatever",
        }

        response = self.client.post("/zivinetz/dashboard/", data)
        self.assertContains(response, "Codeword is incorrect.")
        self.assertContains(response, "Date period is invalid.")

        factories.CodewordFactory.create(key="einsatz", codeword="blaaa")
        data["codeword"] = "blaaa"

        data["date_until"] = date.today() + timedelta(days=60)

        response = self.client.post("/zivinetz/dashboard/", data)
        self.assertRedirects(response, "/zivinetz/dashboard/")

        assignment = Assignment.objects.get()
        self.assertEqual(assignment.date_from, date.today())
        self.assertEqual(assignment.status, Assignment.TENTATIVE)
        self.assertEqual(AssignmentChange.objects.count(), 1)

        response = self.client.get(assignment.pdf_url())
        self.assertEqual(response["content-type"], "application/pdf")
        self.assertEqual(
            response["content-disposition"],
            f"attachment; filename=eiv-{assignment.pk}.pdf",
        )
        self.assertTrue(len(response.content))

        # Fast forward a bit.
        assignment.arranged_on = assignment.mobilized_on = date.today()
        assignment.save()
        factories.CompensationSetFactory.create()
        assignment.generate_expensereports()

        report = assignment.reports.all()[0]
        response = self.client.get(report.pdf_url())
        self.assertEqual(response["content-type"], "application/pdf")
        self.assertEqual(
            response["content-disposition"],
            'attachment; filename="expense-report-%d.pdf"' % report.id,
        )
        self.assertTrue(len(response.content))
