# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-03-27 14:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django_fsm


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Credential',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('access_key', models.CharField(max_length=64)),
                ('secret_key', models.CharField(max_length=64)),
                ('enabled', models.BooleanField(default=True, help_text='Allow these credentials to be used.')),
                ('valid', models.BooleanField()),
                ('region', models.CharField(default='eu-central-1', max_length=64)),
                ('last_validated', models.DateTimeField(null=True)),
                ('last_result', models.TextField(default='')),
            ],
        ),
        migrations.CreateModel(
            name='ContainerConfiguration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('image', models.CharField(default='registry.gitlab.com/failmap/failmap:latest', max_length=200)),
                ('command', models.CharField(default='celery worker --log info --concurrency 1', max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='ContainerGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('enabled', models.BooleanField(default=True, help_text='When disabled are containers are removed and scaling is not possible.')),
                ('minimum', models.IntegerField(default=0)),
                ('maximum', models.IntegerField(default=1)),
                ('desired', models.IntegerField(default=1)),
                ('state', django_fsm.FSMField(default='new', max_length=50)),
                ('current', models.IntegerField(default=0)),
                ('configuration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hypersh.ContainerConfiguration')),
                ('credential', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hypersh.Credential')),
            ],
        ),
    ]