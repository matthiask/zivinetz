from django.conf.urls.defaults import *

from zivinetz.views.modelviews import (assignment_views, drudge_views,
    expense_report_views, regional_office_views, scope_statement_views,
    specification_views, waitlist_views, jobreference_views)


urlpatterns = patterns('zivinetz.views',
    url(r'^$', 'home.home'),

    url(r'^dashboard/$', 'drudge.dashboard', name='drudge_dashboard'),
    url(r'^profile/$', 'drudge.profile', name='drudge_profile'),

    #url(r'^assignments/$', 'home.assignments', name='drudge_assignments'),

    url(r'^admin/$', 'home.admin'),

    url(r'^admin/regional_offices/', include(regional_office_views.urls)),
    url(r'^admin/scope_statements/', include(scope_statement_views.urls)),
    url(r'^admin/specifications/', include(specification_views.urls)),
    url(r'^admin/drudges/', include(drudge_views.urls)),
    url(r'^admin/assignments/', include(assignment_views.urls)),
    url(r'^admin/expense_reports/', include(expense_report_views.urls)),
    url(r'^admin/waitlist/', include(waitlist_views.urls)),
    url(r'^admin/jobreferences/', include(jobreference_views.urls)),

    url(r'^admin/scheduling/$', 'scheduling.scheduling'),

    url(r'^assignments/pdf/(\d+)/$', 'reporting.assignment_pdf'),
    url(r'^expense_report_pdf/(\d+)/$', 'reporting.expense_report_pdf'),
    url(r'^references/pdf/(\d+)/$', 'reporting.reference_pdf'),

    url(r'^expense_statistics_pdf/$', 'expenses.expense_statistics_pdf'),
)
