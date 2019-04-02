# Generated by Django 2.1.7 on 2019-04-01 13:58

import django.db.models.deletion
import jsonfield.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0054_auto_20190325_1005'),
        ('map', '0046_highlevelstatistic'),
        ('reporting', '0006_auto_20190401_1356')
    ]

    state_operations = [
        migrations.CreateModel(
            name='OrganizationReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_issues', models.IntegerField(default=0, help_text='The summed number of all vulnerabilities and failures.')),
                ('high', models.IntegerField(default=0, help_text='The number of high risk vulnerabilities and failures.')),
                ('medium', models.IntegerField(default=0, help_text='The number of medium risk vulnerabilities and failures.')),
                ('low', models.IntegerField(default=0, help_text='The number of low risk vulnerabilities and failures.')),
                ('ok', models.IntegerField(default=0, help_text='No issues found at all.')),
                ('total_urls', models.IntegerField(default=0, help_text='Amount of urls for this organization.')),
                ('high_urls', models.IntegerField(default=0, help_text='Amount of urls with (1 or more) high risk issues.')),
                ('medium_urls', models.IntegerField(default=0, help_text='Amount of urls with (1 or more) medium risk issues.')),
                ('low_urls', models.IntegerField(default=0, help_text='Amount of urls with (1 or more) low risk issues.')),
                ('ok_urls', models.IntegerField(default=0, help_text='Amount of urls with zero issues.')),
                ('total_endpoints', models.IntegerField(default=0, help_text='Amount of endpoints for this url.')),
                ('high_endpoints', models.IntegerField(default=0,
                                                       help_text='Amount of endpoints with (1 or more) high risk issues.')),
                ('medium_endpoints', models.IntegerField(default=0,
                                                         help_text='Amount of endpoints with (1 or more) medium risk issues.')),
                ('low_endpoints', models.IntegerField(default=0, help_text='Amount of endpoints with (1 or more) low risk issues.')),
                ('ok_endpoints', models.IntegerField(default=0, help_text='Amount of endpoints with zero issues.')),
                ('total_url_issues', models.IntegerField(default=0, help_text='Total amount of issues on url level.')),
                ('url_issues_high', models.IntegerField(default=0, help_text='Number of high issues on url level.')),
                ('url_issues_medium', models.IntegerField(default=0, help_text='Number of medium issues on url level.')),
                ('url_issues_low', models.IntegerField(default=0, help_text='Number of low issues on url level.')),
                ('url_ok', models.IntegerField(default=0, help_text='Zero issues on these urls.')),
                ('total_endpoint_issues', models.IntegerField(default=0, help_text='Total amount of issues on endpoint level.')),
                ('endpoint_issues_high', models.IntegerField(default=0, help_text='Total amount of issues on endpoint level.')),
                ('endpoint_issues_medium', models.IntegerField(default=0,
                                                               help_text='Total amount of issues on endpoint level.')),
                ('endpoint_issues_low', models.IntegerField(default=0, help_text='Total amount of issues on endpoint level.')),
                ('endpoint_ok', models.IntegerField(default=0, help_text='Zero issues on these endpoints.')),
                ('explained_total_issues', models.IntegerField(default=0,
                                                               help_text='The summed number of all vulnerabilities and failures.')),
                ('explained_high', models.IntegerField(default=0, help_text='The number of high risk vulnerabilities and failures.')),
                ('explained_medium', models.IntegerField(default=0,
                                                         help_text='The number of medium risk vulnerabilities and failures.')),
                ('explained_low', models.IntegerField(default=0, help_text='The number of low risk vulnerabilities and failures.')),
                ('explained_total_urls', models.IntegerField(default=0, help_text='Amount of urls for this organization.')),
                ('explained_high_urls', models.IntegerField(default=0,
                                                            help_text='Amount of urls with (1 or more) high risk issues.')),
                ('explained_medium_urls', models.IntegerField(default=0,
                                                              help_text='Amount of urls with (1 or more) medium risk issues.')),
                ('explained_low_urls', models.IntegerField(default=0,
                                                           help_text='Amount of urls with (1 or more) low risk issues.')),
                ('explained_total_endpoints', models.IntegerField(default=0, help_text='Amount of endpoints for this url.')),
                ('explained_high_endpoints', models.IntegerField(default=0,
                                                                 help_text='Amount of endpoints with (1 or more) high risk issues.')),
                ('explained_medium_endpoints', models.IntegerField(default=0,
                                                                   help_text='Amount of endpoints with (1 or more) medium risk issues.')),
                ('explained_low_endpoints', models.IntegerField(default=0,
                                                                help_text='Amount of endpoints with (1 or more) low risk issues.')),
                ('explained_total_url_issues', models.IntegerField(
                    default=0, help_text='Total amount of issues on url level.')),
                ('explained_url_issues_high', models.IntegerField(default=0, help_text='Number of high issues on url level.')),
                ('explained_url_issues_medium', models.IntegerField(
                    default=0, help_text='Number of medium issues on url level.')),
                ('explained_url_issues_low', models.IntegerField(default=0, help_text='Number of low issues on url level.')),
                ('explained_total_endpoint_issues', models.IntegerField(
                    default=0, help_text='Total amount of issues on endpoint level.')),
                ('explained_endpoint_issues_high', models.IntegerField(
                    default=0, help_text='Total amount of issues on endpoint level.')),
                ('explained_endpoint_issues_medium', models.IntegerField(
                    default=0, help_text='Total amount of issues on endpoint level.')),
                ('explained_endpoint_issues_low', models.IntegerField(
                    default=0, help_text='Total amount of issues on endpoint level.')),
                ('when', models.DateTimeField(db_index=True)),
                ('calculation', jsonfield.fields.JSONField(
                    help_text='Contains JSON with a calculation of all scanners at this moment, for all urls of this organization. This can be a lot.')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='organizations.Organization')),
            ],
            options={
                'verbose_name': 'Organization Report',
                'verbose_name_plural': 'Organization Reports',
                'get_latest_by': 'when',
            },
        ),
        migrations.AlterIndexTogether(
            name='organizationreport',
            index_together={('when', 'id')},
        ),

    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations)
    ]