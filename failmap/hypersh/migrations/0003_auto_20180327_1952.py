# Generated by Django 2.0.3 on 2018-03-27 19:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hypersh', '0002_environment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='containerenvironment',
            name='configuration',
        ),
        migrations.AddField(
            model_name='containerenvironment',
            name='configuration',
            field=models.ManyToManyField(to='hypersh.ContainerConfiguration'),
        ),
        migrations.RemoveField(
            model_name='containerenvironment',
            name='group',
        ),
        migrations.AddField(
            model_name='containerenvironment',
            name='group',
            field=models.ManyToManyField(to='hypersh.ContainerGroup'),
        ),
        migrations.AlterField(
            model_name='containergroup',
            name='configuration',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='hypersh.ContainerConfiguration'),
        ),
        migrations.AlterField(
            model_name='containergroup',
            name='credential',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='hypersh.Credential'),
        ),
    ]
