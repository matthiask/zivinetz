from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from feincms.module.page.extensions.navigation import NavigationExtension, PagePretender


class ZivinetzNavigationExtension(NavigationExtension):
    name = _("Zivinetz navigation extension")

    def children(self, page, **kwargs):
        request = kwargs.get("request")

        if request.user.is_authenticated and request.user.is_staff:
            urls = [
                (_("scheduling"), "admin/scheduling/"),
                (_("drudges"), "admin/drudges/"),
                (_("assignments"), "admin/assignments/"),
                (_("groups"), "admin/groups/"),
                (_("absences"), "admin/absences/"),
                (_("expense reports"), "admin/expense_reports/"),
                (_("regional offices"), "admin/regional_offices/"),
                (_("scope statements"), "admin/scope_statements/"),
                (_("specifications"), "admin/specifications/"),
                (_("job references"), "admin/jobreferences/"),
                (_("reporting"), "reporting/"),
            ]
        else:
            urls = [(_("dashboard"), "dashboard/"), (_("profile"), "profile/")]

        return [
            PagePretender(
                title=capfirst(title),
                url=f"{page.get_navigation_url()}{url}",
                level=page.level + 1,
                tree_id=page.tree_id,
            )
            for title, url in urls
        ]
