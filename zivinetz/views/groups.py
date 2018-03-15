from collections import defaultdict
from datetime import timedelta

from openpyxl import Workbook
from openpyxl.styles import (
    Alignment, Border, Font, NamedStyle, PatternFill, Side,
)

from zivinetz.models import Absence, Assignment, Group, GroupAssignment


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
    days = [day + timedelta(days=i) for i in range(5)]

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

    border = NamedStyle('borderLeft')
    border.border = Border(left=Side(border_style='medium', color='00000000'))
    wb.add_named_style(border)

    center = Alignment(horizontal='center', vertical='center')
    vertical_text = Alignment(text_rotation=90)

    def day_column(weekday):
        return 2 + 9 * weekday

    def style_row(row, style):
        for i in range(0, day_column(5) + 1):
            ws[c(i, row)].style = style

    def column_width(column, width):
        ws.column_dimensions[columns[column]].width = width

    def row_height(row, height):
        ws.row_dimensions[row + 1].height = height

    for i, cell in enumerate([
            day.strftime('%B %y'),
            day.strftime('Woche %W'),
            'Auftragsnummer Arbeit',
            'LEITUNG',
            'ZIVIS',
    ]):
        ws[c(0, i + 1)] = cell
        ws[c(day_column(5), i + 1)] = cell
        if i < 2:
            ws[c(0, i + 1)].alignment = center
            ws[c(day_column(5), i + 1)].alignment = center

    column_width(0, 20)
    column_width(1, 9)
    column_width(day_column(5), 20)

    for i, current in enumerate(days):
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
        for k in range(2, 499):
            ws[c(day_column(i), k)].style = 'borderLeft'
        for j in range(1, 9):
            ws[c(day_column(i) + j, 2)] = '%s)' % j
            if j % 2 == 0:
                for k in range(2, 499):
                    ws[c(day_column(i) + j, k)].style = 'dark'

            ws[c(day_column(i) + j, 2)].alignment = vertical_text
            column_width(day_column(i) + j, 4)
        ws[c(day_column(i), 2)].alignment = vertical_text
        column_width(day_column(i), 4)

    row_height(2, 50)
    row_height(3, 35)
    row_height(4, 35)

    # ZIVIS line
    style_row(5, 'darker')

    assignments = defaultdict(list)
    seen_assignments = set()
    for ga in GroupAssignment.objects.filter(
            week=day,
    ).select_related('assignment__drudge__user'):
        assignments[ga.group_id].append(ga.assignment)
        seen_assignments.add(ga.assignment_id)

    free_assignments = Assignment.objects.for_date(day).exclude(
        pk__in=seen_assignments,
    ).select_related('drudge__user')

    absences = defaultdict(dict)
    for absence in Absence.objects.filter(days__overlap=days):
        for day in absence.days:
            absences[absence.assignment_id][day] = absence

    def add_group(row, group_name, assignments):
        ws[c(0, row)] = group_name
        ws[c(day_column(5), row)] = group_name
        style_row(row, 'darker')

        # TODO courses (UNA/MSK)

        for assignment in assignments:
            row += 1
            ws[c(0, row)] = assignment.drudge.user.get_full_name()
            ws[c(day_column(5), row)] = assignment.drudge.user.get_full_name()
            row_height(row, 35)
            if assignment.date_from in days:
                ws[c(1, row)] = 'NEU'
            else:
                ws[c(1, row)] =\
                    assignment.determine_date_until().strftime('%d.%m.%y')

            for i, current in enumerate(days):
                if current < assignment.date_from:
                    ws[c(day_column(i), row)] = 'Vor Beginn'
                elif current > assignment.determine_date_until():
                    ws[c(day_column(i), row)] = 'Nach Ende'
                elif current in absences[assignment.id]:
                    ws[c(day_column(i), row)] = absences[assignment.id][current].get_reason_display()

        # Skip some lines
        for i in range(0, max(3, 10 - len(assignments))):
            row += 1
            row_height(row, 35)

        row += 1
        return row

    row = 6
    for group in Group.objects.active():
        row = add_group(row, group.name, assignments[group.id])
    row = add_group(row, 'Nicht zugeteilt', free_assignments)

    return wb
