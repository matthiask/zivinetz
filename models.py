from datetime import date, datetime, timedelta
from decimal import Decimal

from towel.managers import SearchManager

from django.contrib.auth.models import User
from django.contrib.localflavor.ch import ch_states
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _, ugettext


class ScopeStatement(models.Model):
    is_active = models.BooleanField(_('is active'), default=True)
    eis_no = models.CharField(_('EIS No.'), unique=True, max_length=10)
    name = models.CharField(_('name'), max_length=100)

    class Meta:
        ordering = ['name']
        verbose_name = _('scope statement')
        verbose_name_plural = _('scope statements')

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.eis_no)


class Choices(object):
    def __init__(self, choices):
        self._choices = choices
        self._choice_dict = dict(choices)

    @property
    def kwargs(self):
        return {
            'max_length': 20,
            'choices': self.__dict__['_choices'],
            'default': self.__dict__['_choices'][0][0],
            }

    def __getattr__(self, k):
        self.__dict__['_choice_dict'][k] # raise KeyError if key does not exist
        return k


class Specification(models.Model):
    ACCOMODATION = Choices((
        ('provided', _('provided')),
        ('compensated', _('compensated')),
        ))

    MEAL = Choices((
        ('no_compensation', _('no compensation')),
        ('at_accomodation', _('at accomodation')),
        ('external', _('external')),
        ))

    CLOTHING = Choices((
        ('provided', _('provided')),
        ('compensated', _('compensated')),
        ))

    scope_statement = models.ForeignKey(ScopeStatement,
        verbose_name=_('scope statement'), related_name='specifications')

    with_accomodation = models.BooleanField(_('with accomodation'))
    code = models.CharField(_('code'), max_length=10,
        help_text=_('Short, unique code identifying this specification.'))

    accomodation_working = models.CharField(_('accomodation on working days'), **ACCOMODATION.kwargs)
    breakfast_working = models.CharField(_('breakfast on working days'), **MEAL.kwargs)
    lunch_working = models.CharField(_('lunch on working days'), **MEAL.kwargs)
    supper_working = models.CharField(_('supper on working days'), **MEAL.kwargs)

    accomodation_sick = models.CharField(_('accomodation on sick days'), **ACCOMODATION.kwargs)
    breakfast_sick = models.CharField(_('breakfast on sick days'), **MEAL.kwargs)
    lunch_sick = models.CharField(_('lunch on sick days'), **MEAL.kwargs)
    supper_sick = models.CharField(_('supper on sick days'), **MEAL.kwargs)

    accomodation_free = models.CharField(_('accomodation on free days'), **ACCOMODATION.kwargs)
    breakfast_free = models.CharField(_('breakfast on free days'), **MEAL.kwargs)
    lunch_free = models.CharField(_('lunch on free days'), **MEAL.kwargs)
    supper_free = models.CharField(_('supper on free days'), **MEAL.kwargs)

    clothing = models.CharField(_('clothing'), **CLOTHING.kwargs)

    class Meta:
        ordering = ['scope_statement', 'with_accomodation']
        unique_together = (('scope_statement', 'with_accomodation'),)
        verbose_name = _('specification')
        verbose_name_plural = _('specifications')

    def __unicode__(self):
        return u'%s - %s' % (
            self.scope_statement,
            self.with_accomodation and ugettext('with accomodation') or ugettext('without accomodation'),
            )

    def compensation(self, for_date=date.today):
        cset = CompensationSet.objects.for_date(for_date)

        compensation = {
            'spending_money': cset.spending_money,
            }

        for day_type in ('working', 'sick', 'free'):
            key = 'accomodation_%s' % day_type
            value = getattr(self, key)

            if value == self.ACCOMODATION.provided:
                compensation[key] = Decimal('0.00')
            else:
                compensation[key] = cset.accomodation_home

            for meal in ('breakfast', 'lunch', 'supper'):
                key = '%s_%s' % (meal, day_type)
                value = getattr(self, key)

                if value == self.MEAL.no_compensation:
                    compensation[key] = Decimal('0.00')
                else:
                    compensation[key] = getattr(cset, '%s_%s' % (meal, value))

        if self.clothing == self.CLOTHING.provided:
            compensation.update({
                'clothing': Decimal('0.00'),
                'clothing_limit_per_assignment': Decimal('0.00'),
                })
        else:
            compensation.update({
                'clothing': cset.clothing,
                'clothing_limit_per_assignment': cset.clothing_limit_per_assignment,
                })

        return compensation


class CompensationSetManager(models.Manager):
    def for_date(self, for_date=date.today):
        try:
            return self.filter(valid_from__lte=for_date).order_by('-valid_from')[0]
        except IndexError:
            raise self.model.DoesNotExist


class CompensationSet(models.Model):
    valid_from = models.DateField(_('valid from'), unique=True)

    spending_money = models.DecimalField(_('spending money'), max_digits=10, decimal_places=2)

    breakfast_at_accomodation = models.DecimalField(_('breakfast at accomodation'), max_digits=10, decimal_places=2)
    lunch_at_accomodation = models.DecimalField(_('lunch at accomodation'), max_digits=10, decimal_places=2)
    supper_at_accomodation = models.DecimalField(_('supper at accomodation'), max_digits=10, decimal_places=2)

    breakfast_external = models.DecimalField(_('external breakfast'), max_digits=10, decimal_places=2)
    lunch_external = models.DecimalField(_('external lunch'), max_digits=10, decimal_places=2)
    supper_external = models.DecimalField(_('external supper'), max_digits=10, decimal_places=2)

    accomodation_home = models.DecimalField(_('accomodation'), max_digits=10, decimal_places=2,
        help_text=_('Daily compensation if drudge returns home for the night.'))

    private_transport_per_km = models.DecimalField(_('private transport per km'), max_digits=10, decimal_places=2,
        help_text=_('Only applies if public transport use is not reasonable.'))

    clothing = models.DecimalField(_('clothing'), max_digits=10, decimal_places=6,
        help_text=_('Daily compensation for clothes if clothing isn\'t offered by the company.'))
    clothing_limit_per_assignment = models.DecimalField(_('clothing limit per assignment'),
        max_digits=10, decimal_places=2,
        help_text=_('Maximal compensation for clothing per assignment.'))

    class Meta:
        ordering = ['-valid_from']
        verbose_name = _('compensation set')
        verbose_name_plural = _('compensation sets')

    objects = CompensationSetManager()

    def __unicode__(self):
        return ugettext('compensation set, valid from %s') % self.valid_from


class RegionalOffice(models.Model):
    name = models.CharField(_('name'), max_length=100)
    city = models.CharField(_('city'), max_length=100)
    address = models.TextField(_('address'), blank=True)
    code = models.CharField(_('code'), max_length=10,
        help_text=_('Short, unique identifier.'))

    class Meta:
        ordering = ['name']
        verbose_name = _('regional office')
        verbose_name_plural = _('regional offices')

    def __unicode__(self):
            return self.name


class DrudgeManager(SearchManager):
    search_fields = ('user__first_name', 'user__last_name', 'zdp_no', 'address',
        'zip_code', 'city', 'place_of_citizenship_city', 'place_of_citizenship_state',
        'phone_home', 'phone_office', 'mobile', 'bank_account', 'health_insurance_account',
        'health_insurance_company', 'education_occupation')


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

    environment_course = models.BooleanField(_('environment course'), default=False,
        help_text=_('Has taken the environment course already.'))
    motor_saw_course = models.CharField(_('motor saw course'), max_length=10, choices=(
        ('2-day', _('2 day course')),
        ('5-day', _('5 day course')),
        ), blank=True, null=True, help_text=_('Has taken the motor saw course already.'))

    regional_office = models.ForeignKey(RegionalOffice, verbose_name=_('regional office'))
    notes = models.TextField(_('notes'), blank=True)

    class Meta:
        ordering = ['user__last_name', 'user__first_name', 'zdp_no']
        verbose_name = _('drudge')
        verbose_name_plural = _('drudges')

    objects = DrudgeManager()

    def __unicode__(self):
        return u'%s %s (%s)' % (
            self.user.first_name,
            self.user.last_name,
            self.zdp_no,
            )


class AssignmentManager(SearchManager):
    search_fields = ['specification__scope_statement__name', 'specification__code'] +\
        ['drudge__%s' % f for f in DrudgeManager.search_fields]

    def for_date(self, day=None):
        day = day if day else date.today()

        return self.filter(
            Q(date_from__lte=day) & (
                Q(date_until__gte=day) | (
                    Q(date_until_extension__isnull=False) & Q(date_until_extension__gte=day)
                )
            ))


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

    created = models.DateTimeField(_('created'), default=datetime.now)
    modified = models.DateTimeField(_('modified'), auto_now=True)

    specification = models.ForeignKey(Specification,
        verbose_name=_('specification'))
    drudge = models.ForeignKey(Drudge, verbose_name=_('drudge'),
        related_name='assignments')
    regional_office = models.ForeignKey(RegionalOffice,
        verbose_name=_('regional office'))

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

    arranged_on = models.DateField(_('arranged on'), blank=True, null=True)
    mobilized_on = models.DateField(_('mobilized on'), blank=True, null=True)

    class Meta:
        ordering = ['-date_from', '-date_until']
        verbose_name = _('assignment')
        verbose_name_plural = _('assignments')

    objects = AssignmentManager()

    def __unicode__(self):
        return u'%s on %s (%s - %s)' % (
            self.drudge,
            self.specification.code,
            self.date_from,
            self.determine_date_until(),
            )

    def determine_date_until(self):
        return self.date_until_extension or self.date_until
    determine_date_until.short_description = _('eff. until date')

    def assignment_days(self, until=None):
        day = self.date_from
        until = until or self.determine_date_until()
        one_day = timedelta(days=1)

        public_holidays = PublicHoliday.objects.filter(
            date__range=(day, until)).values_list('date', flat=True)
        company_holidays = list(CompanyHoliday.objects.filter(
            date_from__lte=until,
            date_until__gte=day))

        vacation_days = 0
        assignment_days = (self.date_until - self.date_from).days + 1 # +1 because the range is inclusive

        if assignment_days >= 180:
            # 30 days isn't exactly one month. But that's good enough for us.
            # We grant 2 additional vacation days per 30 full days only
            # (see ZDV Art. 72)
            vacation_days = 8 + int((assignment_days - 180) / 30) * 2

        days = {
            'assignment_days': assignment_days,
            'vacation_days': vacation_days,

            'company_holidays': 0,
            'public_holidays_during_company_holidays': 0,
            'public_holidays_outside_company_holidays': 0,

            'vacation_days_during_company_holidays': 0,

            'freely_definable_vacation_days': vacation_days,
            'working_days': 0,

            'countable_days': 0,
            'forced_leave_days': 0, # days which aren't countable and are forced upon the drudge
            }

        monthly_expense_days = {}

        def pop_company_holiday():
            try:
                return company_holidays.pop(0)
            except IndexError:
                return None

        company_holiday = pop_company_holiday()

        while day <= until:
            is_weekend = day.weekday() in (5, 6)
            is_public_holiday = day in public_holidays
            is_company_holiday = company_holiday and company_holiday.is_contained(day)
            slot = 'free'

            if is_company_holiday:
                days['company_holidays'] += 1

                if is_public_holiday:
                    # At least we have public holidays too.
                    days['public_holidays_during_company_holidays'] += 1
                    days['countable_days'] += 1
                else:
                    if is_weekend:
                        # We were lucky once again.
                        days['countable_days'] += 1
                    else:
                        # Oh no, company holiday and neither public holiday nor
                        # weekend. Now the draconian regime of the swiss
                        # administration comes to full power.

                        if days['freely_definable_vacation_days']:
                            # Vacations need to be taken during public holidays
                            # if possible at all. Unfortunately for drudges.
                            days['freely_definable_vacation_days'] -= 1

                            # At least they are countable towards assignment total.-
                            days['countable_days'] += 1
                        else:
                            # Damn. No vacation days left (if there were any in the
                            # beginning. The drudge has to pause his assignment for
                            # this time.
                            days['forced_leave_days'] += 1
                            slot = 'forced'

            else:
                # No company holiday... business as usual, maybe.
                days['countable_days'] += 1 # Nice!

                if not (is_public_holiday or is_weekend):
                    # Hard beer-drinking and pickaxing action.
                    days['working_days'] += 1
                    slot = 'working'


            key = (day.year, day.month)
            monthly_expense_days.setdefault(key, {
                'free': 0, 'working': 0, 'forced': 0, 'start': day})
            monthly_expense_days[key][slot] += 1
            monthly_expense_days[key]['end'] = day

            day += one_day

            # Fetch new company holiday once the old one starts smelling funny.
            if company_holiday and company_holiday.date_until < day:
                company_holiday = pop_company_holiday()

        return days, sorted(monthly_expense_days.items(), key=lambda item: item[0])

    def expenses(self):
        """
        This calculates an estimate
        """

        assignment_days, monthly_expense_days = self.assignment_days()
        specification = self.specification

        clothing_total = Decimal('240.00') # TODO don't hardcode this
        expenses = {}

        for month, days in monthly_expense_days:
            compensation = specification.compensation(date(month[0], month[1], 1))

            free = days['free']
            working = days['working']

            total = free + working

            expenses[month] = {
                'spending_money': total * compensation['spending_money'],
                'clothing': total * compensation['clothing'],
                'accomodation': free * compensation['accomodation_free'] +\
                                working * compensation['accomodation_working'],
                'food': free * (compensation['breakfast_free'] +\
                                compensation['lunch_free'] +\
                                compensation['supper_free']) +\
                        working * (compensation['breakfast_working'] +\
                                   compensation['lunch_working'] +\
                                   compensation['supper_working']),
                }

            clothing_total -= expenses[month]['clothing']

            if clothing_total < 0:
                expenses[month]['clothing'] += clothing_total
                clothing_total = 0

        return expenses

    @models.permalink
    def pdf_url(self):
        return ('zivinetz.views.reporting.assignment_pdf', (self.pk,), {})

    def admin_pdf_url(self):
        return u'<a href="%s">PDF</a>' % self.pdf_url()
    admin_pdf_url.allow_tags = True
    admin_pdf_url.short_description = 'PDF'

    def generate_expensereports(self):
        self.reports.all().delete()

        assignment_days, monthly_expense_days = self.assignment_days()

        for ym, days in monthly_expense_days:
            report = self.reports.create(
                date_from=days['start'],
                date_until=days['end'],
                working_days=days['working'],
                free_days=days['free'],
                sick_days=0,
                holi_days=0,
                forced_leave_days=days['forced'],
                )

            report.periods.create(
                specification=self.specification,
                date_from=days['start'],
                )


class ExpenseReportManager(SearchManager):
    search_fields = ['report_no'] + \
        ['assignment__%s' % f for f in AssignmentManager.search_fields]


class ExpenseReport(models.Model):
    PENDING = 10
    FILLED = 20
    PAID = 30

    STATUS_CHOICES = (
        (PENDING, _('pending')),
        (FILLED, _('filled')),
        (PAID, _('paid')),
        )

    assignment = models.ForeignKey(Assignment, verbose_name=_('assignment'),
        related_name='reports')
    date_from = models.DateField(_('date from'))
    date_until = models.DateField(_('date until'))
    report_no = models.CharField(_('report no.'), max_length=10, blank=True)

    status = models.IntegerField(_('status'), choices=STATUS_CHOICES,
        default=PENDING)

    working_days = models.PositiveIntegerField(_('working days'))
    working_days_notes = models.CharField(_('notes'), max_length=100, blank=True)
    free_days = models.PositiveIntegerField(_('free days'))
    free_days_notes = models.CharField(_('notes'), max_length=100, blank=True)
    sick_days = models.PositiveIntegerField(_('sick days'))
    sick_days_notes = models.CharField(_('notes'), max_length=100, blank=True)
    holi_days = models.PositiveIntegerField(_('holiday days'),
        help_text=_('These days are still countable towards the assignment total days.'))
    holi_days_notes = models.CharField(_('notes'), max_length=100, blank=True)
    forced_leave_days = models.PositiveIntegerField(_('forced leave days'))
    forced_leave_days_notes = models.CharField(_('notes'), max_length=100, blank=True)

    clothing_expenses = models.DecimalField(_('clothing expenses'),
        max_digits=10, decimal_places=2, default=Decimal('0.00'))
    clothing_expenses_notes = models.CharField(_('notes'), max_length=100, blank=True)
    transport_expenses = models.DecimalField(_('transport expenses'),
        max_digits=10, decimal_places=2, default=Decimal('0.00'))
    transport_expenses_notes = models.CharField(_('notes'), max_length=100, blank=True)

    miscellaneous = models.DecimalField(_('miscellaneous'),
        max_digits=10, decimal_places=2, default=Decimal('0.00'))
    miscellaneous_notes = models.CharField(_('notes'), max_length=100, blank=True)

    total = models.DecimalField(_('total'), max_digits=10, decimal_places=2,
        default=0)

    class Meta:
        ordering = ['-date_from']
        verbose_name = _('expense report')
        verbose_name_plural = _('expense reports')

    objects = ExpenseReportManager()

    def __unicode__(self):
        return u'%s - %s' % (self.date_from, self.date_until)

    def is_editable(self):
        return self.status < self.PAID
    is_editable.boolean = True
    is_editable.short_description = _('is editable')

    @property
    def total_days(self):
        return self.working_days + self.free_days + self.sick_days + self.holi_days\
            + self.forced_leave_days

    @models.permalink
    def pdf_url(self):
        return ('zivinetz.views.reporting.expense_report_pdf', (self.pk,), {})

    def recalculate_total(self, save=True):
        _n1, _n2, self.total = self.compensations()
        if save:
            self.save()

    def compensations(self):
        period = self.periods.get() # TODO handle more than one / non-existing period

        compensation = period.specification.compensation(
            self.assignment.mobilized_on or self.assignment.date_from) # TODO handle mobilized_on IS NULL case

        # spending_money, accomodation, breakfast, lunch, supper, total

        def line(title, day_type, days):
            l = [
                compensation['spending_money'],
                compensation['accomodation_%s' % day_type],
                compensation['breakfast_%s' % day_type],
                compensation['lunch_%s' % day_type],
                compensation['supper_%s' % day_type],
                ]

            return [u'%s %s' % (days, title)] + l + [sum(l) * days]


        ret = [[
            '',
            ugettext('spending money'),
            ugettext('accomodation'),
            ugettext('breakfast'),
            ugettext('lunch'),
            ugettext('supper'),
            ugettext('Total'),
            ]]

        ret.append(line(
            ugettext('working days'),
            'working',
            self.working_days))
        ret.append(line(
            ugettext('free days'),
            'free',
            self.free_days))
        ret.append(line(
            ugettext('sick days'),
            'sick',
            self.sick_days))

        # holiday counts as work
        ret.append(line(
            ugettext('holiday days'),
            'free',
            self.holi_days))

        # forced leave counts zero
        ret.append([
            u'%s %s' % (self.forced_leave_days, ugettext('forced leave days'))
            ] + [Decimal('0.00')] * 6)

        additional = [
            (ugettext('transport expenses'), self.transport_expenses),
            (ugettext('clothing expenses'), self.clothing_expenses),
            ]

        total = sum(r[6] for r in ret[1:]) + sum(r[1] for r in additional)

        return ret, additional, total


class ExpenseReportPeriod(models.Model):
    expense_report = models.ForeignKey(ExpenseReport, verbose_name=_('expense report'),
        related_name='periods')
    specification = models.ForeignKey(Specification,
        verbose_name=_('specification'))

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

    def is_contained(self, day):
        return self.date_from <= day <= self.date_until


class WaitList(models.Model):
    created = models.DateTimeField(_('created'), default=datetime.now)
    drudge = models.ForeignKey(Drudge, verbose_name=_('drudge'))

    specification = models.ForeignKey(Specification,
        verbose_name=_('specification'))
    assignment_date_from = models.DateField(_('available from'))
    assignment_date_until = models.DateField(_('available until'))
    assignment_duration = models.PositiveIntegerField(_('duration in days'))

    notes = models.TextField(_('notes'), blank=True)

    class Meta:
        ordering = ['created']
        verbose_name = _('waitlist')
        verbose_name_plural = _('waitlist')

    def __unicode__(self):
        return u'%s - %s, %s days' % (
            self.assignment_date_from,
            self.assignment_date_until,
            self.assignment_duration,
            )


class Assessment(models.Model):
    created = models.DateTimeField(_('created'), default=datetime.now)
    drudge = models.ForeignKey(Drudge, verbose_name=_('drudge'),
        related_name='assessments')
    mark = models.IntegerField(_('mark'), choices=zip(range(1, 7), range(1, 7)))
    comment = models.TextField(_('comment'), blank=True)

    class Meta:
        ordering = ['-created']
        verbose_name = _('internal assessment')
        verbose_name_plural = _('internal assessments')

    def __unicode__(self):
        return 'Mark %s for drudge %s' % (self.mark, self.drudge)


class CodewordManager(models.Manager):
    def word(self, key):
        try:
            return self.filter(key=key).latest().codeword
        except self.model.DoesNotExist:
            return u''


class Codeword(models.Model):
    created = models.DateTimeField(_('created'), default=datetime.now)
    key = models.CharField(_('key'), max_length=10, db_index=True)
    codeword = models.CharField(_('codeword'), max_length=20)

    class Meta:
        get_latest_by = 'created'
        ordering = ['-created']
        verbose_name = _('codeword')
        verbose_name_plural = _('codewords')

    objects = CodewordManager()

    def __unicode__(self):
        return self.codeword


class JobReferenceTemplate(models.Model):
    title = models.CharField(_('title'), max_length=100)
    text = models.TextField(_('text'))

    class Meta:
        ordering = ['title']
        verbose_name = _('job reference template')
        verbose_name_plural = _('job reference templates')

    def __unicode__(self):
        return self.title


class JobReference(models.Model):
    assignment = models.ForeignKey(Assignment, verbose_name=_('assignment'),
        related_name='jobreferences')
    created = models.DateField(_('created'))
    text = models.TextField(_('text'))

    class Meta:
        verbose_name = _('job reference')
        verbose_name_plural = _('job references')

    def __unicode__(self):
        return 'job reference for %s' % self.assignment

    @models.permalink
    def pdf_url(self):
        return ('zivinetz.views.reporting.reference_pdf', (self.pk,), {})
