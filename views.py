# coding=utf-8

import os

from django import forms
from django.forms.models import modelform_factory, inlineformset_factory
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _, ugettext_lazy

from towel import modelview
from towel import forms as towel_forms

from pdfdocument.document import PDFDocument, cm, mm
from pdfdocument.elements import create_stationery_fn
from pdfdocument.utils import pdf_response

from zivinetz.models import Assignment, CompanyHoliday, Drudge,\
    ExpenseReport,\
    ExpenseReportPeriod, RegionalOffice, ScopeStatement,\
    Specification


class ZivinetzModelView(modelview.ModelView):
    def get_context(self, request, context):
        ctx = super(ZivinetzModelView, self).get_context(request, context)
        ctx['base_template'] = 'zivinetz_base.html'
        return ctx

    def get_form(self, request, instance=None, **kwargs):
        return modelform_factory(self.model,
            formfield_callback=towel_forms.stripped_formfield_callback, **kwargs)


class RegionalOfficeModelView(ZivinetzModelView):
    def deletion_allowed(self, request, instance):
        return self.deletion_allowed_if_only(request, instance, [RegionalOffice])


regional_office_views = RegionalOfficeModelView(RegionalOffice)


SpecificationFormSet = inlineformset_factory(ScopeStatement,
    Specification,
    extra=0,
    formfield_callback=towel_forms.stripped_formfield_callback,
    )


class ScopeStatementModelView(ZivinetzModelView):
    def deletion_allowed(self, request, instance):
        return self.deletion_allowed_if_only(request, instance, [ScopeStatement, Specification])


scope_statement_views = ScopeStatementModelView(ScopeStatement)


class SpecificationModelView(ZivinetzModelView):
    def deletion_allowed(self, request, instance):
        return self.deletion_allowed_if_only(request, instance, [Specification])


specification_views = SpecificationModelView(Specification)


class DrudgeModelView(ZivinetzModelView):
    def deletion_allowed(self, request, instance):
        return self.deletion_allowed_if_only(request, instance, [Drudge])


class DrudgeSearchForm(towel_forms.SearchForm):
    pass


drudge_views = DrudgeModelView(Drudge,
    search_form=DrudgeSearchForm)


class AssignmentModelView(ZivinetzModelView):
    def deletion_allowed(self, request, instance):
        return self.deletion_allowed_if_only(request, instance, [Assignment])


class AssignmentSearchForm(towel_forms.SearchForm):
    default = {
        'status': (Assignment.TENTATIVE, Assignment.ARRANGED),
        }

    specification__scope_statement = forms.ModelChoiceField(
        ScopeStatement.objects.all(), label=ugettext_lazy('scope statement'), required=False)
    drudge = forms.ModelChoiceField(
        Drudge.objects.all(), label=ugettext_lazy('drudge'), required=False)
    status = forms.MultipleChoiceField(
        Assignment.STATUS_CHOICES, label=ugettext_lazy('status'), required=False)


assignment_views = AssignmentModelView(Assignment,
    search_form=AssignmentSearchForm)


ExpenseReportPeriodFormSet = inlineformset_factory(ExpenseReport,
    ExpenseReportPeriod,
    extra=0,
    formfield_callback=towel_forms.stripped_formfield_callback,
    )


class ExpenseReportModelView(ZivinetzModelView):
    def deletion_allowed(self, request, instance):
        return self.deletion_allowed_if_only(request, instance,
            [ExpenseReport, ExpenseReportPeriod])

    def get_formset_instances(self, request, instance=None, **kwargs):
        args = self.extend_args_if_post(request, [])
        kwargs['instance'] = instance

        return {
            'periods': ExpenseReportPeriodFormSet(*args, **kwargs),
            }


expense_report_views = ExpenseReportModelView(ExpenseReport,
    paginate_by=5)



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
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
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


def assignment_pdf(request, assignment_id):
    assignment = get_object_or_404(Assignment, pk=assignment_id)

    pdf, response = pdf_response('assignment-%s' % assignment.pk)
    #pdf.show_boundaries = True
    pdf.init_report(page_fn=create_stationery_fn(AssignmentPDFStationery(assignment)))

    pdf.pagebreak()
    pdf.pagebreak()

    pdf.generate()
    return response
