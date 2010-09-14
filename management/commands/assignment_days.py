from datetime import date, datetime, timedelta
import pprint

from django.core.management.base import BaseCommand
from django.db.models import Q

from zivinetz.models import Assignment, PublicHoliday, CompanyHoliday


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        for assignment in Assignment.objects.all():
            print 'Calculating days for %s' % assignment
            pprint.pprint(self.calculate_days(assignment))

    def calculate_days(self, assignment):
        day = assignment.date_from
        until = assignment.determine_date_until
        one_day = timedelta(days=1)

        public_holidays = PublicHoliday.objects.filter(
            date__range=(day, until)).values_list('date', flat=True)
        company_holidays = list(CompanyHoliday.objects.filter(
            date_from__lte=until,
            date_until__gte=day))

        vacation_days = 0
        assignment_days = (assignment.date_until - assignment.date_from).days + 1 # +1 because the range is inclusive

        if assignment_days >= 180:
            # TODO 30 days isn't exactly one month... (see ZDV Art. 72)
            vacation_days = 8 + (assignment_days - 180) / 30 * 2

        days = {
            'assignment_days': assignment_days,
            'vacation_days': vacation_days,

            'company_holidays': 0,
            'public_holidays_during_company_holidays': 0,
            'public_holidays_outside_company_holidays': 0,

            'vacation_days_during_company_holidays': 0,

            'freely_definable_vacation_days': vacation_days,
            'working_days': 0,

            'countable_days': 0,
            'forced_leave_days': 0, # days which aren't countable and are forced upon the drudge
            }

        def pop_company_holiday():
            try:
                return company_holidays.pop(0)
            except IndexError:
                return None

        company_holiday = pop_company_holiday()

        while day <= until:
            is_weekend = day.weekday() in (5, 6)
            is_public_holiday = day in public_holidays
            is_company_holiday = company_holiday and company_holiday.is_contained(day)

            if is_company_holiday:
                days['company_holidays'] += 1

                if is_public_holiday:
                    # At least we have public holidays too.
                    days['public_holidays_during_company_holidays'] += 1
                    days['countable_days'] += 1
                else:
                    if is_weekend:
                        # We were lucky once again.
                        days['countable_days'] += 1
                    else:
                        # Oh no, company holiday and neither public holiday nor
                        # weekend. Now the draconian regime of the swiss
                        # administration comes to full power.

                        if days['freely_definable_vacation_days']:
                            # Vacations need to be taken during public holidays
                            # if possible at all. Unfortunately for drudges.
                            days['freely_definable_vacation_days'] -= 1

                            # At least they are countable towards assignment total.-
                            days['countable_days'] += 1
                        else:
                            # Damn. No vacation days left (if there were any in the
                            # beginning. The drudge has to pause his assignment for
                            # this time.
                            days['forced_leave_days'] += 1

            else:
                # No company holiday... business as usual, maybe.
                days['countable_days'] += 1 # Nice!

                if not (is_public_holiday or is_weekend):
                    # Hard beer-drinking and pickaxing action.
                    days['working_days'] += 1


            day += one_day

            # Fetch new company holiday once the old one starts smelling funny.
            if company_holiday and company_holiday.date_until < day:
                company_holiday = pop_company_holiday()

        return days
