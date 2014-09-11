# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zivinetz', '0003_drudge_internal_notes'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='environment_course_date',
            field=models.DateField(null=True, verbose_name='environment course date', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assignment',
            name='motor_saw_course_date',
            field=models.DateField(null=True, verbose_name='motor saw course date', blank=True),
            preserve_default=True,
        ),
    ]
