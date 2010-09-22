# Create your views here.

from django.forms.models import inlineformset_factory
from django.shortcuts import get_object_or_404

from django_modelviews import generic

from zivinetz.models import Assignment, Drudge, ExpenseReport,\
    ExpenseReportPeriod, RegionalOffice, ScopeStatement,\
    ScopeStatementExpense


class RegionalOfficeModelView(generic.ModelView):
    def deletion_allowed(self, request, instance):
        # TODO run a few checks here
        return True


regional_office_views = RegionalOfficeModelView(RegionalOffice)


ScopeStatementExpenseFormSet = inlineformset_factory(ScopeStatement,
    ScopeStatementExpense,
    extra=1,
    #formfield_callback=forms.stripped_formfield_callback,
    )


class ScopeStatementModelView(generic.ModelView):
    def get_formset_instances(self, request, instance=None, **kwargs):
        args = self.extend_args_if_post(request, [])
        kwargs['instance'] = instance

        return {
            'expenses': ScopeStatementExpenseFormSet(*args, **kwargs),
            }


scope_statement_views = ScopeStatementModelView(ScopeStatement)


drudge_views = generic.ModelView(Drudge)
assignment_views = generic.ModelView(Assignment)


ExpenseReportPeriodFormSet = inlineformset_factory(ExpenseReport,
    ExpenseReportPeriod,
    extra=1,
    )


class ExpenseReportModelView(generic.ModelView):
    def get_formset_instances(self, request, instance=None, **kwargs):
        args = self.extend_args_if_post(request, [])
        kwargs['instance'] = instance

        return {
            'periods': ExpenseReportPeriodFormSet(*args, **kwargs),
            }


expense_report_views = ExpenseReportModelView(ExpenseReport)



from pdfdocument.document import PDFDocument, cm, mm
from pdfdocument.elements import create_stationery_fn
from pdfdocument.utils import pdf_response


class AssignmentPDFStationery(object):
    def __call__(self, canvas, pdfdocument):
        canvas.saveState()
        """
        pdfdocument.draw_svg(canvas,
            '/home/mk/Projects/sites/naturnetz.ch/zivinetz/data/einsatzvereinbarung-1.svg',
            0,
            0,
            xsize=21*cm,
            )
            """
        canvas.drawImage('/home/mk/Projects/sites/naturnetz.ch/zivinetz/data/3-0.jpg',
            0, 0, 21*cm, 29.4*cm)
        canvas.restoreState()


def assignment_pdf(request, assignment_id):
    assignment = get_object_or_404(Assignment, pk=assignment_id)

    pdf, response = pdf_response('assignment-%s' % assignment.pk)
    pdf.init_report(page_fn=create_stationery_fn(AssignmentPDFStationery()))

    pdf.p('something')

    pdf.generate()
    return response
