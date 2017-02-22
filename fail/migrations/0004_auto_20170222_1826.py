# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-22 18:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fail', '0003_auto_20170222_1817'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coordinate',
            name='organization',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to='fail.Organization'),
        ),
        migrations.AlterField(
            model_name='url',
            name='organization',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to='fail.Organization'),
        ),
    ]
