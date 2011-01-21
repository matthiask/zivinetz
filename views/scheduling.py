import calendar
from datetime import datetime, date, timedelta

from django import forms
from django.db.models import Max, Min
from django.shortcuts import render
from django.utils.translation import ugettext_lazy

from towel.forms import SearchForm, stripped_formfield_callback

from zivinetz.models import Assignment, Specification


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

        if self.date_from: # Is None if no assignments in queryset
            self.week_count = (self.date_until - self.date_from).days // 7 + 1

    def weeks(self):
        if self.date_from:
            monday = self.date_from - timedelta(days=self.date_from.weekday())

            while True:
                yield (monday,) + calendar_week(monday)

                monday += timedelta(days=7)
                if monday > self.date_until:
                    break

    def _schedule_assignment(self, date_from, date_until):
        week_from = (date_from - self.date_from).days // 7
        week_until = (date_until - self.date_from).days // 7

        weeks = [[False, '']] * week_from
        weeks.append([True, date_from.day])
        # TODO handle single-week assignments
        weeks.extend([[True, '']] * (week_until - week_from - 1))
        weeks.append([True, date_until.day])
        weeks.extend([[False, '']] * (self.week_count - week_until - 1))

        return weeks

    def assignments(self):
        for assignment in self.queryset.select_related('specification__scope_statement',
                'drudge').order_by('date_from', 'date_until'):
            yield assignment, self._schedule_assignment(
                assignment.date_from, assignment.determine_date_until())


class SchedulingSearchForm(SearchForm):
    default = {
        'date_from__gte': lambda request: date(date.today().year, 1, 1),
        'date_from__lte': lambda request: date(date.today().year, 12, 31),
        }

    specification = forms.ModelMultipleChoiceField(Specification.objects.all(),
        label=ugettext_lazy('specification'), required=False)
    date_from__gte = forms.DateField(label=ugettext_lazy('Start date after'),
        required=False, widget=forms.DateInput(attrs={'class': 'dateinput'}))
    date_from__lte = forms.DateField(label=ugettext_lazy('Start date before'),
        required=False, widget=forms.DateInput(attrs={'class': 'dateinput'}))


def scheduling(request):
    search_form = SchedulingSearchForm(request.GET, request=request)
    scheduler = Scheduler(search_form.queryset(Assignment))

    return render(request, 'zivinetz/scheduling.html', {
        'scheduler': scheduler,
        'search_form': search_form,
        })
