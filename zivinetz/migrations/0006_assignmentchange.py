# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('zivinetz', '0005_auto_20140911_0930'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssignmentChange',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, verbose_name='created')),
                ('assignment_description', models.CharField(max_length=200, verbose_name='assignment description')),
                ('changed_by', models.CharField(default=b'nobody', max_length=100, verbose_name='changed by')),
                ('changes', models.TextField(verbose_name='changes', blank=True)),
                ('assignment', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='assignment', blank=True, to='zivinetz.Assignment', null=True)),
            ],
            options={
                'ordering': ['created'],
                'verbose_name': 'assignment change',
                'verbose_name_plural': 'assignment changes',
            },
            bases=(models.Model,),
        ),
    ]
