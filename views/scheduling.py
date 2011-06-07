import calendar
from datetime import datetime, date, timedelta
import operator

from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Max, Min
from django.http import HttpResponseRedirect
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
    def __init__(self, assignments, date_range):
        self.queryset = assignments
        self.date_range = date_range

        max_min = self.queryset.aggregate(min=Min('date_from'), max=Max('date_until'))
        max_ext = self.queryset.filter(date_until_extension__isnull=False).aggregate(
            max=Max('date_until_extension'))

        self.date_from = max_min['min']
        self.date_until = max_min['max']

        if max_ext['max']:
            self.date_until = max(self.date_until, max_ext['max'])

        if self.date_from: # Is None if no assignments in queryset
            self.week_count = (self.date_until - self.date_from).days // 7 + 1

            self.date_slice = slice(
                (self.date_range[0] - self.date_from).days // 7,
                (self.date_range[1] - self.date_from).days // 7 + 2)

    def weeks(self):
        ret = []

        if self.date_from:
            monday = _monday(self.date_from)
            this_monday = _monday(date.today())

            while True:
                ret.append((monday,) + calendar_week(monday) + (monday == this_monday,))

                monday += timedelta(days=7)
                if monday > self.date_until:
                    break

            ret = ret[self.date_slice]

        return ret

    def _schedule_assignment(self, date_from, date_until):
        week_from = (date_from - self.date_from).days // 7
        week_until = (date_until - self.date_from).days // 7

        weeks = [[0, '']] * week_from
        weeks.append([1, date_from.day])
        # TODO handle single-week assignments
        weeks.extend([[1, '']] * (week_until - week_from - 1))
        weeks.append([1, date_until.day])
        weeks.extend([[0, '']] * (self.week_count - week_until - 1))

        return weeks[self.date_slice]

    def assignments(self):
        assignments = [(
            assignment,
            self._schedule_assignment(assignment.date_from, assignment.determine_date_until()),
            ) for assignment in self.queryset.select_related('specification__scope_statement',
                'drudge').order_by('date_from', 'date_until')]

        data = [[a for a, b in d] for a, d in assignments]

        return [[
            None, [(sum(week), sum(week)) for week in zip(*data)]
            ]] + assignments

        return assignments


def _monday(day):
    return day - timedelta(days=day.weekday())


class SchedulingSearchForm(SearchForm):
    default = {
        'date_until__gte': lambda request: _monday(date.today()),
        'date_from__lte': lambda request: _monday(date.today()) + timedelta(days=26 * 7 + 4),
        'status': (Assignment.TENTATIVE, Assignment.ARRANGED, Assignment.MOBILIZED),
        }

    specification = forms.ModelMultipleChoiceField(Specification.objects.all(),
        label=ugettext_lazy('specification'), required=False)
    status = forms.MultipleChoiceField(choices=Assignment.STATUS_CHOICES,
        label=ugettext_lazy('status'), required=False)
    date_until__gte = forms.DateField(label=ugettext_lazy('Start date'),
        required=False, widget=forms.DateInput(attrs={'class': 'dateinput'}))
    date_from__lte = forms.DateField(label=ugettext_lazy('End date'),
        required=False, widget=forms.DateInput(attrs={'class': 'dateinput'}))

    def queryset(self):
        data = self.safe_cleaned_data
        queryset = self.apply_filters(Assignment.objects.search(data.get('query')),
            data, exclude=())
        return queryset


@staff_member_required
def scheduling(request):
    search_form = SchedulingSearchForm(request.GET, request=request)

    date_range = (
        search_form.safe_cleaned_data.get('date_until__gte'),
        search_form.safe_cleaned_data.get('date_from__lte'))
    if not all(date_range):
        return HttpResponseRedirect('?clear=1')

    scheduler = Scheduler(search_form.queryset(), date_range)

    return render(request, 'zivinetz/scheduling.html', {
        'scheduler': scheduler,
        'search_form': search_form,
        })
