from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from zivinetz.models import Drudge


def drudge_required(view_func):
    @wraps(view_func)
    def _fn(request, *args, **kwargs):
        try:
            kwargs['drudge'] = Drudge.objects.get(user=request.user)
        except Drudge.DoesNotExist:
            return redirect('profile_edit')

        return view_func(request, *args, **kwargs)
    return login_required(_fn)
