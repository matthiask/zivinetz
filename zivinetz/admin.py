from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.utils import six

from zivinetz import models


str_method = '__str__' if six.PY3 else '__unicode__'


class SpecificationInline(admin.StackedInline):
    model = models.Specification
    can_delete = False
    extra = 0
    max_num = 2
    fieldsets = (
        (None, {
            'fields': (
                'code',
                'with_accomodation', 'clothing',
                'accomodation_throughout',
                'food_throughout',
                'conditions',
            ),
        }),
        (_('working days'), {
            'fields': (
                'accomodation_working', 'breakfast_working',
                'lunch_working', 'supper_working'),
        }),
        (_('sick days'), {
            'fields': (
                'accomodation_sick', 'breakfast_sick', 'lunch_sick',
                'supper_sick'),
        }),
        (_('free days'), {
            'fields': (
                'accomodation_free', 'breakfast_free', 'lunch_free',
                'supper_free'),
        }),
    )


class CompanyHolidayAdmin(admin.ModelAdmin):
    filter_horizontal = ('applies_to',)
    list_display = ('date_from', 'date_until', 'scope_statements')
    save_as = True

    def scope_statements(self, instance):
        return mark_safe(u'<br>'.join(
            '%s' % object for object in instance.applies_to.all()
        ))
    scope_statements.short_description = _('scope statements')


admin.site.register(
    models.ScopeStatement,
    list_display=('is_active', 'eis_no', 'name'),
    list_display_links=('name',),
    list_filter=('is_active',),
    inlines=[SpecificationInline],
)

admin.site.register(
    models.DrudgeQuota,
    date_hierarchy='week',
    list_display=(str_method, 'scope_statement', 'quota'),
    list_editable=('quota',),
    list_filter=('scope_statement',),
    ordering=('week',),
)

admin.site.register(
    models.CompensationSet,
    save_as=True,
    fieldsets=(
        (None, {
            'fields': (
                'valid_from', 'spending_money', 'accomodation_home',
                'private_transport_per_km'),
        }),
        (_('clothing'), {
            'fields': ('clothing', 'clothing_limit_per_assignment'),
        }),
        (_('meals at accomodation'), {
            'fields': (
                'breakfast_at_accomodation', 'lunch_at_accomodation',
                'supper_at_accomodation'),
        }),
        (_('meals external'), {
            'fields': (
                'breakfast_external', 'lunch_external',
                'supper_external'),
        })
    ),
)

admin.site.register(models.RegionalOffice)

admin.site.register(
    models.Drudge,
    list_display=(
        str_method, 'date_of_birth', 'phone_home', 'phone_office',
        'mobile', 'regional_office'),
    list_filter=('regional_office', 'driving_license'),
    raw_id_fields=('user',),
    search_fields=(
        'user__first_name', 'user__last_name', 'user__email',
        'address', 'zip_code', 'city'),
)

admin.site.register(
    models.Assignment,
    date_hierarchy='date_from',
    list_display=(
        'specification', 'drudge', 'date_from',
        'determine_date_until', 'status', 'admin_pdf_url'),
    list_filter=('specification', 'part_of_long_assignment', 'status'),
    raw_id_fields=('drudge',),
)

admin.site.register(
    models.AssignmentChange,
    date_hierarchy='created',
    list_display=(
        'created', 'assignment_description', 'changed_by', 'changes'),
    list_filter=('changed_by',),
    raw_id_fields=('assignment',),
)

admin.site.register(
    models.ExpenseReport,
    date_hierarchy='date_from',
    list_display=(
        str_method, 'assignment', 'date_from', 'date_until',
        'status'),
    list_filter=('status',),
    raw_id_fields=('assignment',),
    search_fields=models.ExpenseReport.objects.search_fields,
)

admin.site.register(
    models.PublicHoliday,
    list_display=('name', 'date'),
    save_as=True,
)

admin.site.register(
    models.CompanyHoliday,
    CompanyHolidayAdmin,
)

admin.site.register(
    models.Codeword,
    list_display=('key', 'codeword', 'created'),
    list_filter=('key',),
)

admin.site.register(models.JobReferenceTemplate)

admin.site.register(
    models.JobReference,
    list_display=('assignment', 'created'),
    raw_id_fields=('assignment',),
)

admin.site.register(
    models.Assessment,
    list_display=('drudge', 'mark', 'comment'),
    raw_id_fields=('drudge',),
)

admin.site.register(
    models.Specification,
    list_display=(str_method, 'ordering'),
    list_editable=('ordering',),
    readonly_fields=[
        f.name for f in
        models.Specification._meta.get_fields(include_hidden=False)
        if not f.one_to_many
    ],
)
