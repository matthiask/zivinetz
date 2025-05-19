from django import template
from django.db.models import Avg
from django.template.defaultfilters import stringfilter

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


@register.filter
def has_user_type(user, user_types):
    """
    Template filter to check if a user has one of the specified user types.
    Usage: {% if request.user|has_user_type:"admin,dev_admin" %}
    """
    try:
        if not user or not hasattr(user, "userprofile"):
            return False

        user_type = user.userprofile.user_type
        allowed_types = [ut.strip() for ut in user_types.split(",")]

        # Special case for admin and dev_admin
        if user_type in ("admin", "dev_admin"):
            return True

        return user_type in allowed_types
    except Exception as e:
        print(f"Error in has_user_type: {e}")
        return False
