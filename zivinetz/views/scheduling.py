import calendar
import itertools
from collections import OrderedDict, defaultdict
from datetime import date, timedelta

from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import gettext_lazy
from towel.forms import SearchForm

from zivinetz.models import Assignment, DrudgeQuota, ScopeStatement


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


class Scheduler:
    def __init__(self, assignments, date_range):
        self.queryset = assignments
        self.date_range = date_range

        self.date_from = _monday(date_range[0])
        self.date_until = date_range[1]

        if self.date_from:  # Is None if no assignments in queryset
            self.week_count = (self.date_range[1] - self.date_range[0]).days // 7

            self.date_slice = slice(
                max(0, (self.date_range[0] - self.date_from).days // 7),
                (self.date_range[1] - self.date_from).days // 7 + 1,
            )

        self.date_list = list(daterange(self.date_from, self.date_until))
        self.drudge_days_per_week = OrderedDict()
        for day in self.date_list:
            self.drudge_days_per_week.setdefault(
                calendar_week(day), (day, defaultdict(lambda: 0))
            )

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

    def _schedule_assignment(self, date_from, date_until, courses={}):
        weeks = []
        cw = None
        inside = False

        # Not all courses start on a monday, but we have to normalize
        # dates to monday otherwise we wont find them while scheduling.
        week_courses = {
            _monday(day) if day else None: (day, type) for day, type in courses.items()
        }

        for day in self.date_list:
            new_cw = calendar_week(day)
            if new_cw == cw:
                continue
            cw = new_cw

            if date_from <= day <= date_until:
                css = "a"
                title = None
                if day in week_courses:
                    css += " c-%s" % week_courses[day][1].lower()
                    title = "{} (Start: {})".format(
                        week_courses[day][0],
                        week_courses[day][0].strftime("%A %d.%m."),
                    )

                if inside:
                    weeks.append([css, "", title])
                else:
                    inside = True
                    if calendar_week(day) == calendar_week(date_from):
                        weeks.append([css, date_from.day, title])
                    else:
                        # assignment has not started this week
                        weeks.append([css, "", title])
            else:
                if inside:
                    inside = False
                    weeks[-1][1] = date_until.day
                weeks.append(["", "", None])
        return weeks

    def add_quotas(self, with_accomodation, scope_statements):
        if with_accomodation is not None:
            self.quota_per_week = None
            return

        quota = DrudgeQuota.objects.filter(
            week__gte=self.date_from, week__lte=self.date_until
        ).order_by()

        if scope_statements:
            quota = quota.filter(scope_statement__in=scope_statements)

        self.quota_per_week = {
            q["week"]: q["quota__sum"]
            for q in quota.values("week").annotate(Sum("quota"))
        }

    def assignments(self):
        assignments_dict = OrderedDict()

        assignments = self.queryset.select_related(
            "specification__scope_statement", "drudge__user"
        ).order_by("date_from", "date_until")

        una_courses_per_week = defaultdict(list)

        for assignment in assignments:
            for day in daterange(
                assignment.date_from, assignment.determine_date_until()
            ):
                self.drudge_days_per_week.setdefault(
                    calendar_week(day), (_monday(day), defaultdict(int))
                )[1][assignment.drudge_id] += 1

            if assignment.environment_course_date and (
                assignment.date_from
                <= assignment.environment_course_date
                <= assignment.determine_date_until()
            ):
                # Only subtract env course if it is during the assignment.
                # (Can be outside in rare cases.)
                una_courses_per_week[
                    _monday(assignment.environment_course_date)
                ].append(assignment)

            if assignment.drudge not in assignments_dict:
                assignments_dict[assignment.drudge] = []

            assignments_dict[assignment.drudge].append(
                (
                    assignment,
                    self._schedule_assignment(
                        assignment.date_from,
                        assignment.determine_date_until(),
                        {
                            assignment.motor_saw_course_date: "MSK",
                            assignment.environment_course_date: "UNA",
                        },
                    ),
                )
            )

        # linearize assignments, but still give precedence to drudge
        assignments = list(itertools.chain.from_iterable(assignments_dict.values()))

        filtered_days_per_drudge_and_week = [
            (day, week)
            for day, week in self.drudge_days_per_week.values()
            if self.date_from <= day <= self.date_until
        ]

        # Weekly count is determined by the count of drudges which are
        # available at least 3 days in a week.
        def drudges_count_tuple(week):
            count = sum((1 for days in week.values() if days >= 3), 0)
            return ("", count, "")  # class, text, title

        quasi_full_drudge_weeks = [
            drudges_count_tuple(week) for day, week in filtered_days_per_drudge_and_week
        ]
        una_courses_per_week = [
            (
                "",
                len(una_courses_per_week.get(day, ())),
                "\n".join("%s" % a for a in una_courses_per_week.get(day, ())),
            )
            for day, week in filtered_days_per_drudge_and_week
        ]

        quota_per_week = [
            (
                "",
                (self.quota_per_week.get(day, "-") if self.quota_per_week else "-"),
                "",
            )
            for day, week in filtered_days_per_drudge_and_week
        ]

        full_drudge_weeks = [
            ["", a[1] - b[1], ""]
            for a, b in zip(quasi_full_drudge_weeks, una_courses_per_week)
        ]

        for a, b in zip(quota_per_week, full_drudge_weeks):
            try:
                quota = int(a[1])
            except (TypeError, ValueError):
                continue

            full = b[1]

            if full < quota - 6:
                b[0] = "quota darkblue"
            elif full < quota - 1:
                b[0] = "quota blue"
            elif full > quota + 6:
                b[0] = "quota red"
            elif full > quota + 1:
                b[0] = "quota orange"

        try:
            filtered_days_per_week = [
                sum(week.values(), 0.0)
                for day, week in filtered_days_per_drudge_and_week
            ]
            self.average = sum(filtered_days_per_week, 0.0) / (
                (self.date_until - self.date_from).days
            )
        except ArithmeticError:
            self.average = 0

        self.head = [
            # ['IST vor Abzug Kurse', quasi_full_drudge_weeks],
            # ['Umwelt-Kurse', una_courses_per_week],
            ["Zivi-Bedarf", quota_per_week],
            ["IST nach Abzug UNA-Kurse", full_drudge_weeks],
        ]

        return assignments


def _monday(day):
    return day - timedelta(days=day.weekday())


class SchedulingSearchForm(SearchForm):
    default = {
        "date_until__gte": lambda request: _monday(date.today()),
        "date_from__lte": lambda request: _monday(date.today())
        + timedelta(days=35 * 7 + 4),
        "status": (Assignment.TENTATIVE, Assignment.ARRANGED, Assignment.MOBILIZED),
    }

    specification__scope_statement = forms.ModelMultipleChoiceField(
        ScopeStatement.objects.all(),
        label=gettext_lazy("scope statement"),
        required=False,
    )
    specification__with_accomodation = forms.NullBooleanField(
        label=gettext_lazy("with accomodation"), required=False
    )
    status = forms.MultipleChoiceField(
        choices=Assignment.STATUS_CHOICES, label=gettext_lazy("status"), required=False
    )
    date_until__gte = forms.DateField(
        label=gettext_lazy("Start date"),
        required=False,
        widget=forms.DateInput(attrs={"class": "dateinput"}),
    )
    date_from__lte = forms.DateField(
        label=gettext_lazy("End date"),
        required=False,
        widget=forms.DateInput(attrs={"class": "dateinput"}),
    )

    drudge__motor_saw_course = forms.MultipleChoiceField(
        label=gettext_lazy("motor saw course"),
        required=False,
        choices=(
            ("2-day", gettext_lazy("2 day course")),
            ("5-day", gettext_lazy("5 day course")),
        ),
    )
    drudge__driving_license = forms.NullBooleanField(
        label=gettext_lazy("driving license"), required=False
    )

    def queryset(self):
        data = self.safe_cleaned_data
        queryset = self.apply_filters(
            Assignment.objects.search(data.get("query")),
            data,
            exclude=("date_until__gte",),
        )
        if data.get("date_until__gte"):
            queryset = queryset.filter(
                Q(
                    date_until_extension__isnull=True,
                    date_until__gte=data.get("date_until__gte"),
                )
                | Q(
                    date_until_extension__isnull=False,
                    date_until_extension__gte=data.get("date_until__gte"),
                )
            )
        return queryset


@staff_member_required
def scheduling(request):
    search_form = SchedulingSearchForm(request.GET, request=request)

    date_range = (
        search_form.safe_cleaned_data.get("date_until__gte"),
        search_form.safe_cleaned_data.get("date_from__lte"),
    )
    if not all(date_range):
        return HttpResponseRedirect("?clear=1")

    scheduler = Scheduler(search_form.queryset(), date_range)

    scheduler.add_quotas(
        with_accomodation=search_form.safe_cleaned_data.get(
            "specification__with_accomodation"
        ),
        scope_statements=search_form.safe_cleaned_data.get(
            "specification__scope_statement"
        ),
    )

    year = date.today().year

    return render(
        request,
        "zivinetz/scheduling.html",
        {
            "scheduler": scheduler,
            "search_form": search_form,
            "years": range(year, year + 4),
        },
    )
