# coding=utf-8

from __future__ import unicode_literals

from datetime import date
from decimal import Decimal

from django.test import TestCase

from zivinetz.models import AssignmentChange, CompensationSet, ScopeStatement
from zivinetz.utils.holidays import get_public_holidays

from testapp import factories


class ExampleAssignmentsTestCase(TestCase):
    def test_assignment_factory(self):
        assignment = factories.AssignmentFactory.create()

        self.assertEqual(assignment.regional_office, assignment.drudge.regional_office)
        self.assertEqual(AssignmentChange.objects.count(), 1)

        self.assertRaises(
            CompensationSet.DoesNotExist, assignment.generate_expensereports
        )

        factories.CompensationSetFactory.create()

        assignment.generate_expensereports()
        self.assertTrue(assignment.reports.exists())

    def _generate_compensation_sets(self):
        factories.CompensationSetFactory.create()
        factories.CompensationSetFactory.create(
            valid_from=date(2000, 1, 1),
            accomodation_home=Decimal("11.50"),
            breakfast_at_accomodation=Decimal("3.50"),
            lunch_at_accomodation=Decimal("10.00"),
            supper_at_accomodation=Decimal("8.00"),
            breakfast_external=Decimal("8.00"),
            lunch_external=Decimal("19.00"),
            supper_external=Decimal("15.00"),
        )

    def _generate_pa_specification(self):
        return factories.SpecificationFactory(
            scope_statement__eis_no="53378",
            scope_statement__name="Projektadministration",
            with_accomodation=False,
            code="PA",
            accomodation_working="compensated",
            breakfast_working="at_accomodation",
            lunch_working="external",
            supper_working="at_accomodation",
            accomodation_sick="compensated",
            breakfast_sick="at_accomodation",
            lunch_sick="at_accomodation",
            supper_sick="at_accomodation",
            accomodation_free="compensated",
            breakfast_free="at_accomodation",
            lunch_free="at_accomodation",
            supper_free="at_accomodation",
            clothing="compensated",
            accomodation_throughout=False,
            food_throughout=False,
        )

    def _generate_fu_specification(self):
        return factories.SpecificationFactory(
            scope_statement__eis_no="53377",
            scope_statement__name="Naturschutzgruppe Feld",
            with_accomodation=True,
            code="F(U)",
            accomodation_working="provided",
            breakfast_working="no_compensation",
            lunch_working="external",
            supper_working="no_compensation",
            accomodation_sick="provided",
            breakfast_sick="no_compensation",
            lunch_sick="no_compensation",
            supper_sick="no_compensation",
            accomodation_free="provided",
            breakfast_free="no_compensation",
            lunch_free="no_compensation",
            supper_free="no_compensation",
            clothing="compensated",
            accomodation_throughout=True,
            food_throughout=False,
        )

    def test_assignment_1504(self):
        # http://www.naturnetz.ch/zivildienst/zivinetz/admin/assignments/1504/

        self._generate_compensation_sets()

        assignment = factories.AssignmentFactory.create(
            specification=self._generate_pa_specification(),
            date_from=date(2014, 9, 8),
            date_until=date(2014, 10, 3),
            arranged_on=date(2014, 1, 29),
            mobilized_on=date(2014, 6, 2),
        )

        assignment.generate_expensereports()
        reports = list(assignment.reports.all())
        self.assertEqual(len(reports), 2)

        self.assertEqual(reports[0].date_from, date(2014, 9, 8))
        self.assertEqual(reports[0].date_until, date(2014, 9, 30))

        self.assertEqual(reports[1].date_from, date(2014, 10, 1))
        self.assertEqual(reports[1].date_until, date(2014, 10, 3))

        self.assertEqual(reports[0].total_days, 23)
        self.assertEqual(reports[1].total_days, 3)

        self.assertEqual(reports[0].working_days, 17)
        self.assertEqual(reports[1].working_days, 3)

        self.assertEqual(reports[0].free_days, 6)
        self.assertEqual(reports[1].free_days, 0)

        self.assertAlmostEqual(reports[0].clothing_expenses, Decimal("52.90"))
        self.assertAlmostEqual(reports[1].clothing_expenses, Decimal("6.90"))

        self.assertAlmostEqual(reports[0].total, Decimal("742.90"))
        self.assertAlmostEqual(reports[1].total, Decimal("96.90"))

    def test_assignment_266(self):
        # http://www.naturnetz.ch/zivildienst/zivinetz/admin/assignments/266/

        self._generate_compensation_sets()

        for year in range(2000, 2030):
            for day, name in get_public_holidays(year).items():
                factories.PublicHolidayFactory.create(date=day, name=name)

        assignment = factories.AssignmentFactory.create(
            specification=self._generate_pa_specification(),
            date_from=date(2010, 8, 23),
            date_until=date(2011, 2, 18),
            part_of_long_assignment=True,
            arranged_on=date(2010, 4, 15),
            mobilized_on=date(2010, 4, 15),
        )

        cf = factories.CompanyHolidayFactory.create(
            date_from=date(2010, 12, 25), date_until=date(2011, 1, 2)
        )
        cf.applies_to.set(ScopeStatement.objects.all())

        assignment.generate_expensereports()
        reports = list(assignment.reports.all())
        self.assertEqual(len(reports), 7)

        # Umweltkurs
        reports[1].forced_leave_days += 2
        reports[1].working_days -= 2
        reports[1].recalculate_total()

        # Additional holidays
        # Already handled by Assignment.assignment_days()
        # reports[4].holi_days += 5
        # reports[4].free_days -= 5
        # reports[4].recalculate_total()

        def _assert_equal(attribute, list):
            self.assertEqual([getattr(report, attribute) for report in reports], list)

        _assert_equal("total_days", [9, 30, 31, 30, 31, 31, 18])
        _assert_equal("working_days", [7, 20, 21, 22, 18, 21, 14])
        _assert_equal("free_days", [2, 8, 10, 8, 8, 10, 4])
        _assert_equal("sick_days", [0, 0, 0, 0, 0, 0, 0])
        _assert_equal("holi_days", [0, 0, 0, 0, 5, 0, 0])
        _assert_equal("forced_leave_days", [0, 2, 0, 0, 0, 0, 0])

        def _assert_almost_equal(attribute, list):
            for pair in zip([getattr(report, attribute) for report in reports], list):
                self.assertAlmostEqual(*pair)

        _assert_almost_equal(
            "clothing_expenses", [Decimal(s) for s in "20.7 69 71.3 69 10 0 0".split()]
        )
        _assert_almost_equal(
            "total",
            [Decimal(s) for s in "425.7 1313 1438.3 1407 1350 1367 810".split()],
        )

    def test_assignment_811(self):
        # http://www.naturnetz.ch/zivildienst/zivinetz/admin/assignments/811/

        self._generate_compensation_sets()

        for year in range(2012, 2014):
            for day, name in get_public_holidays(year).items():
                factories.PublicHolidayFactory.create(date=day, name=name)

        assignment = factories.AssignmentFactory.create(
            specification=self._generate_fu_specification(),
            date_from=date(2012, 8, 13),
            date_until=date(2013, 2, 15),
            part_of_long_assignment=False,
            arranged_on=date(2012, 5, 16),
            mobilized_on=date(2012, 5, 16),
        )

        cf = factories.CompanyHolidayFactory.create(
            date_from=date(2012, 12, 22), date_until=date(2013, 1, 13)
        )
        cf.applies_to.set(ScopeStatement.objects.all())

        assignment.generate_expensereports()
        reports = list(assignment.reports.all())
        self.assertEqual(len(reports), 7)

        # Krank
        reports[1].sick_days += 2
        reports[1].working_days -= 2

        # Transports
        reports[1].transport_expenses = Decimal("246.40")

        # Krank
        reports[2].sick_days += 4
        reports[2].working_days -= 4

        # Umweltkurs
        reports[2].forced_leave_days += 5
        reports[2].working_days -= 5

        # Konzert und Pilotenprüfung
        reports[3].forced_leave_days += 2
        reports[3].working_days -= 2

        # Transports
        reports[3].transport_expenses = Decimal("104.00")

        # Krank
        reports[4].sick_days += 1
        reports[4].working_days -= 1

        # Ferientage 24, 27, 28, 31 Dez
        # Zwangsferien während Betriebsferien
        # Should be automatically handled by Assignment.assignment_days()
        # reports[4].holi_days += 4
        # reports[4].free_days -= 4

        # Transports
        reports[4].transport_expenses = Decimal("16.10")

        # Krank
        reports[5].sick_days += 3
        reports[5].working_days -= 3

        # Ferien und Urlaub während Betriebsferien
        # Should be automatically handled by Assignment.assignment_days()
        # reports[5].holi_days += 4
        # reports[5].free_days -= 4

        # Transports
        reports[6].transport_expenses = Decimal("84.50")

        [report.recalculate_total() for report in reports]

        def _assert_equal(attribute, list):
            self.assertEqual([getattr(report, attribute) for report in reports], list)

        _assert_equal("total_days", [19, 30, 31, 30, 31, 31, 15])
        _assert_equal("working_days", [15, 18, 14, 20, 14, 11, 11])
        _assert_equal("free_days", [4, 10, 8, 8, 12, 10, 4])
        _assert_equal("sick_days", [0, 2, 4, 0, 1, 3, 0])
        _assert_equal("holi_days", [0, 0, 0, 0, 4, 4, 0])
        _assert_equal("forced_leave_days", [0, 0, 5, 2, 0, 3, 0])

        def _assert_almost_equal(attribute, list):
            other = [getattr(report, attribute) for report in reports]
            for pair in zip(list, other):
                self.assertAlmostEqual(*pair)

        _assert_almost_equal(
            "clothing_expenses", [Decimal(s) for s in "43.7 69 71.3 56 0 0 0".split()]
        )
        _assert_almost_equal(
            "total",
            [Decimal(s) for s in "273.7 627.4 327.3 480 297.1 239 258.5".split()],
        )
