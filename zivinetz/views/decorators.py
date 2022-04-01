from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.translation import gettext as _

from zivinetz.models import Drudge


def drudge_required(view_func):
    @wraps(view_func)
    def _fn(request, *args, **kwargs):
        try:
            kwargs["drudge"] = Drudge.objects.get(user=request.user)

            if not kwargs["drudge"].profile_image:
                messages.error(
                    request, _("Please add an image of yourself to your profile.")
                )
                return redirect("drudge_profile")
        except Drudge.DoesNotExist:
            return redirect("drudge_profile")

        return view_func(request, *args, **kwargs)

    return login_required(_fn)
