from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import ugettext as _

from zivinetz.models import Drudge
from zivinetz.views.decorators import drudge_required


@drudge_required
def home(request, drudge):
    return render(request, 'zivinetz/home.html', {
        'is_staff': request.user.is_staff,
        })



class DrudgeForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'

    class Meta:
        model = Drudge
        exclude = ('user', 'notes') # Exclude notes?


@login_required
def profile(request):
    try:
        drudge = Drudge.objects.get(user=request.user)
    except Drudge.DoesNotExist:
        drudge = None

    if request.method == 'POST':
        form = DrudgeForm(request.POST, instance=drudge)

        if form.is_valid():
            drudge = form.save(commit=False)
            drudge.user = request.user
            drudge.save()

    else:
        form = DrudgeForm(instance=drudge)

    return render(request, 'modelview/object_form.html', {
        'object': drudge,
        'form': form,
        'title': _('Edit profile'),
        'base_template': 'zivinetz/base.html',
        })
