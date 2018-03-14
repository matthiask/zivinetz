from datetime import timedelta

from openpyxl import Workbook
from openpyxl.styles import Alignment, NamedStyle, Font, PatternFill

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

    dark = NamedStyle('dark')
    dark.font = Font(name='Calibri')
    dark.fill = PatternFill('solid', 'cccccc')
    wb.add_named_style(dark)

    darker = NamedStyle('darker')
    darker.font = Font(name='Calibri', bold=True)
    darker.fill = PatternFill('solid', 'aaaaaa')
    wb.add_named_style(darker)

    center = Alignment(horizontal='center', vertical='center')
    vertical_text = Alignment(text_rotation=90)

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
        ws[c(day_column(i), 0)].alignment = center
        ws[c(day_column(i), 1)].alignment = center
        ws.merge_cells('%s:%s' % (
            c(day_column(i), 0),
            c(day_column(i + 1) - 1, 0),
        ))
        ws.merge_cells('%s:%s' % (
            c(day_column(i), 1),
            c(day_column(i + 1) - 1, 1),
        ))

        ws[c(day_column(i), 2)] = 'Absenz'
        for j in range(1, 9):
            ws[c(day_column(i) + j, 2)] = '%s)' % j
            if j % 2 == 0:
                for k in range(2, 499):
                    ws[c(day_column(i) + j, k)].style = 'dark'

            ws[c(day_column(i) + j, 2)].alignment = vertical_text
            ws.column_dimensions[columns[day_column(i) + j]].width = 4
        ws[c(day_column(i), 2)].alignment = vertical_text
        ws.column_dimensions[columns[day_column(i)]].width = 4

    ws.row_dimensions[3].height = 50

    for i in range(0, day_column(6)):
        ws[c(i, 4)].style = 'darker'
        ws[c(i, 5)].style = 'darker'

    return wb
