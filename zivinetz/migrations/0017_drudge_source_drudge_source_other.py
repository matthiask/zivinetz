# Generated by Django 4.0.8 on 2023-02-04 16:29

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("zivinetz", "0016_remove_compensationset_spending_money"),
    ]

    operations = [
        migrations.AddField(
            model_name="drudge",
            name="source",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Instagram", "Instagram"),
                    ("Linkedin", "Linkedin"),
                    ("Facebook", "Facebook"),
                    ("Freunde/Familie/Bekannte", "Freunde/Familie/Bekannte"),
                    ("Internetsuche", "Internetsuche"),
                    ("E-Zivi", "E-Zivi"),
                    ("Plakat/Flyer", "Plakat/Flyer"),
                    (
                        "Fahrzeug oder Einsatzgruppe gesehen",
                        "Fahrzeug oder Einsatzgruppe gesehen",
                    ),
                    ("Anderes:", "Anderes:"),
                ],
                max_length=100,
                verbose_name="Wie hast du vom Naturnetz erfahren?",
            ),
        ),
        migrations.AddField(
            model_name="drudge",
            name="source_other",
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name="Wie hast du vom Naturnetz erfahren?",
            ),
        ),
    ]