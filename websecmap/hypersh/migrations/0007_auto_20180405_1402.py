# Generated by Django 2.0.4 on 2018-04-05 14:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hypersh', '0006_auto_20180404_1318'),
    ]

    operations = [
        migrations.RenameField(
            model_name='containerconfiguration',
            old_name='volumes_from',
            new_name='volumes',
        ),
    ]