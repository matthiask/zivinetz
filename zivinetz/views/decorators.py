from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
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


def user_type_required(allowed_types):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                if (
                    hasattr(request.user, "userprofile")
                    and request.user.userprofile.user_type not in allowed_types
                ):
                    print(request.user.userprofile.user_type, allowed_types)
                    raise PermissionDenied
            except ObjectDoesNotExist:
                messages.error(request, _("Please complete your profile first."))
                return redirect("drudge_profile")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
