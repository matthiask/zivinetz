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

from zivinetz.models import (Assignment, Drudge,
    ExpenseReport, RegionalOffice, ScopeStatement,
    Specification, WaitList, Assessment, JobReferenceTemplate,
    JobReference)


class ZivinetzMixin(object):
    base_template = 'zivinetz/base.html'
    deletion_cascade_allowed = ()

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


regionaloffice_url = resource_url_fn(
    RegionalOffice,
    mixins=(ZivinetzMixin,),
    decorators=(staff_member_required,),
    deletion_cascade_allowed=(RegionalOffice,),
    )


urlpatterns = patterns('',
    url(r'^regional_offices/', include(patterns(
        '',
        regionaloffice_url('list', False, resources.ListView, suffix=''),
        regionaloffice_url('add', False, resources.AddView),
        regionaloffice_url('edit', True, resources.EditView),
        regionaloffice_url('delete', True, resources.DeleteView),
        url(r'^\d+/$', lambda request: redirect('zivinetz_regionaloffice_list')),
    ))),
)
