from collections import OrderedDict
from datetime import date
from decimal import Decimal

from django.contrib.admin.views.decorators import staff_member_required
from pdfdocument.document import Frame, PageTemplate, cm, mm
from pdfdocument.utils import pdf_response

from zivinetz.models import ExpenseReport



@staff_member_required
def expense_statistics_pdf(request):
    return generate_expense_statistics_pdf(
        ExpenseReport.objects.filter(date_from__year=date.today().year)
    )


def generate_expense_statistics_pdf(reports):
    pdf, response = pdf_response("expense-statistics")

    pdf.doc.addPageTemplates(
        [
            PageTemplate(
                id="First",
                frames=[
                    Frame(
                        0.5 * cm,
                        0.5 * cm,
                        19.8 * cm,
                        28.5 * cm,
                        showBoundary=0,
                        leftPadding=0,
                        rightPadding=0,
                        topPadding=0,
                        bottomPadding=0,
                    )
                ],
            )
        ]
    )
    pdf.generate_style(font_size=6)

    pdf.h1("Spesenstatistik")

    table_head = (
        "ZDP",
        "Name",
        "Periode",
        "",
        "Arbeitstage",
        "",
        "Freitage",
        "",
        "Krankheit",
        "",
        "Ferien",
        "",
        "Urlaub",
        "Anreise",
        "Kleider",
        "Extra",
        "",
        "Total",
    )
    table_cols = (
        1 * cm,
        3 * cm,
        2.2 * cm,
        0.6 * cm,
        1.1 * cm,
        0.6 * cm,
        1.1 * cm,
        0.6 * cm,
        1.1 * cm,
        0.6 * cm,
        1.1 * cm,
        0.6 * cm,
        1.1 * cm,
        1 * cm,
        1 * cm,
        1 * cm,
        0.85 * cm,
        1.25 * cm,
    )

    data = OrderedDict()

    for report in reports.order_by("date_from", "assignment__drudge").select_related(
        "assignment__specification__scope_statement", "assignment__drudge__user"
    ):
        compensation = report.compensation_data()
        if not compensation:
            # Attention! Using current date instead of real mobilization date
            compensation = report.compensation_data(date.today())
            if not compensation:
                continue

        def add(keys):
            return sum(compensation[k] for k in keys.split())

        tpl = (
            "spending_money accomodation_%(t)s breakfast_%(t)s lunch_%(t)s"
            " supper_%(t)s"
        )
        working_day = add(tpl % {"t": "working"})
        free_day = add(tpl % {"t": "free"})
        sick_day = add(tpl % {"t": "sick"})

        line = [
            report.assignment.drudge.zdp_no,
            report.assignment.drudge.user.get_full_name(),
            "%s - %s"
            % (
                report.date_from.strftime("%d.%m.%y"),
                report.date_until.strftime("%d.%m.%y"),
            ),
            report.working_days,
            report.working_days * working_day,
            report.free_days,
            report.free_days * free_day,
            report.sick_days,
            report.sick_days * sick_day,
            report.holi_days,
            report.holi_days * free_day,
            report.forced_leave_days,
            Decimal("0.00"),  # forced leave day -- always zero
            report.transport_expenses,
            report.clothing_expenses,
            report.miscellaneous,
            report.total_days,
            report.total,
        ]

        data.setdefault(
            report.assignment.specification.scope_statement, OrderedDict()
        ).setdefault((report.date_from.year, report.date_from.month), []).append(line)

    def _add_sum(reports, title=""):
        transposed = list(zip(*reports))
        total = ["Total %s" % title, "", ""] + [
            sum(transposed[i], 0) for i in range(3, 18)
        ]
        pdf.table([total], table_cols, pdf.style.tableHead)
        pdf.spacer()
        return total

    totals = []

    for scope_statement, ss_data in data.items():
        pdf.h2("%s" % scope_statement)
        complete = []

        for year_month, reports in ss_data.items():
            title = date(year_month[0], year_month[1], 1).strftime("%B %Y")
            pdf.h3(title)
            pdf.spacer(2 * mm)
            pdf.table([table_head] + reports, table_cols, pdf.style.tableHead)
            _add_sum(reports, title)
            pdf.spacer()
            complete.extend(reports)

        totals.append(_add_sum(complete, "%s" % scope_statement))
        pdf.pagebreak()

    pdf.h2("Zusammenfassung")
    pdf.table([table_head] + totals, table_cols, pdf.style.tableHead)
    _add_sum(totals, "Total")

    pdf.generate()
    return response
