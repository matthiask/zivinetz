from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _

from feincms.module.page.extensions.navigation import NavigationExtension, PagePretender


class ZivinetzNavigationExtension(NavigationExtension):
    name = _('Zivinetz navigation extension')

    def children(self, page, **kwargs):
        url = page.get_navigation_url()

        request = kwargs.get('request')

        if request.user.is_authenticated() and request.user.is_staff:

            return [
                PagePretender(
                    title=capfirst(_('drudges')),
                    url='%sadmin/drudges/' % url,
                    level=page.level+1,
                    tree_id=page.tree_id,
                    ),
                PagePretender(
                    title=capfirst(_('regional offices')),
                    url='%sadmin/regional_offices/' % url,
                    level=page.level+1,
                    tree_id=page.tree_id,
                    ),
                PagePretender(
                    title=capfirst(_('scope statements')),
                    url='%sadmin/scope_statements/' % url,
                    level=page.level+1,
                    tree_id=page.tree_id,
                    ),
                PagePretender(
                    title=capfirst(_('specifications')),
                    url='%sadmin/specifications/' % url,
                    level=page.level+1,
                    tree_id=page.tree_id,
                    ),
                PagePretender(
                    title=capfirst(_('assignments')),
                    url='%sadmin/assignments/' % url,
                    level=page.level+1,
                    tree_id=page.tree_id,
                    ),
                PagePretender(
                    title=capfirst(_('expense reports')),
                    url='%sadmin/expense_reports/' % url,
                    level=page.level+1,
                    tree_id=page.tree_id,
                    ),

                PagePretender(
                    title=capfirst(_('scheduling')),
                    url='%sadmin/scheduling/' % url,
                    level=page.level+1,
                    tree_id=page.tree_id,
                    ),
                ]

        else:

            return [
                PagePretender(
                    title=capfirst(_('home')),
                    url='%s' % url,
                    level=page.level+1,
                    tree_id=page.tree_id,
                    ),
                PagePretender(
                    title=capfirst(_('profile')),
                    url='%sprofile/' % url,
                    level=page.level+1,
                    tree_id=page.tree_id,
                    ),
                ]
