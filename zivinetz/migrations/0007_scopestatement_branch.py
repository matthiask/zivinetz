# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zivinetz', '0006_assignmentchange'),
    ]

    operations = [
        migrations.AddField(
            model_name='scopestatement',
            name='branch',
            field=models.CharField(default='Kloster Fahr', max_length=100, verbose_name='branch'),
            preserve_default=False,
        ),
    ]
