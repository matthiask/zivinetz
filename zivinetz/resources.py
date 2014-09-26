from django import forms
from django.conf.urls import patterns, include, url
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template import Template, Context
from django.utils.translation import ugettext as _, ugettext_lazy

from towel import resources
from towel.forms import WarningsForm, towel_formfield_callback
from towel.resources.urls import resource_url_fn
from towel.utils import safe_queryset_and

from towel_foundation.widgets import SelectWithPicker

from pdfdocument.document import cm
from pdfdocument.utils import pdf_response

from zivinetz.forms import (
    AssignmentSearchForm, DrudgeSearchForm, AssessmentForm,
    ExpenseReportSearchForm, EditExpenseReportForm, JobReferenceForm,
    JobReferenceSearchForm, WaitListSearchForm)
from zivinetz.models import (
    Assessment, Assignment, Drudge, ExpenseReport, RegionalOffice,
    ScopeStatement, Specification, WaitList, JobReferenceTemplate,
    JobReference)
from zivinetz.views.expenses import generate_expense_statistics_pdf


class LimitedPickerView(resources.PickerView):
    def get_context_data(self, object_list, **kwargs):
        return super(LimitedPickerView, self).get_context_data(
            object_list=object_list[:50],
            **kwargs)


class ZivinetzMixin(object):
    base_template = 'zivinetz/base.html'
    deletion_cascade_allowed = ()
    send_emails_selector = None

    def allow_add(self, silent=True):
        return self.request.user.has_perm('{}.add_{}'.format(
            self.model._meta.app_label,
            self.model._meta.model_name,
        ))

    def allow_edit(self, object=None, silent=True):
        return self.request.user.has_perm('{}.change_{}'.format(
            self.model._meta.app_label,
            self.model._meta.model_name,
        ))

    def allow_delete(self, object=None, silent=True):
        if not self.request.user.has_perm('{}.delete_{}'.format(
                self.model._meta.app_label,
                self.model._meta.model_name,
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
            body = forms.CharField(
                label=ugettext_lazy('body'), widget=forms.Textarea)
            attachment = forms.FileField(
                label=ugettext_lazy('attachment'), required=False)

        if 'confirm' in self.request.POST:
            form = EmailForm(self.request.POST, self.request.FILES)
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
                    }
                )
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

        context = resources.ModelResourceView.get_context_data(
            self,
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

    def form_valid(self, form):
        self.object = form.save()
        messages.success(
            self.request,
            _('The %(verbose_name)s has been successfully saved.') %
            self.object._meta.__dict__
        )
        if '_continue' in self.request.POST:
            return redirect(self.object.urls.url('edit'))
        return redirect(self.object)


class DrudgeDetailView(resources.DetailView):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(
            object=self.object,
            assessment_form=AssessmentForm(),
        )
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = AssessmentForm(request.POST)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.drudge = self.object
            assessment.save()
        else:
            messages.error(request, _('Form invalid: %s') % form.errors)
        return redirect(self.object)


class AssessmentMixin(ZivinetzMixin):
    def form_valid(self, form):
        super(AssessmentMixin, self).form_valid(form)
        return redirect(self.object.drudge)

    def deletion_form_valid(self, form):
        self.object.delete()
        messages.success(
            self.request,
            _('The %(verbose_name)s has been successfully deleted.') %
            self.object._meta.__dict__,
        )
        return redirect(self.object.drudge)


class JobReferenceFromTemplateView(resources.ModelResourceView):
    def get(self, request, template_id, assignment_id):
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
            'date_until': assignment.determine_date_until().strftime(
                '%d.%m.%Y'),
            'place_of_citizenship': u'%s %s' % (
                assignment.drudge.place_of_citizenship_city,
                assignment.drudge.place_of_citizenship_state,
            ),
        }

        if assignment.drudge.date_of_birth:
            ctx['birth_date'] = assignment.drudge.date_of_birth.strftime(
                '%d.%m.%Y')
        else:
            ctx['birth_date'] = '-' * 10

        instance.text = template.render(Context(ctx))
        instance.save()

        messages.success(request, _('Successfully created job reference.'))

        return HttpResponseRedirect(instance.urls.url('edit'))


class AssignmentMixin(ZivinetzMixin):
    def get_form_class(self):
        base_form = super(AssignmentMixin, self).get_form_class()
        request = self.request

        class AssignmentForm(base_form, WarningsForm):
            motor_saw_course = forms.ChoiceField(
                label=_('Set motor saw course field on drudge to'),
                required=False,
                choices=(
                    ('', '-' * 10),
                ) + Drudge.MOTOR_SAW_COURSE_CHOICES)

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

                if (data.get('motor_saw_course_date')
                        and 'motor_saw_course_date' in self.changed_data
                        and data.get('drudge').motor_saw_course):
                    self.add_warning(
                        _('Drudge already visited a motor saw course.'))
                if (data.get('environment_course_date')
                        and 'environment_course_date' in self.changed_data
                        and data.get('drudge').environment_course):
                    self.add_warning(
                        _('Drudge already visited an environment course.'))

                if (data.get('motor_saw_course_date') and (
                        not data.get('drudge').motor_saw_course
                        and not data.get('motor_saw_course'))):

                    raise forms.ValidationError(_(
                        'Please also provide a value in the motor saw course'
                        ' selector when entering a starting date.'))

                return data

        return AssignmentForm

    def form_valid(self, form):
        self.object = form.save()
        messages.success(
            self.request,
            _('The %(verbose_name)s has been successfully saved.') %
            self.object._meta.__dict__,
        )

        if (self.object.environment_course_date
                and not self.object.drudge.environment_course):
            self.object.drudge.environment_course = True
            self.object.drudge.save()
            messages.success(self.request, _(
                'The drudge is now registered as having visited the'
                ' environment course.'))

        if form.cleaned_data.get('motor_saw_course'):
            self.object.drudge.motor_saw_course = form.cleaned_data.get(
                'motor_saw_course')
            self.object.drudge.save()
            messages.success(self.request, _(
                'The drudge is now registered as having visited the'
                ' motor saw course.'))

        for report in self.object.reports.all():
            report.recalculate_total()

        if ('date_until_extension' in form.changed_data
                and self.object.reports.exists()):
            messages.warning(self.request, _(
                'The extended until date has been changed. Please check'
                ' whether you need to generate additional expense'
                ' reports.'))

        if '_continue' in self.request.POST:
            return redirect(self.object.urls.url('edit'))
        return redirect(self.object)


class CreateExpenseReportView(resources.ModelResourceView):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.allow_edit(self.object, silent=False):
            raise PermissionDenied
        created = self.object.generate_expensereports()
        if created:
            messages.success(
                request,
                _('Successfully created %s expense reports.') % created)
        else:
            messages.info(
                request,
                _('No expense reports created, all months occupied already?'))
        return redirect(self.object)


class RemoveExpenseReportView(resources.ModelResourceView):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.allow_edit(self.object, silent=False):
            raise PermissionDenied
        self.object.reports.filter(status=ExpenseReport.PENDING).delete()
        messages.success(
            request, _('Successfully removed pending expense reports.'))
        return redirect(self.object)


class PhonenumberPDFExportView(resources.ModelResourceView):
    def get(self, request):
        self.object_list = self.get_queryset()
        search_form = AssignmentSearchForm(request.GET, request=request)
        if not search_form.is_valid():
            messages.error(request, _('The search query was invalid.'))
            return redirect('zivinetz_assignment_list')
        self.object_list = safe_queryset_and(
            self.object_list, search_form.queryset(self.model))

        pdf, response = pdf_response('phones')
        pdf.init_report()

        specification = None
        for assignment in self.object_list.order_by('specification', 'drudge'):
            drudge = assignment.drudge

            if specification != assignment.specification:
                pdf.h2('%s' % assignment.specification)
                specification = assignment.specification

            pdf.table([
                (u'%s' % drudge, drudge.user.email, u'%s - %s' % (
                    assignment.date_from.strftime('%d.%m.%y'),
                    assignment.determine_date_until().strftime('%d.%m.%y'),
                )),
                (drudge.phone_home, drudge.phone_office, drudge.mobile),
                (
                    u'%s, %s %s' % (
                        drudge.address,
                        drudge.zip_code,
                        drudge.city,
                    ),
                    '',
                    drudge.education_occupation,
                ),
            ], (6.4 * cm, 5 * cm, 5 * cm))
            pdf.hr_mini()

        pdf.generate()
        return response


class ExpenseReportMixin(ZivinetzMixin):
    def allow_edit(self, object=None, silent=True):
        if object is not None and object.status >= object.PAID:
            return False
        return super(ExpenseReportMixin, self).allow_edit(
            object=object, silent=silent)

    def get_form_class(self):
        if self.object:
            return EditExpenseReportForm

        request = self.request

        class ModelForm(forms.ModelForm):
            assignment = forms.ModelChoiceField(
                Assignment.objects.all(),
                label=ugettext_lazy('assignment'),
                widget=SelectWithPicker(model=Assignment, request=request),
            )

            class Meta:
                model = self.model
                exclude = ('total', 'calculated_total_days')

            formfield_callback = towel_formfield_callback

        return ModelForm

    def form_valid(self, form):
        self.object = form.save()
        messages.success(
            self.request,
            _('The %(verbose_name)s has been successfully saved.') %
            self.object._meta.__dict__,
        )
        self.object.recalculate_total()

        if self.request.POST.get('transport_expenses_copy'):
            for report in self.object.assignment.reports.filter(
                    date_from__gt=self.object.date_from):
                report.transport_expenses = self.object.transport_expenses
                report.transport_expenses_notes =\
                    self.object.transport_expenses_notes
                report.recalculate_total()

        if '_continue' in self.request.POST:
            return redirect(self.object.urls.url('edit'))
        return redirect(self.object)


class ExpenseReportPDFExportView(resources.ModelResourceView):
    def get(self, request):
        self.object_list = self.get_queryset()
        search_form = ExpenseReportSearchForm(request.GET, request=request)
        if not search_form.is_valid():
            messages.error(request, _('The search query was invalid.'))
            return redirect('zivinetz_expensereport_list')
        self.object_list = safe_queryset_and(
            self.object_list, search_form.queryset(self.model))
        return generate_expense_statistics_pdf(self.object_list)


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
drudge_url = resource_url_fn(
    Drudge,
    mixins=(ZivinetzMixin,),
    decorators=(staff_member_required,),
    deletion_cascade_allowed=(Drudge,),
)
assessment_url = resource_url_fn(
    Assessment,
    mixins=(AssessmentMixin,),
    decorators=(staff_member_required,),
    deletion_cascade_allowed=(Assessment,),
)
assignment_url = resource_url_fn(
    Assignment,
    mixins=(AssignmentMixin,),
    decorators=(staff_member_required,),
    deletion_cascade_allowed=(Assignment,),
)
expensereport_url = resource_url_fn(
    ExpenseReport,
    mixins=(ExpenseReportMixin,),
    decorators=(staff_member_required,),
    deletion_cascade_allowed=(ExpenseReport,),
)
jobreference_url = resource_url_fn(
    JobReference,
    mixins=(ZivinetzMixin,),
    decorators=(staff_member_required,),
    deletion_cascade_allowed=(JobReference,),
)
waitlist_url = resource_url_fn(
    WaitList,
    mixins=(ZivinetzMixin,),
    decorators=(staff_member_required,),
    deletion_cascade_allowed=(WaitList,),
    send_emails_selector='drudge__user__email',
)


urlpatterns = patterns(
    '',
    url(
        r'^regional_offices/',
        include(patterns(
            '',
            regionaloffice_url('list', url=r'^$'),
            regionaloffice_url('add', url=r'^add/$'),
            regionaloffice_url('edit'),
            regionaloffice_url('delete'),
            url(r'^\d+/$',
                lambda request: redirect('zivinetz_regionaloffice_list')),
        ))
    ),
    url(
        r'^scope_statements/',
        include(patterns(
            '',
            scopestatement_url('list', url=r'^$'),
            scopestatement_url('detail', url=r'^(?P<pk>\d+)/$'),
            scopestatement_url('add', url=r'^add/$'),
            scopestatement_url('edit'),
            scopestatement_url('delete'),
        ))
    ),
    url(
        r'^specifications/',
        include(patterns(
            '',
            specification_url('list', url='^$'),
            specification_url('detail', url=r'^(?P<pk>\d+)/$'),
            specification_url('add', url=r'^add/$'),
            specification_url('edit'),
            specification_url('delete'),
        ))
    ),
    url(
        r'^drudges/',
        include(patterns(
            '',
            drudge_url(
                'list',
                url=r'^$',
                paginate_by=50,
                search_form=DrudgeSearchForm,
                send_emails_selector='user__email',
                ),
            drudge_url('picker', view=LimitedPickerView, url=r'^picker/$'),
            drudge_url('detail', view=DrudgeDetailView, url=r'^(?P<pk>\d+)/$'),
            drudge_url('add', url=r'^add/$'),
            drudge_url('edit'),
            drudge_url('delete'),
        ))
    ),
    url(
        r'^assessment/',
        include(patterns(
            '',
            assessment_url('edit', form_class=AssessmentForm),
            assessment_url('delete'),
        )),
    ),
    url(
        r'^assignments/',
        include(patterns(
            '',
            assignment_url(
                'list',
                url=r'^$',
                paginate_by=50,
                search_form=AssignmentSearchForm,
                send_emails_selector='drudge__user__email',
                ),
            assignment_url('picker', view=LimitedPickerView, url=r'^picker/$'),
            assignment_url(
                'pdf',
                view=PhonenumberPDFExportView,
                url=r'^pdf/$',
            ),
            assignment_url('detail', url=r'^(?P<pk>\d+)/$'),
            assignment_url('add', url=r'^add/$'),
            assignment_url('edit'),
            assignment_url('delete'),
            assignment_url(
                'create_expensereports', view=CreateExpenseReportView),
            assignment_url(
                'remove_expensereports', view=RemoveExpenseReportView),
        ))
    ),
    url(
        r'^expense_reports/',
        include(patterns(
            '',
            expensereport_url(
                'list',
                url=r'^$',
                paginate_by=50,
                search_form=ExpenseReportSearchForm,
                ),
            expensereport_url(
                'pdf',
                view=ExpenseReportPDFExportView,
                url=r'^pdf/$',
            ),
            expensereport_url('detail', url=r'^(?P<pk>\d+)/$'),
            expensereport_url('add', url=r'^add/$'),
            expensereport_url('edit'),
            expensereport_url('delete'),
        ))
    ),
    url(
        r'^jobreferences/',
        include(patterns(
            '',
            jobreference_url(
                'list',
                url=r'^$',
                paginate_by=50,
                search_form=JobReferenceSearchForm,
                ),
            jobreference_url('detail', url=r'^(?P<pk>\d+)/$'),
            jobreference_url('edit', form_class=JobReferenceForm),
            jobreference_url('delete'),

            jobreference_url(
                'from_template',
                view=JobReferenceFromTemplateView,
                url=r'^(\d+)/(\d+)/$',
            ),
        ))
    ),
    url(
        r'^waitlist/',
        include(patterns(
            '',
            waitlist_url(
                'list',
                url=r'^$',
                paginate_by=50,
                search_form=WaitListSearchForm,
                ),
            waitlist_url('detail', url=r'^(?P<pk>\d+)/$'),
            waitlist_url('edit'),
            waitlist_url('delete'),
        ))
    ),
)
