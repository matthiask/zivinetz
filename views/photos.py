from __future__ import absolute_import

from django.contrib.auth.decorators import login_required

from photos.models import Album, Photo
from photos.views import AlbumModelView, PhotoModelView

from zivinetz.views.decorators import drudge_required


album_views = AlbumModelView(Album,
    view_decorator=login_required,
    base_template='zivinetz/base.html',
    paginate_by=20,
    )
photo_views = AlbumModelView(Album,
    view_decorator=login_required,
    base_template='zivinetz/base.html',
    paginate_by=20,
    )
