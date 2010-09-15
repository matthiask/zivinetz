# Create your views here.

from django_modelviews import generic

from zivinetz.models import RegionalOffice


class RegionalOfficeModelView(generic.ModelView):
    def deletion_allowed(self, request, instance):
        # TODO run a few checks here
        return True


regional_office_views = RegionalOfficeModelView(RegionalOffice)
