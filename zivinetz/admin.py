from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from zivinetz import models


class SpecificationInline(admin.StackedInline):
    model = models.Specification
    can_delete = False
    extra = 0
    max_num = 2
    fieldsets = (
        (None, {
            'fields': ('with_accomodation', 'clothing'),
        }),
        (_('working days'), {
            'fields': ('accomodation_working', 'breakfast_working',
                'lunch_working', 'supper_working'),
        }),
        (_('sick days'), {
            'fields': ('accomodation_sick', 'breakfast_sick', 'lunch_sick',
                'supper_sick'),
        }),
        (_('free days'), {
            'fields': ('accomodation_free', 'breakfast_free', 'lunch_free',
                'supper_free'),
        }),
    )

admin.site.register(models.ScopeStatement,
    list_display=('is_active', 'eis_no', 'name'),
    list_display_links=('name',),
    list_filter=('is_active',),
    inlines=[SpecificationInline],
    )

admin.site.register(models.CompensationSet,
    save_as=True,
    fieldsets=(
        (None, {
            'fields': ('valid_from', 'spending_money', 'accomodation_home',
                'private_transport_per_km'),
        }),
        (_('clothing'), {
            'fields': ('clothing', 'clothing_limit_per_assignment'),
        }),
        (_('meals at accomodation'), {
            'fields': ('breakfast_at_accomodation', 'lunch_at_accomodation',
                'supper_at_accomodation'),
        }),
        (_('meals external'), {
            'fields': ('breakfast_external', 'lunch_external',
                'supper_external'),
        })
        ),
    )

admin.site.register(models.RegionalOffice)

admin.site.register(models.Drudge,
    list_display=('__unicode__', 'date_of_birth', 'phone_home', 'phone_office',
        'mobile', 'regional_office'),
    list_filter=('regional_office', 'driving_license'),
    search_fields=('user__first_name', 'user__last_name', 'user__email',
        'address', 'zip_code', 'city'),
    )

admin.site.register(models.Assignment,
    date_hierarchy='date_from',
    list_display=('specification', 'drudge', 'date_from',
        'determine_date_until', 'status', 'admin_pdf_url'),
    list_filter=('specification', 'part_of_long_assignment', 'status'),
    )


admin.site.register(models.ExpenseReport,
    date_hierarchy='date_from',
    list_display=('__unicode__', 'assignment', 'date_from', 'date_until',
        'status'),
    list_filter=('status',),
    raw_id_fields=('assignment',),
    search_fields=models.ExpenseReport.objects.search_fields,
    )

admin.site.register(models.PublicHoliday,
    list_display=('name', 'date'),
    save_as=True,
    )

admin.site.register(models.CompanyHoliday,
    list_display=('date_from', 'date_until'),
    save_as=True,
    )

admin.site.register(models.WaitList,
    list_display=('created', 'drudge', '__unicode__'),
    raw_id_fields=('drudge',),
    )

admin.site.register(models.Codeword,
    list_display=('key', 'codeword', 'created'),
    list_filter=('key',),
    )

admin.site.register(models.JobReferenceTemplate)

admin.site.register(models.JobReference,
    list_display=('assignment', 'created'),
    )

admin.site.register(models.Assessment,
    list_display=('drudge', 'mark', 'comment'),
    raw_id_fields=('drudge',),
    )
