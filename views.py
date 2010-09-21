# Create your views here.

from django.forms.models import inlineformset_factory

from django_modelviews import generic

from zivinetz.models import Assignment, Drudge, RegionalOffice, ScopeStatement, ScopeStatementExpense


class RegionalOfficeModelView(generic.ModelView):
    def deletion_allowed(self, request, instance):
        # TODO run a few checks here
        return True


regional_office_views = RegionalOfficeModelView(RegionalOffice)


ScopeStatementExpenseFormSet = inlineformset_factory(ScopeStatement,
    ScopeStatementExpense,
    extra=1,
    #formfield_callback=forms.stripped_formfield_callback,
    )


class ScopeStatementModelView(generic.ModelView):
    def get_formset_instances(self, request, instance=None, **kwargs):
        args = self.extend_args_if_post(request, [])
        kwargs['instance'] = instance

        return {
            'expenses': ScopeStatementExpenseFormSet(*args, **kwargs),
            }


scope_statement_views = ScopeStatementModelView(ScopeStatement)


drudge_views = generic.ModelView(Drudge)
assignment_views = generic.ModelView(Assignment)
