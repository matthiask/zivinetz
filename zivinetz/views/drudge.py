import csv
import os
from datetime import date
from io import BytesIO

import schwifty
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext as _, gettext_lazy
from pdfdocument.utils import pdf_response
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from towel.forms import towel_formfield_callback

from zivinetz.forms import AssignmentSearchForm, DrudgeSearchForm
from zivinetz.models import Assignment, Codeword, Drudge, ExpenseReport, RegionalOffice
from zivinetz.views.base import BaseView
from zivinetz.views.decorators import drudge_required


class AssignmentExportSearchForm(forms.Form):
    status = forms.ChoiceField(
        choices=Assignment.STATUS_CHOICES, required=False, label=_("Status")
    )
    regional_office = forms.ModelChoiceField(
        queryset=RegionalOffice.objects.all(),
        required=False,
        label=_("Regional Office"),
    )
    specification = forms.ModelChoiceField(
        queryset=Assignment.objects.values_list("specification", flat=True).distinct(),
        required=False,
        label=_("Specification"),
    )


class DrudgeExportSearchForm(forms.Form):
    status = forms.ChoiceField(
        choices=Drudge.STATE_CHOICES, required=False, label=_("Status")
    )
    regional_office = forms.ModelChoiceField(
        queryset=RegionalOffice.objects.all(),
        required=False,
        label=_("Regional Office"),
    )
    environment_course = forms.NullBooleanField(
        required=False, label=_("Environment Course")
    )
    motor_saw_course = forms.NullBooleanField(required=False, label=_("Motor Saw Course"))


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
        self.fields["source"].blank = False

    def clean(self):
        data = super().clean()
        source = data.get("source")

        if not source:
            self.add_error("source", "Dieses Feld ist zwingend erforderlich.")

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


class AssignmentExportBaseView(BaseView):
    """Base class for all assignment export views."""

    model = Assignment

    def get_queryset(self):
        """Get and filter assignments based on request parameters."""
        # Get the search form and apply its filters
        search_form = AssignmentSearchForm(self.request.GET, request=self.request)
        if not search_form.is_valid():
            return Assignment.objects.none()

        # Get the filtered queryset using the search form's logic
        queryset = search_form.queryset(Assignment)

        # Apply additional filters using the export search form
        export_form = AssignmentExportSearchForm(self.request.GET)
        if export_form.is_valid():
            if export_form.cleaned_data.get("status"):
                queryset = queryset.filter(status=export_form.cleaned_data["status"])
            if export_form.cleaned_data.get("regional_office"):
                queryset = queryset.filter(
                    regional_office=export_form.cleaned_data["regional_office"]
                )
            if export_form.cleaned_data.get("specification"):
                queryset = queryset.filter(
                    specification=export_form.cleaned_data["specification"]
                )

        return queryset

    def check_permissions(self, request):
        """Check if the user has permission to access this view."""
        if not request.user.userprofile.user_type == "dev_admin":
            return False
        return True

    def get_prepared_data(self):
        """Prepare the data for export."""
        # Get filtered queryset with prefetched related data
        return (
            self.get_queryset()
            .select_related("drudge", "drudge__user", "specification")
            .order_by(
                "drudge__user__last_name", "drudge__user__first_name", "-date_from"
            )
        )

    def format_course_info(self, drudge):
        """Format the course information for a drudge."""
        courses = []
        if drudge.environment_course:
            courses.append("Umweltkurs")
        if drudge.motor_saw_course:
            courses.append("Motorsägenkurs")
        return courses

    def format_date(self, date_obj):
        """Format a date object consistently."""
        if date_obj:
            return date_obj.strftime("%d.%m.%Y")
        return "-"


class AssignmentPDFExportView(AssignmentExportBaseView):
    """Generate a PDF export of assignments."""

    def get(self, request, *args, **kwargs):
        if not self.check_permissions(request):
            return HttpResponseForbidden(
                _("You don't have permission to access this page.")
            )

        queryset = self.get_prepared_data()

        # Create PDF
        pdf, response = pdf_response("assignment_list")
        pdf.init_report()

        # Add title
        pdf.h1(_("Assignment List"))
        pdf.spacer()

        # Add date
        current_time = timezone.now()
        pdf.p(_("Generated on: %s") % current_time.strftime("%d.%m.%Y %H:%M"))
        pdf.spacer()

        # Add search parameters if any
        if request.GET.get("s"):
            self.add_search_parameters(pdf, request)

        # Add data rows
        for assignment in queryset:
            self.add_assignment_data(pdf, assignment)

        pdf.generate()
        return response

    def add_search_parameters(self, pdf, request):
        """Add search parameters to the PDF."""
        pdf.h2(_("Search Parameters"))
        for key, value in request.GET.items():
            if key != "s" and value:
                param_text = self.format_search_parameter(key, value)
                pdf.p(param_text)
        pdf.spacer()

    def add_assignment_data(self, pdf, assignment):
        """Add a single assignment's data to the PDF."""
        # Get course information
        courses = self.format_course_info(assignment.drudge)

        pdf.table(
            [
                (_("ZDP No."), str(assignment.drudge.zdp_no)),
                (
                    _("Name"),
                    f"{assignment.drudge.user.last_name}, {assignment.drudge.user.first_name}",
                ),
                (_("Email"), assignment.drudge.user.email),
                (
                    _("Phone"),
                    f"{assignment.drudge.phone_home or '-'} / {assignment.drudge.mobile or '-'}",
                ),
                (_("Kurse"), ", ".join(courses) if courses else "-"),
                (_("Pflichtenheft"), assignment.specification.code),
                (
                    _("Date"),
                    f"{self.format_date(assignment.date_from)} - {self.format_date(assignment.determine_date_until())}",
                ),
                (_("Status"), assignment.get_status_display()),
                (_("Quelle"), assignment.drudge.source),
            ],
            (4 * cm, 12.4 * cm),
        )
        pdf.spacer()
        pdf.hr_mini()


class AssignmentCSVExportView(AssignmentExportBaseView):
    """Generate a CSV export of assignments."""

    def get(self, request, *args, **kwargs):
        if not self.check_permissions(request):
            return HttpResponseForbidden(
                _("You don't have permission to access this page.")
            )

        queryset = self.get_prepared_data()

        # Create CSV response
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="assignment_list.csv"'

        # Create CSV writer
        writer = csv.writer(response)

        # Write header row
        writer.writerow(self.get_header_row())

        # Write data rows
        for assignment in queryset:
            writer.writerow(self.format_row(assignment))

        return response

    def get_header_row(self):
        """Get the CSV header row."""
        return [
            _("ZDP-Nr."),
            _("Nachname"),
            _("Vorname"),
            _("Adresse"),
            _("PLZ"),
            _("Ort"),
            _("E-Mail"),
            _("Telefon"),
            _("Mobile"),
            _("Geburtsdatum"),
            _("Ausbildung / Beruf"),
            _("Führerausweis"),
            _("Generalabonnement"),
            _("Halbtax"),
            _("Umweltkurs"),
            _("Motorsägenkurs"),
            _("Pflichtenheft"),
            _("Datum von"),
            _("Datum bis"),
            _("Status"),
            _("Quelle")
        ]

    def format_row(self, assignment):
        """Format a single row for CSV export."""
        return [
            assignment.drudge.zdp_no,
            assignment.drudge.user.last_name,
            assignment.drudge.user.first_name,
            assignment.drudge.address,
            assignment.drudge.zip_code,
            assignment.drudge.city,
            assignment.drudge.user.email,
            assignment.drudge.phone_home or "-",
            assignment.drudge.mobile or "-",
            assignment.drudge.date_of_birth.strftime("%d.%m.%Y"),
            assignment.drudge.education_occupation,
            "Ja" if assignment.drudge.driving_license else "Nein",
            "Ja" if assignment.drudge.general_abonnement else "Nein",
            "Ja" if assignment.drudge.half_fare_card else "Nein",
            "Ja" if assignment.drudge.environment_course else "Nein",
            "Ja" if assignment.drudge.motor_saw_course else "Nein",
            assignment.specification.code,
            self.format_date(assignment.date_from),
            self.format_date(assignment.determine_date_until()),
            assignment.get_status_display(),
            assignment.drudge.source
        ]


class DrudgePDFExportView(BaseView):
    #Generate a PDF export of drudges.

    model = Drudge
    template_name = "zivinetz/drudge_list.html"

    @staticmethod
    def draw_wrapped_text(p, text, x, y, max_width, font_name, font_size):
        #Draw text with word wrapping.#
        if not text:
            return y - 0.5 * cm

        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            if p.stringWidth(test_line, font_name, font_size) < max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        for line in lines:
            p.drawString(x, y, line)
            y -= 0.5 * cm

        return y

    def get_queryset(self):
        # Get the search form and apply its filters
        search_form = DrudgeSearchForm(self.request.GET, request=self.request)
        if not search_form.is_valid():
            return Drudge.objects.none()

        # Get the filtered queryset using the search form's logic
        queryset = search_form.queryset(Drudge)

        # Apply additional filters using the export search form
        export_form = DrudgeExportSearchForm(self.request.GET)
        if export_form.is_valid():
            if export_form.cleaned_data.get("status"):
                queryset = queryset.filter(status=export_form.cleaned_data["status"])
            if export_form.cleaned_data.get("regional_office"):
                queryset = queryset.filter(
                    regional_office=export_form.cleaned_data["regional_office"]
                )
            if export_form.cleaned_data.get("environment_course") is not None:
                queryset = queryset.filter(
                    environment_course=export_form.cleaned_data["environment_course"]
                )
            if export_form.cleaned_data.get("motor_saw_course") is not None:
                # For motor_saw_course, we need to handle the boolean conversion
                # since the model field is a CharField but we're filtering as boolean
                motor_saw_value = export_form.cleaned_data["motor_saw_course"]
                if motor_saw_value is True:
                    # Filter for drudges who have any motor saw course
                    queryset = queryset.filter(motor_saw_course__isnull=False).exclude(motor_saw_course="")
                elif motor_saw_value is False:
                    # Filter for drudges who have no motor saw course
                    queryset = queryset.filter(motor_saw_course__isnull=True) | queryset.filter(motor_saw_course="")
        return queryset

    def get_active_status(self, drudge):
        """Get the current status of a drudge based on their active assignments."""
        from zivinetz.models import Assignment

        # Check for active assignments
        active_assignments = drudge.assignments.filter(
            status__in=(Assignment.ARRANGED, Assignment.MOBILIZED),
            date_from__lte=date.today(),
            date_until__gte=date.today(),
        )

        if active_assignments.exists():
            return "Aufgeboten"
        return (
            drudge.get_status_display()
            if hasattr(drudge, "get_status_display")
            else "-"
        )

    def format_search_parameter(self, key, value):
        """Format search parameters for display in German."""
        from zivinetz.models import Assignment, RegionalOffice

        # Map of parameter keys to German labels
        param_labels = {
            "s": "Suche",
            "status": "Status",
            "regional_office": "Regionalstelle",
            "environment_course": "Umweltkurs",
            "motor_saw_course": "Motorsägenkurs",
            "only_active": "Nur aktive",
            "driving_license": "Führerschein",
            "date_from__gte": "Datum von",
            "date_until__lte": "Datum bis",
        }

        # Get the label for the parameter
        label = param_labels.get(key, key)

        # Format the value based on the parameter type
        if key == "status":
            status_map = dict(Assignment.STATUS_CHOICES)
            return f"{label}: {status_map.get(value, value)}"
        if key == "regional_office":
            try:
                office = RegionalOffice.objects.get(id=value)
                return f"{label}: {office.name}"
            except RegionalOffice.DoesNotExist:
                return f"{label}: {value}"
        elif key in ["environment_course", "motor_saw_course"]:
            if value == "True":
                return f"{label}: Ja"
            if value == "False":
                return f"{label}: Nein"
            return f"{label}: {value}"
        elif key == "only_active":
            if value == "1":
                return f"{label}: Ja"
            return f"{label}: Nein"
        elif key in ["date_from__gte", "date_until__lte"]:
            try:
                from datetime import datetime

                date_obj = datetime.strptime(value, "%Y-%m-%d")
                return f"{label}: {date_obj.strftime('%d.%m.%Y')}"
            except ValueError:
                return f"{label}: {value}"

        return f"{label}: {value}"

    def get(self, request, *args, **kwargs):
        if not request.user.userprofile.user_type == "dev_admin":
            return HttpResponseForbidden(
                _("You don't have permission to access this page.")
            )

        # Get filtered queryset with prefetched related data
        queryset = (
            self.get_queryset()
            .select_related("user", "regional_office")
            .prefetch_related(
                "assignments", "assignments__specification", "assignments__assessments"
            )
        )

        # Create PDF
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="drudge_list.pdf"'

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)

        # Register font once
        font_path = os.path.join(settings.STATIC_ROOT, "fonts", "DejaVuSans.ttf")
        if not os.path.exists(font_path):
            font_path = os.path.join(settings.STATIC_ROOT, "DejaVuSans.ttf")
        if not os.path.exists(font_path):
            p.setFont("Helvetica", 10)
            font_name = "Helvetica"
            bold_font_name = "Helvetica-Bold"
        else:
            pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
            p.setFont("DejaVuSans", 10)
            font_name = "DejaVuSans"
            bold_font_name = "DejaVuSans-Bold"

        # Set up page
        width, height = A4
        margin = 1.5 * cm
        line_height = 0.5 * cm
        y = height - margin

        # Add title
        p.setFont(font_name, 16)
        p.drawString(margin, y, _("Zivi-Liste Export"))
        y -= line_height * 2

        # Add date
        p.setFont(font_name, 10)
        current_time = timezone.now()
        p.drawString(
            margin, y, _("Generiert am: %s") % current_time.strftime("%d.%m.%Y %H:%M")
        )
        y -= line_height * 2

        # Add search parameters if any
        if request.GET.get("s"):
            p.setFont(bold_font_name, 10)
            p.drawString(margin, y, _("Suchparameter:"))
            y -= line_height

            # Format and display search parameters
            p.setFont(font_name, 10)
            for key, value in request.GET.items():
                if key != "s" and value:
                    param_text = self.format_search_parameter(key, value)
                    y = self.draw_wrapped_text(
                        p,
                        param_text,
                        margin + cm,
                        y,
                        width - (2 * margin),
                        font_name,
                        10,
                    )
            y -= line_height

        # Draw header line
        p.line(margin, y, width - margin, y)
        y -= line_height

        # Add data rows
        p.setFont(font_name, 9)

        # Process drudges in batches
        batch_size = 50
        for i in range(0, len(queryset), batch_size):
            batch = queryset[i : i + batch_size]

            for drudge in batch:
                # Check if we need a new page
                if y < margin + (8 * line_height):
                    p.showPage()
                    y = height - margin
                    p.setFont(font_name, 9)

                # Calculate average mark from assessments (using prefetched data)
                avg_mark = None
                total_mark = 0
                count = 0
                for assignment in drudge.assignments.all():
                    for assessment in assignment.assessments.all():
                        if assessment.mark is not None:
                            total_mark += assessment.mark
                            count += 1
                if count > 0:
                    avg_mark = round(total_mark / count, 1)

                # Format assignments (using prefetched data)
                assignments_list = []
                for assignment in drudge.assignments.all():
                    date_from = (
                        assignment.date_from.strftime("%d.%m.%Y")
                        if assignment.date_from
                        else "-"
                    )
                    date_until = (
                        assignment.determine_date_until().strftime("%d.%m.%Y")
                        if assignment.determine_date_until()
                        else "-"
                    )
                    assignments_list.append(
                        f"{assignment.specification.code} ({date_from} - {date_until})"
                    )

                last_assignment_str = assignments_list[0] if assignments_list else "-"
                assignments_str = (
                    "; ".join(assignments_list) if assignments_list else "-"
                )

                # Format courses
                courses = []
                if drudge.environment_course:
                    courses.append("ENV")
                if drudge.motor_saw_course:
                    courses.append("MOT")
                courses_str = ", ".join(courses) if courses else "-"

                # Draw drudge information
                x = margin
                p.setFont(bold_font_name, 9)
                p.drawString(x, y, "ZDP:")
                x += p.stringWidth("ZDP:", bold_font_name, 9) + 0.2 * cm
                p.setFont(font_name, 9)
                p.drawString(x, y, str(drudge.zdp_no))
                x += p.stringWidth(str(drudge.zdp_no), font_name, 9) + 0.5 * cm

                p.setFont(bold_font_name, 9)
                p.drawString(x, y, "Name:")
                x += p.stringWidth("Name:", bold_font_name, 9) + 0.2 * cm
                p.setFont(font_name, 9)
                name_text = f"{drudge.user.first_name} {drudge.user.last_name}"
                p.drawString(x, y, name_text)
                x += p.stringWidth(name_text, font_name, 9) + 0.5 * cm

                # Status
                p.setFont(bold_font_name, 9)
                p.drawString(x, y, "Status:")
                x += p.stringWidth("Status:", bold_font_name, 9) + 0.2 * cm
                p.setFont(font_name, 9)
                status_text = self.get_active_status(drudge)
                p.drawString(x, y, status_text)
                y -= line_height

                # Address
                x = margin
                p.setFont(bold_font_name, 9)
                p.drawString(x, y, "Adresse:")
                x += p.stringWidth("Adresse:", bold_font_name, 9) + 0.2 * cm
                p.setFont(font_name, 9)
                address_text = f"{drudge.address}, {drudge.zip_code} {drudge.city}"
                y = self.draw_wrapped_text(
                    p, address_text, x, y, width - margin - x, font_name, 9
                )

                # Contact information
                x = margin
                p.setFont(bold_font_name, 9)
                p.drawString(x, y, "Tel:")
                x += p.stringWidth("Tel:", bold_font_name, 9) + 0.2 * cm
                p.setFont(font_name, 9)
                phone_text = f"{drudge.phone_home or '-'} / {drudge.mobile or '-'}"
                p.drawString(x, y, phone_text)
                x += p.stringWidth(phone_text, font_name, 9) + 0.5 * cm

                # Email
                p.setFont(bold_font_name, 9)
                p.drawString(x, y, "E-Mail:")
                x += p.stringWidth("E-Mail:", bold_font_name, 9) + 0.2 * cm
                p.setFont(font_name, 9)
                y = self.draw_wrapped_text(
                    p, drudge.user.email, x, y, width - margin - x, font_name, 9
                )

                # Education and courses
                x = margin
                p.setFont(bold_font_name, 9)
                p.drawString(x, y, "Bildung/Beruf:")
                x += p.stringWidth("Bildung/Beruf:", bold_font_name, 9) + 0.2 * cm
                p.setFont(font_name, 9)
                education_text = drudge.education_occupation or "-"
                y = self.draw_wrapped_text(
                    p, education_text, x, y, width - margin - x, font_name, 9
                )

                # Courses
                x = margin
                p.setFont(bold_font_name, 9)
                p.drawString(x, y, "Kurse:")
                x += p.stringWidth("Kurse:", bold_font_name, 9) + 0.2 * cm
                p.setFont(font_name, 9)
                p.drawString(x, y, courses_str)
                y -= line_height

                # Last assignment
                x = margin
                p.setFont(bold_font_name, 9)
                p.drawString(x, y, "Letzter Einsatz:")
                x += p.stringWidth("Letzter Einsatz:", bold_font_name, 9) + 0.2 * cm
                p.setFont(font_name, 9)
                y = self.draw_wrapped_text(
                    p, last_assignment_str, x, y, width - margin - x, font_name, 9
                )

                # All assignments
                x = margin
                p.setFont(bold_font_name, 9)
                p.drawString(x, y, "Alle Einsätze:")
                x += p.stringWidth("Alle Einsätze:", bold_font_name, 9) + 0.2 * cm
                p.setFont(font_name, 9)
                y = self.draw_wrapped_text(
                    p, assignments_str, x, y, width - margin - x, font_name, 9
                )

                # Average mark
                x = margin
                p.setFont(bold_font_name, 9)
                p.drawString(x, y, "Durchschnittsnote:")
                x += p.stringWidth("Durchschnittsnote:", bold_font_name, 9) + 0.2 * cm
                p.setFont(font_name, 9)
                p.drawString(x, y, str(avg_mark) if avg_mark is not None else "-")
                y -= line_height * 1.5

                # Draw separator line
                p.line(margin, y, width - margin, y)
                y -= line_height

        p.showPage()
        p.save()

        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)

        return response


class DrudgeCSVExportView(BaseView):
    model = Drudge

    def get_queryset(self):
        # Get the search form and apply its filters
        search_form = DrudgeSearchForm(self.request.GET, request=self.request)
        if not search_form.is_valid():
            return Drudge.objects.none()

        # Get the filtered queryset using the search form's logic
        queryset = search_form.queryset(Drudge)

        # Apply additional filters using the export search form
        export_form = DrudgeExportSearchForm(self.request.GET)
        if export_form.is_valid():
            if export_form.cleaned_data.get("status"):
                queryset = queryset.filter(status=export_form.cleaned_data["status"])
            if export_form.cleaned_data.get("regional_office"):
                queryset = queryset.filter(
                    regional_office=export_form.cleaned_data["regional_office"]
                )
            if export_form.cleaned_data.get("environment_course") is not None:
                queryset = queryset.filter(
                    environment_course=export_form.cleaned_data["environment_course"]
                )
            if export_form.cleaned_data.get("motor_saw_course") is not None:
                queryset = queryset.filter(
                    motor_saw_course=export_form.cleaned_data["motor_saw_course"]
                )

        return queryset

    def get_active_status(self, drudge):
        """Get the current status of a drudge based on their active assignments."""
        from zivinetz.models import Assignment

        # Check for active assignments
        active_assignments = drudge.assignments.filter(
            status__in=(Assignment.ARRANGED, Assignment.MOBILIZED),
            date_from__lte=date.today(),
            date_until__gte=date.today(),
        )

        if active_assignments.exists():
            return "Aufgeboten"
        return (
            drudge.get_status_display()
            if hasattr(drudge, "get_status_display")
            else "-"
        )

    def get(self, request, *args, **kwargs):
        if not request.user.userprofile.user_type == "dev_admin":
            return HttpResponseForbidden(
                _("You don't have permission to access this page.")
            )

        # Get filtered queryset with prefetched related data
        queryset = (
            self.get_queryset()
            .select_related("user", "regional_office")
            .prefetch_related(
                "assignments", "assignments__specification", "assignments__assessments"
            )
        )

        # Create CSV response
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="drudge_list.csv"'

        # Create CSV writer
        writer = csv.writer(response)

        # Write header row
        writer.writerow(
            [
                _("ZDP-Nr."),
                _("Nachname"),
                _("Vorname"),
                _("Status"),
                _("Regionalstelle"),
                _("Umweltkurs"),
                _("Motorsägenkurs"),
                _("Bildung/Beruf"),
                _("Durchschnittsnote"),
                _("Alle Einsätze"),
            ]
        )

        # Write data rows
        for drudge in queryset:
            # Calculate average mark
            avg_mark = None
            total_mark = 0
            count = 0
            for assignment in drudge.assignments.all():
                for assessment in assignment.assessments.all():
                    if assessment.mark is not None:
                        total_mark += assessment.mark
                        count += 1
            if count > 0:
                avg_mark = round(total_mark / count, 1)

            # Format assignments
            assignments_list = []
            for assignment in drudge.assignments.all():
                date_from = (
                    assignment.date_from.strftime("%d.%m.%Y")
                    if assignment.date_from
                    else "-"
                )
                date_until = (
                    assignment.determine_date_until().strftime("%d.%m.%Y")
                    if assignment.determine_date_until()
                    else "-"
                )
                assignments_list.append(
                    f"{assignment.specification.code} ({date_from} - {date_until})"
                )

            assignments_str = "; ".join(assignments_list) if assignments_list else "-"

            # Write row
            writer.writerow(
                [
                    drudge.zdp_no,
                    drudge.user.last_name,
                    drudge.user.first_name,
                    self.get_active_status(drudge),
                    drudge.regional_office.name if drudge.regional_office else "-",
                    "Ja" if drudge.environment_course else "Nein",
                    "Ja" if drudge.motor_saw_course else "Nein",
                    drudge.education_occupation or "-",
                    str(avg_mark) if avg_mark is not None else "-",
                    assignments_str,
                ]
            )

        return response
