# Generated by Django 2.1.3 on 2018-12-18 11:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pro', '0003_auto_20181218_1125'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='urllistreport',
            options={'get_latest_by': 'when'},
        ),
    ]