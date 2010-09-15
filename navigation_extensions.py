from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _

from feincms.module.page.extensions.navigation import NavigationExtension, PagePretender


class ZivinetzNavigationExtension(NavigationExtension):
    name = _('Zivinetz navigation extension')

    def children(self, page, **kwargs):
        page.rght += 2 # Yeah, this page does have children
        url = page.get_navigation_url()

        return [
            PagePretender(
                title=capfirst(_('Regional offices')),
                url='%sregional_offices/' % url,
                level=3,
                tree_id=page.tree_id,
                lft=page.lft,
                rght=page.rght+1,
                ),
            ]
