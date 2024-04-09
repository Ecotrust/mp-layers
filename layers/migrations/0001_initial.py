# Generated by Django 3.2.12 on 2024-04-08 00:12

import colorfield.fields
import django.contrib.sites.managers
from django.db import migrations, models
import django.db.models.deletion
import layers.models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttributeInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('display_name', models.CharField(blank=True, max_length=255, null=True)),
                ('field_name', models.CharField(blank=True, max_length=255, null=True)),
                ('precision', models.IntegerField(blank=True, null=True)),
                ('order', models.IntegerField(default=1)),
                ('preserve_format', models.BooleanField(default=False, help_text='Prevent portal from making any changes to the data to make it human-readable')),
            ],
        ),
        migrations.CreateModel(
            name='Layer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('uuid', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('slug_name', models.CharField(blank=True, max_length=200, null=True)),
                ('layer_type', models.CharField(choices=[('XYZ', 'XYZ'), ('WMS', 'WMS'), ('ArcRest', 'ArcRest'), ('ArcFeatureServer', 'ArcFeatureServer'), ('Vector', 'Vector'), ('VectorTile', 'VectorTile'), ('slider', 'slider')], help_text='use placeholder to temporarily remove layer from TOC', max_length=50)),
                ('url', models.TextField(blank=True, default='')),
                ('proxy_url', models.BooleanField(default=False, help_text='proxy layer url through marine planner')),
                ('shareable_url', models.BooleanField(default=True, help_text='Indicates whether the data layer (e.g. map tiles) can be shared with others (through the Map Tiles Link)')),
                ('is_disabled', models.BooleanField(default=False, help_text='when disabled, the layer will still appear in the TOC, only disabled')),
                ('disabled_message', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('is_visible', models.BooleanField(default=True)),
                ('utfurl', models.CharField(blank=True, max_length=255, null=True)),
                ('show_legend', models.BooleanField(default=True, help_text='show the legend for this layer if available')),
                ('legend', models.CharField(blank=True, help_text='URL or path to the legend image file', max_length=255, null=True)),
                ('legend_title', models.CharField(blank=True, help_text='alternative to using the layer name', max_length=255, null=True)),
                ('legend_subtitle', models.CharField(blank=True, max_length=255, null=True)),
                ('geoportal_id', models.CharField(blank=True, default=None, help_text='GeoPortal UUID', max_length=255, null=True)),
                ('description', models.TextField(blank=True, default='')),
                ('overview', models.TextField(blank=True, default='')),
                ('data_source', models.CharField(blank=True, max_length=255, null=True)),
                ('data_notes', models.TextField(blank=True, default='')),
                ('data_publish_date', models.DateField(blank=True, default=None, help_text='YYYY-MM-DD', null=True, verbose_name='Date published')),
                ('catalog_name', models.TextField(blank=True, help_text='name of associated record in catalog', null=True, verbose_name='Catalog Record Name')),
                ('catalog_id', models.TextField(blank=True, help_text='unique ID of associated record in catalog', null=True, verbose_name='Catalog Record Id')),
                ('metadata', models.CharField(blank=True, help_text='link to view/download the metadata', max_length=255, null=True)),
                ('source', models.CharField(blank=True, help_text='link back to the data source', max_length=255, null=True)),
                ('bookmark', models.CharField(blank=True, help_text='link to view data layer in the planner', max_length=755, null=True)),
                ('kml', models.CharField(blank=True, help_text='link to download the KML', max_length=255, null=True)),
                ('data_download', models.CharField(blank=True, help_text='link to download the data', max_length=255, null=True)),
                ('learn_more', models.CharField(blank=True, default=None, help_text='link to view description in the Learn section', max_length=255, null=True)),
                ('map_tiles', models.CharField(blank=True, help_text='internal link to a page that details how others might consume the data', max_length=255, null=True)),
                ('label_field', models.CharField(blank=True, help_text='Which field should be used for labels and feature identification in reports?', max_length=255, null=True)),
                ('attribute_event', models.CharField(choices=[('click', 'click'), ('mouseover', 'mouseover')], default='click', max_length=35)),
                ('annotated', models.BooleanField(default=False)),
                ('compress_display', models.BooleanField(default=False)),
                ('mouseover_field', models.CharField(blank=True, default=None, help_text='feature level attribute used in mouseover display', max_length=75, null=True)),
                ('lookup_field', models.CharField(blank=True, help_text='To override the style based on specific attributes, provide the attribute name here and define your attributes in the Lookup table below.', max_length=255, null=True)),
                ('espis_enabled', models.BooleanField(default=False)),
                ('espis_search', models.CharField(blank=True, default=None, help_text='keyphrase search for ESPIS Link', max_length=255, null=True)),
                ('espis_region', models.CharField(blank=True, choices=[('Mid Atlantic', 'Mid Atlantic')], default=None, help_text='Region to search within', max_length=100, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('minZoom', models.FloatField(blank=True, default=None, null=True, verbose_name='Minimum zoom')),
                ('maxZoom', models.FloatField(blank=True, default=None, null=True, verbose_name='Maximum zoom')),
                ('attribute_fields', models.ManyToManyField(blank=True, to='layers.AttributeInfo')),
            ],
            bases=(models.Model, layers.models.SiteFlags),
            managers=[
                ('objects', django.contrib.sites.managers.CurrentSiteManager('site')),
                ('all_objects', layers.models.AllObjectsManager()),
            ],
        ),
        migrations.CreateModel(
            name='LookupInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('value', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.CharField(blank=True, default=None, max_length=255, null=True)),
                ('color', colorfield.fields.ColorField(blank=True, default=None, image_field=None, max_length=18, null=True, samples=[('#FFFFFF', 'white'), ('#888888', 'gray'), ('#000000', 'black'), ('#FF0000', 'red'), ('#FFFF00', 'yellow'), ('#00FF00', 'green'), ('#00FFFF', 'cyan'), ('#0000FF', 'blue'), ('#FF00FF', 'magenta')], verbose_name='Fill Color')),
                ('stroke_color', colorfield.fields.ColorField(blank=True, default=None, image_field=None, max_length=18, null=True, samples=[('#FFFFFF', 'white'), ('#888888', 'gray'), ('#000000', 'black'), ('#FF0000', 'red'), ('#FFFF00', 'yellow'), ('#00FF00', 'green'), ('#00FFFF', 'cyan'), ('#0000FF', 'blue'), ('#FF00FF', 'magenta')], verbose_name='Stroke Color')),
                ('stroke_width', models.IntegerField(blank=True, default=None, null=True, verbose_name='Stroke Width')),
                ('dashstyle', models.CharField(choices=[('dot', 'dot'), ('dash', 'dash'), ('dashdot', 'dashdot'), ('longdash', 'longdash'), ('longdashdot', 'longdashdot'), ('solid', 'solid')], default='solid', max_length=11)),
                ('fill', models.BooleanField(default=False)),
                ('graphic', models.CharField(blank=True, max_length=255, null=True)),
                ('graphic_scale', models.FloatField(blank=True, default=None, help_text='Scale the graphic from its original size.', null=True, verbose_name='Graphic Scale')),
            ],
        ),
        migrations.CreateModel(
            name='MultilayerAssociation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('layer', models.ForeignKey(blank=True, db_column='associatedlayer', default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='associated_layer', to='layers.layer')),
            ],
        ),
        migrations.CreateModel(
            name='MultilayerDimension',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('name', models.CharField(help_text='name to be used for selection in admin tool forms', max_length=200)),
                ('label', models.CharField(help_text='label to be used in mapping tool slider', max_length=50)),
                ('order', models.IntegerField(default=100, help_text='the order in which this dimension will be presented among other dimensions on this layer')),
                ('animated', models.BooleanField(default=False, help_text='enable auto-toggling of layers across this dimension')),
                ('angle_labels', models.BooleanField(default=False, help_text='display labels at an angle to make more fit')),
            ],
            options={
                'ordering': ('order',),
            },
        ),
        migrations.CreateModel(
            name='Library',
            fields=[
                ('layer_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='layers.layer')),
                ('queryable', models.BooleanField(default=False, help_text='Select when layers are queryable - e.g. MDAT and CAS')),
            ],
            bases=('layers.layer',),
            managers=[
                ('objects', django.contrib.sites.managers.CurrentSiteManager('site')),
                ('all_objects', layers.models.AllObjectsManager()),
            ],
        ),
        migrations.CreateModel(
            name='Theme',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('uuid', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('display_name', models.CharField(max_length=100)),
                ('theme_type', models.CharField(blank=True, choices=[('radio', 'radio'), ('checkbox', 'checkbox'), ('slider', 'slider')], help_text='use placeholder to temporarily remove layer from TOC', max_length=50)),
                ('order', models.PositiveIntegerField(blank=True, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('is_visible', models.BooleanField(default=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('overview', models.TextField(blank=True, default='', null=True)),
                ('slug_name', models.CharField(blank=True, max_length=200, null=True)),
                ('header_image', models.CharField(blank=True, max_length=255, null=True)),
                ('header_attrib', models.CharField(blank=True, max_length=255, null=True)),
                ('thumbnail', models.URLField(blank=True, max_length=255, null=True)),
                ('factsheet_thumb', models.CharField(blank=True, max_length=255, null=True)),
                ('factsheet_link', models.CharField(blank=True, max_length=255, null=True)),
                ('feature_image', models.CharField(blank=True, max_length=255, null=True)),
                ('feature_excerpt', models.TextField(blank=True, null=True)),
                ('feature_link', models.CharField(blank=True, max_length=255, null=True)),
                ('site', models.ManyToManyField(related_name='theme_site', to='sites.Site')),
            ],
            options={
                'ordering': ['order'],
            },
            bases=(models.Model, layers.models.SiteFlags),
            managers=[
                ('objects', django.contrib.sites.managers.CurrentSiteManager('site')),
                ('all_objects', layers.models.AllObjectsManager()),
            ],
        ),
        migrations.CreateModel(
            name='MultilayerDimensionValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('value', models.CharField(help_text='Actual value of selection', max_length=200)),
                ('label', models.CharField(help_text='Label for this selection seen in mapping tool slider', max_length=50)),
                ('order', models.IntegerField(default=100)),
                ('associations', models.ManyToManyField(to='layers.MultilayerAssociation')),
                ('dimension', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='layers.multilayerdimension')),
            ],
            options={
                'ordering': ('order',),
            },
        ),
        migrations.AddField(
            model_name='multilayerdimension',
            name='theme',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='layers.theme'),
        ),
        migrations.AddField(
            model_name='multilayerassociation',
            name='parentLayer',
            field=models.ForeignKey(db_column='parentlayer', on_delete=django.db.models.deletion.CASCADE, related_name='parent_layer', to='layers.theme'),
        ),
        migrations.CreateModel(
            name='LayerXYZ',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query_by_point', models.BooleanField(default=False, help_text='Do not buffer selection clicks (not recommended for point or line data)')),
                ('layer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='layers.layer')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LayerWMS',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query_by_point', models.BooleanField(default=False, help_text='Do not buffer selection clicks (not recommended for point or line data)')),
                ('wms_help', models.BooleanField(default=False, help_text='Enable simple selection for WMS fields. Only supports WMS 1.1.1')),
                ('wms_slug', models.CharField(blank=True, max_length=255, null=True, verbose_name='WMS Layer Name')),
                ('wms_version', models.CharField(blank=True, choices=[(None, ''), ('1.0.0', '1.0.0'), ('1.1.0', '1.1.0'), ('1.1.1', '1.1.1'), ('1.3.0', '1.3.0')], default=None, help_text='WMS Versioning - usually either 1.1.1 or 1.3.0', max_length=10, null=True)),
                ('wms_format', models.CharField(blank=True, default=None, help_text='most common: image/png. Only image types supported.', max_length=100, null=True, verbose_name='WMS Format')),
                ('wms_srs', models.CharField(blank=True, default=None, help_text='If not EPSG:3857 WMS requests will be proxied', max_length=100, null=True, verbose_name='WMS SRS')),
                ('wms_timing', models.CharField(blank=True, default=None, help_text='http://docs.geoserver.org/stable/en/user/services/wms/time.html#specifying-a-time', max_length=255, null=True, verbose_name='WMS Time')),
                ('wms_time_item', models.CharField(blank=True, default=None, help_text='Time Attribute Field, if different from "TIME". Proxy only.', max_length=255, null=True, verbose_name='WMS Time Field')),
                ('wms_styles', models.CharField(blank=True, default=None, help_text='pre-determined styles, if exist', max_length=255, null=True, verbose_name='WMS Styles')),
                ('wms_additional', models.TextField(blank=True, default='', help_text='additional WMS key-value pairs: &key=value...', null=True, verbose_name='WMS Additional Fields')),
                ('wms_info', models.BooleanField(default=False, help_text='enable Feature Info requests on click')),
                ('wms_info_format', models.CharField(blank=True, default=None, help_text='Available supported feature info formats', max_length=255, null=True)),
                ('layer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='layers.layer')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LayerVector',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('custom_style', models.CharField(blank=True, choices=[(None, '------'), ('color', 'color'), ('random', 'random')], default=None, help_text="Apply a custom styling rule: i.e. 'color' for Native-Land.ca layers, or 'random' to assign arbitary colors", max_length=255, null=True)),
                ('outline_width', models.IntegerField(blank=True, default=None, null=True, verbose_name='Vector Stroke Width')),
                ('outline_color', colorfield.fields.ColorField(blank=True, default=None, image_field=None, max_length=18, null=True, samples=[('#FFFFFF', 'white'), ('#888888', 'gray'), ('#000000', 'black'), ('#FF0000', 'red'), ('#FFFF00', 'yellow'), ('#00FF00', 'green'), ('#00FFFF', 'cyan'), ('#0000FF', 'blue'), ('#FF00FF', 'magenta')], verbose_name='Vector Stroke Color')),
                ('outline_opacity', models.FloatField(blank=True, default=None, null=True, verbose_name='Vector Stroke Opacity')),
                ('fill_opacity', models.FloatField(blank=True, default=None, null=True, verbose_name='Vector Fill Opacity')),
                ('color', colorfield.fields.ColorField(blank=True, default=None, image_field=None, max_length=18, null=True, samples=[('#FFFFFF', 'white'), ('#888888', 'gray'), ('#000000', 'black'), ('#FF0000', 'red'), ('#FFFF00', 'yellow'), ('#00FF00', 'green'), ('#00FFFF', 'cyan'), ('#0000FF', 'blue'), ('#FF00FF', 'magenta')], verbose_name='Vector Fill Color')),
                ('point_radius', models.IntegerField(blank=True, default=None, help_text='Used only for for Point layers (default is 2)', null=True)),
                ('graphic', models.CharField(blank=True, default=None, help_text='address of image to use for point data', max_length=255, null=True, verbose_name='Vector Graphic')),
                ('graphic_scale', models.FloatField(blank=True, default=1.0, help_text='Scale for the vector graphic from original size.', null=True, verbose_name='Vector Graphic Scale')),
                ('opacity', models.FloatField(blank=True, default=0.5, null=True, verbose_name='Initial Opacity')),
                ('layer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='layers.layer')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LayerArcREST',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query_by_point', models.BooleanField(default=False, help_text='Do not buffer selection clicks (not recommended for point or line data)')),
                ('arcgis_layers', models.CharField(blank=True, help_text='comma separated list of arcgis layer IDs', max_length=255, null=True)),
                ('password_protected', models.BooleanField(default=False, help_text='check this if the server requires a password to show layers')),
                ('disable_arcgis_attributes', models.BooleanField(default=False, help_text='Click to disable clickable ArcRest layers')),
                ('layer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='layers.layer')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LayerArcFeatureService',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('custom_style', models.CharField(blank=True, choices=[(None, '------'), ('color', 'color'), ('random', 'random')], default=None, help_text="Apply a custom styling rule: i.e. 'color' for Native-Land.ca layers, or 'random' to assign arbitary colors", max_length=255, null=True)),
                ('outline_width', models.IntegerField(blank=True, default=None, null=True, verbose_name='Vector Stroke Width')),
                ('outline_color', colorfield.fields.ColorField(blank=True, default=None, image_field=None, max_length=18, null=True, samples=[('#FFFFFF', 'white'), ('#888888', 'gray'), ('#000000', 'black'), ('#FF0000', 'red'), ('#FFFF00', 'yellow'), ('#00FF00', 'green'), ('#00FFFF', 'cyan'), ('#0000FF', 'blue'), ('#FF00FF', 'magenta')], verbose_name='Vector Stroke Color')),
                ('outline_opacity', models.FloatField(blank=True, default=None, null=True, verbose_name='Vector Stroke Opacity')),
                ('fill_opacity', models.FloatField(blank=True, default=None, null=True, verbose_name='Vector Fill Opacity')),
                ('color', colorfield.fields.ColorField(blank=True, default=None, image_field=None, max_length=18, null=True, samples=[('#FFFFFF', 'white'), ('#888888', 'gray'), ('#000000', 'black'), ('#FF0000', 'red'), ('#FFFF00', 'yellow'), ('#00FF00', 'green'), ('#00FFFF', 'cyan'), ('#0000FF', 'blue'), ('#FF00FF', 'magenta')], verbose_name='Vector Fill Color')),
                ('point_radius', models.IntegerField(blank=True, default=None, help_text='Used only for for Point layers (default is 2)', null=True)),
                ('graphic', models.CharField(blank=True, default=None, help_text='address of image to use for point data', max_length=255, null=True, verbose_name='Vector Graphic')),
                ('graphic_scale', models.FloatField(blank=True, default=1.0, help_text='Scale for the vector graphic from original size.', null=True, verbose_name='Vector Graphic Scale')),
                ('opacity', models.FloatField(blank=True, default=0.5, null=True, verbose_name='Initial Opacity')),
                ('arcgis_layers', models.CharField(blank=True, help_text='comma separated list of arcgis layer IDs', max_length=255, null=True)),
                ('password_protected', models.BooleanField(default=False, help_text='check this if the server requires a password to show layers')),
                ('disable_arcgis_attributes', models.BooleanField(default=False, help_text='Click to disable clickable ArcRest layers')),
                ('layer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='layers.layer')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='layer',
            name='lookup_table',
            field=models.ManyToManyField(blank=True, to='layers.LookupInfo'),
        ),
        migrations.AddField(
            model_name='layer',
            name='site',
            field=models.ManyToManyField(related_name='layer_site', to='sites.Site'),
        ),
        migrations.CreateModel(
            name='Companionship',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('companions', models.ManyToManyField(related_name='companion_to', to='layers.Layer')),
                ('layer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='companionships', to='layers.layer')),
            ],
        ),
        migrations.CreateModel(
            name='ChildOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('order', models.PositiveIntegerField()),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('parent_theme', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='children', to='layers.theme')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
    ]
