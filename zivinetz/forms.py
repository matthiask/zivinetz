from django import forms
from django.utils.translation import ugettext_lazy as _

from towel.forms import SearchForm

from zivinetz.models import ScopeStatement


class WaitListSearchForm(SearchForm):
    specification__scope_statement = forms.ModelMultipleChoiceField(
        queryset=ScopeStatement.objects.all(),
        label=_('scope statement'),
        required=False)
    assignment_date_from__gte = forms.DateField(
        label=_('date from'), required=False,
        widget=forms.DateInput(attrs={'class': 'dateinput'}))
    assignment_date_until__lte = forms.DateField(
        label=_('date until'), required=False,
        widget=forms.DateInput(attrs={'class': 'dateinput'}))
