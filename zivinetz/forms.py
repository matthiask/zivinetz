from django import forms
from django.db.models import Avg
from django.utils.translation import ugettext_lazy as _

from towel.forms import SearchForm

from zivinetz.models import (Assessment, Assignment, Drudge, RegionalOffice,
    ScopeStatement)


def add_last_assignment_and_mark(queryset):
    drudges = dict((d.id, d) for d in queryset)
    marks = Assessment.objects.filter(drudge__in=drudges.keys()).order_by().values(
        'drudge').annotate(Avg('mark'))

    for mark in marks:
        drudges[mark['drudge']].average_mark = mark['mark__avg']

    for assignment in Assignment.objects.select_related(
            'specification__scope_statement').order_by('-date_from').iterator():

        if assignment.drudge_id in drudges:
            drudges[assignment.drudge_id].last_assignment = assignment
            del drudges[assignment.drudge_id]

        if not drudges:
            # All drudges have a last assignment now
            break


class DrudgeSearchForm(SearchForm):
    orderings = {
        'date_joined': 'user__date_joined',
        }
    regional_office = forms.ModelChoiceField(RegionalOffice.objects.all(),
        label=_('regional office'), required=False)
    only_active = forms.BooleanField(label=_('only active'),
        required=False)
    motor_saw_course = forms.MultipleChoiceField(
        label=_('motor saw course'), required=False,
        choices=Drudge.MOTOR_SAW_COURSE_CHOICES)
    driving_license = forms.NullBooleanField(
        label=_('driving license'), required=False)

    def queryset(self, model):
        query, data = self.query_data()
        queryset = self.apply_filters(model.objects.search(query),
            data, exclude=('only_active',))

        if data.get('only_active'):
            queryset = queryset.filter(
                id__in=Assignment.objects.for_date().filter(status__in=(
                    Assignment.ARRANGED, Assignment.MOBILIZED,
                    )).values('drudge'))

        return self.apply_ordering(queryset, data.get('o')).transform(
            add_last_assignment_and_mark)


class WaitListSearchForm(SearchForm):
    specification__scope_statement = forms.ModelMultipleChoiceField(
        queryset=ScopeStatement.objects.all(),
        label=_('scope statement'),
        required=False)
    assignment_date_from__gte = forms.DateField(
        label=_('date from'), required=False,
        widget=forms.DateInput(attrs={'class': 'dateinput'}))
    assignment_date_until__lte = forms.DateField(
        label=_('date until'), required=False,
        widget=forms.DateInput(attrs={'class': 'dateinput'}))
