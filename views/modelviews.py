# coding=utf-8

from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.forms.models import modelform_factory, inlineformset_factory
from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext as _, ugettext_lazy

from towel import modelview
from towel import forms as towel_forms

from zivinetz.models import Assignment, CompanyHoliday, Drudge,\
    ExpenseReport,\
    ExpenseReportPeriod, RegionalOffice, ScopeStatement,\
    Specification


class ZivinetzModelView(modelview.ModelView):
    def view_decorator(self, func):
        return login_required(func)

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


class DrudgeModelView(ZivinetzModelView):
    paginate_by = 50

    class search_form(towel_forms.SearchForm):
        regional_office = forms.ModelChoiceField(RegionalOffice.objects.all(),
            label=ugettext_lazy('regional office'), required=False)

    def deletion_allowed(self, request, instance):
        return self.deletion_allowed_if_only(request, instance, [Drudge])

drudge_views = DrudgeModelView(Drudge)


class AssignmentModelView(ZivinetzModelView):
    paginate_by = 50

    class search_form(towel_forms.SearchForm):
        default = {
            'status': (Assignment.TENTATIVE, Assignment.ARRANGED),
            }

        specification__scope_statement = forms.ModelChoiceField(
            ScopeStatement.objects.all(), label=ugettext_lazy('scope statement'), required=False)
        drudge = forms.ModelChoiceField(
            Drudge.objects.all(), label=ugettext_lazy('drudge'), required=False)
        status = forms.MultipleChoiceField(
            Assignment.STATUS_CHOICES, label=ugettext_lazy('status'), required=False)

    def deletion_allowed(self, request, instance):
        return self.deletion_allowed_if_only(request, instance, [Assignment])

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
            Assignment.objects.all(), label=ugettext_lazy('assignment'), required=False)
        assignment__drudge = forms.ModelChoiceField(
            Drudge.objects.all(), label=ugettext_lazy('drudge'), required=False)

    def deletion_allowed(self, request, instance):
        return self.deletion_allowed_if_only(request, instance,
            [ExpenseReport, ExpenseReportPeriod])

    def get_formset_instances(self, request, instance=None, change=None, **kwargs):
        args = self.extend_args_if_post(request, [])
        kwargs['instance'] = instance

        return {
            'periods': ExpenseReportPeriodFormSet(*args, **kwargs),
            }

expense_report_views = ExpenseReportModelView(ExpenseReport)
