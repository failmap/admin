# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-22 19:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fail', '0004_auto_20170222_1826'),
    ]

    operations = [
        migrations.AlterField(
            model_name='url',
            name='isdead',
            field=models.BooleanField(db_column='isDead', default=False),
        ),
        migrations.AlterField(
            model_name='url',
            name='isdeadreason',
            field=models.CharField(
                blank=True, db_column='isDeadReason', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='url',
            name='isdeadsince',
            field=models.DateTimeField(
                blank=True, db_column='isDeadSince', null=True),
        ),
    ]