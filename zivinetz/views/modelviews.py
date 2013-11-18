# coding=utf-8

from StringIO import StringIO

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import EmailMessage
from django.forms.models import modelform_factory
from django.utils.translation import ugettext as _

from towel.forms import BatchForm, towel_formfield_callback

from towel_foundation.modelview import PickerModelView

from zivinetz.forms import DrudgeSearchForm, AssessmentFormSet
from zivinetz.models import Drudge


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
