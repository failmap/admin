# Generated by Django 2.0.3 on 2018-03-20 11:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0024_auto_20180320_0947'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coordinate',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='organizations.Organization'),
        ),
    ]
