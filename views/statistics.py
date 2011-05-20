from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.shortcuts import render

from zivinetz.models import (ExpenseReport)


@staff_member_required
def expenses(request):
    stats = {}

    for row in ExpenseReport.objects.values('date_from').annotate(Sum('total')):
        day = row['date_from']
        total = row['total__sum']

        stats.setdefault((day.year, day.month), 0)
        stats[(day.year, day.month)] += total

    return render(request, 'zivinetz/stats_expenses.html', {
        'stats': sorted(stats.items(), reverse=True),
        })

