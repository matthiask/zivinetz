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

urlpatterns = [
    path("", home.home),
    path("dashboard/", drudge.dashboard, name="drudge_dashboard"),
    path("profile/", drudge.profile, name="drudge_profile"),
    path(
        "admin/",
        user_type_required(["admin", "user_plus", "squad_leader", "dev_admin"])(
            home.admin
        ),
    ),
    path(
        "admin/scheduling/",
        user_type_required(["admin", "user_plus", "dev_admin"])(scheduling.scheduling),
    ),
    path(
        "admin/scheduling/quotas/<int:year>/",
        user_type_required(["admin", "user_plus", "dev_admin"])(quota.quota_year),
    ),
    path("admin/", include("zivinetz.resources")),
    # Resource-based PDF URLs
    path(
        "assignments/<int:pk>/pdf/",
        user_type_required(["admin", "user_plus", "squad_leader", "dev_admin"])(
            reporting.assignment_pdf
        ),
        name="zivinetz_assignment_pdf",
    ),
    path(
        "assignments/phone-list/",
        user_type_required(["admin", "user_plus", "squad_leader", "dev_admin"])(
            reporting.assignment_phone_list
        ),
        name="zivinetz_assignment_phone_list",
    ),
    path(
        "expense_reports/<int:pk>/pdf/",
        user_type_required(["admin", "dev_admin"])(reporting.expense_report_pdf),
        name="zivinetz_expensereport_pdf",
    ),
    path(
        "references/<int:pk>/pdf/",
        user_type_required(["admin", "user_plus", "dev_admin"])(
            reporting.reference_pdf
        ),
        name="zivinetz_reference_pdf",
    ),
    path(
        "reporting/",
        user_type_required(["admin", "user_plus", "dev_admin"])(
            generic.TemplateView.as_view(template_name="zivinetz/reporting.html")
        ),
    ),
    path(
        "reporting/courses/",
        user_type_required(["admin", "user_plus", "dev_admin"])(reporting.course_list),
    ),
    path(
        "reporting/assignmentchanges/",
        user_type_required(["admin", "dev_admin"])(reporting.assignmentchange_list),
    ),
    path(
        "expense_statistics_pdf/",
        user_type_required(["admin", "dev_admin"])(expenses.expense_statistics_pdf),
    ),
    # Export URLs
    path(
        "admin/drudges/pdf/",
        user_type_required(["dev_admin"])(DrudgePDFExportView.as_view()),
        name="drudge_export",
    ),
    path(
        "admin/drudges/csv/",
        user_type_required(["dev_admin"])(DrudgeCSVExportView.as_view()),
        name="drudge_export_csv",
    ),
    path(
        "admin/assignments/pdf/",
        user_type_required(["admin", "user_plus", "dev_admin"])(
            AssignmentPDFExportView.as_view()
        ),
        name="assignment_export",
    ),
    path(
        "admin/assignments/csv/",
        user_type_required(["admin", "user_plus", "dev_admin"])(
            AssignmentCSVExportView.as_view()
        ),
        name="assignment_export_csv",
    ),
]
