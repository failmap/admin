# Generated by Django 2.0.3 on 2018-04-04 18:54

import django.db.models.deletion
import django_countries.fields
import djgeojson.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organizations', '0030_auto_20180403_1547'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Whatever name the team wants. Must be at least PEGI 88.', max_length=42)),
                ('logo_filename', models.CharField(help_text='A nice filename for contest logos.', max_length=255)),
                ('website', models.CharField(help_text='Whatever name the team wants. Must be at least PEGI 88.', max_length=255)),
                ('from_moment', models.DateTimeField(blank=True, help_text='Moment the compo opens.', null=True)),
                ('until_moment', models.DateTimeField(blank=True, help_text='Moment the compo closes.', null=True)),
                ('target_country', django_countries.fields.CountryField(
                    help_text='The country (if any) under which submissions fall.', max_length=2)),
            ],
            options={
                'verbose_name': 'contest',
                'verbose_name_plural': 'contests',
            },
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('organization_country', django_countries.fields.CountryField(max_length=2)),
                ('organization_type_name', models.CharField(default='unknown',
                                                            help_text='The contest the team is participating in.', max_length=42)),
                ('organization_name', models.CharField(default='unknown',
                                                       help_text='The contest the team is participating in.', max_length=42)),
                ('organization_address', models.CharField(default='unknown',
                                                          help_text='The address of the (main location) of the organization. This will be used for geocoding.', max_length=600)),
                ('organization_address_geocoded', djgeojson.fields.GeoJSONField(
                    help_text='Automatic geocoded organization address.', max_length=5000)),
                ('url', models.CharField(help_text='The URL the team has submitted, for review before acceptance.', max_length=500)),
                ('has_been_accepted', models.BooleanField(default=False,
                                                          help_text='If the admin likes it, they can accept the submission to be part of the real system')),
                ('added_on', models.DateTimeField(blank=True,
                                                  help_text='Automatically filled when creating a new submission.', null=True)),
            ],
            options={
                'verbose_name': 'submission',
                'verbose_name_plural': 'submissions',
            },
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Whatever name the team wants. Must be at least PEGI 88.', max_length=42)),
                ('secret', models.CharField(
                    help_text='A secret that allows them to add URLS under their team (for scoring purposes)', max_length=42)),
                ('allowed_to_submit_things', models.BooleanField(
                    default=False, help_text='Disables teams from submitting things.')),
                ('participating_in_contest', models.ForeignKey(blank=True, null=True,
                                                               on_delete=django.db.models.deletion.CASCADE, to='game.Contest')),
            ],
            options={
                'verbose_name': 'team',
                'verbose_name_plural': 'teams',
            },
        ),
        migrations.AddField(
            model_name='submission',
            name='added_by_team',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='game.Team'),
        ),
        migrations.AddField(
            model_name='submission',
            name='url_in_system',
            field=models.ForeignKey(blank=True, help_text='This reference will be used to calculate the score and to track imports.',
                                    null=True, on_delete=django.db.models.deletion.CASCADE, to='organizations.Url'),
        ),
    ]
