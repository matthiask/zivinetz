import calendar
from collections import defaultdict, OrderedDict
from datetime import date, timedelta
import itertools

from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Max, Min, Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import ugettext_lazy

from towel.forms import SearchForm

from zivinetz.models import Assignment, Specification, WaitList


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
        if _has_53_weeks(day.year):
            return (day.year, 53)
        # Otherwise, it is already week one of the next year
        return (day.year + 1, 1)


def daterange(start_date, end_date):
    """Iterate over a range of dates (includes the end_date)"""
    for nr in range((end_date - start_date).days + 1):
        yield start_date + timedelta(days=nr)


class Scheduler(object):
    def __init__(self, assignments, date_range):
        self.queryset = assignments
        self.date_range = date_range
        self.waitlist = None

        self.date_from = _monday(date_range[0])
        self.date_until = date_range[1]

        if self.date_from:  # Is None if no assignments in queryset
            self.week_count = (
                self.date_range[1] - self.date_range[0]).days // 7

            self.date_slice = slice(
                max(0, (self.date_range[0] - self.date_from).days // 7),
                (self.date_range[1] - self.date_from).days // 7 + 1)

        self.date_list = list(daterange(self.date_from, self.date_until))
        self.data_weeks = OrderedDict()
        for day in self.date_list:
            self.data_weeks.setdefault(
                calendar_week(day),
                (day, defaultdict(lambda: 0)))

    def add_waitlist(self, queryset):
        self.waitlist = queryset

        if not self.queryset.exists() and self.waitlist.exists():
            max_min = self.waitlist.aggregate(
                min=Min('assignment_date_from'),
                max=Max('assignment_date_until'))

            self.date_from = max_min['min']
            self.date_until = max_min['max']

            if self.date_from:  # Is None if no assignments in queryset
                self.week_count = (
                    self.date_until - self.date_from).days // 7 + 1

                self.date_slice = slice(
                    max(0, (self.date_range[0] - self.date_from).days // 7),
                    (self.date_range[1] - self.date_from).days // 7 + 2)

    def weeks(self):
        ret = []

        if self.date_from:
            monday = _monday(self.date_from)
            this_monday = _monday(date.today())

            while True:
                ret.append(
                    (monday,)
                    + calendar_week(monday)
                    + (monday == this_monday,))

                monday += timedelta(days=7)
                if monday > self.date_until:
                    break

            ret = ret[self.date_slice]

        return ret

    def _schedule_assignment(self, date_from, date_until, courses={}):
        weeks = []
        cw = None
        inside = False

        for day in self.date_list:
            new_cw = calendar_week(day)
            if new_cw == cw:
                continue
            else:
                cw = new_cw

            if date_from <= day <= date_until:
                css = 'a'
                title = None
                if day in courses:
                    css += ' c'
                    title = '%s (Start: %s)' % (
                        courses[day],
                        day.strftime('%d.%m.%Y'),
                    )

                if inside:
                    weeks.append([css, '', title])
                else:
                    inside = True
                    if calendar_week(day) == calendar_week(date_from):
                        weeks.append([css, date_from.day, title])
                    else:
                        # assignment has not started this week
                        weeks.append([css, '', title])
            else:
                if inside:
                    inside = False
                    weeks[-1][1] = date_until.day
                weeks.append(['', '', None])
        return weeks

    def assignments(self):
        assignments_dict = OrderedDict()

        assignments = self.queryset.select_related(
            'specification__scope_statement', 'drudge__user',
        ).order_by('date_from', 'date_until')

        for assignment in assignments:
            for day in daterange(
                    assignment.date_from,
                    assignment.determine_date_until(),
            ):
                self.data_weeks.setdefault(
                    calendar_week(day),
                    (day, defaultdict(int)),
                )[1][assignment.drudge_id] += 1

            if assignment.drudge not in assignments_dict:
                assignments_dict[assignment.drudge] = []

            assignments_dict[assignment.drudge].append((
                assignment,
                self._schedule_assignment(
                    assignment.date_from,
                    assignment.determine_date_until(),
                    {
                        assignment.motor_saw_course_date: 'MSK',
                        assignment.environment_course_date: 'UNA',
                    },
                ),
            ))

        # linearize assignments, but still give precedence to drudge
        assignments = list(itertools.chain(*assignments_dict.values()))

        waitlist = []
        if self.waitlist is not None:
            for entry in self.waitlist.select_related(
                'specification__scope_statement',
                'drudge__user',
            ).order_by('assignment_date_from'):
                entry.status = 'wl'  # special waitlist entry status
                item = (
                    entry,
                    self._schedule_assignment(
                        entry.assignment_date_from,
                        entry.assignment_date_until),
                )

                if entry.drudge in assignments_dict:
                    assignments_dict[entry.drudge].append(item)
                else:
                    waitlist.append(item)

            # linearize assignments with waitlist entries intermingled
            assignments = list(itertools.chain(*assignments_dict.values()))

        filtered_data_weeks = [
            (day, week)
            for day, week in self.data_weeks.values()
            if self.date_from <= _monday(day) <= self.date_until]

        # Weekly count is determined by the count of drudges which are
        # available at least 3 days in a week.
        sums = [(
            sum((1 for days in week.values() if days >= 3), 0),
            u'%d' % sum((1 for days in week.values() if days >= 3), 0),
        ) for day, week in filtered_data_weeks]

        try:
            self.average = sum(
                (sum(week.values(), 0.0) for day, week in filtered_data_weeks),
                0.0) / (self.date_until - self.date_from).days
        except ArithmeticError:
            self.average = 0

        return [[None, sums]] + waitlist + assignments


def _monday(day):
    return day - timedelta(days=day.weekday())


class SchedulingSearchForm(SearchForm):
    default = {
        'date_until__gte': lambda request: _monday(date.today()),
        'date_from__lte': lambda request: _monday(
            date.today()) + timedelta(days=35 * 7 + 4),
        'status': (
            Assignment.TENTATIVE, Assignment.ARRANGED, Assignment.MOBILIZED),
        'mode': 'both',
    }

    specification = forms.ModelMultipleChoiceField(
        Specification.objects.all(),
        label=ugettext_lazy('specification'), required=False)
    status = forms.MultipleChoiceField(
        choices=Assignment.STATUS_CHOICES,
        label=ugettext_lazy('status'), required=False)
    date_until__gte = forms.DateField(
        label=ugettext_lazy('Start date'),
        required=False, widget=forms.DateInput(attrs={'class': 'dateinput'}))
    date_from__lte = forms.DateField(
        label=ugettext_lazy('End date'),
        required=False, widget=forms.DateInput(attrs={'class': 'dateinput'}))

    drudge__motor_saw_course = forms.MultipleChoiceField(
        label=ugettext_lazy('motor saw course'), required=False, choices=(
            ('2-day', ugettext_lazy('2 day course')),
            ('5-day', ugettext_lazy('5 day course')),
        ))
    drudge__driving_license = forms.NullBooleanField(
        label=ugettext_lazy('driving license'), required=False)

    mode = forms.ChoiceField(label=ugettext_lazy('Mode'), choices=(
        ('both', ugettext_lazy('both')),
        ('assignments', ugettext_lazy('only assignments')),
        ('waitlist', ugettext_lazy('only waitlist entries')),
    ), required=False)

    def queryset(self):
        data = self.safe_cleaned_data
        queryset = self.apply_filters(
            Assignment.objects.search(data.get('query')),
            data, exclude=('mode', 'date_until__gte'))
        if data.get('date_until__gte'):
            queryset = queryset.filter(
                Q(
                    date_until_extension__isnull=True,
                    date_until__gte=data.get('date_until__gte'),
                ) | Q(
                    date_until_extension__isnull=False,
                    date_until_extension__gte=data.get('date_until__gte'),
                )
            )
        return queryset

    def waitlist_queryset(self):
        data = self.safe_cleaned_data
        return self.apply_filters(WaitList.objects.search(data.get('query')), {
            'assignment_date_until__gte': data.get('date_until__gte'),
            'assignment_date_from__lte': data.get('date_from__lte'),
        })


@staff_member_required
def scheduling(request):
    search_form = SchedulingSearchForm(request.GET, request=request)

    date_range = (
        search_form.safe_cleaned_data.get('date_until__gte'),
        search_form.safe_cleaned_data.get('date_from__lte'))
    if not all(date_range):
        return HttpResponseRedirect('?clear=1')

    mode = search_form.safe_cleaned_data.get('mode')

    if mode != 'waitlist':
        scheduler = Scheduler(search_form.queryset(), date_range)
    else:
        scheduler = Scheduler(search_form.queryset().none(), date_range)

    if mode != 'assignments':
        scheduler.add_waitlist(search_form.waitlist_queryset())

    return render(request, 'zivinetz/scheduling.html', {
        'scheduler': scheduler,
        'search_form': search_form,
    })
