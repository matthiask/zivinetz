#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pprint

from django.core.management.base import BaseCommand

from zivinetz.models import PublicHoliday
from zivinetz.utils.holidays import get_public_holidays


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        for year in range(2000, 2030):
            holidays = get_public_holidays(year)
            for date, name in holidays.items():
                PublicHoliday.objects.get_or_create(date=date, defaults={"name": name})
            self.stdout.write(pprint.pformat(holidays))
