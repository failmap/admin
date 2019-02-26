# Generated by Django 2.0.7 on 2018-08-06 08:38

import colorful.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0009_team_color'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='color',
            field=colorful.fields.RGBColorField(blank=True, colors=['#F2D7D5', '#FADBD8', '#EBDEF0', '#E8DAEF', '#D4E6F1',
                                                                    '#D6EAF8', '#D1F2EB', '#D0ECE7', '#D4EFDF', '#D5F5E3', '#FCF3CF', '#FDEBD0', '#FAE5D3', '#F6DDCC'], null=True),
        ),
    ]