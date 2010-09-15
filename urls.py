from django.conf.urls.defaults import *

from zivinetz.views import regional_office_views


urlpatterns = patterns('',
    url(r'^regional_offices/', include(regional_office_views.urls)),
)
