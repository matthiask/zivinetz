import pprint

from django.core.management.base import BaseCommand

from zivinetz.models import Specification


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        for spec in Specification.objects.all():
            self.stdout.write(u'%s\n' % spec)
            self.stdout.write(pprint.pformat(spec.compensation()))
            self.stdout.write(u'\n')
