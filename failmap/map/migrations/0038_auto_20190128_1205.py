# Generated by Django 2.1.5 on 2019-01-28 12:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map', '0037_auto_20190125_0923'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configuration',
            name='display_order',
            field=models.PositiveIntegerField(default=0, help_text='Setting this to 0 will automatically set the country at a guessed position. For example: near thesame country or at the end of the list.', verbose_name='order'),
        ),
    ]
