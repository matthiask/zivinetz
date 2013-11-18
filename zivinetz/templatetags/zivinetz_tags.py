from django import template

from zivinetz.models import JobReferenceTemplate


register = template.Library()


@register.assignment_tag
def job_reference_templates():
    return JobReferenceTemplate.objects.all()
