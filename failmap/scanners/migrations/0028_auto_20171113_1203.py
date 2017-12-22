# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-13 12:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scanners', '0027_auto_20171113_1028'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='endpoint',
            name='domain',
        ),
        migrations.RemoveField(
            model_name='endpoint',
            name='ip',
        ),
        migrations.RemoveField(
            model_name='endpoint',
            name='server_name',
        ),
        migrations.AlterField(
            model_name='endpoint',
            name='ip_version',
            field=models.IntegerField(default=4, help_text="Either 4: IPv4 or 6: IPv6. There are basically two possibilities to reach the endpoint, which due to immaturity often look very different. The old way is using IPv4addresses (4) and the newer method is uing IPv6 (6). The internet looks a whole lotdifferent between IPv4 or IPv6. That shouldn't be the case, but it is."),
        ),
        migrations.AlterField(
            model_name='endpoint',
            name='is_dead',
            field=models.BooleanField(default=False, help_text="Use the 'declare dead' button to autofill the date. If the port is closed, or the endpoint is otherwisenot reachable over the specified protocol, then markit as dead. A scanner for this port/protocol can alsodeclare it dead. This port is closed on this protocol."),
        ),
        migrations.AlterField(
            model_name='endpoint',
            name='protocol',
            field=models.CharField(
                help_text='Lowercase. Mostly application layer protocols, such as HTTP, FTP,SSH and so on. For more, read here: https://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol', max_length=20),
        ),
    ]