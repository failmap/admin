# Generated by Django 2.1.5 on 2019-01-11 16:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scanners', '0057_scanproxy_protocol'),
    ]

    operations = [
        migrations.AddField(
            model_name='scanproxy',
            name='check_result',
            field=models.CharField(default='Unchecked.',
                                   help_text="The result of the latest 'check proxy' call.", max_length=60),
        ),
        migrations.AddField(
            model_name='scanproxy',
            name='check_result_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
