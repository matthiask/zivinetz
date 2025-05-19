import operator
import os

from datetime import date, timedelta, datetime
from functools import reduce
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils import timezone
from pdfdocument.document import PDFDocument, cm, mm
from pdfdocument.elements import create_stationery_fn
from pdfdocument.utils import pdf_response
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from django.template.loader import render_to_string

from zivinetz.models import Assignment, AssignmentChange, ExpenseReport, JobReference
from zivinetz.views.decorators import user_type_required
from zivinetz.forms import AssignmentSearchForm


class AssignmentPDFStationery:
    def __init__(self, assignment):
        self.assignment = assignment

    def __call__(self, canvas, pdfdocument):
        # canvas.saveState()
        # canvas.restoreState()

        if pdfdocument.doc.page == 1:
            self.page_1(canvas, pdfdocument)
        elif pdfdocument.doc.page == 2:
            self.page_2(canvas, pdfdocument)

    markers = {
        "standard": (53.5, 94),
        "trial": (81, 94),
        "long_assignment": (113.5, 94),
        # 'working_time_fixed': (112, 60),
        # 'working_time_nightshift': (151, 59),
        # 'working_time_flexible': (112, 55),
        # 'working_time_weekend': (151, 55),
        # "vegetarianism": (113.5, 40),
        # "no_vegetarianism": (155, 40),
        # "pocket_money": (31, 167),
        # 'accomodation_working_compensated': (56, 230),
        # 'accomodation_working_provided': (85, 230),
        # 'accomodation_free_compensated': (113.5, 230),
        # 'accomodation_free_provided': (143, 230),
        # 'accomodation_used': (75, 251),
        # 'accomodation_notused': (113.5, 251),
        #
        "breakfast_working_at_company": (92, 161),
        "breakfast_working_at_home": (110, 161),
        "breakfast_working_external": (110, 161),
        #
        "breakfast_free_at_company": (147.5, 161),
        "breakfast_free_at_home": (165, 161),
        "breakfast_free_external": (165, 161),
        #
        "lunch_working_at_company": (92, 157),
        "lunch_working_at_home": (110, 157),
        "lunch_working_external": (110, 157),
        #
        "lunch_free_at_company": (147.5, 157),
        "lunch_free_at_home": (165, 157),
        "lunch_free_external": (165, 157),
        #
        "supper_working_at_company": (92, 152.5),
        "supper_working_at_home": (110, 152.5),
        "supper_working_external": (110, 152.5),
        #
        "supper_free_at_company": (147.5, 152.5),
        "supper_free_at_home": (165, 152.5),
        "supper_free_external": (165, 152.5),
        #
        "accomodation_throughout": (31, 257),
        "accomodation_not_throughout": (100, 258),
        #
        "food_throughout": (31, 183),
        "food_not_throughout": (31, 178.5),
        #
        "drudge_uses_accomodation": (35.5, 252.5),
        "drudge_renounce_accomodation_1": (35.5, 243),
        # "drudge_renounce_accomodation_2": (186, 250),
        #
        "public_transports": (31, 206.5),
        "private_transport": (31, 201.5),
        #
        "special_tickets_yes": (39, 248.5),
        # "special_tickets_no": (186, 137),
        "clothing_provided": (31, 125),
        "clothing_compensated": (31, 121),
        #
        # "arrangement_timely": (31, 102),
        # "arrangement_late": (31, 102),
        #
        "legalese_0": (175.5, 101),
        "legalese_1": (185, 80),
        "legalese_2": (185, 71),
        "legalese_3": (185, 62.5),
    }

    def draw_marker(self, canvas, key):
        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawString(self.markers[key][0] * mm, self.markers[key][1] * mm, "x")

    def _draw_all_markers(self, canvas):  # pragma: no cover
        canvas.setFillColorRGB(1, 0, 0)
        canvas.setFont("Helvetica-Bold", 14)
        for key, pos in self.markers.items():
            canvas.drawString(pos[0] * mm, pos[1] * mm, f"x {key}")
            # canvas.drawString(pos[0] * mm, pos[1] * mm, "x")

    def page_1(self, canvas, pdfdocument):
        # self._draw_all_markers(canvas)
        drudge = self.assignment.drudge
        scope_statement = self.assignment.specification.scope_statement

        frame_1 = [
            drudge.user.last_name,
            drudge.address.replace("\r", "").replace("\n", " "),
            " / ".join(phone for phone in (drudge.phone_home, drudge.mobile) if phone),
            (drudge.date_of_birth and drudge.date_of_birth.strftime("%d.%m.%Y") or ""),
            drudge.health_insurance_company,
        ]

        frame_2 = [
            drudge.zdp_no,
            drudge.user.first_name,
            f"{drudge.zip_code} {drudge.city}",
            drudge.user.email,
            drudge.bank_account,
            drudge.education_occupation.replace("\r", "").replace("\n", ", "),
            # drudge.health_insurance_account,
        ]

        # frame_3 = []
        # frame_4 = []

        frame_5 = [
            "",
            scope_statement.company_name or "Verein Naturnetz",
            scope_statement.company_address or "Chlosterstrasse",
            "",
            scope_statement.company_contact_name or "Marco Sacchi",
            scope_statement.company_contact_phone or "044 533 11 44",
        ]

        # frame_5a = ["", scope_statement.company_contact_function or "Geschäftsleiter"]

        frame_6 = [
            scope_statement.branch_no,
            "",
            scope_statement.company_contact_location or "8109 Kloster Fahr",
            "",
            scope_statement.company_contact_function or "Geschäftsleiter",
            scope_statement.company_contact_email or "ms@naturnetz.ch",
        ]

        # frame_6a = [
        #     scope_statement.company_contact_name or "Marco Sacchi",
        #     scope_statement.company_contact_phone or "044 533 11 44",
        # ]

        frame_7 = [
            "%s %s"
            % (
                self.assignment.specification.scope_statement.eis_no,
                self.assignment.specification.scope_statement.name,
            ),
            self.assignment.date_from.strftime("%d.%m.%Y"),
        ]

        frame_8 = [
            scope_statement.work_location or "Kloster Fahr, ganze Schweiz",
            "",
            self.assignment.date_until.strftime("%d.%m.%Y"),
        ]

        frame_9 = []

        # frame_10 = [self.assignment.regional_office.city]
        # frame_11 = []

        frames = [
            (frame_1, 53 * mm, 190 * mm, 7 * mm),
            (frame_2, 143 * mm, 190 * mm, 6.9 * mm),
            # (frame_3, 63 * mm, 174 * mm, 11 * mm),
            # (frame_4, 140 * mm, 174 * mm, 11 * mm),
            (frame_5, 56 * mm, 143 * mm, 7 * mm),
            (frame_6, 130 * mm, 143 * mm, 7 * mm),
            # (frame_5a, 63 * mm, 138 * mm, 7.2 * mm),
            # (frame_6a, 140 * mm, 138 * mm, 7.2 * mm),
            (frame_7, 56 * mm, 116 * mm, 8 * mm),
            (frame_8, 136 * mm, 116 * mm, 8 * mm),
            (frame_9, 87 * mm, 99 * mm, 7.4 * mm),
            # (frame_10, 127 * mm, 268 * mm, 0),
            # (frame_11, 63 * mm, 55 * mm, 8.5 * mm),
        ]

        canvas.setFont("Helvetica", 9)
        for frame, x, y, line in frames:
            for i, text in enumerate(reversed(frame)):
                canvas.drawString(x, y + i * line, text)

        try:
            scope_statement = self.assignment.specification.scope_statement
            company_holiday = scope_statement.company_holidays.filter(
                date_until__gte=self.assignment.date_from,
                date_from__lte=self.assignment.date_until,
            )[0]
        except IndexError:
            company_holiday = None

        if company_holiday:
            canvas.drawString(
                120 * mm, 86 * mm, company_holiday.date_from.strftime("%d.%m.%Y")
            )
            canvas.drawString(
                165 * mm, 86 * mm, company_holiday.date_until.strftime("%d.%m.%Y")
            )

        if False:
            canvas.drawString(120 * mm, 86 * mm, "01.02.2003")
            canvas.drawString(165 * mm, 86 * mm, "01.02.2003")

        if self.assignment.part_of_long_assignment:
            self.draw_marker(canvas, "long_assignment")
        else:
            self.draw_marker(canvas, "standard")

        # self.draw_marker(canvas, 'working_time_fixed')

        # if drudge.vegetarianism:
        #     self.draw_marker(canvas, 'vegetarianism')
        # else:
        #     self.draw_marker(canvas, 'no_vegetarianism')

    def page_2(self, canvas, pdfdocument):
        # self._draw_all_markers(canvas)
        spec = self.assignment.specification
        # drudge = self.assignment.drudge

        # self.draw_marker(canvas, 'pocket_money')

        for meal in ("breakfast", "lunch", "supper"):
            for day_type in ("working", "free"):
                marker = "{}_{}_{}".format(
                    meal,
                    day_type,
                    getattr(spec, f"{meal}_{day_type}"),
                )

                if marker.endswith("at_accomodation"):
                    marker = marker.replace(
                        "at_accomodation",
                        spec.with_accomodation and "at_company" or "at_home",
                    )
                elif marker.endswith("no_compensation"):
                    # in this context, at_company is the same
                    # as no_compensation
                    marker = marker.replace("no_compensation", "at_company")

                self.draw_marker(canvas, marker)

        self.draw_marker(canvas, "clothing_%s" % spec.clothing)

        if spec.accomodation_throughout:
            self.draw_marker(canvas, "accomodation_throughout")

            if spec.with_accomodation:
                self.draw_marker(canvas, "drudge_uses_accomodation")
                self.draw_marker(canvas, "special_tickets_yes")
            else:
                self.draw_marker(canvas, "drudge_renounce_accomodation_1")

        if not spec.with_accomodation:
            self.draw_marker(canvas, "public_transports")

        if spec.food_throughout:
            self.draw_marker(canvas, "food_throughout")
        else:
            self.draw_marker(canvas, "food_not_throughout")

        # if drudge.vegetarianism:
        #     canvas.drawString(55 * mm, 188 * mm, "Vegetarisch")

        self.draw_marker(canvas, "legalese_0")
        self.draw_marker(canvas, "legalese_1")
        self.draw_marker(canvas, "legalese_2")
        self.draw_marker(canvas, "legalese_3")


@login_required
def assignment_pdf(request, assignment_id):
    assignment = get_object_or_404(
        Assignment.objects.select_related("drudge__user"), pk=assignment_id
    )

    if not request.user.is_staff:
        if assignment.drudge.user != request.user:
            return HttpResponseForbidden("<h1>Access forbidden</h1>")

    result_writer = PdfWriter()

    # Generate the first page ################################################
    first_page = BytesIO()
    pdf = PDFDocument(first_page)

    pdf.init_report()
    pdf.generate_style(font_size=10)

    scope_statement = assignment.specification.scope_statement
    address = [
        scope_statement.company_name or "Verein Naturnetz",
        scope_statement.company_address or "Chlosterstrasse",
        scope_statement.company_contact_location or "8109 Kloster Fahr",
    ]

    pdf.spacer(25 * mm)
    pdf.table(list(zip(address, address)), (8.2 * cm, 8.2 * cm), pdf.style.tableBase)
    pdf.spacer(30 * mm)

    pdf.p_markup(
        """
Lieber Zivi<br /><br />

Vielen Dank fürs Erstellen deiner Einsatzvereinbarung! Du findest hier nun die
Einsatzvereinbarung und einige Hinweise zum Einsatz beim Naturnetz. Bitte lies
alles nochmals genau durch und überprüfe deine Daten auf Fehler. Wenn alles
korrekt ist, unterschreibe die Einsatzvereinbarung und schicke diese ans
Naturnetz. Die Naturnetz-Adresse ist oben aufgedruckt (passend für ein
Fenstercouvert). Die Blätter mit den Hinweisen solltest du bei dir behalten
und für deinen Zivildiensteinsatz aufbewahren. Mit deiner Unterschrift
bestätigst du, dass du die Bestimmungen gelesen und akzeptiert hast. Die
Adresse unten wird von uns benutzt, um die Einsatzvereinbarung an das
Regionalzentrum weiterzuleiten.<br /><br />

Bestätigung: Ich akzeptiere die internen Bestimmungen des Naturnetz (Beilagen
zur Einsatzvereinbarung).<br /><br /><br /><br />

_________________________________________<br />
%s, %s<br /><br />

Wir freuen uns auf deinen Einsatz!
"""
        % (date.today().strftime("%d.%m.%Y"), assignment.drudge.user.get_full_name())
    )
    pdf.spacer(26 * mm)

    address = "\n".join(
        [assignment.regional_office.name, assignment.regional_office.address]
    ).replace("\r", "")

    pdf.table([(address, address)], (8.2 * cm, 8.2 * cm), pdf.style.tableBase)

    pdf.generate()

    # Add the first page to the output #######################################
    first_page_reader = PdfReader(first_page)
    result_writer.add_page(first_page_reader.pages[0])

    # Generate the form ######################################################
    overlay = BytesIO()
    pdf = PDFDocument(overlay)

    # pdf.show_boundaries = True
    pdf.init_report(page_fn=create_stationery_fn(AssignmentPDFStationery(assignment)))

    pdf.pagebreak()
    pdf.pagebreak()

    pdf.generate()

    # Merge the form and the overlay, and add everything to the output #######
    eiv_reader = PdfReader(
        os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data",
            "Einsatzvereinbarung.pdf",
        )
    )
    overlay_reader = PdfReader(overlay)

    for idx in range(2):
        page = eiv_reader.pages[idx]
        page.merge_page(overlay_reader.pages[idx])
        result_writer.add_page(page)

    # Add the conditions PDF if it exists ####################################
    if assignment.specification.conditions:
        conditions_reader = PdfReader(assignment.specification.conditions.open("rb"))
        for page in conditions_reader.pages:
            result_writer.add_page(page)

    # Response! ##############################################################
    response = HttpResponse(content_type="application/pdf")
    result_writer.write(response)

    response["Content-Disposition"] = "attachment; filename=eiv-{}.pdf".format(
        assignment.pk,
    )
    return response


@login_required
def expense_report_pdf(request, expense_report_id):
    report = get_object_or_404(
        ExpenseReport.objects.select_related("assignment__drudge__user"),
        pk=expense_report_id,
    )

    if not request.user.is_staff:
        if report.assignment.drudge.user != request.user:
            return HttpResponseForbidden("<h1>Access forbidden</h1>")

    table, additional, total = report.compensations()

    if not all((t is not None) for t in (table, additional, total)):
        messages.error(request, _("No expense data, cannot generate report."))
        return redirect(report.assignment)

    assignment = report.assignment
    drudge = assignment.drudge
    scope_statement = assignment.specification.scope_statement

    pdf, response = pdf_response("expense-report-%s" % report.pk)
    pdf.init_report()

    pdf.h1("Spesenrapport")
    pdf.h2(
        "Einsatzbetrieb %s - %s, %s, %s %s"
        % (
            scope_statement.branch_no,
            scope_statement.company_name,
            scope_statement.company_address,
            scope_statement.company_zip_code,
            scope_statement.company_city,
        )
    )
    pdf.spacer()

    pdf.table(
        [
            ("Pflichtenheft:", "%s" % report.assignment.specification),
            ("Name, Vorname:", "%s" % drudge.user.get_full_name()),
            (
                "Adresse:",
                f"{drudge.address}, {drudge.zip_code} {drudge.city}",
            ),
            ("ZDP:", drudge.zdp_no),
            (
                "Gesamteinsatz:",
                "%s - %s"
                % (
                    assignment.date_from.strftime("%d.%m.%Y"),
                    assignment.date_until.strftime("%d.%m.%Y"),
                ),
            ),
            (
                "Meldeperiode:",
                "%s - %s"
                % (
                    report.date_from.strftime("%d.%m.%Y"),
                    report.date_until.strftime("%d.%m.%Y"),
                ),
            ),
        ],
        (4 * cm, 12.4 * cm),
        pdf.style.tableLLR,
    )

    pdf.spacer()

    def notes(from_):
        return (
            ("FONT", (0, from_), (-1, from_), "Helvetica-Oblique", 8),
            # ('LEFTPADDING', (0, from_), (-1, from_), 3 * mm),
        )

    pdf.table(
        table,
        (4 * cm, 2 * cm, 2 * cm, 2 * cm, 2 * cm, 2 * cm, 2.4 * cm),
        pdf.style.tableHead
        + tuple(reduce(operator.add, (notes(i) for i in range(2, 12, 2)))),
    )
    pdf.table(
        additional,
        (14 * cm, 2.4 * cm),
        pdf.style.table + notes(1) + notes(3) + notes(5),
    )
    pdf.spacer(1 * mm)
    pdf.table([(_("Total"), total)], (14 * cm, 2.4 * cm), pdf.style.tableHead)

    pdf.spacer()

    pdf.table(
        [(_("bank account") + ":", drudge.bank_account)],
        (4 * cm, 12.4 * cm),
        pdf.style.tableLLR,
    )

    pdf.bottom_table(
        [(_("Place, Date"), "", _("Jobholder"), "", _("Employer"))],
        (44 * mm, 10 * mm, 50 * mm, 10 * mm, 50 * mm),
        style=pdf.style.table
        + (
            ("TOPPADDING", (0, 0), (-1, -1), 1 * mm),
            ("LINEABOVE", (0, 0), (0, 0), 0.2, colors.black),
            ("LINEABOVE", (2, 0), (2, 0), 0.2, colors.black),
            ("LINEABOVE", (4, 0), (4, 0), 0.2, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ),
    )

    pdf.generate()
    return response


class NaturnetzStationery:
    def __call__(self, canvas, pdfdocument):
        canvas.saveState()

        try:
            canvas.drawImage(
                os.path.join(settings.BASE_DIR, "naturnetz", "data", "logo-new.jpg"),
                x=16 * cm,
                y=24 * cm,
                width=177 * 0.5,
                height=246 * 0.5,
            )
        except OSError:
            pass

        canvas.restoreState()


@login_required
def reference_pdf(request, reference_id):
    reference = get_object_or_404(
        JobReference.objects.select_related("assignment__drudge__user"), pk=reference_id
    )

    if not request.user.is_staff:
        if reference.assignment.drudge.user != request.user:
            return HttpResponseForbidden("<h1>Access forbidden</h1>")

    drudge = reference.assignment.drudge

    pdf, response = pdf_response("reference-%s" % reference.pk)
    pdf.init_letter(page_fn=create_stationery_fn(NaturnetzStationery()))

    pdf.p(drudge.user.get_full_name())
    pdf.p(drudge.address)
    pdf.p(f"{drudge.zip_code} {drudge.city}")
    pdf.next_frame()

    pdf.p("Kloster Fahr, %s" % reference.created.strftime("%d.%m.%Y"))

    pdf.h1("ARBEITSZEUGNIS")
    pdf.spacer()

    pdf.p(reference.text)

    pdf.spacer(10 * mm)
    pdf.p("Dr. Marco Sacchi\nGeschäftsführer")

    pdf.generate()
    return response


@staff_member_required
def course_list(request):
    earliest = date.today() - timedelta(days=7)

    assignments = Assignment.objects.filter(
        Q(environment_course_date__isnull=False, environment_course_date__gte=earliest)
        | Q(motor_saw_course_date__isnull=False, motor_saw_course_date__gte=earliest)
    ).select_related("drudge__user", "specification__scope_statement")

    branches = set(
        assignments.values_list("specification__scope_statement__branch", flat=True)
    )
    branch = request.GET.get("branch")
    if branch in branches:
        assignments = assignments.filter(specification__scope_statement__branch=branch)

    courses = []
    for assignment in assignments:
        if assignment.environment_course_date:
            courses.append((assignment.environment_course_date, assignment))
        if assignment.motor_saw_course_date:
            courses.append((assignment.motor_saw_course_date, assignment))

    return render(
        request,
        "zivinetz/course_list.html",
        {
            "course_list": sorted(
                courses,
                key=lambda row: (
                    row[0],
                    row[1].drudge.user.last_name,
                    row[1].drudge.user.first_name,
                ),
            ),
            "branches": sorted(branches),
        },
    )


@staff_member_required
def assignmentchange_list(request):
    earliest = date.today() - timedelta(days=14)

    changes = AssignmentChange.objects.filter(created__gte=earliest).select_related(
        "assignment__drudge__user", "assignment__specification__scope_statement"
    )

    return render(
        request, "zivinetz/assignmentchange_list.html", {"change_list": changes}
    )


@user_type_required(['dev_admin'])
def assignment_phone_list(request):
    """Generate a PDF phone list of assignments."""
    # Get the search form and apply its filters
    search_form = AssignmentSearchForm(request.GET, request=request)
    if not search_form.is_valid():
        return HttpResponse(_("Invalid search parameters."))

    # Get the filtered queryset using the search form's logic
    queryset = search_form.queryset(Assignment)
    
    # Apply additional filters if needed
    if request.GET.get('status'):
        queryset = queryset.filter(status=request.GET.get('status'))
    if request.GET.get('regional_office'):
        queryset = queryset.filter(regional_office=request.GET.get('regional_office'))
    if request.GET.get('specification'):
        queryset = queryset.filter(specification=request.GET.get('specification'))
    
    # Order by drudge name and date
    queryset = queryset.select_related(
        'drudge',
        'drudge__user',
        'specification'
    ).order_by('drudge__user__last_name', 'drudge__user__first_name', '-date_from')
    
    # Generate PDF
    pdf, response = pdf_response("assignment_list")
    pdf.init_report()

    # Add title
    pdf.h1(_("Assignment List"))
    pdf.spacer()

    # Add date (django.utils.timezone)
    current_time = timezone.now
    pdf.p(_("Generated on: %s") % current_time.strftime("%d.%m.%Y %H:%M"))
    pdf.spacer()

    # Add search parameters if any
    if request.GET.get('s'):
        pdf.h2(_("Search Parameters"))
        for key, value in request.GET.items():
            if key != 's' and value:
                param_text = self.format_search_parameter(key, value)
                pdf.p(param_text)
        pdf.spacer()

    # Group assignments by drudge
    current_drudge = None
    for assignment in queryset:
        # If this is a new drudge, add drudge information
        if current_drudge != assignment.drudge:
            current_drudge = assignment.drudge
            
            # Add drudge header
            pdf.h2(f"{current_drudge.user.last_name}, {current_drudge.user.first_name}")
            
            # Add drudge details
            pdf.table([
                (_("ZDP No."), str(current_drudge.zdp_no)),
                (_("Email"), current_drudge.user.email),
                (_("Phone"), f"{current_drudge.phone_home or '-'} / {current_drudge.mobile or '-'}"),
            ], (4 * cm, 12.4 * cm))
            pdf.spacer()
            
            # Add course information
            courses = []
            if current_drudge.environment_course:
                courses.append("Umweltkurs")
            if current_drudge.motor_saw_course:
                courses.append("Motorsägenkurs")
            if courses:
                pdf.table([
                    (_("Kurse"), ", ".join(courses)),
                ], (4 * cm, 12.4 * cm))
                pdf.spacer()
        
        # Add assignment information
        pdf.table([
            (_("Pflichtenheft"), assignment.specification.code),
            (_("Date"), f"{assignment.date_from.strftime('%d.%m.%Y')} - {assignment.determine_date_until().strftime('%d.%m.%Y')}"),
            (_("Status"), assignment.get_status_display()),
        ], (4 * cm, 12.4 * cm))
        pdf.spacer()
        pdf.hr_mini()

    pdf.generate()
    return response
