# Generated by Django 4.0.8 on 2022-11-07 16:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("zivinetz", "0014_drudge_youth_association"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="drudge",
            name="vegetarianism",
        ),
        migrations.AlterField(
            model_name="drudge",
            name="notes",
            field=models.TextField(
                blank=True,
                help_text="Allergies, anything else we should be aware of?",
                verbose_name="notes",
            ),
        ),
    ]