from django.utils.translation import gettext_lazy as _
from django.utils.text import capfirst


def zivinetz(request):
    # Get user_type from userprofile
    user_type = getattr(request.user.userprofile, 'user_type', None) if hasattr(request.user, 'userprofile') else None

    if request.user.is_authenticated and request.user.is_staff:
        if user_type in ['admin', 'dev_admin']:
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
        elif user_type == 'user_plus':
            # User plus sees everything except expense reports
            urls = [
                (_("scheduling"), "/zivinetz/admin/scheduling/"),
                (_("drudges"), "/zivinetz/admin/drudges/"),
                (_("assignments"), "/zivinetz/admin/assignments/"),
                (_("groups"), "/zivinetz/admin/groups/"),
                (_("absences"), "/zivinetz/admin/absences/"),
                (_("regional offices"), "/zivinetz/admin/regional_offices/"),
                (_("scope statements"), "/zivinetz/admin/scope_statements/"),
                (_("specifications"), "/zivinetz/admin/specifications/"),
                (_("job references"), "/zivinetz/admin/jobreferences/"),
                (_("reporting"), "/zivinetz/reporting/"),
            ]
        elif user_type == 'squad_leader':
            # Squad leader sees limited admin functions
            urls = [
                (_("drudges"), "/zivinetz/admin/drudges/"),
                (_("assignments"), "/zivinetz/admin/assignments/"),
            ]
        else:
            urls = [
            (_("dashboard"), "/zivinetz/dashboard/"),
            (_("profile"), "/zivinetz/profile/"),
            ]
    else:
        urls = [
            (_("dashboard"), "/zivinetz/dashboard/"),
            (_("profile"), "/zivinetz/profile/"),
        ]

    return {"pages": urls}
