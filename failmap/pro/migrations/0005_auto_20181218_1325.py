# Generated by Django 2.1.3 on 2018-12-18 13:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pro', '0004_auto_20181218_1144'),
    ]

    operations = [
        migrations.CreateModel(
            name='CreditMutation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('credits_received', models.PositiveIntegerField(blank=True, default=0,
                                                                 help_text='A positive number of amount of credits received.', null=True)),
                ('credits_spent', models.PositiveIntegerField(blank=True, default=0,
                                                              help_text='A positive number of the amount of credits spent.', null=True)),
                ('credit_mutation', models.IntegerField(blank=True, default=0,
                                                        help_text='The amount of credits received is positive, amount spent is negative.', null=True)),
                ('goal', models.TextField(blank=True, help_text="Description on how the mutation came to be. For example: deposit, scan on XYZ, etc. Be as complete as possible so it's obvious why credits where received and spent.", max_length=1024, null=True)),
                ('when', models.DateTimeField(blank=True, help_text='When the transaction was made.', null=True)),
            ],
            options={
                'ordering': ('when',),
                'get_latest_by': 'when',
            },
        ),
        migrations.AddField(
            model_name='account',
            name='credits',
            field=models.PositiveIntegerField(
                blank=True, default=0, help_text='Credits limit the amount of scans an account can make. Otherwise they might scan-flood.', null=True),
        ),
        migrations.AddField(
            model_name='creditmutation',
            name='account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pro.Account'),
        ),
    ]
