from django.conf.urls import patterns, include, url
from django.views import generic

from zivinetz.views import photos


urlpatterns = patterns(
    'zivinetz.views',
    url(r'^$', 'home.home'),

    url(r'^dashboard/$', 'drudge.dashboard', name='drudge_dashboard'),
    url(r'^profile/$', 'drudge.profile', name='drudge_profile'),

    url(r'^admin/$', 'home.admin'),
    url(r'^admin/scheduling/$', 'scheduling.scheduling'),
    url(r'^admin/', include('zivinetz.resources')),

    # TODO Convert those to resource URLs.
    url(r'^assignments/pdf/(\d+)/$', 'reporting.assignment_pdf'),
    url(r'^expense_report_pdf/(\d+)/$', 'reporting.expense_report_pdf'),
    url(r'^references/pdf/(\d+)/$', 'reporting.reference_pdf'),

    url(r'^reporting/$', generic.TemplateView.as_view(
        template_name='zivinetz/reporting.html',
        )),
    url(r'^reporting/courses/$', 'reporting.course_list'),
    url(r'^reporting/assignmentchanges/$', 'reporting.assignmentchange_list'),

    url(r'^expense_statistics_pdf/$', 'expenses.expense_statistics_pdf'),

    url(r'^photos/', include(photos.album_views.urls)),
    url(r'^photos/(?P<album_id>\d+)/p/', include(photos.photo_views.urls)),
)
