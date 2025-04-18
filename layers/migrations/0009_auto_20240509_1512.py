# Generated by Django 3.2.12 on 2024-05-09 15:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0008_theme_data_download'),
    ]

    operations = [
        migrations.AlterField(
            model_name='layer',
            name='data_notes',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='layer',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='layer',
            name='disabled_message',
            field=models.CharField(blank=True, default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='layer',
            name='overview',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='layer',
            name='url',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='layerwms',
            name='wms_additional',
            field=models.TextField(blank=True, default=None, help_text='additional WMS key-value pairs: &key=value...', null=True, verbose_name='WMS Additional Fields'),
        ),
        migrations.AlterField(
            model_name='theme',
            name='description',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='theme',
            name='overview',
            field=models.TextField(blank=True, default=None, null=True),
        ),
    ]
