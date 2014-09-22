# coding=utf-8

from __future__ import unicode_literals

from datetime import date, timedelta
from decimal import Decimal
import factory
import factory.fuzzy
import random

from django.contrib.auth.models import User

from zivinetz.models import (
    ScopeStatement, Specification, CompensationSet, RegionalOffice, Drudge,
    Assignment, ExpenseReport, PublicHoliday, CompanyHoliday, WaitList,
    Assessment, Codeword, JobReferenceTemplate, JobReference)


class ScopeStatementFactory(factory.DjangoModelFactory):
    eis_no = factory.Sequence(lambda n: '%06d' % n)
    name = 'Naturschutzgruppe Feld'

    company_name = 'Verein Naturnetz'
    company_address = 'Chlosterstrasse'
    company_zip_code = '8109'
    company_city = 'Kloster Fahr'
    company_contact_name = 'Marco Sacchi'
    company_contact_email = 'info@naturnetz.ch'
    company_contact_function = 'Geschäftsführer'
    company_contact_phone = '044 533 11 44'
    work_location = 'Kanton Zürich'

    class Meta:
        model = ScopeStatement


class SpecificationFactory(factory.DjangoModelFactory):
    scope_statement = factory.SubFactory(ScopeStatementFactory)

    class Meta:
        model = Specification


class CompensationSetFactory(factory.DjangoModelFactory):
    valid_from = date(2011, 2, 1)
    spending_money = Decimal('5.00')
    accomodation_home = Decimal('5.00')
    private_transport_per_km = Decimal('0.65')
    clothing = Decimal('2.30')
    clothing_limit_per_assignment = Decimal('240.00')

    breakfast_at_accomodation = Decimal('4.00')
    lunch_at_accomodation = Decimal('9.00')
    supper_at_accomodation = Decimal('7.00')

    breakfast_external = Decimal('4.00')
    lunch_external = Decimal('9.00')
    supper_external = Decimal('7.00')

    class Meta:
        model = CompensationSet


class RegionalOfficeFactory(factory.DjangoModelFactory):
    name = factory.Iterator([
        'Regionalzentrum Aarau', 'Regionalzentrum Luzern',
        'Regionalzentrum Rueti/ZH', 'Regionalzentrum Thun'])
    city = factory.Iterator(['Aarau', 'Luzern', 'Rueti/ZH', 'Thun'])
    address = factory.Iterator([
        'Zivildienst\nBahnhofstrasse 29\n5000 Aarau',
        'Zivildienst\nAlpenstrasse 6\nPostfach 6583\n6000 Luzern 6',
        'Zivildienst\nSpitalstrasse 31\n8630 Rueti/ZH',
        'Zivildienst\nMalerweg 6\n3600 Thun'])
    code = factory.Iterator(['A', 'L', 'R', 'T'])

    class Meta:
        model = RegionalOffice


class UserFactory(factory.DjangoModelFactory):
    first_name = factory.Sequence(lambda n: 'Vorname %d' % n)
    last_name = factory.Sequence(lambda n: 'Nachname %d' % n)
    email = factory.Sequence(lambda n: 'mail%d@gmail.com' % n)

    class Meta:
        model = User


class DrudgeFactory(factory.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    zdp_no = factory.Sequence(lambda n: '%05d' % (n + 11000))
    address = 'Whatever'
    zip_code = 8000
    city = 'Zürich'
    date_of_birth = factory.fuzzy.FuzzyDate(
        date(1975, 1, 1), date(2000, 1, 1))
    place_of_citizenship_city = 'Wil'
    place_of_citizenship_state = 'SG'
    bank_account = 'alles meins'
    regional_office = factory.SubFactory(RegionalOfficeFactory)
    profile_image = factory.django.ImageField()

    class Meta:
        model = Drudge


class AssignmentFactory(factory.DjangoModelFactory):
    specification = factory.SubFactory(SpecificationFactory)
    drudge = factory.SubFactory(DrudgeFactory)
    regional_office = factory.SelfAttribute('drudge.regional_office')
    date_from = factory.fuzzy.FuzzyDate(
        date(2012, 1, 1), date.today() + timedelta(days=500))
    date_until = factory.LazyAttribute(
        lambda o: o.date_from + timedelta(random.randint(30, 365)))

    class Meta:
        model = Assignment


class ExpenseReportFactory(factory.DjangoModelFactory):
    assignment = factory.SubFactory(AssignmentFactory)
    specification = factory.SelfAttribute('assignment.specification')

    class Meta:
        model = ExpenseReport


class PublicHolidayFactory(factory.DjangoModelFactory):
    class Meta:
        model = PublicHoliday


class CompanyHolidayFactory(factory.DjangoModelFactory):
    class Meta:
        model = CompanyHoliday


class WaitListFactory(factory.DjangoModelFactory):
    drudge = factory.SubFactory(DrudgeFactory)
    specification = factory.SubFactory(SpecificationFactory)

    class Meta:
        model = WaitList


class AssessmentFactory(factory.DjangoModelFactory):
    drudge = factory.SubFactory(DrudgeFactory)

    class Meta:
        model = Assessment


class CodewordFactory(factory.DjangoModelFactory):
    key = factory.Iterator(['register', 'warteliste', 'einsatz'])
    codeword = factory.Iterator(['velo', 'demo', 'lustig'])

    class Meta:
        model = Codeword


class JobReferenceTemplateFactory(factory.DjangoModelFactory):
    class Meta:
        model = JobReferenceTemplate


class JobReferenceFactory(factory.DjangoModelFactory):
    assignment = factory.SubFactory(AssignmentFactory)
    created = factory.LazyAttribute(lambda o: date.today())

    class Meta:
        model = JobReference
