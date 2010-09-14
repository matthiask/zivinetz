#!/usr/bin/env python
# -*- coding: utf-8 -*-


import pprint

from django.core.management.base import BaseCommand

from zivinetz.utils.holidays import get_public_holidays


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        for year in range(2000, 2015):
            pprint.pprint(get_public_holidays(year))

