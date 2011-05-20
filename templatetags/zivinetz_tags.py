from django import template
from django.db.models import Sum


register = template.Library()


@register.inclusion_tag('zivinetz/stats_expenses.html')
def stats_expenses(object_list):
    stats = {}

    for row in object_list.values('date_from').annotate(Sum('total')):
        day = row['date_from']
        total = row['total__sum']

        stats.setdefault((day.year, day.month), 0)
        stats[(day.year, day.month)] += total

    return {
        'stats': sorted(stats.items(), reverse=True),
        }
