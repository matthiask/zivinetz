import pprint

from django.core.management.base import BaseCommand

from zivinetz.models import Assignment


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        for assignment in Assignment.objects.all():
            print 'Calculating days for %s' % assignment
            pprint.pprint(assignment.calculate_days())
