# coding=utf-8

from StringIO import StringIO

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import EmailMessage
from django.forms.models import modelform_factory
from django.shortcuts import redirect
from django.utils.translation import ugettext as _

from towel.forms import BatchForm, towel_formfield_callback

from towel_foundation.modelview import PickerModelView
from towel_foundation.widgets import SelectWithPicker

from pdfdocument.document import cm
from pdfdocument.utils import pdf_response

from zivinetz.forms import (AssignmentSearchForm, DrudgeSearchForm,
    AssessmentFormSet, ExpenseReportFormSet)
from zivinetz.models import Assignment, Drudge, ExpenseReport


def create_email_batch_form(selector):
    class EmailBatchForm(BatchForm):
        mail_subject = forms.CharField(label=_('subject'))
        mail_body = forms.CharField(label=_('body'), widget=forms.Textarea)
        mail_attachment = forms.FileField(label=_('attachment'),
            required=False)

        def process(self):
            mails = 0
            attachment = None

            if self.cleaned_data['mail_attachment']:
                attachment = StringIO(
                    self.cleaned_data['mail_attachment'].read())

            for email in set(
                    self.batch_queryset.values_list(selector, flat=True)):
                message = EmailMessage(
                    subject=self.cleaned_data['mail_subject'],
                    body=self.cleaned_data['mail_body'],
                    to=[email],
                    from_email='info@naturnetz.ch',
                    headers={
                        'Reply-To': self.request.user.email,
                    })
                if self.cleaned_data['mail_attachment']:
                    message.attach(
                        self.cleaned_data['mail_attachment'].name,
                        attachment.getvalue(),
                        )
                message.send()
                mails += 1

            if mails:
                messages.success(self.request,
                    _('Successfully sent mails to %s people.') % mails)
            else:
                messages.error(self.request,
                    _('Did not send any mails. Did you select people?'))

            return self.batch_queryset

    return EmailBatchForm


class ZivinetzModelView(PickerModelView):
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
            formfield_callback=towel_formfield_callback, **kwargs)

    def adding_allowed(self, request):
        return request.user.has_perm('{}.add_{}'.format(
            self.model._meta.app_label,
            self.model._meta.module_name,
            ))

    def editing_allowed(self, request, instance):
        return request.user.has_perm('{}.change_{}'.format(
            self.model._meta.app_label,
            self.model._meta.module_name,
            ), instance)

    def deletion_allowed(self, request, instance):
        return request.user.has_perm('{}.delete_{}'.format(
            self.model._meta.app_label,
            self.model._meta.module_name,
            ), instance)


class DrudgeModelView(ZivinetzModelView):
    paginate_by = 50
    batch_form = create_email_batch_form('user__email')
    search_form = DrudgeSearchForm

    def additional_urls(self):
        return [
            (r'^picker/$', self.view_decorator(self.picker)),
        ]

    def deletion_allowed(self, request, instance):
        return (
            super(DrudgeModelView, self).deletion_allowed(request, instance)
            and self.deletion_allowed_if_only(request, instance, [Drudge]))

    def get_formset_instances(self, request, instance=None, change=None,
            **kwargs):
        args = self.extend_args_if_post(request, [])
        kwargs['instance'] = instance

        return {
            'assessments': AssessmentFormSet(*args, **kwargs),
            }

drudge_views = DrudgeModelView(Drudge)


class AssignmentModelView(ZivinetzModelView):
    paginate_by = 50
    batch_form = create_email_batch_form('drudge__user__email')
    search_form = AssignmentSearchForm

    def additional_urls(self):
        return [
            (r'^picker/$', self.view_decorator(self.picker)),
            (r'^%(detail)s/create_expensereports/$',
                self.crud_view_decorator(self.create_expensereports)),
            (r'^%(detail)s/remove_expensereports/$',
                self.crud_view_decorator(self.remove_expensereports)),
        ]

    def create_expensereports(self, request, *args, **kwargs):
        instance = self.get_object_or_404(request, *args, **kwargs)
        created = instance.generate_expensereports()

        if created:
            messages.success(request,
                _('Successfully created %s expense reports.') % created)
        else:
            messages.info(request,
                _('No expense reports created, all months occupied already?'))
        return redirect(instance)

    def remove_expensereports(self, request, *args, **kwargs):
        instance = self.get_object_or_404(request, *args, **kwargs)
        instance.reports.filter(status=ExpenseReport.PENDING).delete()
        messages.success(
            request, _('Successfully removed pending expense reports.'))
        return redirect(instance)

    def handle_search_form(self, request, *args, **kwargs):
        queryset, response = super(
            AssignmentModelView, self
            ).handle_search_form(request, *args, **kwargs)

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
                    ], (6.4 * cm, 5 * cm, 5 * cm))
                pdf.hr_mini()

            pdf.generate()
            return queryset, response

        return queryset, response

    def get_form(self, request, instance=None, change=None, **kwargs):
        base_form = super(AssignmentModelView, self).get_form(request,
            instance=instance)

        class AssignmentForm(base_form):
            class Meta:
                model = Assignment
                widgets = {
                    'drudge': SelectWithPicker(model=Drudge, request=request),
                }
                exclude = ('created',)

            def clean(self):
                data = super(AssignmentForm, self).clean()

                if data.get('status') == Assignment.MOBILIZED:
                    if not data.get('mobilized_on'):
                        raise forms.ValidationError(_(
                            'Mobilized on date must be set when status is'
                            ' mobilized.'))
                return data

        return AssignmentForm

    def deletion_allowed(self, request, instance):
        return (
            super(AssignmentModelView, self).deletion_allowed(
                request, instance)
            and self.deletion_allowed_if_only(request, instance, [Assignment]))

    def get_formset_instances(self, request, instance=None, change=None,
            **kwargs):
        args = self.extend_args_if_post(request, [])
        kwargs['instance'] = instance

        return {
            'expensereports': ExpenseReportFormSet(*args, **kwargs),
            }

    def post_save(self, request, instance, form, formset, change):
        for report in instance.reports.all():
            report.recalculate_total()

        if ('date_until_extension' in form.changed_data
                and instance.reports.exists()):
            messages.warning(request,
                _('The extended until date has been changed. Please check'
                    ' whether you need to generate additional expense'
                    ' reports.'))


assignment_views = AssignmentModelView(Assignment)
