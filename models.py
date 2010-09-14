from django.contrib.auth.models import User
from django.contrib.localflavor.ch import ch_states
from django.db import models
from django.utils.translation import ugettext_lazy as _, ugettext




class ScopeStatement(models.Model):
    is_active = models.BooleanField(_('is active'), default=True)
    eis_no = models.CharField(_('EIS No.'), unique=True, max_length=10)
    name = models.CharField(_('name'), max_length=100)

    class Meta:
        verbose_name = _('scope statement')
        verbose_name_plural = _('scope statements')

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.eis_no)


class DayType(object):
    WORKING = 'working'
    FREE = 'free'
    SICK = 'sick'
    PAID_LEAVE = 'paid_leave'
    UNPAID_LEAVE = 'unpaid_leave'

    CHOICES = (
        (WORKING, _('working')),
        (FREE, _('free')),
        (SICK, _('sick')),
        (PAID_LEAVE, _('paid leave')),
        (UNPAID_LEAVE, _('unpaid leave')),
        )


class ScopeStatementExpense(models.Model):
    scope_statement = models.ForeignKey(ScopeStatement,
        verbose_name=_('scope statement'),
        related_name='expenses')
    accomodation = models.BooleanField(_('accomodation'), default=True)

    # these are all daily values
    spending_money = models.DecimalField(_('spending money'), max_digits=10, decimal_places=2)
    clothing = models.DecimalField(_('clothing'), max_digits=10, decimal_places=2)

    accomodation_working = models.DecimalField(_('accomodation (working)'), max_digits=10, decimal_places=2)
    accomodation_sick = models.DecimalField(_('accomodation (sick)'), max_digits=10, decimal_places=2)
    accomodation_free = models.DecimalField(_('accomodation (free)'), max_digits=10, decimal_places=2)

    breakfast_working = models.DecimalField(_('breakfast (working)'), max_digits=10, decimal_places=2)
    breakfast_sick = models.DecimalField(_('breakfast (sick)'), max_digits=10, decimal_places=2)
    breakfast_free = models.DecimalField(_('breakfast (free)'), max_digits=10, decimal_places=2)

    lunch_working = models.DecimalField(_('lunch (working)'), max_digits=10, decimal_places=2)
    lunch_sick = models.DecimalField(_('lunch (sick)'), max_digits=10, decimal_places=2)
    lunch_free = models.DecimalField(_('lunch (free)'), max_digits=10, decimal_places=2)

    supper_working = models.DecimalField(_('supper (working)'), max_digits=10, decimal_places=2)
    supper_sick = models.DecimalField(_('supper (sick)'), max_digits=10, decimal_places=2)
    supper_free = models.DecimalField(_('supper (free)'), max_digits=10, decimal_places=2)

    class Meta:
        unique_together = (('scope_statement', 'accomodation'),)
        verbose_name = _('scope statement expense')
        verbose_name_plural = _('scope statement expenses')

    def __unicode__(self):
        return u'%s - %s' % (
            self.scope_statement,
            self.accomodation and ugettext('with accomodation') or ugettext('without accomodation'),
            )


class RegionalOffice(models.Model):
    name = models.CharField(_('name'), max_length=100)

    class Meta:
        ordering = ['name']
        verbose_name = _('regional office')
        verbose_name_plural = _('regional offices')

    def __unicode__(self):
            return self.name


class Drudge(models.Model):
    user = models.OneToOneField(User)

    zdp_no = models.CharField(_('ZDP No.'), unique=True, max_length=10)

    address = models.TextField(_('address'))
    zip_code = models.CharField(_('ZIP code'), max_length=10)
    city = models.CharField(_('city'), max_length=100)

    date_of_birth = models.DateField(_('date of birth'))

    place_of_citizenship_city = models.CharField(_('place of citizenship'), max_length=100)
    place_of_citizenship_state = models.CharField(_('place of citizenship'), max_length=2,
        choices=ch_states.STATE_CHOICES)

    phone_home = models.CharField(_('phone (home)'), max_length=20, blank=True)
    phone_office = models.CharField(_('phone (office)'), max_length=20, blank=True)
    mobile = models.CharField(_('mobile'), max_length=20, blank=True)

    bank_account = models.CharField(_('bank account'), max_length=100,
        help_text=_('Either enter your IBAN or your Swiss post account number.'))

    health_insurance_company = models.CharField(_('health insurance company'),
        max_length=100, blank=True)
    health_insurance_account = models.CharField(_('health insurance account'),
        max_length=100, blank=True)

    education_occupation = models.TextField(_('education / occupation'),
        blank=True)

    driving_license = models.BooleanField(_('driving license'), default=False)
    general_abonnement = models.BooleanField(_('general abonnement'), default=False)
    half_fare_card = models.BooleanField(_('half-fare card'), default=False)
    other_card = models.CharField(_('other card'), max_length=100,
        blank=True)

    class Meta:
        verbose_name = _('drudge')
        verbose_name_plural = _('drudges')

    def __unicode__(self):
        return u'%s %s (%s)' % (
            self.user.first_name,
            self.user.last_name,
            self.zdp_no,
            )


class Assignment(models.Model):
    TENTATIVE = 10
    ARRANGED = 20
    MOBILIZED = 30
    DECLINED = 40

    STATUS_CHOICES = (
        (TENTATIVE, _('tentative')),
        (ARRANGED, _('arranged')),
        (MOBILIZED, _('mobilized')),
        (DECLINED, _('declined')),
        )

    scope_statement_expense = models.ForeignKey(ScopeStatementExpense,
        verbose_name=_('scope statement expense'))
    drudge = models.ForeignKey(Drudge, verbose_name=_('drudge'))
    regional_office = models.ForeignKey(RegionalOffice,
        verbose_name=('regional office'))

    date_from = models.DateField(_('date from'))
    date_until = models.DateField(_('date until'))
    date_until_extension = models.DateField(_('date until (extended)'),
        blank=True, null=True,
        help_text=_('Only fill out if assignment has been extended.'))

    part_of_long_assignment = models.BooleanField(_('part of long assignment'),
        default=False)

    # TODO assignment days, leave days etc.

    status = models.IntegerField(_('status'), choices=STATUS_CHOICES,
        default=TENTATIVE)

    class Meta:
        ordering = ['date_from']
        verbose_name = _('assignment')
        verbose_name_plural = _('assignments')

    def __unicode__(self):
        return u'%s (%s - %s)' % (
            self.drudge,
            self.date_from,
            self.determine_date_until,
            )

    @property
    def determine_date_until(self):
        return self.date_until_extension or self.date_until


class ExpenseReport(models.Model):
    assignment = models.ForeignKey(Assignment, verbose_name=_('assignment'),
        related_name='reports')
    date_from = models.DateField(_('date from'))
    date_until = models.DateField(_('date until'))

    class Meta:
        ordering = ['date_from']
        verbose_name = _('expense report')
        verbose_name_plural = _('expense reports')

    def __unicode__(self):
        return u'%s - %s' % (self.date_from, self.date_until)


class ExpenseReportPeriod(models.Model):
    expense_report = models.ForeignKey(ExpenseReport, verbose_name=_('expense report'),
        related_name='periods')
    scope_statement_expense = models.ForeignKey(ScopeStatementExpense,
        verbose_name=_('scope statement expense'))

    date_from = models.DateField(_('date from'))

    class Meta:
        ordering = ['date_from']
        verbose_name = _('expense report period')
        verbose_name_plural = _('expense report periods')

    def __unicode__(self):
        return u'%s, starting on %s' % (self.expense_report, self.date_from)


class PublicHoliday(models.Model):
    name = models.CharField(_('name'), max_length=100)
    date = models.DateField(_('date'), unique=True)

    class Meta:
        ordering = ['date']
        verbose_name = _('public holiday')
        verbose_name_plural = _('public holidays')

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.date)


class CompanyHoliday(models.Model):
    date_from = models.DateField(_('date from'))
    date_until = models.DateField(_('date until'))

    class Meta:
        ordering = ['date_from']
        verbose_name = _('company holiday')
        verbose_name_plural = _('company holidays')

    def __unicode__(self):
        return u'%s - %s' % (self.date_from, self.date_until)
