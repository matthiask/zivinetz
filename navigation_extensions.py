from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _

from feincms.module.page.extensions.navigation import NavigationExtension, PagePretender


class ZivinetzNavigationExtension(NavigationExtension):
    name = _('Zivinetz navigation extension')

    def children(self, page, **kwargs):
        url = page.get_navigation_url()

        return [
            PagePretender(
                title=capfirst(_('drudges')),
                url='%sdrudges/' % url,
                level=page.level+1,
                tree_id=page.tree_id,
                ),
            PagePretender(
                title=capfirst(_('regional offices')),
                url='%sregional_offices/' % url,
                level=page.level+1,
                tree_id=page.tree_id,
                ),
            PagePretender(
                title=capfirst(_('scope statements')),
                url='%sscope_statements/' % url,
                level=page.level+1,
                tree_id=page.tree_id,
                ),
            PagePretender(
                title=capfirst(_('specifications')),
                url='%sspecifications/' % url,
                level=page.level+1,
                tree_id=page.tree_id,
                ),
            PagePretender(
                title=capfirst(_('assignments')),
                url='%sassignments/' % url,
                level=page.level+1,
                tree_id=page.tree_id,
                ),
            PagePretender(
                title=capfirst(_('expense reports')),
                url='%sexpense_reports/' % url,
                level=page.level+1,
                tree_id=page.tree_id,
                ),
            ]
