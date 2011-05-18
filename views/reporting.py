# coding=utf-8

from datetime import date
import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from zivinetz.models import (Assignment, CompanyHoliday, ExpenseReport,
    CompensationSet, JobReference)

from reportlab.lib import colors

from pdfdocument.document import PDFDocument, cm, mm
from pdfdocument.elements import create_stationery_fn
from pdfdocument.utils import pdf_response


class AssignmentPDFStationery(object):
    def __init__(self, assignment):
        self.assignment = assignment

    def __call__(self, canvas, pdfdocument):
        #canvas.saveState()
        #canvas.restoreState()

        if pdfdocument.doc.page == 1:
            self.page_1(canvas, pdfdocument)
        elif pdfdocument.doc.page == 2:
            self.page_2(canvas, pdfdocument)

    def background(self, canvas, image):
        canvas.drawImage(
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'data', image),
            0, 0, 21*cm, 29.4*cm)

    markers = {
        'trial': (75, 71),
        'long_assignment': (112, 71),

        'working_time_fixed': (112, 60),
        'working_time_nightshift': (151, 59),
        'working_time_flexible': (112, 55),
        'working_time_weekend': (151, 55),

        'accomodation_offered': (69.5, 256),
        'accomodation_used': (75, 251),
        'accomodation_notused': (113.5, 251),
        'accomodation_at_home': (69.5, 247),

        'breakfast_working_at_company': (69.5, 236),
        'breakfast_working_at_home': (69.5, 231.5),
        'breakfast_working_external': (69.5, 227),

        'breakfast_free_at_company': (113.5, 236),
        'breakfast_free_at_home': (113.5, 231.5),

        'lunch_working_at_company': (69.5, 223),
        'lunch_working_at_home': (69.5, 218.5),
        'lunch_working_external': (69.5, 214),

        'lunch_free_at_company': (113.5, 223),
        'lunch_free_at_home': (113.5, 218.5),

        'supper_working_at_company': (69.5, 210),
        'supper_working_at_home': (69.5, 205.5),
        'supper_working_external': (69.5, 201),

        'supper_free_at_company': (113.5, 210),
        'supper_free_at_home': (113.5, 205.5),

        'public_transports': (31, 159),
        'private_transport': (113.5, 159),
        'special_tickets': (31, 152),

        'clothing_provided': (31, 124),
        'clothing_compensated': (113.5, 124),

        'arrangement_timely': (31, 89),
        'arrangement_late': (31, 80),
        }

    def draw_marker(self, canvas, key):
        canvas.setFont('Helvetica', 11)
        canvas.drawString(self.markers[key][0]*mm, self.markers[key][1]*mm, 'x')

    def _draw_all_markers(self, canvas):
        canvas.setFillColorRGB(1, 0, 0)
        for key, pos in self.markers.items():
            canvas.drawString(pos[0]*mm, pos[1]*mm, u'x %s' % key)

    def page_1(self, canvas, pdfdocument):
        self.background(canvas, '3-0.jpg')

        drudge = self.assignment.drudge

        frame_1 = [
            drudge.user.last_name,
            drudge.address,
            drudge.phone_home,
            drudge.mobile,
            drudge.date_of_birth and drudge.date_of_birth.strftime('%d.%m.%Y') or u'',
            ]

        frame_2 = [
            drudge.zdp_no,
            drudge.user.first_name,
            u'%s %s' % (drudge.zip_code, drudge.city),
            drudge.phone_office,
            drudge.user.email,
            drudge.education_occupation,
            ]

        frame_3 = [
            drudge.bank_account,
            drudge.health_insurance_company,
            ]

        frame_4 = [
            drudge.bank_account,
            drudge.health_insurance_account,
            ]

        frame_5 = [
            'Verein Naturnetz',
            'Chlosterstrasse',
            'Marco Sacchi',
            '044 533 11 44',
            ]

        frame_6 = [
            '123456',
            '',
            '8109 Kloster Fahr',
            u'Geschäftsleiter',
            'ms@verein-naturnetz.ch',
            ]

        frame_7 = [
            'Marco Sacchi',
            ]

        frame_8 = [
            u'Geschäftsleiter',
            '044 533 11 44',
            ]

        frame_9 = [
            self.assignment.date_from.strftime('%d.%m.%Y'),
            self.assignment.date_until.strftime('%d.%m.%Y'),
            ]

        frame_10 = [
            u'%s %s' % (
                self.assignment.specification.scope_statement.eis_no,
                self.assignment.specification.scope_statement.name,
                ),
            ]

        frame_11 = [
            '42',
            'Kloster Fahr',
            ]

        frames = [
            (frame_1, 55*mm, 192*mm, 7.3*mm),
            (frame_2, 140*mm, 192*mm, 7.3*mm),
            (frame_3, 55*mm, 166*mm, 11*mm),
            (frame_4, 140*mm, 166*mm, 11*mm),
            (frame_5, 55*mm, 125*mm, 7.5*mm),
            (frame_6, 140*mm, 125*mm, 7.5*mm),
            (frame_7, 55*mm, 106.5*mm, 0),
            (frame_8, 140*mm, 106.5*mm, 8.4*mm),
            (frame_9, 140*mm, 89*mm, 7.4*mm),
            (frame_10, 90*mm, 81*mm, 0),
            (frame_11, 55*mm, 55*mm, 8.5*mm),
            ]

        canvas.setFont('Helvetica', 9)
        for frame, x, y, line in frames:
            for i, text in enumerate(reversed(frame)):
                canvas.drawString(x, y + i*line, text)


        try:
            company_holiday = CompanyHoliday.objects.filter(
                date_until__gte=self.assignment.date_from,
                date_from__lte=self.assignment.date_until,
                )[0]
        except IndexError:
            company_holiday = None

        if company_holiday:
            canvas.drawString(125*mm, 47*mm, company_holiday.date_from.strftime('%d.%m.%Y'))
            canvas.drawString(160*mm, 47*mm, company_holiday.date_until.strftime('%d.%m.%Y'))


        if self.assignment.part_of_long_assignment:
            self.draw_marker(canvas, 'long_assignment')

        self.draw_marker(canvas, 'working_time_fixed')

    def page_2(self, canvas, pdfdocument):
        self.background(canvas, '3-1.jpg')

        spec = self.assignment.specification

        if spec.with_accomodation:
            self.draw_marker(canvas, 'accomodation_offered')
            self.draw_marker(canvas, 'accomodation_used')
        else:
            self.draw_marker(canvas, 'accomodation_at_home')

        for meal in ('breakfast', 'lunch', 'supper'):
            for day_type in ('working', 'free'):
                marker = '%s_%s_%s' % (
                    meal,
                    day_type,
                    getattr(spec, '%s_%s' % (meal, day_type)))

                if marker.endswith('at_accomodation'):
                    marker = marker.replace('at_accomodation',
                        spec.with_accomodation and 'at_company' or 'at_home')
                elif marker.endswith('no_compensation'):
                    # in this context, at_company is the same
                    # as no_compensation
                    marker = marker.replace('no_compensation', 'at_company')

                self.draw_marker(canvas, marker)

        self.draw_marker(canvas, 'clothing_%s' % spec.clothing)
        # TODO automatically draw arrangement marker?


@login_required
def assignment_pdf(request, assignment_id):
    assignment = get_object_or_404(Assignment.objects.select_related('drudge__user'),
        pk=assignment_id)

    if not request.user.is_staff:
        if assignment.drudge.user != request.user:
            return HttpResponseForbidden('<h1>Access forbidden</h1>')

    pdf, response = pdf_response('assignment-%s' % assignment.pk)
    #pdf.show_boundaries = True
    pdf.init_report(page_fn=create_stationery_fn(AssignmentPDFStationery(assignment)))

    pdf.pagebreak()
    pdf.pagebreak()

    pdf.generate()
    return response


@login_required
def expense_report_pdf(request, expense_report_id):
    report = get_object_or_404(ExpenseReport.objects.select_related('assignment__drudge__user'),
        pk=expense_report_id)

    if not request.user.is_staff:
        if report.assignment.drudge.user != request.user:
            return HttpResponseForbidden('<h1>Access forbidden</h1>')

    assignment = report.assignment
    drudge = assignment.drudge

    pdf, response = pdf_response('expense-report-%s' % report.pk)
    pdf.init_report()

    pdf.h1('Spesenrapport')
    pdf.h2('Einsatzbetrieb 20995 - Naturnetz, Chlosterstrasse, 8109 Kloster Fahr')
    pdf.spacer()

    pdf.table([
        (u'Pflichtenheft:', u'%s' % report.assignment.specification),
        (u'Name, Vorname:', u'%s' % drudge.user.get_full_name()),
        (u'Adresse:', u'%s, %s %s' % (drudge.address, drudge.zip_code, drudge.city)),
        (u'ZDP:', drudge.zdp_no),
        (u'Gesamteinsatz:', u'%s - %s' % (
            assignment.date_from.strftime('%d.%m.%Y'),
            assignment.date_until.strftime('%d.%m.%Y'))),
        (u'Meldeperiode:',  u'%s - %s' % (
            report.date_from.strftime('%d.%m.%Y'),
            report.date_until.strftime('%d.%m.%Y'))),
        ], (4*cm, 12.4*cm), pdf.style.tableLLR)

    pdf.spacer()

    table, additional, total = report.compensations()
    pdf.table(table,
        (4*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2.4*cm),
        pdf.style.tableHead)
    pdf.table(additional,
        (14*cm, 2.4*cm),
        pdf.style.table)
    pdf.spacer(1*mm)
    pdf.table([
        (_('Total'), total),
        ], (14*cm, 2.4*cm), pdf.style.tableHead)

    pdf.spacer()

    pdf.table([
        (_('bank account') + ':', drudge.bank_account),
        ], (4*cm, 12.4*cm), pdf.style.tableLLR)

    pdf.bottom_table([
        (_('Place, Date'), '', _('Jobholder'), '', _('Employer')),
        ], (44*mm, 10*mm, 50*mm, 10*mm, 50*mm), style=pdf.style.table+(
            ('TOPPADDING', (0, 0), (-1, -1), 1*mm),
            ('LINEABOVE', (0, 0), (0, 0), 0.2, colors.black),
            ('LINEABOVE', (2, 0), (2, 0), 0.2, colors.black),
            ('LINEABOVE', (4, 0), (4, 0), 0.2, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ))

    pdf.generate()
    return response


class NaturnetzStationery(object):
    def __call__(self, canvas, pdfdocument):
        canvas.saveState()

        """
        pdfdocument.draw_svg(canvas,
            os.path.join(settings.APP_BASEDIR, 'naturnetz', 'data', 'NN_Logo.svg'),
            18*cm,
            24*cm,
            xsize=3*cm,
            )
        """
        canvas.drawImage(
            os.path.join(settings.APP_BASEDIR, 'naturnetz', 'data', 'logo.png'),
            x=16*cm, y=24*cm,
            width=177 * 0.5,
            height=250 * 0.5,
            )

        canvas.restoreState()


@login_required
def reference_pdf(request, reference_id):
    reference = get_object_or_404(JobReference.objects.select_related('assignment__drudge__user'),
        pk=reference_id)

    if not request.user.is_staff:
        if reference.assignment.drudge.user != request.user:
            return HttpResponseForbidden('<h1>Access forbidden</h1>')

    drudge = reference.assignment.drudge

    pdf, response = pdf_response('reference-%s' % reference.pk)
    pdf.init_letter(page_fn=create_stationery_fn(NaturnetzStationery()))

    pdf.p(drudge.user.get_full_name())
    pdf.p(drudge.address)
    pdf.p(u'%s %s' % (drudge.zip_code, drudge.city))
    pdf.next_frame()

    pdf.p('Kloster Fahr, %s' % reference.created.strftime('%d.%m.%Y'))

    pdf.h1('ARBEITSZEUGNIS')
    pdf.spacer()

    pdf.p(reference.text)

    pdf.spacer(10*mm)
    pdf.p(u'Dr. Marco Sacchi\nGeschäftsführer')

    pdf.generate()
    return response
