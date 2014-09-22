from __future__ import unicode_literals

from datetime import date
from decimal import Decimal

from django.test import TestCase

from zivinetz.models import AssignmentChange, CompensationSet
from zivinetz.tests import factories


class ZivinetzTestCase(TestCase):
    def test_assignment_factory(self):
        assignment = factories.AssignmentFactory.create()

        self.assertEqual(
            assignment.regional_office, assignment.drudge.regional_office)
        self.assertEqual(
            AssignmentChange.objects.count(), 1)

        self.assertRaises(
            CompensationSet.DoesNotExist,
            assignment.generate_expensereports)

        factories.CompensationSetFactory.create()

        assignment.generate_expensereports()
        self.assertTrue(assignment.reports.exists())

    def test_assignment_1504(self):
        # http://www.naturnetz.ch/zivildienst/zivinetz/admin/assignments/1504/

        spec = factories.SpecificationFactory(
            scope_statement__eis_no='53378',
            scope_statement__name='Projektadministration',

            with_accomodation=False,
            code='PA',

            accomodation_working='compensated',
            breakfast_working='at_accomodation',
            lunch_working='external',
            supper_working='at_accomodation',

            accomodation_sick='compensated',
            breakfast_sick='at_accomodation',
            lunch_sick='at_accomodation',
            supper_sick='at_accomodation',

            accomodation_free='compensated',
            breakfast_free='at_accomodation',
            lunch_free='at_accomodation',
            supper_free='at_accomodation',

            clothing='compensated',
            accomodation_throughout=False,
            food_throughout=False,
        )

        factories.CompensationSetFactory.create()

        assignment = factories.AssignmentFactory.create(
            specification=spec,
            date_from=date(2014, 9, 8),
            date_until=date(2014, 10, 3),
            arranged_on=date(2014, 1, 29),
            mobilized_on=date(2014, 6, 2),
        )

        assignment.generate_expensereports()
        reports = list(assignment.reports.all())
        self.assertEqual(len(reports), 2)

        self.assertEqual(
            reports[0].date_from,
            date(2014, 9, 8))
        self.assertEqual(
            reports[0].date_until,
            date(2014, 9, 30))

        self.assertEqual(
            reports[1].date_from,
            date(2014, 10, 1))
        self.assertEqual(
            reports[1].date_until,
            date(2014, 10, 3))

        self.assertEqual(
            reports[0].total_days,
            23)
        self.assertEqual(
            reports[1].total_days,
            3)

        self.assertEqual(
            reports[0].working_days,
            17)
        self.assertEqual(
            reports[1].working_days,
            3)

        self.assertEqual(
            reports[0].free_days,
            6)
        self.assertEqual(
            reports[1].free_days,
            0)

        self.assertAlmostEqual(
            reports[0].clothing_expenses,
            Decimal('52.90'))
        self.assertAlmostEqual(
            reports[1].clothing_expenses,
            Decimal('6.90'))

        self.assertAlmostEqual(
            reports[0].total,
            Decimal('742.90'))
        self.assertAlmostEqual(
            reports[1].total,
            Decimal('96.90'))
