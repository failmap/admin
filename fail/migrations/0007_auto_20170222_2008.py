# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-22 20:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fail', '0006_merge_20170222_2003'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scansssllabs',
            name='isdead',
            field=models.IntegerField(db_column='isDead', default=False),
        ),
        migrations.AlterField(
            model_name='scansssllabs',
            name='isdeadreason',
            field=models.CharField(
                blank=True, db_column='isDeadReason', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='scansssllabs',
            name='isdeadsince',
            field=models.DateTimeField(
                blank=True, db_column='isDeadSince', null=True),
        ),
    ]
