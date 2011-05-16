# coding=utf-8

from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core import urlresolvers
from django.forms.models import modelform_factory, inlineformset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import simplejson
from django.utils.translation import ugettext as _, ugettext_lazy

from towel import modelview
from towel import forms as towel_forms

from zivinetz.models import Assignment, CompanyHoliday, Drudge,\
    ExpenseReport,\
    ExpenseReportPeriod, RegionalOffice, ScopeStatement,\
    Specification, WaitList, Assessment


class ZivinetzModelView(modelview.ModelView):
    def view_decorator(self, func):
        return staff_member_required(func)

    def crud_view_decorator(self, func):
        return staff_member_required(func)

    def get_context(self, request, context):
        ctx = super(ZivinetzModelView, self).get_context(request, context)
        ctx['base_template'] = 'zivinetz/base.html'
        return ctx

    def get_form(self, request, instance=None, **kwargs):
        return modelform_factory(self.model,
            formfield_callback=towel_forms.stripped_formfield_callback, **kwargs)


class RegionalOfficeModelView(ZivinetzModelView):
    def deletion_allowed(self, request, instance):
        return self.deletion_allowed_if_only(request, instance, [RegionalOffice])

regional_office_views = RegionalOfficeModelView(RegionalOffice)


SpecificationFormSet = inlineformset_factory(ScopeStatement,
    Specification,
    extra=0,
    formfield_callback=towel_forms.stripped_formfield_callback,
    )


class ScopeStatementModelView(ZivinetzModelView):
    def deletion_allowed(self, request, instance):
        return self.deletion_allowed_if_only(request, instance, [ScopeStatement, Specification])

scope_statement_views = ScopeStatementModelView(ScopeStatement)


class SpecificationModelView(ZivinetzModelView):
    def deletion_allowed(self, request, instance):
        return self.deletion_allowed_if_only(request, instance, [Specification])

specification_views = SpecificationModelView(Specification)


AssessmentFormSet = inlineformset_factory(Drudge,
    Assessment,
    extra=0,
    exclude=('created',),
    formfield_callback=towel_forms.stripped_formfield_callback,
    )


class DrudgeModelView(ZivinetzModelView):
    paginate_by = 50

    def additional_urls(self):
        return [
            (r'^autocomplete/$', self.view_decorator(self.autocomplete)),
        ]

    def autocomplete(self, request):
        queryset = Drudge.objects.search(request.GET.get('term', ''))

        return HttpResponse(simplejson.dumps([{
            'label': unicode(d),
            'value': d.id,
            } for d in queryset[:20]]), mimetype='application/json')

    class search_form(towel_forms.SearchForm):
        regional_office = forms.ModelChoiceField(RegionalOffice.objects.all(),
            label=ugettext_lazy('regional office'), required=False)
        only_active = forms.BooleanField(label=ugettext_lazy('only active'),
            required=False)

        def queryset(self, model):
            data = self.safe_cleaned_data
            queryset = self.apply_filters(model.objects.search(data.get('query')),
                data, exclude=('only_active',))

            from datetime import date
            if data.get('only_active'):
                queryset = queryset.filter(
                    id__in=Assignment.objects.for_date().filter(status__in=(
                        Assignment.ARRANGED, Assignment.MOBILIZED)).values('drudge'))

            return queryset

    def deletion_allowed(self, request, instance):
        return self.deletion_allowed_if_only(request, instance, [Drudge])

    def get_formset_instances(self, request, instance=None, change=None, **kwargs):
        args = self.extend_args_if_post(request, [])
        kwargs['instance'] = instance

        return {
            'assessments': AssessmentFormSet(*args, **kwargs),
            }

drudge_views = DrudgeModelView(Drudge)


ExpenseReportFormSet = inlineformset_factory(Assignment,
    ExpenseReport,
    extra=0,
    formfield_callback=towel_forms.stripped_formfield_callback,
    fields=('date_from', 'date_until', 'report_no', 'status'),
    )


class AssignmentModelView(ZivinetzModelView):
    paginate_by = 50

    class search_form(towel_forms.SearchForm):
        #default = {
        #    'status': (Assignment.TENTATIVE, Assignment.ARRANGED),
        #    }

        specification__scope_statement = forms.ModelChoiceField(
            ScopeStatement.objects.all(), label=ugettext_lazy('scope statement'), required=False)
        drudge = forms.ModelChoiceField(Drudge.objects.all(),
            widget=towel_forms.ModelAutocompleteWidget(url=
                lambda: urlresolvers.reverse('zivinetz_drudge_autocomplete')),
            label=ugettext_lazy('drudge'), required=False)
        status = forms.MultipleChoiceField(
            Assignment.STATUS_CHOICES, label=ugettext_lazy('status'), required=False)

    def additional_urls(self):
        return [
            (r'^autocomplete/$', self.view_decorator(self.autocomplete)),
        ]

    def autocomplete(self, request):
        queryset = Assignment.objects.search(request.GET.get('term', ''))

        return HttpResponse(simplejson.dumps([{
            'label': unicode(d),
            'value': d.id,
            } for d in queryset[:20]]), mimetype='application/json')

    def get_form(self, request, instance=None, **kwargs):
        return super(AssignmentModelView, self).get_form(request, instance=instance,
            exclude=('created',))

    def deletion_allowed(self, request, instance):
        return self.deletion_allowed_if_only(request, instance, [Assignment])

    def get_formset_instances(self, request, instance=None, change=None, **kwargs):
        args = self.extend_args_if_post(request, [])
        kwargs['instance'] = instance

        return {
            'expensereports': ExpenseReportFormSet(*args, **kwargs),
            }

    def post_save(self, request, instance, form, formset, change):
        if not instance.reports.count():
            days, monthly_expense_days = instance.assignment_days()

            for month, data in monthly_expense_days:
                report = instance.reports.create(
                    date_from=data['start'],
                    date_until=data['end'],
                    working_days=data['working'],
                    free_days=data['free'],
                    sick_days=0,
                    holi_days=0,
                    forced_leave_days=data['forced'],
                    )

                report.periods.create(
                    specification=instance.specification,
                    date_from=report.date_from,
                    )


assignment_views = AssignmentModelView(Assignment)


ExpenseReportPeriodFormSet = inlineformset_factory(ExpenseReport,
    ExpenseReportPeriod,
    extra=0,
    formfield_callback=towel_forms.stripped_formfield_callback,
    )


class ExpenseReportModelView(ZivinetzModelView):
    paginate_by = 50

    class search_form(towel_forms.SearchForm):
        assignment = forms.ModelChoiceField(
            Assignment.objects.all(), label=ugettext_lazy('assignment'),
            widget=towel_forms.ModelAutocompleteWidget(url=
                lambda: urlresolvers.reverse('zivinetz_assignment_autocomplete')),
            required=False)
        assignment__drudge = forms.ModelChoiceField(
            Drudge.objects.all(), label=ugettext_lazy('drudge'),
            widget=towel_forms.ModelAutocompleteWidget(url=
                lambda: urlresolvers.reverse('zivinetz_drudge_autocomplete')),
            required=False)

    def deletion_allowed(self, request, instance):
        return self.deletion_allowed_if_only(request, instance,
            [ExpenseReport, ExpenseReportPeriod])

    def get_form(self, request, instance=None, **kwargs):
        return super(ExpenseReportModelView, self).get_form(request, instance=instance,
            exclude=('assignment',))

    def get_formset_instances(self, request, instance=None, change=None, **kwargs):
        args = self.extend_args_if_post(request, [])
        kwargs['instance'] = instance

        return {
            'periods': ExpenseReportPeriodFormSet(*args, **kwargs),
            }

expense_report_views = ExpenseReportModelView(ExpenseReport)


class WaitListModelView(ZivinetzModelView):
    paginate_by = 50

    def deletion_allowed(self, request, instance):
        return True

waitlist_views = WaitListModelView(WaitList)
