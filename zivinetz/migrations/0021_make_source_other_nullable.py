from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zivinetz', '0020_create_user_profiles'),
    ]

    operations = [
        migrations.AlterField(
            model_name='drudge',
            name='source_other',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
    ] 