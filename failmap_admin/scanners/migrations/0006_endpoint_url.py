# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-15 13:23
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


"""
+------+------------------------------------+----------------------------+----------------------------+------+----------+---------+----------------+---------------+
| id   | domain                             | server_name                | ip                         | port | protocol | is_dead | is_dead_reason | is_dead_since |
+------+------------------------------------+----------------------------+----------------------------+------+----------+---------+----------------+---------------+
|  300 | geldrop-mierlo.nl                  | rev-196.89.222.77.virtu.nl | 77.222.89.196              |  443 | https    |       0 |                | NULL          |
|  301 | raad.geldrop-mierlo.nl             | rev-196.89.222.77.virtu.nl | 77.222.89.196              |  443 | https    |       0 |                | NULL          |
|  302 | www.geldrop-mierlo.nl              | rev-196.89.222.77.virtu.nl | 77.222.89.196              |  443 | https    |       0 |                | NULL          |
| 4093 | www.veiligheidshuisregioalkmaar.nl | rs201715.rs.hosteurope.de  | 176.28.53.200              |  443 | https    |       0 |                | NULL          |
| 4213 | e-loket.vlissingen.nl              |                            | 2001:67c:45c:f017:0:0:0:16 |  443 | https    |       0 |                | NULL          |
| 4214 | e-loket.vlissingen.nl              |                            | 193.177.166.132            |  443 | https    |       0 |                | NULL          |
| 4251 | aalsmeer.notubiz.nl                | notuwebvm.notubiz.nl       | 195.20.144.21              |  443 | https    |       0 |                | NULL          |
| 4252 | alkmaar.notubiz.nl                 | notuwebvm.notubiz.nl       | 195.20.144.21              |  443 | https    |       0 |                | NULL          |
| 4253 | dongeradeel.notubiz.nl             | notuwebvm.notubiz.nl       | 195.20.144.21              |  443 | https    |       0 |                | NULL          |
| 4254 | kollumerland.notubiz.nl            | notuwebvm.notubiz.nl       | 195.20.144.21              |  443 | https    |       0 |                | NULL          |
| 4255 | ondernemersloket.geldrop-mierlo.nl | rev-196.89.222.77.virtu.nl | 77.222.89.196              |  443 | https    |       0 |                | NULL          |
| 4256 | rotterdam.notubiz.nl               | notuwebvm.notubiz.nl       | 195.20.144.21              |  443 | https    |       0 |                | NULL          |
| 4257 | vianen.notubiz.nl                  | notuwebvm.notubiz.nl       | 195.20.144.21              |  443 | https    |       0 |                | NULL          |
| 4302 | oostgelre.notubiz.nl               | notuwebvm.notubiz.nl       | 195.20.144.21              |  443 | https    |       0 |                | NULL          |
| 4452 | parkeren.meppel.nl                 | rev-124-110.virtu.nl       | 217.114.110.124            |  443 | https    |       0 |                | NULL          |
| 4453 | wozloket.meppel.nl                 |                            | 194.53.75.24               |  443 | https    |       0 |                | NULL          |
+------+------------------------------------+----------------------------+----------------------------+------+----------+---------+----------------+---------------+
"""


def forward(apps, schema_editor):
    """
    Here we try to get an url__id for all urls based on the value in domain.
    After this association we will drop all endpoints that do not have a url.

    This _should_ delete 16 endpoints in the production database.
    todo: This should still be tested instaging.

    AttributeError: 'Endpoint' object has no attribute 'domain'
    Nope, not anymore it does. But it does have that in the database since we're migrating now.


    This doesn't work in the future: because you instantiate an Endpoint at a certain point, with
    columns that don't yet exist. At this version there was no "scanners_endpoint.discovered_on"
    column. So the migration crashes. The code of this migration has now moved to a command:
    migration_domaintourl. This code is here for legacy reasons.

    :param apps:
    :param schema_editor:
    :return:
    """
    # for endpoint in Endpoint.objects.filter():
    #     try:
    #         endpoint.url = Url.objects.filter(url=endpoint.domain).first()
    #         endpoint.save()
    #     except Url.DoesNotExist:
    #         endpoint.delete()


# this is not tested...
def backward(apps, schema_editor):
    """
    We have to duplicate some data.

    All endpoints that don't have a url get dropped.
    :param apps:
    :param schema_editor:
    :return:
    """
    # for endpoint in Endpoint.objects.filter():
    #     try:
    #         # werkt dit uberhaupt?
    #         endpoint.url = Url.objects.filter(url=endpoint.url).first()["url"]
    #         endpoint.save()
    #     except Url.DoesNotExist:
    #         endpoint.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0002_auto_20170226_2007'),
        ('scanners', '0005_auto_20170310_0910'),
    ]

    operations = [
        migrations.AddField(
            model_name='endpoint',
            name='url',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='organizations.Url'),
        ),

        migrations.RunPython(forward, backward),

        # now drop the existing field
        # nope: can't drop it here, you still need it to move the data. Next migration buddy.
        # also: with the existing fields all software will still work and can be migrated safely
        # AND you can fix all conversion errors by hand in the production data.
        # congratulations: you've just created your first legacy column! :))
        # migrations.RemoveField(model_name='endpoint', name='domain'),

        # decided not to rename url to domain, since it can be confusion. We are now working with
        # urls, and not domains (or subdomains, toplevel domains and such).
        # and rename the new field to "domain" (this also has implications on the scanners :'()
        # migrations.RenameField(model_name='endpoint', old_name='url', new_name='domain'),

    ]
