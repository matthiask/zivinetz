from django.conf.urls.defaults import *

from zivinetz.views import assignment_views, drudge_views, regional_office_views, scope_statement_views


urlpatterns = patterns('',
    url(r'^regional_offices/', include(regional_office_views.urls)),
    url(r'^scope_statements/', include(scope_statement_views.urls)),
    url(r'^drudges/', include(drudge_views.urls)),
    url(r'^assignments/', include(assignment_views.urls)),
)
