# Generated by Django 2.0.7 on 2018-09-17 17:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scanners', '0042_auto_20180814_1415'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='endpoint',
            options={'verbose_name': 'endpoint', 'verbose_name_plural': 'endpoint'},
        ),
        migrations.AlterModelOptions(
            name='tlsscan',
            options={'verbose_name': 'tlsscan', 'verbose_name_plural': 'tlsscan'},
        ),
        migrations.AlterModelOptions(
            name='urlip',
            options={'verbose_name': 'urlip', 'verbose_name_plural': 'urlip'},
        ),
    ]
