from django import template
from django.db.models import Avg

from zivinetz.models import JobReferenceTemplate


register = template.Library()


@register.simple_tag
def job_reference_templates():
    return JobReferenceTemplate.objects.all()


@register.filter
def mark_average(queryset):
    return queryset.annotate(mark_average=Avg("assessments__mark")).order_by(
        "date_from", "date_until"
    )
