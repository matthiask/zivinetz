from django.core.management.base import BaseCommand
from django.db.models import Count

from zivinetz.models import Assignment


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        for assignment in Assignment.objects.annotate(count=Count("reports")).filter(
            count=0
        ):
            assignment.generate_expensereports()
