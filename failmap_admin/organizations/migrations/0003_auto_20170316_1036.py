# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-16 10:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0002_auto_20170226_2007'),
    ]

    operations = [
        migrations.RenameField(
            model_name='url',
            old_name='isdead',
            new_name='is_dead',
        ),
        migrations.RenameField(
            model_name='url',
            old_name='isdeadreason',
            new_name='is_dead_reason',
        ),
        migrations.RenameField(
            model_name='url',
            old_name='isdeadsince',
            new_name='is_dead_since',
        ),
    ]
