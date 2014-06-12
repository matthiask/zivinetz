from __future__ import absolute_import

from django.contrib.auth.decorators import login_required

from photos.models import Album, Photo
from photos.views import AlbumModelView, PhotoModelView


album_views = AlbumModelView(
    Album,
    view_decorator=login_required,
    base_template='zivinetz/base.html',
    paginate_by=20)
photo_views = PhotoModelView(
    Photo,
    view_decorator=login_required,
    base_template='zivinetz/base.html',
    paginate_by=20)
