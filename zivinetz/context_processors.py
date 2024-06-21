from django.utils.translation import gettext_lazy as _
from django.utils.text import capfirst


def zivinetz(request):
    if request.user.is_authenticated and request.user.is_staff:
        urls = [
            (_("scheduling"), "/zivinetz/admin/scheduling/"),
            (_("drudges"), "/zivinetz/admin/drudges/"),
            (_("assignments"), "/zivinetz/admin/assignments/"),
            (_("groups"), "/zivinetz/admin/groups/"),
            (_("absences"), "/zivinetz/admin/absences/"),
            (_("expense reports"), "/zivinetz/admin/expense_reports/"),
            (_("regional offices"), "/zivinetz/admin/regional_offices/"),
            (_("scope statements"), "/zivinetz/admin/scope_statements/"),
            (_("specifications"), "/zivinetz/admin/specifications/"),
            (_("job references"), "/zivinetz/admin/jobreferences/"),
            (_("reporting"), "/zivinetz/reporting/"),
        ]
    else:
        urls = [
            (_("dashboard"), "/zivinetz/dashboard/"),
            (_("profile"), "/zivinetz/profile/"),
        ]

    return {"pages": urls}
