import pprint

from django.core.management.base import BaseCommand

from zivinetz.models import Assignment


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        for assignment in Assignment.objects.all():
            self.stdout.write("Assignment days for %s\n" % assignment)
            self.stdout.write(pprint.pformat(assignment.assignment_days()))
            self.stdout.write(pprint.pformat(assignment.expenses()))
