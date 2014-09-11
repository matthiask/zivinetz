# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zivinetz', '0004_auto_20140911_0929'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignment',
            name='environment_course_date',
            field=models.DateField(null=True, verbose_name='environment course starting date', blank=True),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='motor_saw_course_date',
            field=models.DateField(null=True, verbose_name='motor saw course starting date', blank=True),
        ),
    ]
