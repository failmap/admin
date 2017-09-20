# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-26 20:07
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scanners', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Endpoint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(max_length=255)),
                ('server_name', models.CharField(max_length=255)),
                ('ip', models.CharField(max_length=255)),
                ('port', models.IntegerField(default=443)),
                ('protocol', models.CharField(max_length=20)),
                ('is_dead', models.IntegerField(default=False)),
                ('is_dead_since', models.DateTimeField(blank=True)),
                ('is_dead_reason', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='TlsQualysScan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('qualys_rating', models.CharField(default=0, max_length=3)),
                ('qualys_rating_no_trust', models.CharField(default=0, max_length=3)),
                ('pending', models.BooleanField(default=1)),
                ('pending_since', models.DateTimeField(auto_now_add=True)),
                ('scan_date', models.DateField(auto_now_add=True)),
                ('scan_time', models.TimeField(auto_now_add=True)),
                ('scan_moment', models.DateTimeField(auto_now_add=True)),
                ('endpoint', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scanners.Endpoint')),
            ],
            options={
                'db_table': 'scanner_tls_qualys',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TlsQualysScratchpad',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(max_length=255)),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('data', models.TextField()),
            ],
        ),
        migrations.DeleteModel(
            name='ScansDnssec',
        ),
        migrations.DeleteModel(
            name='ScansSsllabs',
        ),
    ]
