import pprint

from django.core.management.base import BaseCommand

from zivinetz.models import Specification


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        for spec in Specification.objects.all():
            print spec
            pprint.pprint(spec.compensation())
            print
