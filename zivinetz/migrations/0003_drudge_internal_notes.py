# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zivinetz', '0002_auto_20140908_1116'),
    ]

    operations = [
        migrations.AddField(
            model_name='drudge',
            name='internal_notes',
            field=models.TextField(default='', help_text='This field is not visible to drudges.', verbose_name='internal notes', blank=True),
            preserve_default=False,
        ),
    ]
