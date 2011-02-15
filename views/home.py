from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def home(request):
    return render(request, 'zivinetz_base.html', {
        })
