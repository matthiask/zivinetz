from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils.translation import ugettext as _

from towel.forms import stripped_formfield_callback

from zivinetz.models import Drudge, ExpenseReport, Assignment, WaitList
from zivinetz.views.decorators import drudge_required


class AssignmentForm(forms.ModelForm):
    formfield_callback = stripped_formfield_callback

    class Meta:
        model = Assignment
        exclude = ('drudge', 'created', 'status', 'date_until_extension')


class WaitListForm(forms.ModelForm):
    formfield_callback = stripped_formfield_callback

    class Meta:
        model = WaitList
        exclude = ('drudge', 'created')


@drudge_required
def dashboard(request, drudge):

    aform_initial = {
        'regional_office': drudge.regional_office_id,
        }

    aform = AssignmentForm(initial=aform_initial)
    wform = WaitListForm()

    if request.method == 'POST':
        if 'assignment' in request.POST:
            aform = AssignmentForm(request.POST)
            if aform.is_valid():
                assignment = aform.save(commit=False)
                assignment.drudge = drudge
                assignment.save()
                messages.success(request, _('Successfully saved new assignment.'))

                return HttpResponseRedirect('.')

        if 'waitlist' in request.POST:
            wform = WaitListForm(request.POST)
            if wform.is_valid():
                waitlist = wform.save(commit=False)
                waitlist.drudge = drudge
                waitlist.save()
                messages.success(request, _('Successfully saved new waitlist entry.'))

                return HttpResponseRedirect('.')

    return render(request, 'zivinetz/drudge_dashboard.html', {
        'drudge': drudge,

        'assignment_form': aform,
        'waitlist_form': wform,

        'assignments': drudge.assignments.order_by('-date_from'),
        'expense_reports': ExpenseReport.objects.filter(assignment__drudge=drudge).order_by('-date_from'),
        'waitlist': WaitList.objects.filter(drudge=drudge),
        })


class UserForm(forms.ModelForm):
    formfield_callback = stripped_formfield_callback
    error_css_class = 'error'
    required_css_class = 'required'

    first_name = forms.CharField(label=_('first name'))
    last_name = forms.CharField(label=_('last name'))

    class Meta:
        model = User
        fields = ('first_name', 'last_name')


class DrudgeForm(forms.ModelForm):
    formfield_callback = stripped_formfield_callback
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

    return render(request, 'zivinetz/drudge_profile.html', {
        'object': drudge,
        'form': form,
        'form2': form2,
        'title': _('Edit profile'),
        })
