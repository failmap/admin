# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-13 14:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0008_auto_20170913_1224'),
    ]

    operations = [
        migrations.AlterField(
            model_name='url',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
