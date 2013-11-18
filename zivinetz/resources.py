from StringIO import StringIO

from django import forms
from django.conf.urls import patterns, include, url
from django.db.models import Q
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import EmailMessage
from django.db.models import Avg
from django.forms.models import modelform_factory, inlineformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template import Template, Context
from django.utils.translation import ugettext as _, ugettext_lazy
from django.views import generic

from towel import forms as towel_forms
from towel import resources
from towel.resources.urls import resource_url_fn

from towel_foundation.widgets import SelectWithPicker

from pdfdocument.document import cm
from pdfdocument.utils import pdf_response

from zivinetz.forms import (WaitListSearchForm,)
from zivinetz.models import (Assignment, Drudge,
    ExpenseReport, RegionalOffice, ScopeStatement,
    Specification, WaitList, Assessment, JobReferenceTemplate,
    JobReference)


class ZivinetzMixin(object):
    base_template = 'zivinetz/base.html'
    deletion_cascade_allowed = ()
    send_emails_selector = None

    def allow_add(self, silent=True):
        return self.request.user.has_perm('{}.add_{}'.format(
            self.model._meta.app_label,
            self.model._meta.module_name,
            ))

    def allow_edit(self, object=None, silent=True):
        return self.request.user.has_perm('{}.change_{}'.format(
            self.model._meta.app_label,
            self.model._meta.module_name,
            ))

    def allow_delete(self, object=None, silent=True):
        if not self.request.user.has_perm('{}.delete_{}'.format(
                self.model._meta.app_label,
                self.model._meta.module_name,
                )):
            return False

        if not object or not self.deletion_cascade_allowed:
            return False

        return self.allow_delete_if_only(
            object,
            related=self.deletion_cascade_allowed,
            silent=silent)

    def send_emails(self, queryset):
        class EmailForm(forms.Form):
            subject = forms.CharField(label=ugettext_lazy('subject'))
            body = forms.CharField(label=ugettext_lazy('body'),
                widget=forms.Textarea)
            attachment = forms.FileField(label=ugettext_lazy('attachment'),
                required=False)

        if 'confirm' in self.request.POST:
            form = EmailForm(self.request.POST)
            if form.is_valid():
                message = EmailMessage(
                    subject=form.cleaned_data['subject'],
                    body=form.cleaned_data['body'],
                    to=[],
                    bcc=list(set(queryset.values_list(
                        self.send_emails_selector, flat=True))),
                    from_email='info@naturnetz.ch',
                    headers={
                        'Reply-To': self.request.user.email,
                    })
                if form.cleaned_data['attachment']:
                    message.attach(
                        form.cleaned_data['attachment'].name,
                        form.cleaned_data['attachment'].read())
                message.send()
                messages.success(
                    self.request, _('Successfully sent the mail.'))

                return queryset
        else:
            form = EmailForm()

        context = resources.ModelResourceView.get_context_data(self,
            title=_('Send emails'),
            form=form,
            action_queryset=queryset,
            action_hidden_fields=self.batch_action_hidden_fields(queryset, [
                ('batch-action', 'send_emails'),
                ('confirm', 1),
                ]),
            )
        self.template_name_suffix = '_action'
        return self.render_to_response(context)

    def get_batch_actions(self):
        actions = super(ZivinetzMixin, self).get_batch_actions()
        if self.send_emails_selector:
            actions.append(('send_emails', _('Send emails'), self.send_emails))
        return actions


regionaloffice_url = resource_url_fn(
    RegionalOffice,
    mixins=(ZivinetzMixin,),
    decorators=(staff_member_required,),
    deletion_cascade_allowed=(RegionalOffice,),
    )
scopestatement_url = resource_url_fn(
    ScopeStatement,
    mixins=(ZivinetzMixin,),
    decorators=(staff_member_required,),
    deletion_cascade_allowed=(ScopeStatement, Specification),
    )
specification_url = resource_url_fn(
    Specification,
    mixins=(ZivinetzMixin,),
    decorators=(staff_member_required,),
    deletion_cascade_allowed=(Specification,),
    )
waitlist_url = resource_url_fn(
    WaitList,
    mixins=(ZivinetzMixin,),
    decorators=(staff_member_required,),
    deletion_cascade_allowed=(WaitList,),
    send_emails_selector='drudge__user__email',
    )


urlpatterns = patterns('',
    url(r'^regional_offices/', include(patterns(
        '',
        regionaloffice_url('list', False, resources.ListView, suffix=''),
        regionaloffice_url('add', False, resources.AddView),
        regionaloffice_url('edit', True, resources.EditView),
        regionaloffice_url('delete', True, resources.DeleteView),
        url(r'^\d+/$',
            lambda request: redirect('zivinetz_regionaloffice_list')),
    ))),
    url(r'^scope_statements/', include(patterns(
        '',
        scopestatement_url('list', False, resources.ListView, suffix=''),
        scopestatement_url('detail', True, resources.DetailView, suffix=''),
        scopestatement_url('add', False, resources.AddView),
        scopestatement_url('edit', True, resources.EditView),
        scopestatement_url('delete', True, resources.DeleteView),
    ))),
    url(r'^specifications/', include(patterns(
        '',
        specification_url('list', False, resources.ListView, suffix=''),
        specification_url('detail', True, resources.DetailView, suffix=''),
        specification_url('add', False, resources.AddView),
        specification_url('edit', True, resources.EditView),
        specification_url('delete', True, resources.DeleteView),
    ))),
    url(r'^waitlist/', include(patterns(
        '',
        waitlist_url('list', False, resources.ListView, suffix='',
            paginate_by=50,
            search_form=WaitListSearchForm,
            ),
        waitlist_url('detail', True, resources.DetailView, suffix=''),
        # waitlist_url('add', False, resources.AddView),
        waitlist_url('edit', True, resources.EditView),
        waitlist_url('delete', True, resources.DeleteView),
    ))),
)
