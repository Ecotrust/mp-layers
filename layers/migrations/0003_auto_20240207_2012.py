# Generated by Django 3.2.23 on 2024-02-07 20:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0002_auto_20240207_1925'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='theme',
            name='data_notes',
        ),
        migrations.RemoveField(
            model_name='theme',
            name='data_source',
        ),
        migrations.RemoveField(
            model_name='theme',
            name='source',
        ),
        migrations.AddField(
            model_name='theme',
            name='factsheet_link',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='factsheet_thumb',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='feature_excerpt',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='feature_image',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='feature_link',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='header_attrib',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='header_image',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='thumbnail',
            field=models.URLField(blank=True, max_length=255, null=True),
        ),
    ]
