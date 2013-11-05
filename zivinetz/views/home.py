from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render

from zivinetz.models import Drudge


@login_required
def home(request):
    try:
        drudge = Drudge.objects.get(user=request.user)
    except Drudge.DoesNotExist:
        drudge = None

    if request.user.is_staff:
        return HttpResponseRedirect('admin/')

    elif not drudge:
        return redirect('drudge_profile')

    return redirect('drudge_dashboard')


@staff_member_required
def admin(request):
    return render(request, 'zivinetz/admin.html', {
        })
