# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zivinetz', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='specification',
            name='accomodation_throughout',
            field=models.BooleanField(default=False, help_text='Accomodation is offered throughout.', verbose_name='accomodation throughout'),
        ),
        migrations.AlterField(
            model_name='specification',
            name='food_throughout',
            field=models.BooleanField(default=False, help_text='Food is offered throughout.', verbose_name='food throughout'),
        ),
        migrations.AlterField(
            model_name='specification',
            name='with_accomodation',
            field=models.BooleanField(default=False, verbose_name='with accomodation'),
        ),
    ]
