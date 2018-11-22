# Generated by Django 2.1.3 on 2018-11-22 12:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0039_auto_20181119_1105'),
    ]

    operations = [
        migrations.AddField(
            model_name='url',
            name='dns_supports_mx',
            field=models.BooleanField(
                default=False, help_text="If there is at least one MX record available, so we can perform mail generic mail scans. (for thesescans we don't need to know what mail-ports and protocols/endpoints are available)."),
        ),
    ]
