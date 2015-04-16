# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zivinetz', '0007_scopestatement_branch'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scopestatement',
            name='company_contact_email',
            field=models.EmailField(max_length=254, verbose_name='company contact email', blank=True),
        ),
    ]
