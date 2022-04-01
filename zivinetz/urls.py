from django.urls import include, path, re_path
from django.views import generic

from zivinetz.views import drudge, expenses, home, quota, reporting, scheduling


urlpatterns = [
    path("", home.home),
    path("dashboard/", drudge.dashboard, name="drudge_dashboard"),
    path("profile/", drudge.profile, name="drudge_profile"),
    path("admin/", home.admin),
    path("admin/scheduling/", scheduling.scheduling),
    path("admin/scheduling/quotas/<int:year>/", quota.quota_year),
    path("admin/", include("zivinetz.resources")),
    # TODO Convert those to resource URLs.
    re_path(
        r"^assignments/pdf/(\d+)/$",
        reporting.assignment_pdf,
        name="zivinetz_assignment_pdf",
    ),
    re_path(
        r"^expense_report_pdf/(\d+)/$",
        reporting.expense_report_pdf,
        name="zivinetz_expensereport_pdf",
    ),
    re_path(
        r"^references/pdf/(\d+)/$",
        reporting.reference_pdf,
        name="zivinetz_reference_pdf",
    ),
    path(
        "reporting/",
        generic.TemplateView.as_view(template_name="zivinetz/reporting.html"),
    ),
    path("reporting/courses/", reporting.course_list),
    path("reporting/assignmentchanges/", reporting.assignmentchange_list),
    path("expense_statistics_pdf/", expenses.expense_statistics_pdf),
]
