# Generated by Django 4.2.20 on 2025-04-08 00:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('layers', '0022_auto_20250207_2230'),
    ]

    operations = [
        migrations.AlterField(
            model_name='layer',
            name='site',
            field=models.ManyToManyField(related_name='%(class)s_site', to='sites.site'),
        ),
        migrations.AlterField(
            model_name='theme',
            name='site',
            field=models.ManyToManyField(related_name='%(class)s_site', to='sites.site'),
        ),
    ]
