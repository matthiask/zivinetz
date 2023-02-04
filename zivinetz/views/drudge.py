from datetime import date

import schwifty
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import gettext as _, gettext_lazy
from towel.forms import towel_formfield_callback

from zivinetz.models import Assignment, Codeword, Drudge, ExpenseReport
from zivinetz.views.decorators import drudge_required


class AssignmentForm(forms.ModelForm):
    codeword = forms.CharField(label=gettext_lazy("Codeword"))

    formfield_callback = towel_formfield_callback

    class Meta:
        model = Assignment
        fields = (
            "specification",
            "regional_office",
            "date_from",
            "date_until",
            "part_of_long_assignment",
        )

    def clean_codeword(self):
        codeword = self.cleaned_data.get("codeword")
        if codeword != Codeword.objects.word(key="einsatz"):
            raise forms.ValidationError(_("Codeword is incorrect."))
        return codeword

    def clean(self):
        data = super().clean()

        if data.get("date_from") and data.get("date_until"):
            if (
                data["date_from"] > data["date_until"]
                or data["date_from"] < date.today()
            ):
                raise forms.ValidationError(_("Date period is invalid."))

        return data


@drudge_required
def dashboard(request, drudge):
    aform_initial = {"regional_office": drudge.regional_office_id}

    aform = AssignmentForm(initial=aform_initial)

    if request.method == "POST":
        if "assignment" in request.POST:
            aform = AssignmentForm(request.POST)
            if aform.is_valid():
                assignment = aform.save(commit=False)
                assignment.drudge = drudge
                assignment.save()
                messages.success(request, _("Successfully saved new assignment."))

                return HttpResponseRedirect(request.path)

    return render(
        request,
        "zivinetz/drudge_dashboard.html",
        {
            "drudge": drudge,
            "assignment_form": aform,
            "assignments": drudge.assignments.order_by("-date_from"),
            "expense_reports": ExpenseReport.objects.filter(
                assignment__drudge=drudge,
                status__in=(ExpenseReport.FILLED, ExpenseReport.PAID),
            ).order_by("-date_from"),
        },
    )


class UserForm(forms.ModelForm):
    formfield_callback = towel_formfield_callback
    error_css_class = "error"
    required_css_class = "required"

    first_name = forms.CharField(label=_("first name"))
    last_name = forms.CharField(label=_("last name"))

    class Meta:
        model = User
        fields = ("first_name", "last_name")


class DrudgeForm(forms.ModelForm):
    formfield_callback = towel_formfield_callback
    error_css_class = "error"
    required_css_class = "required"

    environment_course = forms.NullBooleanField(
        label=_("environment course"),
        required=True,
        help_text=_("I have taken the environment course already."),
    )

    class Meta:
        model = Drudge
        exclude = ("user", "internal_notes")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["youth_association"].label = _(
            "Bist du Mitglied in einem Jugendverband?"
        )
        self.fields["youth_association"].required = True
        self.fields["source"].required = True

    def clean(self):
        data = super().clean()
        if data.get("source") == "Anderes:" and not data.get("source_other"):
            self.add_error(
                "source_other", "Bitte angeben wenn du oben 'Anderes:' gewählt hast."
            )
        return data

    def clean_bank_account(self):
        value = self.cleaned_data.get("bank_account")
        if value:
            try:
                schwifty.IBAN(value)
            except ValueError as exc:
                raise forms.ValidationError(exc)
        return value

    def clean_environment_course(self):
        value = self.cleaned_data.get("environment_course")
        if value is None:
            raise forms.ValidationError(_("Please select either yes or no."))
        return value


@login_required
def profile(request):
    try:
        drudge = Drudge.objects.get(user=request.user)
    except Drudge.DoesNotExist:
        drudge = None

    if request.method == "POST":
        form = DrudgeForm(request.POST, request.FILES, instance=drudge)
        form2 = UserForm(request.POST, request.FILES, instance=request.user)

        if form.is_valid() and form2.is_valid():
            drudge = form.save(commit=False)
            drudge.user = request.user
            drudge.save()

            form2.save()

            messages.success(request, _("Successfully saved profile information."))

            return HttpResponseRedirect(request.path)
    else:
        form = DrudgeForm(instance=drudge)
        form2 = UserForm(instance=request.user)

    return render(
        request,
        "zivinetz/drudge_profile.html",
        {"object": drudge, "form": form, "form2": form2, "title": _("Edit profile")},
    )
