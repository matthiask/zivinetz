from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http import HttpResponse


admin.autodiscover()


urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', lambda request: HttpResponse(repr(request.REQUEST))),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^zivinetz/', include('zivinetz.urls')),
) + staticfiles_urlpatterns()
