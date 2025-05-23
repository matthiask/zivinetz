# Generated by Django 5.0.9 on 2024-11-22 16:56

from django.db import migrations


def forwards(apps, schema_editor):
    seen = set()
    for quota in apps.get_model("zivinetz", "drudgequota").objects.all():
        key = (quota.scope_statement_id, quota.week)
        if key in seen:
            print(quota)
            quota.delete()

        seen.add(key)


class Migration(migrations.Migration):
    dependencies = [
        ("zivinetz", "0017_drudge_source_drudge_source_other"),
    ]

    operations = [
        migrations.RunPython(forwards),
        migrations.AlterUniqueTogether(
            name="drudgequota",
            unique_together={("scope_statement", "week")},
        ),
    ]
