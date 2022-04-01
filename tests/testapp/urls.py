from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http import HttpResponse
from django.urls import include, path


admin.autodiscover()


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", lambda request: HttpResponse(repr(request.REQUEST))),
    path("accounts/", include("django.contrib.auth.urls")),
    path("zivinetz/", include("zivinetz.urls")),
] + staticfiles_urlpatterns()
