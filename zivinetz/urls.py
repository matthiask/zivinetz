from django.urls import path, include
from django.views import generic
from zivinetz.views import drudge, expenses, home, quota, reporting, scheduling
from zivinetz.views.drudge import (
    DrudgePDFExportView,
    DrudgeCSVExportView,
    AssignmentPDFExportView,
    AssignmentCSVExportView,
)
from zivinetz.views.decorators import user_type_required

# Define commonly used decorators
admin_required = user_type_required(["admin", "user_plus", "dev_admin"])
admin_dev_admin_required = user_type_required(["admin", "dev_admin"])
dev_admin_required = user_type_required(["dev_admin"])

urlpatterns = [
    path("", home.home),
    path("dashboard/", drudge.dashboard, name="drudge_dashboard"),
    path("profile/", drudge.profile, name="drudge_profile"),
    path("admin/", admin_required(home.admin)),
    path("admin/scheduling/", admin_required(scheduling.scheduling)),
    path("admin/scheduling/quotas/<int:year>/", admin_required(quota.quota_year)),
    path("admin/", include("zivinetz.resources")),
    # Resource-based PDF URLs
    path(
        "assignments/<int:pk>/pdf/",
        admin_required(reporting.assignment_pdf),
        name="zivinetz_assignment_pdf",
    ),
    path(
        "assignments/phone-list/",
        admin_required(reporting.assignment_phone_list),
        name="zivinetz_assignment_phone_list",
    ),
    path(
        "expense_reports/<int:pk>/pdf/",
        admin_dev_admin_required(reporting.expense_report_pdf),
        name="zivinetz_expensereport_pdf",
    ),
    path(
        "references/<int:pk>/pdf/",
        admin_required(reporting.reference_pdf),
        name="zivinetz_reference_pdf",
    ),
    path(
        "reporting/",
        admin_required(
            generic.TemplateView.as_view(template_name="zivinetz/reporting.html")
        ),
    ),
    path("reporting/courses/", admin_required(reporting.course_list)),
    path(
        "reporting/assignmentchanges/",
        admin_dev_admin_required(reporting.assignmentchange_list),
    ),
    path(
        "expense_statistics_pdf/",
        admin_dev_admin_required(expenses.expense_statistics_pdf),
    ),
    # Export URLs
    path(
        "admin/drudges/pdf/",
        dev_admin_required(DrudgePDFExportView.as_view()),
        name="drudge_export",
    ),
    path(
        "admin/drudges/csv/",
        dev_admin_required(DrudgeCSVExportView.as_view()),
        name="drudge_export_csv",
    ),
    path(
        "admin/assignments/pdf/",
        admin_required(AssignmentPDFExportView.as_view()),
        name="assignment_export",
    ),
    path(
        "admin/assignments/csv/",
        admin_required(AssignmentCSVExportView.as_view()),
        name="assignment_export_csv",
    ),
]
