# Generated by Django 2.1.3 on 2018-12-03 10:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0014_auto_20181203_1038'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='name',
            field=models.CharField(default=None, help_text='Whatever name the team wants. Must be at least PEGI 88.', max_length=42, verbose_name='Team name'),
        ),
    ]
