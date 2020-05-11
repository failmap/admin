# Generated by Django 2.2.10 on 2020-02-27 09:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0056_coordinate_calculated_area_hash'),
    ]

    operations = [
        migrations.AlterField(
            model_name='url',
            name='onboarded_on',
            field=models.DateTimeField(blank=True, help_text='The moment the onboard process finished.', null=True),
        ),
    ]