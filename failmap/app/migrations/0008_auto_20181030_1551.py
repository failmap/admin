# Generated by Django 2.0.8 on 2018-10-30 15:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_auto_20181025_1304'),
    ]

    operations = [
        migrations.AlterField(
            model_name='volunteer',
            name='added_by',
            field=models.TextField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='volunteer',
            name='notes',
            field=models.TextField(blank=True, max_length=2048, null=True),
        ),
        migrations.AlterField(
            model_name='volunteer',
            name='organization',
            field=models.TextField(blank=True, max_length=200, null=True),
        ),
    ]
