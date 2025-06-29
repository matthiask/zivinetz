from datetime import date, timedelta

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template import Context, Template
from django.urls import include, path, re_path
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _, gettext_lazy
from openpyxl.writer.excel import save_virtual_workbook
from pdfdocument.document import cm
from pdfdocument.utils import pdf_response
from towel import resources
from towel.forms import WarningsForm, towel_formfield_callback
from towel.resources.urls import resource_url_fn
from towel.utils import safe_queryset_and
from towel_foundation.widgets import SelectWithPicker

from zivinetz.forms import (
    AbsenceSearchForm,
    AssessmentForm,
    AssignDrudgesToGroupsForm,
    AssignmentSearchForm,
    DrudgeSearchForm,
    EditExpenseReportForm,
    ExpenseReportSearchForm,
    JobReferenceForm,
    JobReferenceSearchForm,
    SpecificationForm,
)
from zivinetz.models import (
    Absence,
    Assessment,
    Assignment,
    Drudge,
    ExpenseReport,
    Group,
    GroupAssignment,
    JobReference,
    JobReferenceTemplate,
    RegionalOffice,
    ScopeStatement,
    Specification,
)
from zivinetz.views.decorators import user_type_required
from zivinetz.views.expenses import generate_expense_statistics_pdf
from zivinetz.views.groups import create_groups_xlsx


class LimitedPickerView(resources.PickerView):
    def get_context_data(self, object_list, **kwargs):
        return super().get_context_data(object_list=object_list[:50], **kwargs)


class ZivinetzMixin:
    base_template = "zivinetz/base.html"
    deletion_cascade_allowed = ()
    send_emails_selector = None

    def get_form_class(self):
        # TODO Remove this hack.
        from django.forms.models import modelform_factory

        kw = {"form": self.form_class, "formfield_callback": towel_formfield_callback}
        _meta = getattr(self.form_class, "_meta", None)
        if not _meta or not (_meta.fields or _meta.exclude):
            # TODO Emit a warning?
            kw["fields"] = "__all__"

        return modelform_factory(self.model, **kw)

    def allow_add(self, silent=True):
        return self.request.user.has_perm(
            f"{self.model._meta.app_label}.add_{self.model._meta.model_name}"
        )

    def allow_edit(self, object=None, silent=True):
        return self.request.user.has_perm(
            f"{self.model._meta.app_label}.change_{self.model._meta.model_name}"
        )

    def allow_delete(self, object=None, silent=True):
        if not self.request.user.has_perm(
            f"{self.model._meta.app_label}.delete_{self.model._meta.model_name}"
        ):
            return False

        if not object or not self.deletion_cascade_allowed:
            return False

        return self.allow_delete_if_only(
            object, related=self.deletion_cascade_allowed, silent=silent
        )

    def send_emails(self, queryset):
        class EmailForm(forms.Form):
            subject = forms.CharField(label=gettext_lazy("subject"))
            body = forms.CharField(label=gettext_lazy("body"), widget=forms.Textarea)
            attachment = forms.FileField(
                label=gettext_lazy("attachment"), required=False
            )

        if "confirm" in self.request.POST:
            form = EmailForm(self.request.POST, self.request.FILES)
            if form.is_valid():
                message = EmailMessage(
                    subject=form.cleaned_data["subject"],
                    body=form.cleaned_data["body"],
                    to=[],
                    bcc=list(
                        set(queryset.values_list(self.send_emails_selector, flat=True))
                    ),
                    from_email="info@naturnetz.ch",
                    headers={"Reply-To": self.request.user.email},
                )
                if form.cleaned_data["attachment"]:
                    message.attach(
                        form.cleaned_data["attachment"].name,
                        form.cleaned_data["attachment"].read(),
                    )
                message.send()
                messages.success(self.request, _("Successfully sent the mail."))

                return queryset
        else:
            form = EmailForm()

        context = resources.ModelResourceView.get_context_data(
            self,
            title=_("Send emails"),
            form=form,
            action_queryset=queryset,
            action_hidden_fields=self.batch_action_hidden_fields(
                queryset, [("batch-action", "send_emails"), ("confirm", 1)]
            ),
        )
        self.template_name_suffix = "_action"
        return self.render_to_response(context)

    def get_batch_actions(self):
        actions = super().get_batch_actions()
        if self.send_emails_selector:
            actions.append(("send_emails", _("Send emails"), self.send_emails))
        return actions

    def form_valid(self, form):
        self.object = form.save()
        messages.success(
            self.request,
            _("The %(verbose_name)s has been successfully saved.")
            % self.object._meta.__dict__,
        )
        if "_continue" in self.request.POST:
            return redirect(self.object.urls.url("edit"))
        return redirect(self.object)


class DrudgeDetailView(resources.DetailView):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(
            object=self.object, assessment_form=AssessmentForm(drudge=self.object)
        )
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = AssessmentForm(request.POST, drudge=self.object)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.created_by = request.user
            assessment.drudge = self.object
            assessment.save()
        else:
            messages.error(request, _("Form invalid: %s") % form.errors)
        return redirect(self.object)


class AssessmentMixin(ZivinetzMixin):
    def form_valid(self, form):
        super().form_valid(form)
        return redirect(self.object.drudge)

    def deletion_form_valid(self, form):
        self.object.delete()
        messages.success(
            self.request,
            _("The %(verbose_name)s has been successfully deleted.")
            % self.object._meta.__dict__,
        )
        return redirect(self.object.drudge)


class JobReferenceFromTemplateView(resources.ModelResourceView):
    def get(self, request, template_id, assignment_id):
        template = get_object_or_404(JobReferenceTemplate, pk=template_id)
        assignment = get_object_or_404(Assignment, pk=assignment_id)

        instance = self.model(
            assignment=assignment, created=assignment.determine_date_until()
        )

        template = Template(template.text)
        ctx = {
            "full_name": assignment.drudge.user.get_full_name(),
            "last_name": assignment.drudge.user.last_name,
            "date_from": assignment.date_from.strftime("%d.%m.%Y"),
            "date_until": assignment.determine_date_until().strftime("%d.%m.%Y"),
            "place_of_citizenship": "%s %s"
            % (
                assignment.drudge.place_of_citizenship_city,
                assignment.drudge.place_of_citizenship_state,
            ),
        }

        if assignment.drudge.date_of_birth:
            ctx["birth_date"] = assignment.drudge.date_of_birth.strftime("%d.%m.%Y")
        else:
            ctx["birth_date"] = "-" * 10

        instance.text = template.render(Context(ctx))
        instance.save()

        messages.success(request, _("Successfully created job reference."))

        return HttpResponseRedirect(instance.urls.url("edit"))


class AssignmentMixin(ZivinetzMixin):
    def get_form_class(self):
        base_form = super().get_form_class()
        request = self.request

        class AssignmentForm(base_form, WarningsForm):
            motor_saw_course = forms.ChoiceField(
                label=_("Set motor saw course field on drudge to"),
                required=False,
                choices=(("", "-" * 10),) + Drudge.MOTOR_SAW_COURSE_CHOICES,
            )

            class Meta:
                model = Assignment
                widgets = {"drudge": SelectWithPicker(model=Drudge, request=request)}
                exclude = ("created",)

            def clean(self):
                data = super().clean()

                if data.get("status") == Assignment.MOBILIZED:
                    if not data.get("mobilized_on"):
                        raise forms.ValidationError(
                            _("Mobilized on date must be set when status is mobilized.")
                        )

                if (
                    data.get("motor_saw_course_date")
                    and "motor_saw_course_date" in self.changed_data
                    and data.get("drudge").motor_saw_course
                ):
                    self.add_warning(_("Drudge already visited a motor saw course."))
                if (
                    data.get("environment_course_date")
                    and "environment_course_date" in self.changed_data
                    and data.get("drudge").environment_course
                ):
                    self.add_warning(_("Drudge already visited an environment course."))

                if data.get("motor_saw_course_date") and (
                    not data.get("drudge").motor_saw_course
                    and not data.get("motor_saw_course")
                ):
                    raise forms.ValidationError(
                        _(
                            "Please also provide a value in the motor saw course"
                            " selector when entering a starting date."
                        )
                    )

                return data

        return AssignmentForm

    def form_valid(self, form):
        self.object = form.save()
        messages.success(
            self.request,
            _("The %(verbose_name)s has been successfully saved.")
            % self.object._meta.__dict__,
        )

        if (
            self.object.environment_course_date
            and not self.object.drudge.environment_course
        ):
            self.object.drudge.environment_course = True
            self.object.drudge.save()
            messages.success(
                self.request,
                _(
                    "The drudge is now registered as having visited the"
                    " environment course."
                ),
            )

        if form.cleaned_data.get("motor_saw_course"):
            self.object.drudge.motor_saw_course = form.cleaned_data.get(
                "motor_saw_course"
            )
            self.object.drudge.save()
            messages.success(
                self.request,
                _(
                    "The drudge is now registered as having visited the"
                    " motor saw course."
                ),
            )

        for report in self.object.reports.all():
            report.recalculate_total()

        if "date_until_extension" in form.changed_data and self.object.reports.exists():
            messages.warning(
                self.request,
                _(
                    "The extended until date has been changed. Please check"
                    " whether you need to generate additional expense"
                    " reports."
                ),
            )

        if "_continue" in self.request.POST:
            return redirect(self.object.urls.url("edit"))
        return redirect(self.object)


class CreateExpenseReportView(resources.ModelResourceView):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.allow_edit(self.object, silent=False):
            raise PermissionDenied
        created = self.object.generate_expensereports()
        if created:
            messages.success(
                request, _("Successfully created %s expense reports.") % created
            )
        else:
            messages.info(
                request, _("No expense reports created, all months occupied already?")
            )
        return redirect(self.object)


class RemoveExpenseReportView(resources.ModelResourceView):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.allow_edit(self.object, silent=False):
            raise PermissionDenied
        self.object.reports.filter(status=ExpenseReport.PENDING).delete()
        messages.success(request, _("Successfully removed pending expense reports."))
        return redirect(self.object)


class PhonenumberPDFExportView(resources.ModelResourceView):
    def get(self, request):
        self.object_list = self.get_queryset()
        search_form = AssignmentSearchForm(request.GET, request=request)
        if not search_form.is_valid():
            messages.error(request, _("The search query was invalid."))
            return redirect("zivinetz_assignment_list")
        self.object_list = safe_queryset_and(
            self.object_list, search_form.queryset(self.model)
        )

        # Filter assignments based on user type
        try:
            user_type = request.user.userprofile.user_type
        except User.userprofile.RelatedObjectDoesNotExist:
            messages.error(
                request, _("User profile not found. Please contact an administrator.")
            )
            return redirect("zivinetz_assignment_list")

        if user_type == "squad_leader":
            # Squad leaders only see active assignments
            self.object_list = self.object_list.filter(
                status__in=(Assignment.ARRANGED, Assignment.MOBILIZED)
            )
        elif user_type == "drudge":
            # Drudges only see their own assignments
            self.object_list = self.object_list.filter(drudge__user=request.user)

        pdf, response = pdf_response("phones")
        pdf.init_report()

        specification = None
        for assignment in self.object_list.order_by("specification", "drudge"):
            drudge = assignment.drudge

            if specification != assignment.specification:
                pdf.h2("%s" % assignment.specification)
                specification = assignment.specification

            # Only show email for admin, dev_admin and user_plus
            email = (
                drudge.user.email
                if user_type in ["admin", "dev_admin", "user_plus"]
                else ""
            )

            pdf.table(
                [
                    (
                        "%s" % drudge,
                        email,
                        "%s - %s"
                        % (
                            assignment.date_from.strftime("%d.%m.%y"),
                            assignment.determine_date_until().strftime("%d.%m.%y"),
                        ),
                    ),
                    (drudge.phone_home, drudge.phone_office, drudge.mobile),
                    (
                        f"{drudge.address}, {drudge.zip_code} {drudge.city}"
                        if user_type in ["admin", "dev_admin", "user_plus"]
                        else "",
                        "",
                        drudge.education_occupation
                        if user_type in ["admin", "dev_admin", "user_plus"]
                        else "",
                    ),
                ],
                (6.4 * cm, 5 * cm, 5 * cm),
            )
            pdf.hr_mini()

        pdf.generate()
        return response


class GroupMixin(ZivinetzMixin):
    def weeks(self):
        monday = GroupAssignment.objects.monday(date.today())
        return [(_("This week"), monday), (_("Next week"), monday + timedelta(days=7))]


class AbsenceMixin(ZivinetzMixin):
    def get_form_class(self):
        request = self.request

        class ModelForm(forms.ModelForm):
            assignment = forms.ModelChoiceField(
                Assignment.objects.all(),
                label=gettext_lazy("assignment"),
                widget=SelectWithPicker(model=Assignment, request=request),
            )

            class Meta:
                model = self.model
                fields = ("assignment", "reason", "internal_notes", "days")
                widgets = {"reason": forms.RadioSelect}

            def save(self):
                instance = super().save(commit=False)
                instance.created_by = request.user
                instance.save()
                return instance

            formfield_callback = towel_formfield_callback

        return ModelForm


class ExpenseReportMixin(ZivinetzMixin):
    def allow_edit(self, object=None, silent=True):
        if object is not None and object.status >= object.PAID:
            if not silent:
                messages.error(
                    self.request, _("Paid expense reports cannot be edited.")
                )
            return False
        return super().allow_edit(object=object, silent=silent)

    def allow_delete(self, object=None, silent=True):
        if object is not None and object.status >= object.PAID:
            if not silent:
                messages.error(
                    self.request, _("Paid expense reports cannot be deleted.")
                )
            return False
        return super().allow_edit(object=object, silent=silent)

    def get_form_class(self):
        if self.object:
            return EditExpenseReportForm

        request = self.request

        class ModelForm(forms.ModelForm):
            assignment = forms.ModelChoiceField(
                Assignment.objects.all(),
                label=gettext_lazy("assignment"),
                widget=SelectWithPicker(model=Assignment, request=request),
            )

            class Meta:
                model = self.model
                exclude = ("total", "calculated_total_days")

            formfield_callback = towel_formfield_callback

        return ModelForm

    def form_valid(self, form):
        self.object = form.save()
        messages.success(
            self.request,
            _("The %(verbose_name)s has been successfully saved.")
            % self.object._meta.__dict__,
        )
        self.object.recalculate_total()

        if self.request.POST.get("transport_expenses_copy"):
            for report in self.object.assignment.reports.filter(
                date_from__gt=self.object.date_from
            ):
                report.transport_expenses = self.object.transport_expenses
                report.transport_expenses_notes = self.object.transport_expenses_notes
                report.recalculate_total()

        if "_continue" in self.request.POST:
            return redirect(self.object.urls.url("edit"))
        return redirect(self.object)

    def get_batch_actions(self):
        return super().get_batch_actions() + [
            ("set_status", _("Set status"), self.set_status)
        ]

    def set_status(self, queryset):
        class SetStatusForm(forms.Form):
            status = forms.ChoiceField(
                label=_("status"), choices=ExpenseReport.STATUS_CHOICES
            )

        form = SetStatusForm(
            self.request.POST if "confirm" in self.request.POST else None
        )
        if form.is_valid():
            count = queryset.update(status=form.cleaned_data["status"])
            messages.success(self.request, _("Updated %s reports.") % count)
            return queryset

        self.template_name_suffix = "_action"
        context = self.get_context_data(
            title=_("Set status"),
            form=form,
            action_queryset=queryset,
            action_hidden_fields=self.batch_action_hidden_fields(
                queryset, [("batch-action", "set_status"), ("confirm", 1)]
            ),
        )
        return self.render_to_response(context)


class ExpenseReportPDFExportView(resources.ModelResourceView):
    def get(self, request):
        self.object_list = self.get_queryset()
        search_form = ExpenseReportSearchForm(request.GET, request=request)
        if not search_form.is_valid():
            messages.error(request, _("The search query was invalid."))
            return redirect("zivinetz_expensereport_list")
        self.object_list = safe_queryset_and(
            self.object_list, search_form.queryset(self.model)
        )
        return generate_expense_statistics_pdf(self.object_list)


class AssignGroupsView(resources.ModelResourceView):
    @method_decorator(user_type_required(["admin", "user_plus", "dev_admin"]))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    template_name = "zivinetz/assign_groups.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("title", _("Assign to groups"))
        kwargs.setdefault(
            "scope_statements", ScopeStatement.objects.filter(is_active=True)
        )
        return super().get_context_data(**kwargs)

    def get(self, request, year, month, day):
        try:
            day = date(int(year), int(month), int(day))
        except Exception as exc:
            print(exc)
            return redirect(self.url("list"))

        self.scope_statement = None
        if request.GET.get("scope_statement"):
            try:
                self.scope_statement = ScopeStatement.objects.get(
                    is_active=True, pk=request.GET["scope_statement"]
                )
            except Exception as exc:
                print(exc)
                return redirect(self.url("list"))

        if request.GET.get("xlsx"):
            response = HttpResponse(
                save_virtual_workbook(create_groups_xlsx(day)),
                content_type=(
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
            )
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                "wochenrapport-%s.xlsx" % day.isoformat(),
            )
            return response

        form = AssignDrudgesToGroupsForm(day=day, scope_statement=self.scope_statement)
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, year, month, day):
        try:
            day = date(int(year), int(month), int(day))
        except Exception:
            return redirect(self.url("list"))

        self.scope_statement = None
        if request.GET.get("scope_statement"):
            try:
                self.scope_statement = ScopeStatement.objects.get(
                    is_active=True, pk=request.GET["scope_statement"]
                )
            except Exception as exc:
                print(exc)
                return redirect(self.url("list"))

        form = AssignDrudgesToGroupsForm(
            request.POST, day=day, scope_statement=self.scope_statement
        )
        if form.is_valid():
            form.save()
            return redirect(self.url("list"))
        return self.render_to_response(self.get_context_data(form=form))


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
group_url = resource_url_fn(
    Group,
    mixins=(GroupMixin,),
    decorators=(staff_member_required,),
    deletion_cascade_allowed=(Group,),
)
absence_url = resource_url_fn(
    Absence,
    mixins=(AbsenceMixin,),
    decorators=(staff_member_required,),
    deletion_cascade_allowed=(Absence,),
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


urlpatterns = [
    path(
        "regional_offices/",
        include(
            [
                regionaloffice_url("list", url=r"^$"),
                regionaloffice_url("add", url=r"^add/$"),
                regionaloffice_url("edit"),
                regionaloffice_url("delete"),
                re_path(
                    r"^\d+/$", lambda request: redirect("zivinetz_regionaloffice_list")
                ),
            ]
        ),
    ),
    path(
        "scope_statements/",
        include(
            [
                scopestatement_url("list", url=r"^$"),
                scopestatement_url("detail", url=r"^(?P<pk>\d+)/$"),
                scopestatement_url("add", url=r"^add/$"),
                scopestatement_url("edit"),
                scopestatement_url("delete"),
            ]
        ),
    ),
    path(
        "specifications/",
        include(
            [
                specification_url("list", url="^$"),
                specification_url("detail", url=r"^(?P<pk>\d+)/$"),
                specification_url("add", url=r"^add/$", form_class=SpecificationForm),
                specification_url("edit", form_class=SpecificationForm),
                specification_url("delete"),
            ]
        ),
    ),
    path(
        "drudges/",
        include(
            [
                drudge_url(
                    "list",
                    url=r"^$",
                    paginate_by=50,
                    search_form=DrudgeSearchForm,
                    send_emails_selector="user__email",
                ),
                drudge_url("picker", view=LimitedPickerView, url=r"^picker/$"),
                drudge_url("detail", view=DrudgeDetailView, url=r"^(?P<pk>\d+)/$"),
                drudge_url("add", url=r"^add/$"),
                drudge_url("edit"),
                drudge_url("delete"),
            ]
        ),
    ),
    path(
        "assessment/",
        include(
            [
                assessment_url("edit", form_class=AssessmentForm),
                assessment_url("delete"),
            ]
        ),
    ),
    path(
        "assignments/",
        include(
            [
                assignment_url(
                    "list",
                    url=r"^$",
                    paginate_by=50,
                    search_form=AssignmentSearchForm,
                    send_emails_selector="drudge__user__email",
                ),
                assignment_url("picker", view=LimitedPickerView, url=r"^picker/$"),
                assignment_url("pdf", view=PhonenumberPDFExportView, url=r"^pdf/$"),
                assignment_url("detail", url=r"^(?P<pk>\d+)/$"),
                assignment_url("add", url=r"^add/$"),
                assignment_url("edit"),
                assignment_url("delete"),
                assignment_url("create_expensereports", view=CreateExpenseReportView),
                assignment_url("remove_expensereports", view=RemoveExpenseReportView),
            ]
        ),
    ),
    path(
        "groups/",
        include(
            [
                group_url(
                    "list",
                    url=r"^$",
                    paginate_by=50,
                    # search_form=AssignmentSearchForm,
                    # send_emails_selector='drudge__user__email',
                ),
                group_url(
                    "assign",
                    view=AssignGroupsView,
                    url=r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})/$",
                ),
                group_url("detail", url=r"^(?P<pk>\d+)/$"),
                group_url("add", url=r"^add/$"),
                group_url("edit"),
                group_url("delete"),
            ]
        ),
    ),
    path(
        "absences/",
        include(
            [
                absence_url(
                    "list",
                    url=r"^$",
                    paginate_by=50,
                    search_form=AbsenceSearchForm,
                    # send_emails_selector='drudge__user__email',
                ),
                absence_url("detail", url=r"^(?P<pk>\d+)/$"),
                absence_url("add", url=r"^add/$"),
                absence_url("edit"),
                absence_url("delete"),
            ]
        ),
    ),
    path(
        "expense_reports/",
        include(
            [
                expensereport_url(
                    "list",
                    url=r"^$",
                    paginate_by=50,
                    search_form=ExpenseReportSearchForm,
                ),
                expensereport_url(
                    "pdf", view=ExpenseReportPDFExportView, url=r"^pdf/$"
                ),
                expensereport_url("detail", url=r"^(?P<pk>\d+)/$"),
                expensereport_url("add", url=r"^add/$"),
                expensereport_url("edit"),
                expensereport_url("delete"),
            ]
        ),
    ),
    path(
        "jobreferences/",
        include(
            [
                jobreference_url(
                    "list",
                    url=r"^$",
                    paginate_by=50,
                    search_form=JobReferenceSearchForm,
                ),
                jobreference_url("detail", url=r"^(?P<pk>\d+)/$"),
                jobreference_url("edit", form_class=JobReferenceForm),
                jobreference_url("delete"),
                jobreference_url(
                    "from_template",
                    view=JobReferenceFromTemplateView,
                    url=r"^(\d+)/(\d+)/$",
                ),
            ]
        ),
    ),
]
