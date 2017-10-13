# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-13 10:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scanners', '0019_auto_20170927_1222'),
    ]

    operations = [
        migrations.AlterField(
            model_name='endpointgenericscan',
            name='rating',
            field=models.CharField(
                default=0, help_text="Preferably an integer, 'True' or 'False'. Keep ratings over time consistent.", max_length=6),
        ),
    ]
