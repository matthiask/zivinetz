# coding=utf-8

from datetime import date
from StringIO import StringIO

from django import forms
from django.db.models import Q
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core import urlresolvers
from django.core.mail import EmailMessage
from django.db.models import Avg
from django.forms.models import modelform_factory, inlineformset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template import Template, Context
from django.utils import simplejson
from django.utils.translation import ugettext as _, ugettext_lazy

from towel import modelview
from towel import forms as towel_forms

from pdfdocument.document import PDFDocument, cm, mm
from pdfdocument.utils import pdf_response

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

    def get_form(self, request, instance=None, change=None, **kwargs):
        return modelform_factory(self.model,
            formfield_callback=towel_forms.towel_formfield_callback, **kwargs)


class RegionalOfficeModelView(ZivinetzModelView):
    def deletion_allowed(self, request, instance):
        return self.deletion_allowed_if_only(request, instance, [RegionalOffice])

regional_office_views = RegionalOfficeModelView(RegionalOffice)


SpecificationFormSet = inlineformset_factory(ScopeStatement,
    Specification,
    extra=0,
    formfield_callback=towel_forms.towel_formfield_callback,
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
    formfield_callback=towel_forms.towel_formfield_callback,
    )


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
        orderings = {
            'date_joined': 'user__date_joined',
            }
        regional_office = forms.ModelChoiceField(RegionalOffice.objects.all(),
            label=ugettext_lazy('regional office'), required=False)
        only_active = forms.BooleanField(label=ugettext_lazy('only active'),
            required=False)
        motor_saw_course = forms.MultipleChoiceField(
            label=ugettext_lazy('motor saw course'), required=False,
            choices=Drudge.MOTOR_SAW_COURSE_CHOICES)
        driving_license = forms.NullBooleanField(
            label=ugettext_lazy('driving license'), required=False)

        def queryset(self, model):
            query, data = self.query_data()
            queryset = self.apply_filters(model.objects.search(query),
                data, exclude=('only_active',))

            if data.get('only_active'):
                queryset = queryset.filter(
                    id__in=Assignment.objects.for_date().filter(status__in=(
                        Assignment.ARRANGED, Assignment.MOBILIZED)).values('drudge'))

            return self.apply_ordering(queryset, data.get('o')).transform(
                add_last_assignment_and_mark)

    class batch_form(towel_forms.BatchForm):
        mail_subject = forms.CharField(label=_('subject'))
        mail_body = forms.CharField(label=_('body'), widget=forms.Textarea)
        mail_attachment = forms.FileField(label=_('attachment'), required=False)

        def process(self):
            mails = 0
            for drudge in self.batch_queryset.select_related('user'):
                message = EmailMessage(
                    subject=self.cleaned_data['mail_subject'],
                    body=self.cleaned_data['mail_body'],
                    to=[drudge.user.email],
                    from_email='info@naturnetz.ch',
                    headers={
                        'Reply-To': self.request.user.email,
                    })
                if self.cleaned_data['mail_attachment']:
                    message.attach(
                        self.cleaned_data['mail_attachment'].name,
                        self.cleaned_data['mail_attachment'].read(),
                        )
                message.send()
                mails += 1

            if mails:
                messages.success(self.request, _('Successfully sent mails to %s people.') % mails)
            else:
                messages.error(self.request, _('Did not send any mails. Did you select people?'))

            return self.batch_queryset

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
    formfield_callback=towel_forms.towel_formfield_callback,
    fields=('date_from', 'date_until', 'report_no', 'status'),
    )


class AssignmentModelView(ZivinetzModelView):
    paginate_by = 50

    class search_form(towel_forms.SearchForm):
        #default = {
        #    'status': (Assignment.TENTATIVE, Assignment.ARRANGED),
        #    }

        specification__scope_statement = forms.ModelMultipleChoiceField(
            ScopeStatement.objects.all(), label=ugettext_lazy('scope statements'), required=False)
        drudge = forms.ModelChoiceField(Drudge.objects.all(),
            widget=towel_forms.ModelAutocompleteWidget(url=
                lambda: urlresolvers.reverse('zivinetz_drudge_autocomplete')),
            label=ugettext_lazy('drudge'), required=False)

        active_on = forms.DateField(label=ugettext_lazy('active on'), required=False,
            widget=forms.DateInput(attrs={'class': 'dateinput'}))

        service_between = forms.DateField(label=ugettext_lazy('service between'),
            required=False,
            widget=forms.DateInput(attrs={'class': 'dateinput'}),
            help_text=ugettext_lazy('Drudges in service any time between the following two dates.'))
        service_and = forms.DateField(label=ugettext_lazy('and'),
            required=False,
            widget=forms.DateInput(attrs={'class': 'dateinput'}))

        status = forms.MultipleChoiceField(
            Assignment.STATUS_CHOICES, label=ugettext_lazy('status'), required=False)

        def queryset(self, model):
            query, data = self.query_data()
            queryset = model.objects.search(query)
            queryset = self.apply_filters(queryset, data,
                exclude=('active_on', 'service_between', 'service_and'))

            if data.get('active_on'):
                active_on = data.get('active_on')

                queryset = queryset.filter(Q(date_from__lte=active_on) & (
                    (Q(date_until_extension__isnull=True) & Q(date_until__gte=active_on)) |
                    Q(date_until_extension__isnull=False, date_until_extension__gte=active_on)
                    ))

            if data.get('service_between') and data.get('service_and'):
                queryset = queryset.filter(
                    Q(date_from__lte=data.get('service_and'))
                    & Q(date_until__gte=data.get('service_between')))

            return self.apply_ordering(queryset, data.get('o'))

    class batch_form(towel_forms.BatchForm):
        mail_subject = forms.CharField(label=_('subject'))
        mail_body = forms.CharField(label=_('body'), widget=forms.Textarea)
        mail_attachment = forms.FileField(label=_('attachment'), required=False)

        def process(self):
            mails = 0
            for assignment in self.batch_queryset.select_related('drudge__user'):
                message = EmailMessage(
                    subject=self.cleaned_data['mail_subject'],
                    body=self.cleaned_data['mail_body'],
                    to=[assignment.drudge.user.email],
                    from_email='info@naturnetz.ch',
                    headers={
                        'Reply-To': self.request.user.email,
                    })
                if self.cleaned_data['mail_attachment']:
                    message.attach(
                        self.cleaned_data['mail_attachment'].name,
                        self.cleaned_data['mail_attachment'].read(),
                        )
                message.send()
                mails += 1

            if mails:
                messages.success(self.request, _('Successfully sent mails to %s people.') % mails)
            else:
                messages.error(self.request, _('Did not send any mails. Did you select people?'))

            return self.batch_queryset

    def additional_urls(self):
        return [
            (r'^autocomplete/$', self.view_decorator(self.autocomplete)),
            (r'^%(detail)s/create_expensereports/$', self.crud_view_decorator(self.create_expensereports)),
            (r'^%(detail)s/remove_expensereports/$', self.crud_view_decorator(self.remove_expensereports)),
        ]

    def autocomplete(self, request):
        queryset = Assignment.objects.search(request.GET.get('term', ''))

        return HttpResponse(simplejson.dumps([{
            'label': unicode(d),
            'value': d.id,
            } for d in queryset[:20]]), mimetype='application/json')

    def create_expensereports(self, request, *args, **kwargs):
        instance = self.get_object_or_404(request, *args, **kwargs)
        created = instance.generate_expensereports()

        if created:
            messages.success(request, _('Successfully created %s expense reports.') % created)
        else:
            messages.info(request, _('No expense reports created, all months occupied already?'))
        return redirect(instance)

    def remove_expensereports(self, request, *args, **kwargs):
        instance = self.get_object_or_404(request, *args, **kwargs)
        instance.reports.filter(status=ExpenseReport.PENDING).delete()
        messages.success(request, _('Successfully removed pending expense reports.'))
        return redirect(instance)

    def handle_search_form(self, request, *args, **kwargs):
        queryset, response = super(AssignmentModelView, self).handle_search_form(request, *args, **kwargs)

        if request.GET.get('s') == 'xls':
            pdf, response = pdf_response('phones')
            pdf.init_report()

            specification = None
            for assignment in queryset.order_by('specification', 'drudge'):
                drudge = assignment.drudge

                if specification != assignment.specification:
                    pdf.h2(unicode(assignment.specification))
                    specification = assignment.specification

                pdf.table([
                    (unicode(drudge), drudge.user.email, u'%s - %s' % (
                        assignment.date_from.strftime('%d.%m.%y'),
                        assignment.determine_date_until().strftime('%d.%m.%y'),
                        )),
                    (drudge.phone_home, drudge.phone_office, drudge.mobile),
                    (u'%s, %s %s' % (
                        drudge.address,
                        drudge.zip_code,
                        drudge.city,
                        ),
                        '',
                        drudge.education_occupation),
                    ], (6.4*cm, 5*cm, 5*cm))
                pdf.hr_mini()

            pdf.generate()
            return queryset, response

        return queryset, response

    def get_form(self, request, instance=None, change=None, **kwargs):
        base_form = super(AssignmentModelView, self).get_form(request, instance=instance,
                exclude=('created',))

        class AssignmentForm(base_form):
            class Meta:
                model = Assignment
                widgets = {
                    'drudge': towel_forms.ModelAutocompleteWidget(
                        url=urlresolvers.reverse('zivinetz_drudge_autocomplete')),
                }

            def clean(self):
                data = super(AssignmentForm, self).clean()

                if data['status'] == Assignment.MOBILIZED:
                    if not data.get('mobilized_on'):
                        raise forms.ValidationError(
                            _('Mobilized on date must be set when status is mobilized.'))
                return data

        return AssignmentForm

    def deletion_allowed(self, request, instance):
        return self.deletion_allowed_if_only(request, instance, [Assignment])

    def get_formset_instances(self, request, instance=None, change=None, **kwargs):
        args = self.extend_args_if_post(request, [])
        kwargs['instance'] = instance

        return {
            'expensereports': ExpenseReportFormSet(*args, **kwargs),
            }

    def post_save(self, request, instance, form, formset, change):
        for report in instance.reports.all():
            report.recalculate_total()

        if 'date_until_extension' in form.changed_data:
            messages.warning(request,
                _('The extended until date has been changed. Please check'
                    ' whether you need to generate additional expense'
                    ' reports.'))


assignment_views = AssignmentModelView(Assignment)


ExpenseReportPeriodFormSet = inlineformset_factory(ExpenseReport,
    ExpenseReportPeriod,
    extra=0,
    formfield_callback=towel_forms.towel_formfield_callback,
    )


class EditExpenseReportForm(forms.ModelForm, towel_forms.WarningsForm):
    class Meta:
        model = ExpenseReport
        exclude = ('assignment', 'total', 'calculated_total_days')

    def clean(self):
        data = super(EditExpenseReportForm, self).clean()

        try:
            total_days = (data['working_days'] + data['free_days'] + data['sick_days']
                + data['holi_days'] + data['forced_leave_days'])
        except (ValueError, TypeError):
            return data

        if total_days != self.instance.calculated_total_days:
            self.add_warning(
                _('The number of days in this form (%(total)s) differs from the calculated number of days for this period (%(calculated)s).') % {
                    'total': total_days,
                    'calculated': self.instance.calculated_total_days,
                    })

        return data


class ExpenseReportModelView(ZivinetzModelView):
    paginate_by = 50

    class search_form(towel_forms.SearchForm):
        default = {
            'assignment__status': (Assignment.ARRANGED, Assignment.MOBILIZED),
            }

        assignment__specification__scope_statement = forms.ModelMultipleChoiceField(
            queryset=ScopeStatement.objects.all(), label=ugettext_lazy('scope statement'),
            required=False)
        assignment__status = forms.MultipleChoiceField(Assignment.STATUS_CHOICES,
            label=ugettext_lazy('assignment status'), required=False)
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

    def handle_search_form(self, request, *args, **kwargs):
        queryset, response = super(ExpenseReportModelView, self).handle_search_form(request, *args, **kwargs)

        if request.GET.get('s') == 'pdf':
            from zivinetz.views import expenses
            return queryset, expenses.generate_expense_statistics_pdf(queryset)

        return queryset, response

    def editing_allowed(self, request, instance):
        if instance and instance.pk:
            return instance.status < instance.PAID
        return True

    def deletion_allowed(self, request, instance):
        return self.deletion_allowed_if_only(request, instance,
            [ExpenseReport, ExpenseReportPeriod])

    def get_form(self, request, instance=None, change=None, **kwargs):
        if instance and instance.pk:
            return EditExpenseReportForm
        else:
            class ModelForm(forms.ModelForm):
                assignment = forms.ModelChoiceField(
                    Assignment.objects.all(), label=ugettext_lazy('assignment'),
                    widget=towel_forms.ModelAutocompleteWidget(url=
                        lambda: urlresolvers.reverse('zivinetz_assignment_autocomplete')))

                class Meta:
                    model = self.model
                    exclude = ('total', 'calculated_total_days')

                formfield_callback = towel_forms.towel_formfield_callback

            return ModelForm

    def get_formset_instances(self, request, instance=None, change=None, **kwargs):
        args = self.extend_args_if_post(request, [])
        kwargs['instance'] = instance

        return {
            'periods': ExpenseReportPeriodFormSet(*args, **kwargs),
            }

    def post_save(self, request, instance, form, formset, change):
        if not change and not instance.periods.count():
            instance.periods.create(
                specification=instance.assignment.specification,
                date_from=instance.date_from)
        instance.recalculate_total()

        if request.POST.get('transport_expenses_copy'):
            for report in instance.assignment.reports.filter(date_from__gt=instance.date_from):
                report.transport_expenses = instance.transport_expenses
                report.transport_expenses_notes = instance.transport_expenses_notes
                report.recalculate_total()

expense_report_views = ExpenseReportModelView(ExpenseReport)


class WaitListModelView(ZivinetzModelView):
    paginate_by = 50

    class search_form(towel_forms.SearchForm):
        specification__scope_statement = forms.ModelMultipleChoiceField(
            queryset=ScopeStatement.objects.all(), label=ugettext_lazy('scope statement'),
            required=False)
        drudge = forms.ModelChoiceField(
            Drudge.objects.all(), label=ugettext_lazy('drudge'),
            widget=towel_forms.ModelAutocompleteWidget(url=
                lambda: urlresolvers.reverse('zivinetz_drudge_autocomplete')),
            required=False)
        assignment_date_from__gte = forms.DateField(label=ugettext_lazy('date from'), required=False,
            widget=forms.DateInput(attrs={'class': 'dateinput'}))
        assignment_date_until__lte = forms.DateField(label=ugettext_lazy('date until'), required=False,
            widget=forms.DateInput(attrs={'class': 'dateinput'}))

    class batch_form(towel_forms.BatchForm):
        mail_subject = forms.CharField(label=_('subject'))
        mail_body = forms.CharField(label=_('body'), widget=forms.Textarea)
        mail_attachment = forms.FileField(label=_('attachment'), required=False)

        def process(self):
            mails = 0
            for entry in self.batch_queryset.select_related('drudge__user'):
                message = EmailMessage(
                    subject=self.cleaned_data['mail_subject'],
                    body=self.cleaned_data['mail_body'],
                    to=[entry.drudge.user.email],
                    from_email='info@naturnetz.ch',
                    headers={
                        'Reply-To': self.request.user.email,
                    })
                if self.cleaned_data['mail_attachment']:
                    message.attach(
                        self.cleaned_data['mail_attachment'].name,
                        self.cleaned_data['mail_attachment'].read(),
                        )
                message.send()
                mails += 1

            if mails:
                messages.success(self.request, _('Successfully sent mails to %s people.') % mails)
            else:
                messages.error(self.request, _('Did not send any mails. Did you select people?'))

            return self.batch_queryset

    def deletion_allowed(self, request, instance):
        return True

waitlist_views = WaitListModelView(WaitList)


class JobReferenceModelView(ZivinetzModelView):
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
        created__gte = forms.DateField(label=ugettext_lazy('date from'), required=False,
            widget=forms.DateInput(attrs={'class': 'dateinput'}))
        created__lte = forms.DateField(label=ugettext_lazy('date until'), required=False,
            widget=forms.DateInput(attrs={'class': 'dateinput'}))

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

    def get_form(self, request, instance=None, change=None, **kwargs):
        return super(JobReferenceModelView, self).get_form(request, instance=instance,
            exclude=('assignment',))

    def adding_allowed(self, request):
        return False

    def deletion_allowed(self, request, instance):
        return True

jobreference_views = JobReferenceModelView(JobReference)
