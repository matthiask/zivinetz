# Generated by Django 4.1.2 on 2022-10-27 02:28

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("zivinetz", "0013_auto_20210629_2108"),
    ]

    operations = [
        migrations.AddField(
            model_name="drudge",
            name="youth_association",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Pfadi", "Pfadi"),
                    ("Cevi", "Cevi"),
                    ("Jubla", "Jubla"),
                    ("Anderer", "Anderer"),
                    ("Keiner", "Keiner"),
                ],
                max_length=100,
                verbose_name="youth association",
            ),
        ),
    ]
