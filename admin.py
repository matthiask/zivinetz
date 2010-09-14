from django.contrib import admin

from zivinetz import models


class ScopeStatementExpenseInline(admin.StackedInline):
    model = models.ScopeStatementExpense
    can_delete = False
    max_num = 2

admin.site.register(models.ScopeStatement,
    list_display=('is_active', 'eis_no', 'name'),
    list_display_links=('name',),
    list_filter=('is_active',),
    inlines=[ScopeStatementExpenseInline],
    )

admin.site.register(models.RegionalOffice)

admin.site.register(models.Drudge)

admin.site.register(models.Assignment,
    date_hierarchy='date_from',
    list_display=('scope_statement_expense', 'drudge', 'date_from',
        'determine_date_until', 'status'),
    list_filter=('scope_statement_expense', 'part_of_long_assignment', 'status'),
    )


class ExpenseReportPeriodInline(admin.TabularInline):
    model = models.ExpenseReportPeriod

admin.site.register(models.ExpenseReport,
    date_hierarchy='date_from',
    list_display=('__unicode__', 'assignment', 'date_from', 'date_until'),
    inlines=[ExpenseReportPeriodInline],
    )

admin.site.register(models.PublicHoliday,
    list_display=('name', 'date'),
    save_as=True,
    )

admin.site.register(models.CompanyHoliday,
    list_display=('date_from', 'date_until'),
    save_as=True,
    )
