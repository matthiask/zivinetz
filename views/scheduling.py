import calendar
from datetime import datetime, date, timedelta

from django.db.models import Max, Min
from django.shortcuts import render

from zivinetz.models import Assignment


# Calendar week calculation according to ISO 8601

def _thursday(day):
    return day + timedelta(days=3 - day.weekday())


def _thursday_week1(year):
    # 4.1. is always in the first calendar week
    return _thursday(date(year, 1, 4))


def _has_53_weeks(year):
    first = _thursday_week1(year)

    if calendar.isleap(year):
        # Year begins on a wednesday
        return first.day == 2
    else:
        # Year begins on a thursday
        return first.day == 1


def calendar_week(day):
    delta = _thursday(day) - _thursday_week1(day.year)
    week = int(1.5 + delta.days / 7)

    if 0 < week < 53:
        return (day.year, week)

    if week == 0:
        if day < _thursday_week1(day.year):
            # Day belongs to last calendar week of the year before
            return (day.year - 1, _has_53_weeks(day.year - 1) and 53 or 52)

        return (day.year, _has_53_weeks(day.year) and 53 or 52)

    if week == 53:
        return (day.year, _has_53_weeks(day.year) and 53 or 1)


class Scheduler(object):
    def __init__(self, assignments):
        self.queryset = assignments

        max_min = self.queryset.aggregate(min=Min('date_from'), max=Max('date_until'))
        max_ext = self.queryset.filter(date_until_extension__isnull=False).aggregate(
            max=Max('date_until_extension'))

        self.date_from = max_min['min']
        self.date_until = max_min['max']

        if max_ext['max']:
            self.date_until = max(self.date_until, max_ext['max'])

        self.week_count = (self.date_until - self.date_from).days // 7 + 1

    def weeks(self):
        monday = self.date_from - timedelta(days=self.date_from.weekday())

        while True:
            yield (monday,) + calendar_week(monday)

            monday += timedelta(days=7)
            if monday > self.date_until:
                break

    def _schedule_assignment(self, date_from, date_until):
        week_from = (date_from - self.date_from).days // 7
        week_until = (date_until - self.date_from).days // 7

        weeks = ['n'] * week_from
        weeks.extend(['a'] * (week_until - week_from + 1))
        weeks.extend(['n'] * (self.week_count - week_until - 1))

        return weeks

    def assignments(self):
        for assignment in self.queryset.select_related('specification__scope_statement',
                'drudge'):
            yield assignment, self._schedule_assignment(
                assignment.date_from, assignment.determine_date_until())


def scheduling(request):
    scheduler = Scheduler(Assignment.objects.all())

    return render(request, 'zivinetz/scheduling.html', {
        'scheduler': scheduler,
        })