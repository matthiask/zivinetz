# Generated by Django 2.0.3 on 2018-03-14 14:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zivinetz', '0007_scopestatement_default_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='available_holi_days',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='available holiday days'),
        ),
    ]