# coding=utf-8

from datetime import date
import operator
import os
import subprocess
import tempfile

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
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
        'standard': (31, 101),
        'trial': (75, 101),
        'long_assignment': (112, 101),

        #'working_time_fixed': (112, 60),
        #'working_time_nightshift': (151, 59),
        #'working_time_flexible': (112, 55),
        #'working_time_weekend': (151, 55),

        'vegetarianism': (113.5, 40),
        'no_vegetarianism': (155, 40),

        'accomodation_working_compensated': (56, 248),
        'accomodation_working_provided': (85, 248),
        'accomodation_free_compensated': (113.5, 248),
        'accomodation_free_provided': (143, 248),

        #'accomodation_used': (75, 251),
        #'accomodation_notused': (113.5, 251),

        'breakfast_working_at_company': (85, 242.5),
        'breakfast_working_at_home': (56, 242.5),
        'breakfast_working_external': (56, 242.5),

        'breakfast_free_at_company': (143, 242.5),
        'breakfast_free_at_home': (113.5, 242.5),

        'lunch_working_at_company': (85, 237),
        'lunch_working_at_home': (56, 237),
        'lunch_working_external': (56, 237),

        'lunch_free_at_company': (143, 237),
        'lunch_free_at_home': (113.5, 237),

        'supper_working_at_company': (85, 231.5),
        'supper_working_at_home': (56, 231.5),
        'supper_working_external': (56, 231.5),

        'supper_free_at_company': (143, 231.5),
        'supper_free_at_home': (113.5, 231.5),

        'accomodation_throughout': (31, 193),
        'food_throughout': (31, 186),

        'public_transports': (31, 149),
        'private_transport': (113.5, 149),
        'special_tickets': (31, 142.5),

        'clothing_provided': (31, 117),
        'clothing_compensated': (113.5, 117),

        'arrangement_timely': (31, 87),
        'arrangement_late': (31, 78),
        }

    def draw_marker(self, canvas, key):
        canvas.setFont('Helvetica', 11)
        canvas.drawString(self.markers[key][0]*mm, self.markers[key][1]*mm, 'x')

    def _draw_all_markers(self, canvas):
        canvas.setFillColorRGB(1, 0, 0)
        for key, pos in self.markers.items():
            #canvas.drawString(pos[0]*mm, pos[1]*mm, u'x %s' % key)
            canvas.drawString(pos[0]*mm, pos[1]*mm, u'x')

    def page_1(self, canvas, pdfdocument):
        #self.background(canvas, '3-0.jpg')

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
            drudge.health_insurance_company,
            '', #drudge.bank_account,
            ]

        frame_4 = [
            drudge.health_insurance_account,
            '', #drudge.bank_account,
            ]

        frame_5 = [
            'Verein Naturnetz',
            'Chlosterstrasse',
            '044 533 11 44',
            ]

        frame_6 = [
            '20995',
            'Marco Sacchi',
            '8109 Kloster Fahr',
            'ms@verein-naturnetz.ch',
            u'Geschäftsleiter',
            '044 533 11 44',
            ]

        frame_7 = [
            ]

        frame_8 = [
            self.assignment.date_from.strftime('%d.%m.%Y'),
            self.assignment.date_until.strftime('%d.%m.%Y'),
            'Kloster Fahr',
            ]

        frame_9 = [
            u'%s %s' % (
                self.assignment.specification.scope_statement.eis_no,
                self.assignment.specification.scope_statement.name,
                ),
            ]

        frame_10 = [
            self.assignment.regional_office.city,
            ]

        frame_11 = [
            ]

        frames = [
            (frame_1, 55*mm, 190*mm, 6.9*mm),
            (frame_2, 140*mm, 190*mm, 6.9*mm),
            (frame_3, 55*mm, 167*mm, 11*mm),
            (frame_4, 140*mm, 167*mm, 11*mm),
            (frame_5, 55*mm, 149*mm, 7.2*mm),
            (frame_6, 140*mm, 133*mm, 7.5*mm),
            (frame_7, 55*mm, 108.5*mm, 0),
            (frame_8, 140*mm, 109*mm, 7.2*mm),
            (frame_9, 90*mm, 87.5*mm, 7.4*mm),
            (frame_10, 127*mm, 272*mm, 0),
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
            canvas.drawString(125*mm, 76*mm, company_holiday.date_from.strftime('%d.%m.%Y'))
            canvas.drawString(160*mm, 76*mm, company_holiday.date_until.strftime('%d.%m.%Y'))


        if self.assignment.part_of_long_assignment:
            self.draw_marker(canvas, 'long_assignment')
        else:
            self.draw_marker(canvas, 'standard')

        #self.draw_marker(canvas, 'working_time_fixed')

        if drudge.vegetarianism:
            self.draw_marker(canvas, 'vegetarianism')
        else:
            self.draw_marker(canvas, 'no_vegetarianism')

    def page_2(self, canvas, pdfdocument):
        #self.background(canvas, '3-1.jpg')

        spec = self.assignment.specification

        if spec.with_accomodation:
            self.draw_marker(canvas, 'special_tickets')
        else:
            self.draw_marker(canvas, 'public_transports')

        for meal in ('accomodation', 'breakfast', 'lunch', 'supper'):
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

        if spec.accomodation_throughout:
            self.draw_marker(canvas, 'accomodation_throughout')
        if spec.food_throughout:
            self.draw_marker(canvas, 'food_throughout')


@login_required
def assignment_pdf(request, assignment_id):
    assignment = get_object_or_404(Assignment.objects.select_related('drudge__user'),
        pk=assignment_id)

    if not request.user.is_staff:
        if assignment.drudge.user != request.user:
            return HttpResponseForbidden('<h1>Access forbidden</h1>')

    with tempfile.NamedTemporaryFile(delete=False) as overlay:
        pdf = PDFDocument(overlay)

        #pdf.show_boundaries = True
        pdf.init_report(page_fn=create_stationery_fn(AssignmentPDFStationery(assignment)))

        pdf.pagebreak()
        pdf.pagebreak()

        pdf.generate()
        overlay.close()

        p = subprocess.Popen(['/usr/bin/pdftk', '-', 'multistamp', overlay.name,
                'output', '-'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        source = open(os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data',
            'Einsatzvereinbarung.pdf',
            ), 'rb')

        result, error = p.communicate(source.read())
        os.unlink(overlay.name)

        if assignment.specification.conditions:
            p = subprocess.Popen(['/usr/bin/pdftk', '-',
                assignment.specification.conditions.path,
                'cat', 'output', '-'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            result, error = p.communicate(result)

    response = HttpResponse(result, mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=eiv.pdf'
    return response


@login_required
def expense_report_pdf(request, expense_report_id):
    report = get_object_or_404(ExpenseReport.objects.select_related('assignment__drudge__user'),
        pk=expense_report_id)

    if not request.user.is_staff:
        if report.assignment.drudge.user != request.user:
            return HttpResponseForbidden('<h1>Access forbidden</h1>')

    table, additional, total = report.compensations()

    if not (table and additional and total):
        messages.error(request, _('No expense data, cannot generate report.'))
        return redirect(report.assignment)

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

    def notes(from_):
        return (
            ('FONT', (0, from_), (-1, from_), 'Helvetica-Oblique', 8),
            #('LEFTPADDING', (0, from_), (-1, from_), 3*mm),
            )

    pdf.table(table,
        (4*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2.4*cm),
        pdf.style.tableHead + tuple(reduce(operator.add, (notes(i) for i in range(2, 12, 2)))))
    pdf.table(additional,
        (14*cm, 2.4*cm),
        pdf.style.table + notes(1) + notes(3) + notes(5))
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
