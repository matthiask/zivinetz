from django.conf.urls.defaults import *

from zivinetz.views.modelviews import assignment_views, drudge_views,\
    expense_report_views, regional_office_views, scope_statement_views,\
    specification_views


urlpatterns = patterns('zivinetz.views',
    url(r'^assignments/pdf/(\d+)/$', 'reporting.assignment_pdf'),

    url(r'^regional_offices/', include(regional_office_views.urls)),
    url(r'^scope_statements/', include(scope_statement_views.urls)),
    url(r'^specifications/', include(specification_views.urls)),
    url(r'^drudges/', include(drudge_views.urls)),
    url(r'^assignments/', include(assignment_views.urls)),
    url(r'^expense_reports/', include(expense_report_views.urls)),

    url(r'^scheduling/$', 'scheduling.scheduling'),
)
