from datetime import timedelta

from openpyxl import Workbook
from openpyxl.styles import NamedStyle, Font, PatternFill

from zivinetz.models import Group, GroupAssignment


letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
columns = {}
columns.update({i: c for i, c in enumerate(letters)})
columns.update({i + 26: 'A%s' % c for i, c in enumerate(letters)})
columns.update({i + 52: 'B%s' % c for i, c in enumerate(letters)})


def c(column, row):
    """Cell name for zero-indexed column/row combination"""
    return '%s%s' % (columns[column], row + 1)


def create_groups_xlsx(day):
    day = GroupAssignment.objects.monday(day)

    wb = Workbook()
    ws = wb.active

    style = NamedStyle('heading')
    style.font = Font(bold=True)
    style.fill = PatternFill('solid', 'cccccc')

    wb.add_named_style(style)

    def day_column(weekday):
        return 2 + 9 * weekday

    for i, cell in enumerate([
            day.strftime('%B %y'),
            day.strftime('Woche %W'),
            'Auftragsnummer Arbeit',
            'LEITUNG',
            'ZIVIS',
    ]):
        ws[c(0, i + 1)] = cell
        ws[c(day_column(5), i + 1)] = cell

    for i in range(5):
        current = day + timedelta(days=i)

        ws[c(day_column(i), 0)] = current.strftime('%A')
        ws[c(day_column(i), 1)] = current.strftime('%d-%b-%y')

        ws[c(day_column(i), 2)] = 'Absenz'
        for j in range(1, 9):
            ws[c(day_column(i) + j, 2)] = '%s)' % j

    return wb
