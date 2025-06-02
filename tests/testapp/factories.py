import random
from datetime import date, timedelta
from decimal import Decimal

import factory
import factory.fuzzy
from django.contrib.auth.models import User
from factory.django import DjangoModelFactory

from zivinetz.models import (
    Assessment,
    Assignment,
    Codeword,
    CompanyHoliday,
    CompensationSet,
    Drudge,
    ExpenseReport,
    JobReference,
    JobReferenceTemplate,
    PublicHoliday,
    RegionalOffice,
    ScopeStatement,
    Specification,
)


class ScopeStatementFactory(DjangoModelFactory):
    eis_no = factory.Sequence(lambda n: "%06d" % n)
    name = "Naturschutzgruppe Feld"

    company_name = "Verein Naturnetz"
    company_address = "Chlosterstrasse"
    company_zip_code = "8109"
    company_city = "Kloster Fahr"
    company_contact_name = "Marco Sacchi"
    company_contact_email = "info@naturnetz.ch"
    company_contact_function = "Geschäftsführer"
    company_contact_phone = "044 533 11 44"
    work_location = "Kanton Zürich"

    class Meta:
        model = ScopeStatement


class SpecificationFactory(DjangoModelFactory):
    scope_statement = factory.SubFactory(ScopeStatementFactory)

    class Meta:
        model = Specification


class CompensationSetFactory(DjangoModelFactory):
    valid_from = date(2011, 2, 1)
    accomodation_home = Decimal("5.00")
    private_transport_per_km = Decimal("0.65")
    clothing = Decimal("2.30")
    clothing_limit_per_assignment = Decimal("240.00")

    breakfast_at_accomodation = Decimal("4.00")
    lunch_at_accomodation = Decimal("9.00")
    supper_at_accomodation = Decimal("7.00")

    breakfast_external = Decimal("4.00")
    lunch_external = Decimal("9.00")
    supper_external = Decimal("7.00")

    class Meta:
        model = CompensationSet


class RegionalOfficeFactory(DjangoModelFactory):
    name = factory.Iterator([
        "Regionalzentrum Aarau",
        "Regionalzentrum Luzern",
        "Regionalzentrum Rueti/ZH",
        "Regionalzentrum Thun",
    ])
    city = factory.Iterator(["Aarau", "Luzern", "Rueti/ZH", "Thun"])
    address = factory.Iterator([
        "Zivildienst\nBahnhofstrasse 29\n5000 Aarau",
        "Zivildienst\nAlpenstrasse 6\nPostfach 6583\n6000 Luzern 6",
        "Zivildienst\nSpitalstrasse 31\n8630 Rueti/ZH",
        "Zivildienst\nMalerweg 6\n3600 Thun",
    ])
    code = factory.Iterator(["A", "L", "R", "T"])

    class Meta:
        model = RegionalOffice
        django_get_or_create = ("code",)


class UserFactory(DjangoModelFactory):
    first_name = factory.Sequence(lambda n: "Vorname %d" % n)
    last_name = factory.Sequence(lambda n: "Nachname %d" % n)
    email = factory.Sequence(lambda n: "mail%d@gmail.com" % n)
    username = factory.Sequence(lambda n: "user%d" % n)
    password = (
        "pbkdf2_sha256$12000$HQbIVphmynXw$HKw4uuZyqNEWTV4pjPRskmuBDzSw9U5a5x1Q5xFw0UI="
    )

    class Meta:
        model = User


class DrudgeFactory(DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    zdp_no = factory.Sequence(lambda n: "%05d" % (n + 11000))
    address = "Whatever"
    zip_code = 8000
    city = "Zürich"
    date_of_birth = factory.fuzzy.FuzzyDate(date(1975, 1, 1), date(2000, 1, 1))
    place_of_citizenship_city = "Wil"
    place_of_citizenship_state = "SG"
    bank_account = "alles meins"
    regional_office = factory.SubFactory(RegionalOfficeFactory)
    profile_image = factory.django.ImageField()

    class Meta:
        model = Drudge


class AssignmentFactory(DjangoModelFactory):
    specification = factory.SubFactory(SpecificationFactory)
    drudge = factory.SubFactory(DrudgeFactory)
    regional_office = factory.SelfAttribute("drudge.regional_office")
    date_from = factory.fuzzy.FuzzyDate(
        date(2012, 1, 1), date.today() + timedelta(days=500)
    )
    date_until = factory.LazyAttribute(
        lambda o: o.date_from + timedelta(random.randint(30, 365))
    )

    class Meta:
        model = Assignment


class ExpenseReportFactory(DjangoModelFactory):
    assignment = factory.SubFactory(AssignmentFactory)
    specification = factory.SelfAttribute("assignment.specification")

    class Meta:
        model = ExpenseReport


class PublicHolidayFactory(DjangoModelFactory):
    class Meta:
        model = PublicHoliday


class CompanyHolidayFactory(DjangoModelFactory):
    class Meta:
        model = CompanyHoliday


class AssessmentFactory(DjangoModelFactory):
    drudge = factory.SubFactory(DrudgeFactory)

    class Meta:
        model = Assessment


class CodewordFactory(DjangoModelFactory):
    key = factory.Iterator(["register", "einsatz"])
    codeword = factory.Iterator(["velo", "lustig"])

    class Meta:
        model = Codeword


class JobReferenceTemplateFactory(DjangoModelFactory):
    class Meta:
        model = JobReferenceTemplate


class JobReferenceFactory(DjangoModelFactory):
    assignment = factory.SubFactory(AssignmentFactory)
    created = factory.LazyAttribute(lambda o: date.today())

    class Meta:
        model = JobReference
