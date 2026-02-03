from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, signals
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext, gettext_lazy as _
from towel.managers import SearchManager
from towel.resources.urls import model_resource_urls


STATE_CHOICES = (
    ("AG", _("Aargau")),
    ("AI", _("Appenzell Innerrhoden")),
    ("AR", _("Appenzell Ausserrhoden")),
    ("BS", _("Basel-Stadt")),
    ("BL", _("Basel-Land")),
    ("BE", _("Berne")),
    ("FR", _("Fribourg")),
    ("GE", _("Geneva")),
    ("GL", _("Glarus")),
    ("GR", _("Graubuenden")),
    ("JU", _("Jura")),
    ("LU", _("Lucerne")),
    ("NE", _("Neuchatel")),
    ("NW", _("Nidwalden")),
    ("OW", _("Obwalden")),
    ("SH", _("Schaffhausen")),
    ("SZ", _("Schwyz")),
    ("SO", _("Solothurn")),
    ("SG", _("St. Gallen")),
    ("TG", _("Thurgau")),
    ("TI", _("Ticino")),
    ("UR", _("Uri")),
    ("VS", _("Valais")),
    ("VD", _("Vaud")),
    ("ZG", _("Zug")),
    ("ZH", _("Zurich")),
)


@model_resource_urls()
class ScopeStatement(models.Model):
    is_active = models.BooleanField(_("is active"), default=True)
    eis_no = models.CharField(_("scope statement No."), unique=True, max_length=10)
    name = models.CharField(_("name"), max_length=100)

    branch_no = models.CharField(_("EIS No."), max_length=10)
    branch = models.CharField(_("branch"), max_length=100)

    company_name = models.CharField(_("company name"), max_length=100, blank=True)
    company_address = models.CharField(_("company address"), max_length=100, blank=True)
    company_zip_code = models.CharField(
        _("company ZIP code"), max_length=10, blank=True
    )
    company_city = models.CharField(_("company city"), max_length=100, blank=True)
    company_contact_name = models.CharField(
        _("company contact name"), max_length=100, blank=True
    )
    company_contact_email = models.EmailField(_("company contact email"), blank=True)
    company_contact_function = models.CharField(
        _("company contact function"), max_length=100, blank=True
    )
    company_contact_phone = models.CharField(
        _("company contact phone"), max_length=100, blank=True
    )
    work_location = models.CharField(_("work location"), max_length=100, blank=True)

    default_group = models.ForeignKey(
        "Group",
        on_delete=models.SET_NULL,
        verbose_name=_("default group"),
        blank=True,
        null=True,
        related_name="+",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = _("scope statement")
        verbose_name_plural = _("scope statements")

    def __str__(self):
        return f"{self.name} ({self.eis_no})"

    @property
    def company_contact_location(self):
        return (f"{self.company_zip_code} {self.company_city}").strip()


class DrudgeQuota(models.Model):
    scope_statement = models.ForeignKey(
        ScopeStatement, on_delete=models.CASCADE, verbose_name=_("scope statement")
    )
    week = models.DateField(_("week"))
    quota = models.PositiveIntegerField(_("quota"))

    class Meta:
        unique_together = [("scope_statement", "week")]
        verbose_name = _("drudge quota")
        verbose_name_plural = _("drudge quotas")

    def __str__(self):
        from zivinetz.views.scheduling import calendar_week

        year, week = calendar_week(self.week)
        return f"{self.scope_statement.name}: {self.quota} Zivis in KW{week} {year}"


class Choices:
    def __init__(self, choices):
        self.kwargs = {"max_length": 20, "choices": choices, "default": choices[0][0]}
        for key, value in choices:
            setattr(self, key, key)


@model_resource_urls()
class Specification(models.Model):
    ACCOMODATION = Choices((
        ("provided", _("provided")),
        ("compensated", _("compensated")),
    ))

    MEAL = Choices((
        ("no_compensation", _("no compensation")),
        ("at_accomodation", _("at accomodation")),
        ("external", _("external")),
    ))

    CLOTHING = Choices((("provided", _("provided")), ("compensated", _("compensated"))))

    scope_statement = models.ForeignKey(
        ScopeStatement,
        on_delete=models.CASCADE,
        verbose_name=_("scope statement"),
        related_name="specifications",
    )

    with_accomodation = models.BooleanField(_("with accomodation"), default=False)
    code = models.CharField(
        _("code"),
        max_length=10,
        help_text=_("Short, unique code identifying this specification."),
    )

    accomodation_working = models.CharField(
        _("accomodation on working days"), **ACCOMODATION.kwargs
    )
    breakfast_working = models.CharField(_("breakfast on working days"), **MEAL.kwargs)
    lunch_working = models.CharField(_("lunch on working days"), **MEAL.kwargs)
    supper_working = models.CharField(_("supper on working days"), **MEAL.kwargs)

    accomodation_sick = models.CharField(
        _("accomodation on sick days"), **ACCOMODATION.kwargs
    )
    breakfast_sick = models.CharField(_("breakfast on sick days"), **MEAL.kwargs)
    lunch_sick = models.CharField(_("lunch on sick days"), **MEAL.kwargs)
    supper_sick = models.CharField(_("supper on sick days"), **MEAL.kwargs)

    accomodation_free = models.CharField(
        _("accomodation on free days"), **ACCOMODATION.kwargs
    )
    breakfast_free = models.CharField(_("breakfast on free days"), **MEAL.kwargs)
    lunch_free = models.CharField(_("lunch on free days"), **MEAL.kwargs)
    supper_free = models.CharField(_("supper on free days"), **MEAL.kwargs)

    clothing = models.CharField(_("clothing"), **CLOTHING.kwargs)

    accomodation_throughout = models.BooleanField(
        _("accomodation throughout"),
        help_text=_("Accomodation is offered throughout."),
        default=False,
    )
    food_throughout = models.BooleanField(
        _("food throughout"), help_text=_("Food is offered throughout."), default=False
    )

    conditions = models.FileField(_("conditions"), upload_to="conditions", blank=True)

    ordering = models.IntegerField(_("ordering"), default=0)

    class Meta:
        ordering = ["ordering", "scope_statement", "with_accomodation"]
        unique_together = (("scope_statement", "with_accomodation"),)
        verbose_name = _("specification")
        verbose_name_plural = _("specifications")

    def __str__(self):
        return "{} - {}".format(
            self.scope_statement,
            (
                self.with_accomodation
                and gettext("with accomodation")
                or gettext("without accomodation")
            ),
        )

    def compensation(self, for_date=date.today):
        cset = CompensationSet.objects.for_date(for_date)

        # The spending_money default is only valid from 2023-01-01
        compensation = {"spending_money": Decimal("7.50")}

        for day_type in ("working", "sick", "free"):
            key = "accomodation_%s" % day_type
            value = getattr(self, key)

            if value == self.ACCOMODATION.provided:
                compensation[key] = Decimal("0.00")
            else:
                compensation[key] = cset.accomodation_home

            for meal in ("breakfast", "lunch", "supper"):
                key = f"{meal}_{day_type}"
                value = getattr(self, key)

                if value == self.MEAL.no_compensation:
                    compensation[key] = Decimal("0.00")
                else:
                    compensation[key] = getattr(cset, f"{meal}_{value}")

        if self.clothing == self.CLOTHING.provided:
            compensation.update({
                "clothing": Decimal("0.00"),
                "clothing_limit_per_assignment": Decimal("0.00"),
            })
        else:
            compensation.update({
                "clothing": cset.clothing,
                "clothing_limit_per_assignment": cset.clothing_limit_per_assignment,
            })

        return compensation


class CompensationSetManager(models.Manager):
    def for_date(self, for_date=date.today):
        if callable(for_date):
            for_date = for_date()

        try:
            return self.filter(valid_from__lte=for_date).order_by("-valid_from")[0]
        except IndexError:
            raise self.model.DoesNotExist


@model_resource_urls()
class CompensationSet(models.Model):
    valid_from = models.DateField(_("valid from"), unique=True)

    breakfast_at_accomodation = models.DecimalField(
        _("breakfast at accomodation"), max_digits=10, decimal_places=2
    )
    lunch_at_accomodation = models.DecimalField(
        _("lunch at accomodation"), max_digits=10, decimal_places=2
    )
    supper_at_accomodation = models.DecimalField(
        _("supper at accomodation"), max_digits=10, decimal_places=2
    )

    breakfast_external = models.DecimalField(
        _("external breakfast"), max_digits=10, decimal_places=2
    )
    lunch_external = models.DecimalField(
        _("external lunch"), max_digits=10, decimal_places=2
    )
    supper_external = models.DecimalField(
        _("external supper"), max_digits=10, decimal_places=2
    )

    accomodation_home = models.DecimalField(
        _("accomodation"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Daily compensation if drudge returns home for the night."),
    )

    private_transport_per_km = models.DecimalField(
        _("private transport per km"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Only applies if public transport use is not reasonable."),
    )

    clothing = models.DecimalField(
        _("clothing"),
        max_digits=10,
        decimal_places=6,
        help_text=_(
            "Daily compensation for clothes if clothing isn't offered by the company."
        ),
    )
    clothing_limit_per_assignment = models.DecimalField(
        _("clothing limit per assignment"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Maximal compensation for clothing per assignment."),
    )

    class Meta:
        ordering = ["-valid_from"]
        verbose_name = _("compensation set")
        verbose_name_plural = _("compensation sets")

    objects = CompensationSetManager()

    def __str__(self):
        return gettext("compensation set, valid from %s") % self.valid_from


@model_resource_urls(default="edit")
class RegionalOffice(models.Model):
    name = models.CharField(_("name"), max_length=100)
    city = models.CharField(_("city"), max_length=100)
    address = models.TextField(_("address"), blank=True)
    code = models.CharField(
        _("code"), max_length=10, help_text=_("Short, unique identifier.")
    )
    phone = models.CharField(_("phone"), max_length=20, blank=True)
    fax = models.CharField(_("fax"), max_length=20, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("regional office")
        verbose_name_plural = _("regional offices")

    def __str__(self):
        return self.name


class DrudgeManager(SearchManager):
    search_fields = (
        "user__first_name",
        "user__last_name",
        "zdp_no",
        "address",
        "zip_code",
        "city",
        "place_of_citizenship_city",
        "place_of_citizenship_state",
        "phone_home",
        "phone_office",
        "mobile",
        "bank_account",
        "health_insurance_account",
        "health_insurance_company",
        "education_occupation",
    )

    def active_set(self, access, additional_ids=None):  # pragma: no cover
        q = Q(id=0)
        if additional_ids:
            q |= Q(id__in=additional_ids)
        return self.filter(q).select_related("user")


@model_resource_urls()
class Drudge(models.Model):
    STATES = [state[0] for state in STATE_CHOICES]
    STATE_CHOICES = zip(STATES, STATES)

    MOTOR_SAW_COURSE_CHOICES = (
        ("2-day", _("2 day course")),
        ("5-day", _("5 day course")),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    zdp_no = models.CharField(_("ZDP No."), unique=True, max_length=10)

    address = models.TextField(_("address"))
    zip_code = models.CharField(_("ZIP code"), max_length=10)
    city = models.CharField(_("city"), max_length=100)

    date_of_birth = models.DateField(_("date of birth"))

    place_of_citizenship_city = models.CharField(
        _("place of citizenship"), max_length=100
    )
    place_of_citizenship_state = models.CharField(
        _("place of citizenship (canton)"), max_length=2, choices=STATE_CHOICES
    )

    phone_home = models.CharField(_("phone (home)"), max_length=20, blank=True)
    phone_office = models.CharField(_("phone (office)"), max_length=20, blank=True)
    mobile = models.CharField(_("mobile"), max_length=20, blank=True)

    bank_account = models.CharField(
        _("bank account"), max_length=100, help_text=_("Enter your IBAN.")
    )

    health_insurance_company = models.CharField(
        _("health insurance company"), max_length=100, blank=True
    )
    health_insurance_account = models.CharField(
        _("health insurance account"), max_length=100, blank=True
    )

    education_occupation = models.TextField(_("education / occupation"), blank=True)

    driving_license = models.BooleanField(_("driving license"), default=False)
    general_abonnement = models.BooleanField(_("general abonnement"), default=False)
    half_fare_card = models.BooleanField(_("half-fare card"), default=False)
    other_card = models.CharField(_("other card"), max_length=100, blank=True)
    youth_association = models.CharField(
        _("youth association"),
        max_length=100,
        blank=True,
        choices=[
            ("Pfadi", _("Pfadi")),
            ("Cevi", _("Cevi")),
            ("Jubla", _("Jubla")),
            ("Anderer", _("Anderer")),
            ("Keiner", _("Keiner")),
        ],
    )
    source = models.CharField(
        "Wie hast du vom Naturnetz erfahren?",
        max_length=100,
        blank=True,
        choices=[
            (choice, choice)
            for choice in [
                "Social Media",
                "Freunde/Familie/Bekannte",
                "Internetsuche",
                "E-Zivi",
                "Plakat/Flyer",
                "Fahrzeug oder Einsatzgruppe gesehen",
            ]
        ],
    )

    environment_course = models.BooleanField(
        _("environment course"),
        default=False,
        help_text=_("I have taken the environment course already."),
    )
    motor_saw_course = models.CharField(
        _("motor saw course"),
        max_length=10,
        choices=MOTOR_SAW_COURSE_CHOICES,
        blank=True,
        null=True,
        help_text=_("I have taken the denoted motor saw course already."),
    )

    regional_office = models.ForeignKey(
        RegionalOffice, verbose_name=_("regional office"), on_delete=models.CASCADE
    )
    notes = models.TextField(
        _("notes"),
        blank=True,
        help_text=_("Allergies, anything else we should be aware of?"),
    )
    internal_notes = models.TextField(
        _("internal notes"),
        blank=True,
        help_text=_("This field is not visible to drudges."),
    )

    profile_image = models.ImageField(
        _("profile image"), blank=True, null=True, upload_to="profile_images/"
    )

    class Meta:
        ordering = ["user__last_name", "user__first_name", "zdp_no"]
        verbose_name = _("drudge")
        verbose_name_plural = _("drudges")

    objects = DrudgeManager()

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.zdp_no})"

    def pretty_motor_saw_course(self):
        """for the scheduling table"""
        msw = self.motor_saw_course or ""
        return msw.replace("-day", "T")


class AssignmentManager(SearchManager):
    search_fields = ["specification__scope_statement__name", "specification__code"] + [
        "drudge__%s" % f for f in DrudgeManager.search_fields
    ]

    def for_date(self, day=None):
        day = day if day else date.today()

        return self.filter(
            Q(date_from__lte=day)
            & (
                Q(date_until__gte=day)
                | Q(date_until_extension__isnull=False, date_until_extension__gte=day)
            )
        )

    def active_set(self, access, additional_ids=None):  # pragma: no cover
        q = Q(id__in=self.for_date())
        if additional_ids:
            q |= Q(id__in=additional_ids)
        return self.filter(q).select_related("specification", "drudge__user")


@model_resource_urls()
class Assignment(models.Model):
    TENTATIVE = 10
    ARRANGED = 20
    MOBILIZED = 30
    DECLINED = 40

    STATUS_CHOICES = (
        (TENTATIVE, _("tentative")),
        (ARRANGED, _("arranged")),
        (MOBILIZED, _("mobilized")),
        (DECLINED, _("declined")),
    )

    created = models.DateTimeField(_("created"), default=timezone.now)
    modified = models.DateTimeField(_("modified"), auto_now=True)

    specification = models.ForeignKey(
        Specification, verbose_name=_("specification"), on_delete=models.CASCADE
    )
    drudge = models.ForeignKey(
        Drudge,
        verbose_name=_("drudge"),
        related_name="assignments",
        on_delete=models.CASCADE,
    )
    regional_office = models.ForeignKey(
        RegionalOffice, verbose_name=_("regional office"), on_delete=models.CASCADE
    )

    date_from = models.DateField(_("date from"))
    date_until = models.DateField(_("date until"))
    date_until_extension = models.DateField(
        _("date until (extended)"),
        blank=True,
        null=True,
        help_text=_("Only fill out if assignment has been extended."),
    )

    available_holi_days = models.PositiveIntegerField(
        _("available holiday days"), blank=True, null=True
    )
    part_of_long_assignment = models.BooleanField(
        _("part of long assignment"), default=False
    )

    status = models.IntegerField(_("status"), choices=STATUS_CHOICES, default=TENTATIVE)

    arranged_on = models.DateField(_("arranged on"), blank=True, null=True)
    mobilized_on = models.DateField(_("mobilized on"), blank=True, null=True)

    environment_course_date = models.DateField(
        _("environment course starting date"), blank=True, null=True
    )
    motor_saw_course_date = models.DateField(
        _("motor saw course starting date"), blank=True, null=True
    )

    class Meta:
        ordering = ["-date_from", "-date_until"]
        verbose_name = _("assignment")
        verbose_name_plural = _("assignments")

    objects = AssignmentManager()

    def __str__(self):
        return f"{self.drudge} on {self.specification.code} ({self.date_from} - {self.determine_date_until()})"

    def determine_date_until(self):
        return self.date_until_extension or self.date_until

    determine_date_until.short_description = _("eff. until date")

    def assignment_days(self):
        day = self.date_from
        until = self.determine_date_until()
        one_day = timedelta(days=1)

        public_holidays = PublicHoliday.objects.filter(
            date__range=(day, until)
        ).values_list("date", flat=True)
        company_holidays = self.specification.scope_statement.company_holidays
        company_holidays = list(
            company_holidays.filter(date_from__lte=until, date_until__gte=day)
        )

        vacation_days = 0
        # +1 because the range is inclusive
        assignment_days = (self.date_until - self.date_from).days + 1

        if assignment_days >= 180:
            # 30 days isn't exactly one month. But that's good enough for us.
            # We grant 2 additional vacation days per 30 full days only
            # (see ZDV Art. 72)
            vacation_days = 8 + int((assignment_days - 180) / 30) * 2

        days = {
            "assignment_days": assignment_days,
            "vacation_days": vacation_days,
            "company_holidays": 0,
            "public_holidays_during_company_holidays": 0,
            "public_holidays_outside_company_holidays": 0,
            "vacation_days_during_company_holidays": 0,
            "freely_definable_vacation_days": vacation_days,
            "working_days": 0,
            "countable_days": 0,
            # days which aren't countable and are forced upon the drudge:
            "forced_leave_days": 0,
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
            slot = "free"

            if is_company_holiday:
                days["company_holidays"] += 1

                if is_public_holiday:
                    # At least we have public holidays too.
                    days["public_holidays_during_company_holidays"] += 1
                    days["countable_days"] += 1
                else:
                    if is_weekend:
                        # We were lucky once again.
                        days["countable_days"] += 1
                    else:
                        # Oh no, company holiday and neither public holiday nor
                        # weekend. Now the draconian regime of the swiss
                        # administration comes to full power.

                        if days["freely_definable_vacation_days"]:
                            # Vacations need to be taken during public holidays
                            # if possible at all. Unfortunately for drudges.
                            days["freely_definable_vacation_days"] -= 1
                            days["vacation_days_during_company_holidays"] += 1
                            slot = "holi"

                            # At least they are countable towards assignment
                            # total.
                            days["countable_days"] += 1
                        else:
                            # Damn. No vacation days left (if there were any in
                            # the beginning. The drudge has to pause his
                            # assignment for this time.
                            days["forced_leave_days"] += 1
                            slot = "forced"

            else:
                # No company holiday... business as usual, maybe.
                days["countable_days"] += 1  # Nice!

                if not (is_public_holiday or is_weekend):
                    # Hard beer-drinking and pickaxing action.
                    days["working_days"] += 1
                    slot = "working"

            key = (day.year, day.month, 1)
            if day.month == self.date_from.month and day.year == self.date_from.year:
                key = (self.date_from.year, self.date_from.month, self.date_from.day)

            if day > self.date_until:
                # Only the case when assignment has been extended
                # If we are in the same month as the original end of the
                # assignment, create a new key for the extension part of
                # the given month only
                if (
                    day.month == self.date_until.month
                    and day.year == self.date_until.year
                ):
                    extended_start = self.date_until + one_day
                    key = (
                        extended_start.year,
                        extended_start.month,
                        extended_start.day,
                    )

            monthly_expense_days.setdefault(
                key, {"free": 0, "working": 0, "holi": 0, "forced": 0, "start": day}
            )
            monthly_expense_days[key][slot] += 1
            monthly_expense_days[key]["end"] = day

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

        clothing_total = None
        expenses = {}

        for month, days in monthly_expense_days:
            compensation = specification.compensation(
                date(month[0], month[1], month[2])
            )

            free = days["free"]
            working = days["working"]

            total = free + working

            expenses[month] = {
                "spending_money": total * compensation["spending_money"],
                "clothing": total * compensation["clothing"],
                "accomodation": (
                    free * compensation["accomodation_free"]
                    + working * compensation["accomodation_working"]
                ),
                "food": free
                * (
                    compensation["breakfast_free"]
                    + compensation["lunch_free"]
                    + compensation["supper_free"]
                )
                + working
                * (
                    compensation["breakfast_working"]
                    + compensation["lunch_working"]
                    + compensation["supper_working"]
                ),
            }

            if clothing_total is None:
                clothing_total = compensation["clothing_limit_per_assignment"]

            clothing_total -= expenses[month]["clothing"]

            if clothing_total < 0:
                expenses[month]["clothing"] += clothing_total
                clothing_total = 0

        return assignment_days, monthly_expense_days, expenses

    def pdf_url(self):
        return reverse("zivinetz_assignment_pdf", args=(self.pk,))

    def admin_pdf_url(self):
        return '<a href="%s">PDF</a>' % self.pdf_url()

    admin_pdf_url.allow_tags = True
    admin_pdf_url.short_description = "PDF"

    def generate_expensereports(self):
        occupied_months = [
            (d.year, d.month, d.day)
            for d in self.reports.values_list("date_from", flat=True)
        ]

        days, monthly_expense_days, expenses = self.expenses()

        created = 0
        for month, data in monthly_expense_days:
            if month in occupied_months:
                continue

            try:
                clothing_expenses = expenses[month]["clothing"]
            except KeyError:
                clothing_expenses = 0

            report = self.reports.create(
                date_from=data["start"],
                date_until=data["end"],
                working_days=data["working"],
                free_days=data["free"],
                sick_days=0,
                holi_days=data["holi"],
                forced_leave_days=data["forced"],
                calculated_total_days=sum(
                    (data["working"], data["free"], data["holi"], data["forced"]), 0
                ),
                clothing_expenses=clothing_expenses,
                specification=self.specification,
            )

            report.recalculate_total()

            created += 1

        return created


@model_resource_urls()
class AssignmentChange(models.Model):
    created = models.DateTimeField(_("created"), default=timezone.now)
    assignment = models.ForeignKey(
        Assignment,
        verbose_name=_("assignment"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    assignment_description = models.CharField(
        _("assignment description"), max_length=200
    )
    changed_by = models.CharField(_("changed by"), max_length=100, default="nobody")
    changes = models.TextField(_("changes"), blank=True)

    class Meta:
        ordering = ["created"]
        verbose_name = _("assignment change")
        verbose_name_plural = _("assignment changes")

    def __str__(self):
        return self.assignment_description


def get_request():
    """Walk up the stack, return the nearest first argument named "request"."""
    import inspect

    frame = None
    try:
        for f in inspect.stack()[1:]:
            frame = f[0]
            code = frame.f_code
            if code.co_varnames[:1] == ("request",):
                return frame.f_locals["request"]
            if code.co_varnames[:2] == ("self", "request"):
                return frame.f_locals["request"]
    finally:
        del frame


@receiver(signals.pre_save, sender=Assignment)
def assignment_pre_save(sender, instance, **kwargs):
    try:
        original = Assignment.objects.get(pk=instance.pk)
    except (AttributeError, Assignment.DoesNotExist):
        original = None

    changes = []
    if not original:
        changes.append(gettext("Assignment has been created."))
    else:
        change_tracked_fields = [
            "specification",
            "drudge",
            "date_from",
            "date_until",
            "date_until_extension",
            "status",
            "arranged_on",
            "mobilized_on",
            "environment_course_date",
            "motor_saw_course_date",
        ]

        def nicify(instance, field):
            if hasattr(instance, "get_%s_display" % field):
                return getattr(instance, "get_%s_display" % field)()
            return getattr(instance, field) or "-"

        for field in change_tracked_fields:
            if getattr(original, field) == getattr(instance, field):
                continue

            field_instance = Assignment._meta.get_field(field)
            changes.append(
                gettext(
                    "The value of `%(field)s` has been changed from %(from)s to %(to)s."
                )
                % {
                    "field": field_instance.verbose_name,
                    "from": nicify(original, field),
                    "to": nicify(instance, field),
                }
            )

    request = get_request()

    instance._assignment_change = dict(
        assignment=instance,
        assignment_description="%s" % instance,
        changed_by=request.user.get_full_name() if request else "unknown",
        changes="\n".join(changes),
    )


@receiver(signals.post_save, sender=Assignment)
def assignment_post_save(sender, instance, **kwargs):
    if getattr(instance, "_assignment_change", None):
        AssignmentChange.objects.create(**instance._assignment_change)


@receiver(signals.post_delete, sender=Assignment)
def assignment_post_delete(sender, instance, **kwargs):
    request = get_request()

    AssignmentChange.objects.create(
        assignment=None,
        assignment_description="%s" % instance,
        changed_by=request.user.get_full_name() if request else "unknown",
        changes=gettext("Assignment has been deleted."),
    )


class ExpenseReportManager(SearchManager):
    search_fields = [
        "report_no",
        "working_days_notes",
        "free_days_notes",
        "sick_days_notes",
        "holi_days_notes",
        "forced_leave_days_notes",
        "clothing_expenses_notes",
        "transport_expenses_notes",
        "miscellaneous_notes",
    ] + ["assignment__%s" % f for f in AssignmentManager.search_fields]


@model_resource_urls()
class ExpenseReport(models.Model):
    PENDING = 10
    FILLED = 20
    PAID = 30

    STATUS_CHOICES = ((PENDING, _("pending")), (FILLED, _("filled")), (PAID, _("paid")))

    assignment = models.ForeignKey(
        Assignment,
        verbose_name=_("assignment"),
        related_name="reports",
        on_delete=models.CASCADE,
    )
    date_from = models.DateField(_("date from"))
    date_until = models.DateField(_("date until"))
    report_no = models.CharField(_("report no."), max_length=10, blank=True)

    status = models.IntegerField(_("status"), choices=STATUS_CHOICES, default=PENDING)

    working_days = models.PositiveIntegerField(_("working days"))
    working_days_notes = models.CharField(_("notes"), max_length=100, blank=True)
    free_days = models.PositiveIntegerField(_("free days"))
    free_days_notes = models.CharField(_("notes"), max_length=100, blank=True)
    sick_days = models.PositiveIntegerField(_("sick days"))
    sick_days_notes = models.CharField(_("notes"), max_length=100, blank=True)
    holi_days = models.PositiveIntegerField(
        _("holiday days"),
        help_text=_(
            "These days are still countable towards the assignment total days."
        ),
    )
    holi_days_notes = models.CharField(_("notes"), max_length=100, blank=True)
    forced_leave_days = models.PositiveIntegerField(_("forced leave days"))
    forced_leave_days_notes = models.CharField(_("notes"), max_length=100, blank=True)

    calculated_total_days = models.PositiveIntegerField(
        _("calculated total days"),
        help_text=_(
            "This field is filled in automatically by the system"
            " and should not be changed."
        ),
        default=0,
    )

    clothing_expenses = models.DecimalField(
        _("clothing expenses"), max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    clothing_expenses_notes = models.CharField(_("notes"), max_length=100, blank=True)
    transport_expenses = models.DecimalField(
        _("transport expenses"),
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    transport_expenses_notes = models.CharField(_("notes"), max_length=100, blank=True)

    miscellaneous = models.DecimalField(
        _("miscellaneous"), max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    miscellaneous_notes = models.CharField(_("notes"), max_length=100, blank=True)

    total = models.DecimalField(_("total"), max_digits=10, decimal_places=2, default=0)

    specification = models.ForeignKey(
        Specification, verbose_name=_("specification"), on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["assignment__drudge", "date_from"]
        verbose_name = _("expense report")
        verbose_name_plural = _("expense reports")

    objects = ExpenseReportManager()

    def __str__(self):
        return f"{self.date_from} - {self.date_until}"

    @property
    def total_days(self):
        return (
            self.working_days
            + self.free_days
            + self.sick_days
            + self.holi_days
            + self.forced_leave_days
        )

    def pdf_url(self):
        return reverse("zivinetz_expensereport_pdf", args=(self.pk,))

    def recalculate_total(self, save=True):
        _n1, _n2, self.total = self.compensations()
        if save:
            self.save()

    def compensation_data(self, arranged_on=None):
        arranged_on = arranged_on or self.assignment.arranged_on
        if not arranged_on:
            return None

        return self.specification.compensation(arranged_on) | {
            "spending_money": Decimal("5.00")
            if self.date_from < date(2023, 1, 1)
            else Decimal("7.50")
        }

    def compensations(self):
        if not self.assignment.arranged_on:
            # Make recalculate_total not fall flat on its face
            return None, None, 0

        compensation = self.compensation_data()

        # spending_money, accomodation, breakfast, lunch, supper, total

        def line(title, day_type, days):
            line = [
                compensation["spending_money"],
                compensation["accomodation_%s" % day_type],
                compensation["breakfast_%s" % day_type],
                compensation["lunch_%s" % day_type],
                compensation["supper_%s" % day_type],
            ]

            return [f"{days} {title}"] + line + [sum(line) * days]

        ret = [
            [
                "",
                gettext("spending money"),
                gettext("accomodation"),
                gettext("breakfast"),
                gettext("lunch"),
                gettext("supper"),
                gettext("Total"),
            ]
        ]

        ret.append(line(gettext("working days"), "working", self.working_days))
        ret.append([self.working_days_notes, "", "", "", "", "", ""])
        ret.append(line(gettext("free days"), "free", self.free_days))
        ret.append([self.free_days_notes, "", "", "", "", "", ""])
        ret.append(line(gettext("sick days"), "sick", self.sick_days))
        ret.append([self.sick_days_notes, "", "", "", "", "", ""])

        # holiday counts as work
        ret.append(line(gettext("holiday days"), "free", self.holi_days))
        ret.append([self.holi_days_notes, "", "", "", "", "", ""])

        # forced leave counts zero
        ret.append(
            ["{} {}".format(self.forced_leave_days, gettext("forced leave days"))]
            + [Decimal("0.00")] * 6
        )
        ret.append([self.forced_leave_days_notes, "", "", "", "", "", ""])

        additional = [
            (gettext("transport expenses"), self.transport_expenses),
            (self.transport_expenses_notes, ""),
            (gettext("clothing expenses"), self.clothing_expenses),
            (self.clothing_expenses_notes, ""),
            (gettext("miscellaneous"), self.miscellaneous),
            (self.miscellaneous_notes, ""),
        ]

        total = sum(r[6] for r in ret[1::2] if r) + sum(r[1] for r in additional[::2])

        return ret, additional, total


@model_resource_urls()
class PublicHoliday(models.Model):
    name = models.CharField(_("name"), max_length=100)
    date = models.DateField(_("date"), unique=True)

    class Meta:
        ordering = ["date"]
        verbose_name = _("public holiday")
        verbose_name_plural = _("public holidays")

    def __str__(self):
        return f"{self.name} ({self.date})"


@model_resource_urls()
class CompanyHoliday(models.Model):
    date_from = models.DateField(_("date from"))
    date_until = models.DateField(_("date until"))
    applies_to = models.ManyToManyField(
        ScopeStatement,
        blank=False,
        verbose_name=_("applies to scope statements"),
        related_name="company_holidays",
    )

    class Meta:
        ordering = ["date_from"]
        verbose_name = _("company holiday")
        verbose_name_plural = _("company holidays")

    def __str__(self):
        return f"{self.date_from} - {self.date_until}"

    def is_contained(self, day):
        return self.date_from <= day <= self.date_until


@model_resource_urls(default="edit")
class Assessment(models.Model):
    created = models.DateTimeField(_("created"), default=timezone.now)
    created_by = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("created by"),
    )
    drudge = models.ForeignKey(
        Drudge,
        verbose_name=_("drudge"),
        related_name="assessments",
        on_delete=models.CASCADE,
    )
    assignment = models.ForeignKey(
        Assignment,
        verbose_name=_("assignment"),
        related_name="assessments",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    mark = models.IntegerField(
        _("mark"), choices=zip(range(1, 7), range(1, 7)), blank=True, null=True
    )

    comment = models.TextField(_("comment"), blank=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = _("internal assessment")
        verbose_name_plural = _("internal assessments")

    def __str__(self):
        return gettext("Mark %(mark)s for %(drudge)s") % {
            "mark": self.mark or "-",
            "drudge": self.drudge,
        }


class CodewordManager(models.Manager):
    def word(self, key):
        try:
            return self.filter(key=key).latest().codeword
        except self.model.DoesNotExist:
            return ""


@model_resource_urls()
class Codeword(models.Model):
    created = models.DateTimeField(_("created"), default=timezone.now)
    key = models.CharField(_("key"), max_length=10, db_index=True)
    codeword = models.CharField(_("codeword"), max_length=20)

    class Meta:
        get_latest_by = "created"
        ordering = ["-created"]
        verbose_name = _("codeword")
        verbose_name_plural = _("codewords")

    objects = CodewordManager()

    def __str__(self):
        return self.codeword


@model_resource_urls()
class JobReferenceTemplate(models.Model):
    title = models.CharField(_("title"), max_length=100)
    text = models.TextField(_("text"))

    class Meta:
        ordering = ["title"]
        verbose_name = _("job reference template")
        verbose_name_plural = _("job reference templates")

    def __str__(self):
        return self.title


class JobReferenceManager(SearchManager):
    search_fields = ["text"] + [
        "assignment__%s" % f for f in AssignmentManager.search_fields
    ]


class JobReferenceAuthor(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        limit_choices_to={"is_staff": True},
    )
    location = models.CharField(_("location"), max_length=100)
    full_name = models.CharField(_("full name"), max_length=100)
    function = models.CharField(_("function"), max_length=100)

    class Meta:
        ordering = ["full_name"]
        verbose_name = _("job reference author")
        verbose_name_plural = _("job reference authors")

    def __str__(self):
        return f"{self.full_name}, {self.function}, {self.location}"


@model_resource_urls()
class JobReference(models.Model):
    assignment = models.ForeignKey(
        Assignment,
        verbose_name=_("assignment"),
        related_name="jobreferences",
        on_delete=models.CASCADE,
    )
    created = models.DateField(_("created"))
    text = models.TextField(_("text"))

    author_location = models.CharField(_("location"), max_length=100)
    author_full_name = models.CharField(_("full name"), max_length=100)
    author_function = models.CharField(_("function"), max_length=100)

    class Meta:
        ordering = ["-created"]
        verbose_name = _("job reference")
        verbose_name_plural = _("job references")

    objects = JobReferenceManager()

    def __str__(self):
        return f"{self._meta.verbose_name}: {self.assignment}"

    def pdf_url(self):
        return reverse("zivinetz_reference_pdf", args=(self.pk,))


class GroupQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


@model_resource_urls()
class Group(models.Model):
    is_active = models.BooleanField(_("is active"), default=True)
    name = models.CharField(_("name"), max_length=100)
    ordering = models.IntegerField(_("ordering"), default=0)

    objects = GroupQuerySet.as_manager()

    class Meta:
        ordering = ["ordering"]
        verbose_name = _("group")
        verbose_name_plural = _("groups")

    def __str__(self):
        return self.name


class GroupAssignmentQuerySet(models.QuerySet):
    def monday(self, day):
        return day - timedelta(days=day.weekday())

    def for_date(self, day):
        return self.filter(week=self.monday(day))


class GroupAssignment(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="group_assignments",
        verbose_name=_("group"),
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="group_assignments",
        verbose_name=_("assignment"),
    )
    week = models.DateField(_("week"))

    objects = GroupAssignmentQuerySet.as_manager()

    class Meta:
        unique_together = (("assignment", "week"),)
        verbose_name = _("group assignment")
        verbose_name_plural = _("group assignments")

    def __str__(self):
        return "{}/{}: {}".format(
            self.group,
            self.assignment,
            " - ".join(d.strftime("%d.%m.%Y") for d in self.date_range),
        )

    def save(self, *args, **kwargs):
        self.week = self.week - timedelta(days=self.week.weekday())
        super().save(*args, **kwargs)

    save.alters_data = True

    @property
    def date_range(self):
        return (self.week, self.week + timedelta(days=4))


class AbsenceManager(SearchManager):
    search_fields = (
        "assignment__drudge__user__first_name",
        "assignment__drudge__user__last_name",
        "internal_notes",
    )

    def for_expense_report(self, report):
        candidate_days = [
            report.date_from + timedelta(days=i)
            for i in range((report.date_until - report.date_from).days)
        ]

        days = defaultdict(int)
        reasons = defaultdict(list)

        for absence in self.filter(
            assignment_id=report.assignment_id, days__overlap=candidate_days
        ):
            in_range = [day for day in sorted(absence.days) if day in candidate_days]
            field = absence.REASON_TO_EXPENSE_REPORT[absence.reason]
            days[field] += len(in_range)
            parts = [absence.get_reason_display()]
            if absence.internal_notes:
                parts.append(" (%s)" % absence.internal_notes)
            parts.append(": ")
            parts.append(", ".join(day.strftime("%a %d.%m.%y") for day in in_range))
            reasons["%s_notes" % field].append("".join(parts))

        return {
            **days,
            **{field: "\n".join(reason) for field, reason in reasons.items()},
        }


@model_resource_urls()
class Absence(models.Model):
    APPROVED_VACATION = "approved-vacation"
    APPROVED_HOLIDAY = "approved-holiday"
    SICK = "sick"
    MOTOR_SAW_COURSE = "motor-saw-course"
    ENVIRONMENT_COURSE = "environment-course"
    ABSENTEEISM = "absenteeism"
    MISSED_WORKING_HOURS = "missed-working-hours"

    REASON_CHOICES = (
        (APPROVED_VACATION, _("approved vacation")),
        (APPROVED_HOLIDAY, _("approved holiday")),
        (SICK, _("sick")),
        (MOTOR_SAW_COURSE, _("motor saw course")),
        (ENVIRONMENT_COURSE, _("environment course")),
        (ABSENTEEISM, _("absenteeism")),
        (MISSED_WORKING_HOURS, _("missed working hours")),
    )

    REASON_TO_EXPENSE_REPORT = {
        APPROVED_VACATION: "forced_leave_days",
        APPROVED_HOLIDAY: "holi_days",
        SICK: "sick_days",
        MOTOR_SAW_COURSE: "working_days",
        ENVIRONMENT_COURSE: "working_days",
        ABSENTEEISM: "forced_leave_days",
        MISSED_WORKING_HOURS: "sick_days",
    }

    PRETTY_REASON = {
        APPROVED_VACATION: "Urlaub",
        APPROVED_HOLIDAY: "Ferien",
        SICK: "Krank",
        MOTOR_SAW_COURSE: "MSK",
        ENVIRONMENT_COURSE: "UNA",
        ABSENTEEISM: "Unentschuldigt",
        MISSED_WORKING_HOURS: "Verpasst",
    }

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="absences",
        verbose_name=_("assignment"),
    )
    created_at = models.DateTimeField(_("created at"), default=timezone.now)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name=_("created by")
    )
    reason = models.CharField(_("reason"), max_length=20, choices=REASON_CHOICES)
    internal_notes = models.TextField(_("internal notes"), blank=True)
    days = ArrayField(models.DateField(), verbose_name=_("days"))

    objects = AbsenceManager()

    class Meta:
        ordering = ["-days"]
        verbose_name = _("absence")
        verbose_name_plural = _("absences")

    def __str__(self):
        return f"Absenz von {self.assignment.drudge.user.get_full_name()} von {min(self.days)} bis {max(self.days)}"

    def pretty_days(self):
        return ", ".join(day.strftime("%a %d.%m.%y") for day in sorted(self.days))

    def pretty_reason(self):
        try:
            return self.PRETTY_REASON[self.reason]
        except KeyError:
            return self.get_reason_display()

    def clean(self):
        if not self.days:
            return

        outside = [
            day
            for day in self.days
            if day < self.assignment.date_from
            or day > self.assignment.determine_date_until()
        ]
        if outside:
            raise ValidationError(
                _("Absence days outside duration of assignment: %s")
                % (", ".join(str(day) for day in sorted(outside)))
            )

        if self.reason == self.APPROVED_HOLIDAY:
            if self.assignment.available_holi_days is None:
                raise ValidationError(
                    _("Define available holiday days on assignment first.")
                )

            already = sum(
                (
                    len(a.days)
                    for a in self.assignment.absences.filter(
                        Q(reason=self.APPROVED_HOLIDAY), ~Q(pk=self.pk)
                    )
                ),
                0,
            )

            if already + len(self.days) > self.assignment.available_holi_days:
                raise ValidationError(
                    _("Not enough holiday days available. Only %s remaining.")
                    % (self.assignment.available_holi_days - already)
                )

        overlapping = self.assignment.absences.filter(
            Q(days__overlap=self.days), ~Q(pk=self.pk)
        ).select_related("assignment__drudge__user")
        if overlapping:
            raise ValidationError(
                _("Overlapping absences are not allowed, days already occupied by %s.")
                % (", ".join(str(o) for o in overlapping))
            )


class UserProfile(models.Model):
    USER_TYPE_CHOICES = (
        ("drudge", _("Drudge")),
        ("squad_leader", _("Squad Leader")),
        ("user_plus", _("User Plus")),
        ("admin", _("Admin")),
        ("dev_admin", _("DEV-Admin")),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(
        max_length=20, choices=USER_TYPE_CHOICES, default="drudge"
    )

    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"
