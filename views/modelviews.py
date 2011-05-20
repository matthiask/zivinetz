# coding=utf-8

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core import urlresolvers
from django.forms.models import modelform_factory, inlineformset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template import Template, Context
from django.utils import simplejson
from django.utils.translation import ugettext as _, ugettext_lazy

from towel import modelview
from towel import forms as towel_forms

from zivinetz.models import (Assignment, CompanyHoliday, Drudge,
    ExpenseReport, ExpenseReportPeriod, RegionalOffice, ScopeStatement,
    Specification, WaitList, Assessment, JobReferenceTemplate,
    JobReference)


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
        assignment__specification__scope_statement = forms.ModelMultipleChoiceField(
            queryset=ScopeStatement.objects.all(), label=ugettext_lazy('scope statement'),
            required=False)
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
        status = forms.MultipleChoiceField(
            ExpenseReport.STATUS_CHOICES, label=ugettext_lazy('status'), required=False)
        date_from__gte = forms.DateField(label=ugettext_lazy('date from'), required=False,
            widget=forms.DateInput(attrs={'class': 'dateinput'}))
        date_until__lte = forms.DateField(label=ugettext_lazy('date until'), required=False,
            widget=forms.DateInput(attrs={'class': 'dateinput'}))

    def deletion_allowed(self, request, instance):
        return self.deletion_allowed_if_only(request, instance,
            [ExpenseReport, ExpenseReportPeriod])

    def get_form(self, request, instance=None, **kwargs):
        return super(ExpenseReportModelView, self).get_form(request, instance=instance,
            exclude=('assignment', 'total'))

    def get_formset_instances(self, request, instance=None, change=None, **kwargs):
        args = self.extend_args_if_post(request, [])
        kwargs['instance'] = instance

        return {
            'periods': ExpenseReportPeriodFormSet(*args, **kwargs),
            }

    def post_save(self, request, instance, form, formset, change):
        instance.recalculate_total()

expense_report_views = ExpenseReportModelView(ExpenseReport)


class WaitListModelView(ZivinetzModelView):
    paginate_by = 50

    def deletion_allowed(self, request, instance):
        return True

waitlist_views = WaitListModelView(WaitList)


class JobReferenceModelView(ZivinetzModelView):
    paginate_by = 50

    def additional_urls(self):
        return [
            (r'^from_template/(\d+)/(\d+)/$', self.crud_view_decorator(self.from_template)),
        ]

    def from_template(self, request, template_id, assignment_id):
        template = get_object_or_404(JobReferenceTemplate, pk=template_id)
        assignment = get_object_or_404(Assignment, pk=assignment_id)

        instance = self.model(
            assignment=assignment,
            created=assignment.determine_date_until(),
            )

        template = Template(template.text)
        ctx = {
            'full_name': assignment.drudge.user.get_full_name(),
            'last_name': assignment.drudge.user.last_name,
            'date_from': assignment.date_from.strftime('%d.%m.%Y'),
            'date_until': assignment.determine_date_until().strftime('%d.%m.%Y'),
            'place_of_citizenship': u'%s %s' % (
                assignment.drudge.place_of_citizenship_city,
                assignment.drudge.place_of_citizenship_state,
                ),
            }

        if assignment.drudge.date_of_birth:
            ctx['birth_date'] = assignment.drudge.date_of_birth.strftime('%d.%m.%Y')
        else:
            ctx['birth_date'] = '-' * 10

        instance.text = template.render(Context(ctx))
        instance.save()

        messages.success(request, _('Successfully created job reference.'))

        return HttpResponseRedirect(instance.get_absolute_url() + 'edit/')

    def get_form(self, request, instance=None, **kwargs):
        return super(JobReferenceModelView, self).get_form(request, instance=instance,
            exclude=('assignment',))

    def deletion_allowed(self, request, instance):
        return True

jobreference_views = JobReferenceModelView(JobReference)
