from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils.translation import ugettext as _

from zivinetz.models import Drudge, ExpenseReport
from zivinetz.views.decorators import drudge_required


@drudge_required
def dashboard(request, drudge):
    return render(request, 'zivinetz/drudge_dashboard.html', {
        'drudge': drudge,

        'assignments': drudge.assignments.order_by('-date_from'),
        'expense_reports': ExpenseReport.objects.filter(assignment__drudge=drudge).order_by('-date_from'),
        })


class UserForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'

    first_name = forms.CharField(label=_('first name'))
    last_name = forms.CharField(label=_('last name'))

    class Meta:
        model = User
        fields = ('first_name', 'last_name')


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
        form2 = UserForm(request.POST, instance=request.user)

        if form.is_valid() and form2.is_valid():
            drudge = form.save(commit=False)
            drudge.user = request.user
            drudge.save()

            form2.save()

            messages.success(request, _('Successfully saved profile information.'))

            return HttpResponseRedirect('.')
    else:
        form = DrudgeForm(instance=drudge)
        form2 = UserForm(instance=request.user)

        print form2

    return render(request, 'zivinetz/drudge_profile.html', {
        'object': drudge,
        'form': form,
        'form2': form2,
        'title': _('Edit profile'),
        })