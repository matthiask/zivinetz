from django import forms
from django.db.models import Avg, Q
from django.utils.translation import ugettext_lazy as _

from towel.forms import SearchForm, WarningsForm

from zivinetz.models import (Assessment, Assignment, Drudge, ExpenseReport,
    JobReference, RegionalOffice, ScopeStatement)


def add_last_assignment_and_mark(queryset):
    drudges = dict((d.id, d) for d in queryset)
    marks = Assessment.objects.filter(
        drudge__in=drudges.keys(),
    ).order_by().values('drudge').annotate(Avg('mark'))

    for mark in marks:
        drudges[mark['drudge']].average_mark = mark['mark__avg']

    for assignment in Assignment.objects.select_related(
            'specification__scope_statement'
            ).order_by('-date_from').iterator():

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


class AssessmentForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = ('mark', 'comment')


class AssignmentSearchForm(SearchForm):
    specification__scope_statement = forms.ModelMultipleChoiceField(
        ScopeStatement.objects.all(),
        label=_('scope statements'), required=False)

    active_on = forms.DateField(label=_('active on'), required=False,
        widget=forms.DateInput(attrs={'class': 'dateinput'}))

    service_between = forms.DateField(label=_('service between'),
        required=False,
        widget=forms.DateInput(attrs={'class': 'dateinput'}),
        help_text=_(
            'Drudges in service any time between the following two dates.'))
    service_and = forms.DateField(label=_('and'),
        required=False,
        widget=forms.DateInput(attrs={'class': 'dateinput'}))

    status = forms.MultipleChoiceField(
        Assignment.STATUS_CHOICES, label=_('status'), required=False)

    def queryset(self, model):
        query, data = self.query_data()
        queryset = model.objects.search(query)
        queryset = self.apply_filters(queryset, data,
            exclude=('active_on', 'service_between', 'service_and'))

        if data.get('active_on'):
            active_on = data.get('active_on')

            queryset = queryset.filter(
                Q(date_from__lte=active_on)
                & (
                    (Q(date_until_extension__isnull=True)
                        & Q(date_until__gte=active_on))
                    | Q(date_until_extension__isnull=False,
                        date_until_extension__gte=active_on)))

        if data.get('service_between') and data.get('service_and'):
            queryset = queryset.filter(
                Q(date_from__lte=data.get('service_and'))
                & Q(date_until__gte=data.get('service_between')))

        return self.apply_ordering(queryset, data.get('o'))


class ExpenseReportSearchForm(SearchForm):
    default = {
        'assignment__status': (Assignment.ARRANGED, Assignment.MOBILIZED),
        }

    assignment__specification__scope_statement =\
        forms.ModelMultipleChoiceField(
            queryset=ScopeStatement.objects.all(),
            label=_('scope statement'), required=False)
    assignment__status = forms.MultipleChoiceField(Assignment.STATUS_CHOICES,
        label=_('assignment status'), required=False)
    status = forms.MultipleChoiceField(
        ExpenseReport.STATUS_CHOICES, label=_('status'),
        required=False)
    date_from__gte = forms.DateField(label=_('date from'),
        required=False,
        widget=forms.DateInput(attrs={'class': 'dateinput'}))
    date_until__lte = forms.DateField(label=_('date until'),
        required=False,
        widget=forms.DateInput(attrs={'class': 'dateinput'}))


class EditExpenseReportForm(forms.ModelForm, WarningsForm):
    class Meta:
        model = ExpenseReport
        exclude = ('assignment', 'total', 'calculated_total_days')

    def clean(self):
        data = super(EditExpenseReportForm, self).clean()

        try:
            total_days = (
                data['working_days']
                + data['free_days']
                + data['sick_days']
                + data['holi_days']
                + data['forced_leave_days'])
        except (KeyError, ValueError, TypeError):
            return data

        if total_days != self.instance.calculated_total_days:
            self.add_warning(
                _(
                    'The number of days in this form (%(total)s) differs from'
                    ' the calculated number of days for this period'
                    ' (%(calculated)s).'
                    ) % {
                    'total': total_days,
                    'calculated': self.instance.calculated_total_days})

        return data


class JobReferenceSearchForm(SearchForm):
    assignment__specification__scope_statement =\
        forms.ModelMultipleChoiceField(
            queryset=ScopeStatement.objects.all(),
            label=_('scope statement'),
            required=False)
    created__gte = forms.DateField(label=_('date from'),
        required=False,
        widget=forms.DateInput(attrs={'class': 'dateinput'}))
    created__lte = forms.DateField(label=_('date until'),
        required=False,
        widget=forms.DateInput(attrs={'class': 'dateinput'}))


class JobReferenceForm(forms.ModelForm):
    class Meta:
        model = JobReference
        fields = ('text',)


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
