from __future__ import absolute_import, unicode_literals

from collections import OrderedDict, defaultdict
from datetime import date, timedelta

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy, ugettext as _

from zivinetz.models import ScopeStatement, DrudgeQuota


def yield_dates(start, step, count):
    for i in range(count):
        yield start + timedelta(days=step * i)


class QuotaForm(forms.Form):
    quota = forms.IntegerField(
        label=ugettext_lazy('quota'),
        required=False,
    )


@staff_member_required
def quota_year(request, year):
    year = int(year)
    first_day = date(year, 1, 1)
    first_monday = first_day - timedelta(days=first_day.weekday())

    all_forms = defaultdict(OrderedDict)
    dates = list(yield_dates(first_monday, 7, 53))

    if request.method == 'POST':
        created = 0
        updated = 0
        deleted = 0

        for scope_statement in ScopeStatement.objects.all():
            existing_quotas = {
                quota.week: quota for quota in scope_statement.drudgequota_set.all()
            }
            for day in dates:
                try:
                    value = int(request.POST['%s_%s-quota' % (
                        scope_statement.id,
                        day.strftime('%Y%m%d'),
                    )])
                except (KeyError, TypeError, ValueError):
                    if day in existing_quotas:
                        existing_quotas[day].delete()
                        deleted += 1
                    continue
                else:
                    if day in existing_quotas:
                        existing_quotas[day].quota = value
                        existing_quotas[day].save()
                        updated += 1
                    else:
                        DrudgeQuota.objects.create(
                            scope_statement=scope_statement,
                            week=day,
                            quota=value,
                        )
                        created += 1

        messages.success(
            request,
            _('Created %(c)s, updated %(u)s, deleted %(d)s quotas') % {
                'c': created,
                'u': updated,
                'd': deleted,
            },
        )
        return redirect('.')

    for scope_statement in ScopeStatement.objects.all():
        forms = all_forms[scope_statement]
        existing_quotas = {
            quota.week: quota.quota
            for quota in scope_statement.drudgequota_set.all()
        }

        for day in dates:
            form = QuotaForm(
                initial={'quota': existing_quotas.get(day)},
                prefix='%s_%s' % (scope_statement.id, day.strftime('%Y%m%d')),
            )
            forms[day] = form

    return render(request, 'zivinetz/quota_year.html', {
        'year': year,
        'dates': dates,
        'all_forms': dict(all_forms),
    })
