from django.db import models, transaction, IntegrityError, connection
from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.sites.models import Site
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.conf import settings
from colorfield.fields import ColorField
import uuid

# Review widgets for ITK database (how are relationships set up)
def get_domain(port=8010):
    try:
        #domain = Site.objects.all()[0].domain
        domain = Site.objects.get(id=SITE_ID).domain
        if 'localhost' in domain:
            domain = 'localhost:{}'.format(port)
        domain = 'http://' + domain
    except:
        domain = '..'
    #print(domain)
    return domain

# Since we migrate raw SQL data into the DB from data_manager, the sequences are not updated. 
#   This catches any time there is a mismatch and tries to update it.
def update_model_sequence(model, unique_key, manager):
    max_theme_pk = manager.all().order_by('pk').last().pk
    sequence_name = 'layers_{}_{}_seq'.format(model.__name__.lower(), unique_key)
    with connection.cursor() as cursor:
        cursor.execute("SELECT setval('{}', {}, true);".format(sequence_name, max_theme_pk))


class SiteFlags(object):#(models.Model):
    """Add-on class for displaying sites in the list_display
    in the admin.
    """
    def primary_site(self):
        return self.site.filter(id=1).exists()
    primary_site.boolean = True

    def preview_site(self):
        return self.site.filter(id=2).exists()
    preview_site.boolean = True

class AllObjectsManager(models.Manager):
    use_in_migrations = True

class Theme(models.Model, SiteFlags):
    THEME_TYPE_CHOICES = (
    ('radio', 'radio: select 1 layer at a time'),
    ('checkbox', 'checkbox: support simultaneous layers'),
    )
    site = models.ManyToManyField(Site,  related_name='%(class)s_site')
    name = models.CharField(max_length=255, verbose_name="System Name",
                            help_text='e.g.: "Grandparent|Parent|Name". Spaces are allowed.')
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    default_keyword = models.CharField(null=True, blank=True, max_length=100)
    placeholder_text = models.CharField(null=True, blank=True, max_length=100)
    display_name = models.CharField(max_length=100)
    is_top_theme = models.BooleanField(default=False, verbose_name="Is Top Level Theme", help_text="Check this box to show this level at the top tier of the layer picker")
    theme_type = models.CharField(max_length=50, choices=THEME_TYPE_CHOICES, blank=True, default='checkbox', 
                                  help_text='This only impacts how many LAYERS can be activated at once. This does not impact child-themes or their layers')
    # Modify Theme model to include order field but don't want subthemes to necessarily have an order, make order field optional
    order = models.PositiveIntegerField(default=10, verbose_name='Default Order', help_text="Only used for 'Top Level Themes'") 

    ######################################################
    #           DATES                                    #
    ######################################################
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    is_visible = models.BooleanField(default=True)

    is_dynamic = models.BooleanField(default=False)
    dynamic_url = models.TextField(blank=True, null=True, default=None)

    # need to add data_source, data_notes, source, (prop) data_url, (prop) catalog_html to match v1 subtheme/parent layer creation
    data_source = models.CharField(max_length=255, blank=True, null=True)
    data_notes = models.TextField(blank=True, null=True, default=None)
    source = models.CharField(max_length=255, blank=True, null=True, help_text='link back to the data source')
    disabled_message = models.CharField(max_length=255, blank=True, null=True, default=None)
    data_download = models.CharField(max_length=255, blank=True, null=True, help_text='link to download the data')


    description = models.TextField(blank=True, null=True, default=None)
    overview = models.TextField(blank=True, null=True, default=None)
    learn_more = models.CharField(max_length=255, blank=True, null=True, default=None, help_text='MDAT/VTR/CAS: link to learn more')
    
    slug_name = models.CharField(max_length=200, blank=True, null=True)

    header_image = models.CharField(max_length=255, blank=True, null=True)
    header_attrib = models.CharField(max_length=255, blank=True, null=True)
    thumbnail = models.URLField(max_length=255, blank=True, null=True)

    factsheet_thumb = models.CharField(max_length=255, blank=True, null=True)
    factsheet_link = models.CharField(max_length=255, blank=True, null=True)

    # not really using these atm
    feature_image = models.CharField(max_length=255, blank=True, null=True)
    feature_excerpt = models.TextField(blank=True, null=True)
    feature_link = models.CharField(max_length=255, blank=True, null=True)

    ######################################################
    #                        LEGEND                      #
    # Child layers can inherit legends from parent themes#
    ######################################################
    show_legend = models.BooleanField(default=True, help_text='show the legend for this layer if available')
    legend = models.CharField(max_length=255, blank=True, null=True, help_text='URL or path to the legend image file')
    legend_title = models.CharField(max_length=255, blank=True, null=True, help_text='alternative to using the layer name')
    legend_subtitle = models.CharField(max_length=255, blank=True, null=True)

    order_records = GenericRelation('ChildOrder')

    objects = CurrentSiteManager('site')
    all_objects = AllObjectsManager()
    
    def url(self):
        # RDH Backward compatibility hack: Of all parent layers, only two had a value for 'url' that wasn't ''.
        #   We can hardcode those 2 values into this property to maintain 100% backward compatibility without needing to maintain new DB Fields.
        v1_parent_layer_urls = {
            "5258": "https://coast.noaa.gov/arcgismc/rest/services/Hosted/WastewaterOutfallPipes/FeatureServer/",
            "5141": "https://oceandata.rad.rutgers.edu/arcgis/rest/services/RenewableEnergy/NYBightProposedCommercialLeases/MapServer/export",
        }

        if str(self.pk) in v1_parent_layer_urls.keys():
            return v1_parent_layer_urls[str(self.pk)]
        elif not self.parent == None:
            return ''

        return '/visualize/#x=-73.24&y=38.93&z=7&logo=true&controls=true&basemap=Ocean&themes[ids][]={}&tab=data&legends=false&layers=true'.format(self.id)
    
    @property
    def learn_link(self):
        domain = get_domain(8000)
        return '{}/learn/{}'.format(domain, self.name)
    
    @property
    def parent(self):
        
        # Get the ContentType for the Theme model
        content_type = ContentType.objects.get_for_model(self.__class__)

        # Find the ChildOrder instance that refers to this theme
        child_orders = ChildOrder.objects.filter(object_id=self.id, content_type=content_type)
        # Child orders have no concept of 'site'. To ensure 'site' is respected between layers 
        #   and themes, we can query 'objects' by the possible ids of matching themes
        parent_theme_ids = [x.parent_theme.pk for x in child_orders]
        parent_theme = Theme.objects.filter(pk__in=parent_theme_ids).order_by('order', 'name', 'id').first()

        if parent_theme:
            return parent_theme
        return None
    
    @property
    def top_parent(self):
        parent = self.parent
        if parent == None:
            return self
        while parent.parent != None:
            parent = parent.parent

        return parent

    @property
    def ancestor_ids(self):
        # Get the ContentType for the Theme model
        content_type = ContentType.objects.get_for_model(self.__class__)

        # Find the ChildOrder instance that refers to this theme
        parent_orders = ChildOrder.objects.filter(object_id=self.id, content_type=content_type)
        # Child orders have no concept of 'site'. To ensure 'site' is respected between layers 
        #   and themes, we can query 'objects' by the possible ids of matching themes
        parent_theme_ids = [x.parent_theme.pk for x in parent_orders]
        parent_themes = Theme.objects.filter(pk__in=parent_theme_ids).order_by('order', 'name', 'id')

        # Initialize an empty list to hold ancestor theme ids
        ancestor_theme_ids = []
        for parent in parent_themes:
            ancestor_theme_ids.append(parent.pk)
            ancestor_theme_ids.extend(parent.ancestor_ids)

        ancestor_theme_ids = list(set(ancestor_theme_ids))
        return ancestor_theme_ids

    @property
    def ancestors(self):
        return Theme.objects.filter(pk__in=self.ancestor_ids)

    ######################################################
    #           CATALOG COMPATIBILITY                    #
    ######################################################

    @property
    def data_url(self):

        if not self.parent:
            data_catalog_url = "/data-catalog/{}/".format(self.name)
            return data_catalog_url
     
        # Return None if DATA_CATALOG_ENABLED is False, or if no parent or slug_name is found
        if settings.DATA_CATALOG_ENABLED and self.is_visible:
            # parent_theme = self.parent
            try:
                parent_theme = self.top_parent
            except IndexError:
                parent_theme = False

            
            if parent_theme:
                # Format the parent theme's name to be URL-friendly
                # This can be custom tailored if you store slugs differently
                parent_theme_slug = parent_theme.name.replace(" ", "-")
                
                # Ensure there's a slug_name to use for constructing the URL
                if self.slug_name:
                    # Construct the URL
                    
                    data_catalog_url = "/data-catalog/{}/#layer-info-{}".format(parent_theme_slug, self.slug_name)
                    return data_catalog_url

        return None
    
    @property
    def bookmark(self):
        # RDH Backward compatibility hack: Of all parent layers, only six had a value for 'bookmark'.
        #   We can hardcode those 6 values into this property to maintain 100% backward compatibility without needing to maintain new DB Fields.
        v1_parent_bookmarks = {
            '271': "/visualize/#x=-75.57&y=39.18&z=7&logo=true&controls=true&dls%5B%5D=false&dls%5B%5D=0.5&dls%5B%5D=272&basemap=Ocean&themes%5Bids%5D%5B%5D=4&tab=data&legends=false&layers=true",
            '292': "/visualize/#x=-75.57&y=39.18&z=7&logo=true&controls=true&dls%5B%5D=true&dls%5B%5D=0.7&dls%5B%5D=311&basemap=Ocean&themes%5Bids%5D%5B%5D=4&tab=active&legends=false&layers=true",
            '80': "/visualize/#x=-73.24&y=38.93&z=7&logo=true&controls=true&dls%5B%5D=true&dls%5B%5D=0.6&dls%5B%5D=80&basemap=Ocean&themes%5Bids%5D%5B%5D=16&tab=data&legends=false&layers=true",
            '97': "/visualize/#x=-73.26&y=39.01&z=7&logo=true&controls=true&dls%5B%5D=true&dls%5B%5D=0.5&dls%5B%5D=98&basemap=Ocean&themes%5Bids%5D%5B%5D=8&tab=data&legends=false&layers=true",
            '224': "/visualize/#x=-74.42&y=39.38&z=7&logo=true&controls=true&dls%5B%5D=true&dls%5B%5D=0.5&dls%5B%5D=225&basemap=Ocean&themes%5Bids%5D%5B%5D=8&tab=data&legends=false&layers=true",
            '142': "/visualize/#x=-73.40&y=39.47&z=7&logo=true&controls=true&dls%5B%5D=true&dls%5B%5D=0.5&dls%5B%5D=143&basemap=Ocean&themes%5Bids%5D%5B%5D=8&tab=data&legends=false&layers=true"
        }
        if str(self.pk) in v1_parent_bookmarks.keys():
            return v1_parent_bookmarks[str(self.pk)]
        return None

    @property
    def bookmark_link(self):
        if self.bookmark and "%5D={}&".format(self.id) in self.bookmark:
            return self.bookmark

        if self.parent and self.parent.bookmark and len(self.parent.bookmark) > 0:
            return self.parent.bookmark.replace('<layer_id>', str(self.id))
        
        if not self.parent == None and self.parent.name in ['vtr', 'mdat', 'cas', 'marine-life-library']:
            # RDH: Most Marine Life layers seem to have bogus bookmarks. If the first line of this def
            #   isn't true, then we likely need to give users something that will work. This should do it.
            root_str = '/visualize/#x=-73.24&y=38.93&z=7&logo=true&controls=true&basemap=Ocean'
            layer_str = '&dls%5B%5D=true&dls%5B%5D=0.5&dls%5B%5D={}'.format(self.id)
            themes_str = ''
            if self.parent:
                themes_str = '&themes%5Bids%5D%5B%5D={}'.format(self.parent.id)

            panel_str = '&tab=data&legends=false&layers=true'

            return "{}{}{}{}".format(root_str, layer_str, themes_str, panel_str)

        if self.parent:
            # RDH 2024-05-06:  All bookmark_link requests are v1 'Layer' requests. If they get here, they wanted a parent layer
            return self.top_parent.url()
        else:
            return self.data_url
    
    @property
    def kml(self):
        # RDH Backward compatibility hack: Of all parent layers, only 26 had a value for 'kml', and all were ''.
        #   We can hardcode those 26 pks to maintain 100% backward compatibility without needing to maintain new DB Fields.
        # if self.pk in [3305, 80, 842, 840, 454, 344, 417, 3324, 838, 3927, 843, 4540, 545, 538, 1338, 163, 210, 136, 780, 1347, 1331, 224, 3310, 4509, 4475, 1756]:
        #     return ""
        # else:
        #     return None

        # RDH: str(None) == 'None'. That is bonkers. KML will always be a string, so we just want to return ''
        return ''
        
    @property
    def data_download_link(self):
        # RDH: str(None) == 'None'. That is bonkers. Links will always be a string, so we just want to return ''
        return str(self.data_download or '')
        
    @property
    def metadata_link(self):
        # RDH Backward compatibility hack: Of all parent layers, only 49 had a value for 'metadata'.
        #   We can hardcode those 49 values to maintain 100% backward compatibility without needing to maintain new DB Fields.
        v1_parent_metadata = {
            "5765": "/static/data_manager/metadata/pdf/BoatRamps_WaterTrails_Metadata_20230718.pdf",
            "5539": "/static/data_manager/metadata/pdf/BoatRamps_WaterTrails_Metadata_20230718.pdf",
            "5849": "/static/data_manager/metadata/pdf/AcidificationMonitoringMidA_Ver202310_metadata.pdf",
            "5775": "/static/data_manager/metadata/pdf/SeaTurtleStrandings_Metadata_10_2023.pdf",
            "842": "http://seamap.env.duke.edu/models/mdat/Fish/MDAT_NEFSC_Fish_Summary_Products_Metadata.pdf",
            "840": "http://seamap.env.duke.edu/models/mdat/Mammal/MDAT_Mammal_Summary_Products_Metadata.pdf",
            "454": "http://seamap.env.duke.edu/models/mdat/Mammal/MDAT_Mammal_Summary_Products_v1_1_2016_08_29_Metadata.pdf",
            "344": "http://seamap.env.duke.edu/models/mdat/Avian/MDAT_Avian_Summary_Products_v1_1_2016_08_29_Metadata.pdf",
            "417": "http://seamap.env.duke.edu/models/mdat/Fish/MDAT_NEFSC_Fish_Summary_Products_v1_1_2016_08_29_Metadata.pdf",
            "2950": "http://seamap.env.duke.edu/models/mdat/Fish/MDAT_NEFSC_Fish_Summary_Products_Metadata.pdf",
            "5258": "https://www.fisheries.noaa.gov/inport/item/66706",
            "841": "http://seamap.env.duke.edu/models/mdat/Mammal/MDAT_Mammal_Summary_Products_Metadata.pdf",
            "839": "http://seamap.env.duke.edu/models/mdat/Avian/MDAT_Avian_Summary_Products_Metadata.pdf",
            "2949": "http://seamap.env.duke.edu/models/mdat/Fish/MDAT_NEFSC_Fish_Summary_Products_Metadata.pdf",
            "838": "http://seamap.env.duke.edu/models/mdat/Avian/MDAT_Avian_Summary_Products_Metadata.pdf",
            "5311": "https://www.northeastoceandata.org/files/metadata/Themes/AIS/AllAISVesselTransitCounts2021.pdf",
            "843": "http://seamap.env.duke.edu/models/mdat/Fish/MDAT_NEFSC_Fish_Summary_Products_Metadata.pdf",
            "5207": "/static/data_manager/metadata/pdf/METADATA__MarineMammalStrandings_5_2022.pdf",
            "5220": "/static/data_manager/metadata/pdf/METADATA__MarineMammalStrandings_5_2022.pdf",
            "545": "/static/data_manager/metadata/html/NPP_SeasonalMax.html",
            "538": "/static/data_manager/metadata/html/Fronts_SeasonalMax.html",
            "313": "/static/data_manager/metadata/html/CASMetadata.html",
            "1338": "https://www.northeastoceandata.org/files/metadata/Themes/AIS/AllAISVesselTransitCounts2017.pdf",
            "163": "/static/data_manager/metadata/html/RecBoaterSurvey_All_Activities_Pts_metadata.html",
            "210": "http://opdgig.dos.ny.gov/geoportal/catalog/search/resource/detailsnoheader.page?uuid={3B5083DA-2060-4F5D-8416-201A0A2B962B}",
            "136": "/static/data_manager/metadata/html/CoastalRec_overview.html",
            "780": "https://www.northeastoceandata.org/files/metadata/Themes/AIS/AllAISVesselTransitCounts2015.pdf",
            "1347": "https://www.northeastoceandata.org/files/metadata/Themes/AIS/AllAISVesselTransitCounts2016.pdf",
            "97": "/static/data_manager/metadata/html/AIS2011.html",
            "1331": "https://www.northeastoceandata.org/files/metadata/Themes/AIS/AllAISVesselTransitCounts2013.pdf",
            "224": "/static/data_manager/metadata/pdf/AtlanticVesselDensity2013Documentation_20150710.pdf",
            "3310": "https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0196127",
            "4509": "https://www.northeastoceandata.org/files/metadata/Themes/AIS/AllAISVesselTransitCounts2019.pdf",
            "4475": "https://www.northeastoceandata.org/files/metadata/Themes/AIS/AllAISVesselTransitCounts2018.pdf",
            "1756": "/static/data_manager/metadata/html/FishSpeciesThroughTime_metadata.htm",
            "3315": "/static/data_manager/metadata/pdf/METADATA__HFRadarSurfaceCurrents_MidAtlantic.pdf",
            "55": "/static/data_manager/metadata/html/CASMetadata.html",
            "4842": "https://www.northeastoceandata.org/files/metadata/Themes/Habitat/FishingEffectsPercentSeabedHabitatDisturbancemetadata.pdf",
            "4841": "https://www.northeastoceandata.org/files/metadata/Themes/Habitat/FishingEffectsPercentSeabedHabitatDisturbancemetadata.pdf",
            "4843": "https://www.northeastoceandata.org/files/metadata/Themes/Habitat/FishingEffectsPercentSeabedHabitatDisturbancemetadata.pdf",
            "5126": "https://www.northeastoceandata.org/files/metadata/Themes/AIS/AllAISVesselTransitCounts2020.pdf",
            "142": "/static/data_manager/metadata/html/AIS2012.html",
            "5787": "/static/data_manager/metadata/pdf/SeaTurtleStrandings_Metadata_10_2023.pdf",
            "5141": "https://www.boem.gov/renewable-energy/state-activities/new-york-bight",
        }
        
        if str(self.pk) in v1_parent_metadata.keys():
            return v1_parent_metadata[str(self.pk)]
        else:
            return None

    @property
    def metadata(self):
        return self.metadata_link

    @property
    def tiles_link(self):
        # RDH Backwards compatibility hack -- allow some parent layer (themes) to share 'tiles' for migration testing purposes
        if self.pk in [4878, ]:
            return self.slug_name
        return None

    @property
    def data_overview(self):
        return self.overview

    @property
    def data_overview_text(self):
        if not self.overview and self.parent:
            return self.parent.overview
        else:
            return self.overview

    @property
    def is_sublayer(self):
        if self.parent:
            return True
        return False

    @property
    def children(self):
        return ChildOrder.objects.filter(parent_theme=self)

    @property
    def layer_count(self):
        layerType = ContentType.objects.get_for_model(Layer)
        themeType = ContentType.objects.get_for_model(Theme)
        children_count = 0
        for child in self.children:
            if child.content_type == layerType:
                children_count += 1
            elif child.content_type == themeType:
                child_layer_count = child.content_object.layer_count
                # dynamic themes will appear to have 0 children, since they have no
                # layer records. Instead, let's count each dynamic subtheme.
                if child_layer_count == 0 and child.content_object.is_dynamic:
                    children_count += 1
                else:
                    children_count += child_layer_count
        return children_count
    
    @property
    def badge(self):
        return self.layer_count
    
    @property
    def badge_text(self):
        return 'Records'

    @property
    def catalog_html(self):
        from django.template.loader import render_to_string
        try:
            return render_to_string(
                "data_catalog/includes/cacheless_layer_info.html",
                {
                    'layer': self,
                    # 'sub_layers': self.sublayers.exclude(layer_type="placeholder")
                }
            )
        except Exception as e:
            print(e)
        
    @property
    def orders(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return ChildOrder.objects.filter(object_id=self.id, content_type=content_type)

    def shortDict(self, site=None, order=None):
        if site == None:
            site_id = ''
        else:
            site_id = site.pk
        cache_label = 'layers_theme_shortdict_{}_{}'.format(self.pk, site_id)
        layers_dict = cache.get(cache_label)
        if not layers_dict:
            childOrders = ChildOrder.objects.filter(parent_theme=self)
            if not site == None:
                site_children_pks = []
                for child in childOrders:
                    if site in child.content_object.site.all():
                        site_children_pks.append(child.pk)
                childOrders = childOrders.filter(pk__in=site_children_pks)
            subthemes = []
            layers = []
            for child in childOrders:
                if child.content_type.model == 'theme' and child.content_object.is_visible:
                    subthemes.append(child.content_object.shortDict(site=site, order=child.order))
                if child.content_type.model == 'layer' and child.content_object.is_visible:
                    layers.append(child.content_object.shortDict(site=site, order=child.order, parent=self))
            
            children_list = subthemes + layers
            sorted_children_list = sorted(children_list, key=lambda x: (x['order'], x['name']))

            layers_dict = {
                'id': self.id,
                'parent': None,
                'order': order if not order == None else 0,
                'name': self.display_name,
                'type': 'theme',
                'slug_name': self.slug_name,
                'bookmark_link': self.bookmark_link,
                'is_sublayer': self.is_sublayer,
                'children': sorted_children_list,
            }
            cache.set(cache_label, layers_dict, 60*60*24*7)
        return layers_dict

    def __str__(self):
        return "{} [T-{}]".format(self.name, self.pk)

    def save(self, *args, **kwargs):
        content_type = ContentType.objects.get_for_model(self.__class__)
        dirty_cache_keys = []
        # clean keys tied to /children/ api
        children = ChildOrder.objects.filter(object_id=self.pk, content_type=content_type)
        ancestor_ids = self.ancestor_ids
        if self.slug_name == None or self.slug_name == '':
            self.slug_name = "{}{}".format(slugify(self.name), self.pk)
        for site_id in [x.pk for x in Site.objects.all()] + ['']:
            for child in children:
                dirty_cache_keys.append('layers_childorder_{}_{}'.format(child.pk, site_id))
            for ancestor_id in ancestor_ids:
                dirty_cache_keys.append('layers_theme_shortdict_{}_{}'.format(ancestor_id, site_id))
            dirty_cache_keys.append('layers_theme_shortdict_{}_{}'.format(self.pk, site_id))        
        for key in dirty_cache_keys:
            cache.delete(key)
            with connection.cursor() as cursor:
                cursor.execute("NOTIFY {}, 'deletecache:{}'".format(settings.DB_CHANNEL, key))
        try:
            with transaction.atomic():
                super(Theme, self).save(*args, **kwargs)
        except IntegrityError as e:
            if 'duplicate key value violates unique constraint' in str(e):
                model = type(self)
                unique_key = str(e).split('Key (')[-1].split(')=(')[0]
                update_model_sequence(model, unique_key, manager=model.all_objects)
                with transaction.atomic():
                    super(Theme, self).save(*args, **kwargs)
            else:
                raise IntegrityError(e)

    class Meta:
        ordering = ['order']
        app_label = 'layers'
        indexes = [
            models.Index(fields=['id',]),
        ]


# in admin, how can we show all layers regardless of layer type, without querying get all layers that are wms, get layers that are arcgis, etc, bc that is a lot of subqueries
class Layer(models.Model, SiteFlags):
    LAYER_TYPE_CHOICES = (
        ('XYZ', 'XYZ'),
        ('WMS', 'WMS'),
        ('ArcRest', 'ArcRest'),
        ('ArcFeatureServer', 'ArcFeatureServer'),
        ('Vector', 'Vector'),
        ('VectorTile', 'VectorTile'),
        ('slider', 'slider'),
    )
    ######################################################
    #                        KEY INFO                    #
    ######################################################
    name = models.CharField(max_length=100)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    slug_name = models.CharField(max_length=200, blank=True, null=True)
    layer_type = models.CharField(max_length=50, choices=LAYER_TYPE_CHOICES, help_text='use placeholder to temporarily remove layer from TOC')
    url = models.TextField(blank=True, null=True, default=None)
    site = models.ManyToManyField(Site, related_name='%(class)s_site')

    order_records = GenericRelation('ChildOrder')
    
    objects = CurrentSiteManager('site')
    all_objects = AllObjectsManager()

    ######################################################
    #                      DISPLAY                       #
    ######################################################
    opacity = models.FloatField(default=.5, blank=True, null=True, verbose_name="Initial Opacity")
    is_disabled = models.BooleanField(default=False, help_text='when disabled, the layer will still appear in the TOC, only disabled')
    disabled_message = models.CharField(max_length=255, blank=True, null=True, default=None)
    is_visible = models.BooleanField(default=True)
    search_query = models.BooleanField(default=False, help_text='Select when layers are queryable - e.g. MDAT and CAS')

    ######################################################
    #                     DATA CATALOG                   #
    ######################################################
    # RDH: geoportal_id is used in data_manager view 'geoportal_ids', which is not used for the built-in catalog tech
    #   but is critical for projects using GeoPortal as their catalog
    geoportal_id = models.CharField(max_length=255, blank=True, null=True, default=None, help_text="GeoPortal UUID")
    #data catalog links
    catalog_name = models.TextField(null=True, blank=True, help_text="name of associated record in catalog", verbose_name='Catalog Record Name')
    catalog_id = models.TextField(null=True, blank=True, help_text="unique ID of associated record in catalog", verbose_name='Catalog Record Id')


    proxy_url = models.BooleanField(default=False, help_text="proxy layer url through marine planner")
    shareable_url = models.BooleanField(default=True, help_text='Indicates whether the data layer (e.g. map tiles) can be shared with others (through the Map Tiles Link)')

    # UTFURL to be deprecated in v25
    utfurl = models.CharField(max_length=255, blank=True, null=True)
    ######################################################
    #                        LEGEND                      #
    ######################################################
    show_legend = models.BooleanField(default=True, help_text='show the legend for this layer if available')
    legend = models.CharField(max_length=255, blank=True, null=True, help_text='URL or path to the legend image file')
    legend_title = models.CharField(max_length=255, blank=True, null=True, help_text='alternative to using the layer name')
    legend_subtitle = models.CharField(max_length=255, blank=True, null=True)


    ######################################################
    #                        METADATA                    #
    ######################################################
    description = models.TextField(blank=True, null=True)
    overview = models.TextField(blank=True, null=True, default=None)     #formerly data_overview in data_manager
    data_source = models.CharField(max_length=255, blank=True, null=True)
    data_notes = models.TextField(blank=True, null=True, default=None)
    data_publish_date = models.DateField(auto_now=False, auto_now_add=False, null=True, blank=True, default=None, verbose_name='Date published', help_text='YYYY-MM-DD')
    
    ######################################################
    #                        LINKS                       #
    ######################################################
    metadata = models.CharField(max_length=255, blank=True, null=True, help_text='link to view/download the metadata')
    source = models.CharField(max_length=255, blank=True, null=True, help_text='link back to the data source')
    bookmark = models.CharField(max_length=755, blank=True, null=True, help_text='link to view data layer in the planner')
    kml = models.CharField(max_length=255, blank=True, null=True, help_text='link to download the KML')
    data_download = models.CharField(max_length=255, blank=True, null=True, help_text='link to download the data')
    learn_more = models.CharField(max_length=255, blank=True, null=True, default=None, help_text='link to view description in the Learn section')
    map_tiles = models.CharField(max_length=255, blank=True, null=True, help_text='internal link to a page that details how others might consume the data')

    ######################################################
    #                  Attribute Reporting               #
    ######################################################
    label_field = models.CharField(max_length=255, blank=True, null=True, help_text="Which field should be used for labels and feature identification in reports?")
    #geojson javascript attribution
    EVENT_CHOICES = (
        ('click', 'click'),
        ('mouseover', 'mouseover')
    )
    # RDH: Adds a 'title' to the serialize_attributes dict - not sure if that's used.
    # attribute_title = models.CharField(max_length=255, blank=True, null=True)
    attribute_event = models.CharField(max_length=35, choices=EVENT_CHOICES, default='click')
    attribute_fields = models.ManyToManyField('AttributeInfo', blank=True)
    # RDH: 2024-05-24: Annotated DOES have visualization logic tied to it,
    #   BUT: all known records are set to 'False'
    annotated = models.BooleanField(default=False)
    # RDH: 2024-05-24: compress_display is NOT USED anymore.
    compress_display = models.BooleanField(default=False)
    mouseover_field = models.CharField(max_length=75, blank=True, null=True, default=None, help_text='feature level attribute used in mouseover display')
    
    ######################################################
    #           ESPIS                                    #
    ######################################################
    #ESPIS Upgrade - RDH 7/23/2017
    #ESPIS Deprecated in 2024, to be removed in v25
    espis_enabled = models.BooleanField(default=False)
    ESPIS_REGION_CHOICES = (
        ('Mid Atlantic', 'Mid Atlantic'),
    )
    espis_search = models.CharField(max_length=255, blank=True, null=True, default=None, help_text="keyphrase search for ESPIS Link")
    espis_region = models.CharField(max_length=100, blank=True, null=True, default=None, choices=ESPIS_REGION_CHOICES, help_text="Region to search within")

    ######################################################
    #           DATES                                    #
    ######################################################
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    minZoom = models.FloatField(blank=True, null=True, default=None, verbose_name="Minimum zoom")
    maxZoom = models.FloatField(blank=True, null=True, default=None, verbose_name="Maximum zoom")

    ######################################################
    #          COMPANION LAYERS                          #
    ######################################################
    @property
    def has_companion(self):
        for companionship in self.companionships.all():
            if companionship.companions.exists():
                return True
        return False


    ######################################################
    #          Data Catalog Stuff                        #
    ######################################################
    @property
    def data_url(self):

        # Return None if DATA_CATALOG_ENABLED is False, or if no parent or slug_name is found
        if settings.DATA_CATALOG_ENABLED:
            parent_theme = False
            try:
                parent_theme = self.parent
                if not parent_theme in self.themes:
                    parent_theme = self.themes.order_by('order', 'name', 'id').first()
            except IndexError:
                pass
            
            if parent_theme and parent_theme.is_visible:
                # Format the parent theme's name to be URL-friendly
                # This can be custom tailored if you store slugs differently
                parent_theme_slug = parent_theme.top_parent.name.replace(" ", "-")
                
                # Ensure there's a slug_name to use for constructing the URL
                if self.slug_name and not self.slug_name == None:
                    slug_name = self.slug_name
                else:
                    slug_name = slugify(self.name)
                    # Construct the URL
                if slug_name:
                    data_catalog_url = "/data-catalog/{}/#layer-info-{}".format(parent_theme_slug, slug_name)
                    return data_catalog_url

        return None
    
    @property
    def attributes(self):
        return {'compress_attributes': self.compress_display,
                'event': self.attribute_event,
                'attributes': [{'display': attr.display_name, 'field': attr.field_name, 'precision': attr.precision} for attr in self.attribute_fields.all().order_by('order')],
                'mouseover_attribute': self.mouseover_field,
                'preserved_format_attributes': [attr.field_name for attr in self.attribute_fields.filter(preserve_format=True)]
        }
    
    @property
    def catalog_html(self):
        from django.template.loader import render_to_string
        try:
            return render_to_string(
                "data_catalog/includes/cacheless_layer_info.html",
                {
                    'layer': self,
                    # 'sub_layers': self.sublayers.exclude(layer_type="placeholder")
                }
            )
        except Exception as e:
            print(e)

    @property
    def data_download_link(self):
        if self.data_download and self.data_download.lower() == 'none':
            return None
        if self.parent and not self.data_download and self.is_sublayer:
            return self.parent.data_download
        else:
            return self.data_download
        
    @property
    def metadata_link(self):
        if self.metadata and self.metadata.lower() == 'none':
            return None
        if not self.metadata:
            if self.is_sublayer and self.parent:
                return self.parent.metadata
            else:
                return None
        else:
            return self.metadata
        
    @property
    def tiles_link(self):
        if self.is_shareable and self.layer_type in ['XYZ', 'ArcRest', 'WMS', 'slider']:
            domain = get_domain(8000)
            return self.slug_name
        return None

    @property
    def lookups(self):
        if not self.specific_instance == None and (
            hasattr(self.specific_instance, 'lookup_field') and
            hasattr(self.specific_instance, 'lookup_table')
        ):
            return {'field': self.specific_instance.lookup_field,
                    'details': [{'value': lookup.value, 'color': lookup.color, 'stroke_color': lookup.stroke_color, 'stroke_width': lookup.stroke_width, 'dashstyle': lookup.dashstyle, 'fill': lookup.fill, 'graphic': lookup.graphic, 'graphic_scale': lookup.graphic_scale} for lookup in self.specific_instance.lookup_table.all()]}
        return {
            'field': None,
            'details': []
        }

    def dimensionRecursion(self, dimensions, associations):
        if not dimensions:
            return None

        dimension = dimensions.pop(0)
        associationArray = {}

        for value in sorted(dimension.multilayerdimensionvalue_set.all(), key=lambda x: x.order):
            value_associations = associations.filter(pk__in=[x.pk for x in value.associations.all()])
            
            if dimensions:  # If there are more dimensions to process
                nested_association_array = self.dimensionRecursion(list(dimensions), value_associations)
                associationArray[str(value.value)] = nested_association_array
            else:  # No more dimensions, just collect the layers
                if len(value_associations) >= 1 and value_associations[0].layer:
                    associationArray[str(value.value)] = value_associations[0].layer.pk
                else:
                    associationArray[str(value.value)] = None

        return associationArray

    @property
    def is_multilayer_parent(self):
        return len(self.multilayerdimension_set.all()) > 0

    @property
    def is_multilayer(self):
        return len(self.associated_layer.all()) > 0

    @property
    def dimensions(self):
        return sorted([
            {
                'label': x.label,
                'name': x.name,
                'order': x.order,
                'animated': x.animated,
                'angle_labels': x.angle_labels,
                'nodes': sorted([
                    {
                        'value': y.value,
                        'label': y.label,
                        'order': y.order
                    }
                    for y in x.multilayerdimensionvalue_set.all()
                ], key=lambda y: y['order'])
            }
            for x in self.multilayerdimension_set.all()
        ], key=lambda x: x['order'])
    
    @property
    def associated_multilayers(self):
        if len(self.multilayerdimension_set.all()) > 0:
            return self.dimensionRecursion(sorted(self.multilayerdimension_set.all(), key=lambda x: x.order), self.parent_layer.all())
        else:
            return {}
        
    @property
    def data_overview(self):
        return self.overview

    @property
    def data_overview_text(self):
        if not self.overview and self.is_sublayer and self.parent:
            return self.parent.overview
        else:
            return self.overview
    
    @property
    def tooltip(self):
        if self.description and self.description.strip() != '':
            return self.description
        elif self.parent and self.parent.description and self.parent.description.strip() != '':
            return self.parent.description
        else:
            return self.data_overview_text
        
    @property
    def is_shareable(self):
        # RDH: Data_Manager had this option for parent layers, but ALL were == True. 
        return self.shareable_url
    
    @property
    def top_parents(self):
        # Get the ContentType for the Layer model
        layer_content_type = ContentType.objects.get_for_model(self.__class__)

        # Find the ChildOrder instances that refer to this layer
        child_orders = ChildOrder.objects.filter(object_id=self.id, content_type=layer_content_type)

        parents = []
        for child in child_orders.order_by('parent_theme__order'):
            parent = child.parent_theme
            while parent.parent != None:
                parent = parent.parent
            parents.append(parent)

        return parents
    
    @property
    def top_parent(self):
        if self.parent == None:
            return None
        else:
            return self.parent.top_parent

    
    @property
    def parent_orders(self):
        # Get the ContentType for the Layer model
        layer_content_type = ContentType.objects.get_for_model(self.__class__)

        # Find the ChildOrder instance that refers to this layer
        child_orders = ChildOrder.objects.filter(
            object_id=self.id, content_type=layer_content_type
        ).order_by(
            'parent_theme__order', 'order', 'parent_theme__name', 'parent_theme__id'
        )
        return child_orders

    @property
    def parents(self):
        # Child orders have no concept of 'site'. To ensure 'site' is respected between layers 
        #   and themes, we can query 'objects' by the possible ids of matching themes
        parent_theme_ids = [x.parent_theme.pk for x in self.parent_orders]
        parent_themes = Theme.all_objects.filter(pk__in=parent_theme_ids).order_by('order', 'name', 'id')
            
        return parent_themes
    
    @property
    def parent(self):
        parent_themes = self.parents
        for pt in parent_themes:
            # A layer can be a sublayer in one theme and a top-level layer in another.
            # This identifies the highest level parent theme
            # This is helpful for matching the old data_manager API v1: bookmark_link <- is_sublayer <- parent
            # It's not terribly important otherwise
            if pt.parent == None:
                return pt
        if parent_themes.count() > 0:
            return parent_themes.first()
        return None

    @property
    def ancestor_ids(self):
        lineage_ids = []
        parents = self.parents
        for parent in parents:
            lineage_ids += [parent.pk,]
            lineage_ids += parent.ancestor_ids
        return list(set(lineage_ids))
    
    @property
    def is_sublayer(self):
        if self.parent == None:
            return False
        return self.parent.parent != None

    
    @property
    def themes(self):
        # Get the ContentType for the Layer model
        layer_content_type = ContentType.objects.get_for_model(self.__class__)

        # Find the ChildOrder instance that refers to this layer
        child_orders = ChildOrder.objects.filter(object_id=self.id, content_type=layer_content_type)
        return Theme.all_objects.filter(pk__in=[co.parent_theme.id for co in child_orders]).order_by('order', 'name', 'id')

    @property
    def bookmark_link(self):
        if self.bookmark and "%5D={}&".format(self.id) in self.bookmark:
            return self.bookmark

        if self.is_sublayer and self.parent.bookmark and len(self.parent.bookmark) > 0:
            return self.parent.bookmark.replace('<layer_id>', str(self.id))

        # RDH 2024-05-02:  All parents are now Themes, not Layers.
        # if self.is_parent:
        #     for theme in self.themes.all():
        #         return theme.url()

        # RDH: Most Marine Life layers seem to have bogus bookmarks. If the first line of this def
        #   isn't true, then we likely need to give users something that will work. This should do it.
        root_str = '/visualize/#x=-73.24&y=38.93&z=7&logo=true&controls=true&basemap=Ocean'
        layer_str = '&dls%5B%5D=true&dls%5B%5D={}&dls%5B%5D={}'.format(str(self.opacity), self.id)
        companion_str = ''
        if self.has_companion:
            for companionship in self.companionships.all():
                for companion in companionship.companions.exclude(pk=self.pk):
                    companion_str += '&dls%5B%5D=false&dls%5B%5D={}&dls%5B%5D={}'.format(str(companion.opacity), companion.id)
        themes_str = ''
        if self.themes.all().count() > 0:
            themes_str = '&themes%5Bids%5D%5B%5D={}'.format(self.parent.id)

        panel_str = '&tab=data&legends=false&layers=true'

        return "{}{}{}{}{}".format(root_str, layer_str, companion_str, themes_str, panel_str)
    
    #RDH: Kept to maintain identical V1 results with data manager. This functionality will be deprecated in v25
    def get_espis_link(self):
        if settings.ESPIS_ENABLED and self.espis_enabled:
            search_dict = {}
            if self.espis_search:
                search_dict['q'] = self.espis_search
            if self.espis_region:
                if self.espis_region == "Mid Atlantic":
                    search_dict['bbox'] = "-81.71531609374854, 35.217958254501944, -69.19090203125185, 45.12716611403635"
            if len(search_dict) > 0:
                try:
                    # python 3
                    from urllib.parse import urlencode
                except (ModuleNotFoundError, ImportError) as e:
                    #python 2
                    from urllib import urlencode
                return 'https://esp-boem.hub.arcgis.com/search?{}'.format(urlencode(search_dict))

        return False

    @property
    def model(self):
        layer_type_to_model = {
            'WMS': LayerWMS,
            'ArcRest': LayerArcREST,
            'ArcFeatureServer': LayerArcFeatureService,
            'Vector': LayerVector,
            'XYZ': LayerXYZ,
            # Add more mappings as necessary
        }
        if self.layer_type in layer_type_to_model.keys():
            return layer_type_to_model.get(self.layer_type)
        return None
    
    @property
    def specific_instance(self):
        if not self.model == None:
            try:
                return self.model.objects.get(layer=self)
            except ObjectDoesNotExist as e:
                pass
        return None

    def __str__(self):
        return "{} [L-{}]".format(self.name, self.pk)
    
    def shortDict(self, site=None, order=None, parent=None):
        children = []
        if parent == None:
            parent = self.parent
        if parent == None:
            parent_dict = {}
            if order == None:
                order = 0
        else:
            parent_dict = {'name': parent.display_name}
            if order == None:
                layer_type = ContentType.objects.get_for_model(self.__class__)
                try:
                    order = ChildOrder.objects.get(parent_theme=parent, object_id=self.pk, content_type=layer_type).order
                except Exception as e:
                    order = 0
                    pass
        layers_dict = {
            'id': self.id,
            'type': 'layer',
            'parent': parent_dict,
            'order': order, 
            'name': self.name,
            'slug_name': self.slug_name,
            'bookmark_link': self.bookmark_link,
            'is_sublayer': self.is_sublayer,
            'children': children,
        }
        return layers_dict
    
    def save(self, *args, **kwargs):
        content_type = ContentType.objects.get_for_model(self.__class__)
        dirty_cache_keys = [
            'layers_layer_serialized_details_{}'.format(self.pk),
        ]
        parent_orders = ChildOrder.objects.filter(object_id=self.pk, content_type=content_type)
        ancestor_ids = self.ancestor_ids
        for site_id in [x.pk for x in Site.objects.all()] + ['',]:
            for parent in parent_orders:
                # clean keys tied to /children/ api
                dirty_cache_keys.append('layers_childorder_{}_{}'.format(parent.pk, site_id))
            for ancestor_id in ancestor_ids:
                # clean keys tied to shortDict and the Data Catalog
                dirty_cache_keys.append('layers_theme_shortdict_{}_{}'.format(ancestor_id, site_id))

        for key in dirty_cache_keys:
            cache.delete(key)
            with connection.cursor() as cursor:
                cursor.execute("NOTIFY {}, 'deletecache:{}'".format(settings.DB_CHANNEL, key))
        try:
            with transaction.atomic():
                super(Layer, self).save(*args, **kwargs)
        except IntegrityError as e:
            if 'duplicate key value violates unique constraint' in str(e):
                model = type(self)
                unique_key = str(e).split('Key (')[-1].split(')=(')[0]
                update_model_sequence(model, unique_key, manager=model.all_objects)
                with transaction.atomic():
                    super(Layer, self).save(*args, **kwargs)
            else:
                raise IntegrityError(e)

    class Meta:
        indexes = [
            models.Index(fields=['id',]),
        ]

class Companionship(models.Model):
    # ForeignKey creates a one-to-many relationship
    # (Each companionship relates to one Layer)
    layer = models.ForeignKey(Layer, on_delete=models.CASCADE, related_name='companionships')

    # ManyToManyField creates a many-to-many relationship
    # (Each companionship can relate to multiple Layers and vice versa)
    companions = models.ManyToManyField(Layer, related_name='companion_to')

class ChildOrder(models.Model):
    CHILD_CONTENT_TYPE_CHOICES = (
        models.Q(app_label='layers', model=Theme.__name__.lower()) |
        models.Q(app_label='layers', model=Layer.__name__.lower())
    )

    parent_theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name='parent_theme')
    
    # The generic relation to point to either Theme or Layer
    content_type = models.ForeignKey(ContentType, limit_choices_to=CHILD_CONTENT_TYPE_CHOICES, on_delete=models.CASCADE, verbose_name='Child Type')
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    order = models.PositiveIntegerField(blank=True, null=True, default=10)

    ######################################################
    #           DATES                                    #
    ######################################################
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    # @property
    # def site(self):
    #     parent_site_ids = [x.pk for x in self.parent_theme.site.all()]
    #     content_site_ids = [x.pk for x in self.content_object.site.all()]
    #     return Site.objects.filter(pk__in=parent_site_ids).filter(pk__in=content_site_ids)

    def save(self, *args, **kwargs):
        dirty_cache_keys = []
        # clean keys tied to /children/ api
        for site in Site.objects.all():
            dirty_cache_keys.append('layers_childorder_{}_{}'.format(self.pk, site.pk))
        for key in dirty_cache_keys:
            cache.delete(key)
            with connection.cursor() as cursor:
                cursor.execute("NOTIFY {}, 'deletecache:{}'".format(settings.DB_CHANNEL, key))
        if not self.object_id == None:
            # During import, if this is a dry run there will be no child object for this order.
            try:
                with transaction.atomic():
                    super(ChildOrder, self).save(*args, **kwargs)
            except IntegrityError as e:
                if 'duplicate key value violates unique constraint' in str(e):
                    model = type(self)
                    unique_key = str(e).split('Key (')[-1].split(')=(')[0]
                    update_model_sequence(model, unique_key, manager=model.objects)
                    with transaction.atomic():
                        super(ChildOrder, self).save(*args, **kwargs)
                else:
                    raise IntegrityError(e)

    # def __str__(self):
    #     try:
    #         "{} [{}]".format(self.content_object.name, self.content_object.pk)
    #     except Exception as e:
    #         print(e)
    #         return 'name_failure'

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['id',]),
            models.Index(fields=['parent_theme',]),
            models.Index(fields=['content_type',]),
        ]

class LayerType(models.Model):
    layer = models.ForeignKey(Layer, on_delete=models.CASCADE, unique=True)

    class Meta:
        abstract = True

class VectorType(LayerType):
    CUSTOM_STYLE_CHOICES = (
        (None, '------'),
        ('color', 'color'),
        ('random', 'random'),
    )
    custom_style = models.CharField(
        max_length=255, 
        null=True, blank=True, default=None, 
        choices=CUSTOM_STYLE_CHOICES,
        help_text="Apply a custom styling rule: i.e. 'color' for Native-Land.ca layers, or 'random' to assign arbitary colors"
    )
    #width of layer's features' lines/outlines in pixels
    outline_width = models.IntegerField(blank=True, null=True, default=None, verbose_name="Vector Stroke Width")
    COLOR_PALETTE = []

    COLOR_PALETTE.append(("#FFFFFF", 'white'))
    COLOR_PALETTE.append(("#888888", 'gray'))
    COLOR_PALETTE.append(("#000000", 'black'))
    COLOR_PALETTE.append(("#FF0000", 'red'))
    COLOR_PALETTE.append(("#FFFF00", 'yellow'))
    COLOR_PALETTE.append(("#00FF00", 'green'))
    COLOR_PALETTE.append(("#00FFFF", 'cyan'))
    COLOR_PALETTE.append(("#0000FF", 'blue'))
    COLOR_PALETTE.append(("#FF00FF", 'magenta'))
    #sets the color of the layer's features' lines or outlines, can be either color's name or hex value (Starts with #)
    outline_color = ColorField(
        blank=True,
        null=True,
        default=None,
        verbose_name="Vector Stroke Color",
        samples=COLOR_PALETTE,
    )
    # RDH 20191106 - This is not a thing.
    outline_opacity = models.FloatField(blank=True, null=True, default=None, verbose_name="Vector Stroke Opacity")
   
    #set the color to fill any polygons or circle-icons for points
    fill_opacity = models.FloatField(blank=True, null=True, default=None, verbose_name="Vector Fill Opacity")
    color = ColorField(
        blank=True,
        null=True,
        default=None,
        verbose_name="Vector Fill Color",
        samples=COLOR_PALETTE,
    )
    #set radius of circle in pixels, only applies to point data with no graphics
    point_radius = models.IntegerField(blank=True, null=True, default=None, help_text='Used only for for Point layers (default is 2)')
    #enter URL for image from online for layer's point data
    graphic = models.CharField(max_length=255, blank=True, null=True, default=None, verbose_name="Vector Graphic", help_text="address of image to use for point data")
    #if you need to resize vector graphic image so it looks appropriate on map
    #to make image smaller, use value less than 1, to make image larger, use values larger than 1
    graphic_scale = models.FloatField(blank=True, null=True, default=1.0, verbose_name="Vector Graphic Scale", help_text="Scale for the vector graphic from original size.")

    #use field to specify attribute on layer that you wish to be considered in adding conditional style formatting
    lookup_field = models.CharField(max_length=255, blank=True, null=True, help_text="To override the style based on specific attributes, provide the attribute name here and define your attributes in the Lookup table below.")
    #use widget along with creating Lookup Info records to apply conditional styling to your layer
    lookup_table = models.ManyToManyField('LookupInfo', blank=True)


    class Meta:
        abstract = True

class RasterType(LayerType):
    query_by_point = models.BooleanField(default=False, help_text='Do not buffer selection clicks (not recommended for point or line data)')

    class Meta:
        abstract = True

class ArcServer(LayerType):
    arcgis_layers = models.CharField(max_length=255, blank=True, null=True, help_text='comma separated list of arcgis layer IDs')
    password_protected = models.BooleanField(default=False, help_text='check this if the server requires a password to show layers')
    disable_arcgis_attributes = models.BooleanField(default=False, help_text='Click to disable clickable ArcRest layers')
    
    class Meta:
        abstract = True

class LayerArcREST(ArcServer, RasterType):
    def save(self, *args, **kwargs):
        if not self.id:  # Check if this is a new instance
            self.layer.layer_type = 'ArcRest'
            self.layer.save()
        super(LayerArcREST, self).save(*args, **kwargs)

class LayerArcFeatureService(ArcServer, VectorType):
    def save(self, *args, **kwargs):
        if not self.id:  # Check if this is a new instance
            self.layer.layer_type = 'ArcFeatureServer'
            self.layer.save()
        super(LayerArcFeatureService, self).save(*args, **kwargs)

class LayerXYZ(RasterType):
    def save(self, *args, **kwargs):
        if not self.id:  # Check if this is a new instance
            self.layer.layer_type = 'XYZ'
            self.layer.save()
        super(LayerXYZ, self).save(*args, **kwargs)

class LayerVector(VectorType):
    def save(self, *args, **kwargs):
        if not self.id:  # Check if this is a new instance
            self.layer.layer_type = 'Vector'
            self.layer.save()
        super(LayerVector, self).save(*args, **kwargs)

class LayerWMS(RasterType):
    wms_help = models.BooleanField(default=False, help_text='Enable simple selection for WMS fields. Only supports WMS 1.1.1')
    WMS_VERSION_CHOICES = (
        (None, ''),
        ('1.0.0', '1.0.0'),
        ('1.1.0', '1.1.0'),
        ('1.1.1', '1.1.1'),
        ('1.3.0', '1.3.0'),
    )
    wms_slug = models.CharField(max_length=255, blank=True, null=True, verbose_name='WMS Layer Name')
    wms_version = models.CharField(max_length=10, blank=True, null=True, default=None, choices=WMS_VERSION_CHOICES, help_text='WMS Versioning - usually either 1.1.1 or 1.3.0')
    wms_format = models.CharField(max_length=100, blank=True, null=True, default=None, help_text='most common: image/png. Only image types supported.', verbose_name='WMS Format')
    wms_srs = models.CharField(max_length=100, blank=True, null=True, default=None, help_text='If not EPSG:3857 WMS requests will be proxied', verbose_name='WMS SRS')
    wms_timing = models.CharField(max_length=255, blank=True, null=True, default=None, help_text='http://docs.geoserver.org/stable/en/user/services/wms/time.html#specifying-a-time', verbose_name='WMS Time')
    wms_time_item = models.CharField(max_length=255, blank=True, null=True, default=None, help_text='Time Attribute Field, if different from "TIME". Proxy only.', verbose_name='WMS Time Field')
    wms_styles = models.CharField(max_length=255, blank=True, null=True, default=None, help_text='pre-determined styles, if exist', verbose_name='WMS Styles')
    wms_additional = models.TextField(blank=True, null=True, default=None, help_text='additional WMS key-value pairs: &key=value...', verbose_name='WMS Additional Fields')
    wms_info = models.BooleanField(default=False, help_text='enable Feature Info requests on click')
    wms_info_format = models.CharField(max_length=255, blank=True, null=True, default=None, help_text='Available supported feature info formats')
    
    def save(self, *args, **kwargs):
        if not self.id:  # Check if this is a new instance
            self.layer.layer_type = 'WMS'
            self.layer.save()
        super(LayerWMS, self).save(*args, **kwargs)

class MultilayerDimension(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    name = models.CharField(max_length=200, help_text='name to be used for selection in admin tool forms')
    label = models.CharField(max_length=50, help_text='label to be used in mapping tool slider')
    order = models.IntegerField(default=100, help_text='the order in which this dimension will be presented among other dimensions on this layer')
    animated = models.BooleanField(default=False, help_text='enable auto-toggling of layers across this dimension')
    angle_labels = models.BooleanField(default=False, help_text='display labels at an angle to make more fit')
    layer = models.ForeignKey(Layer, on_delete=models.CASCADE)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ('order',)

    def save(self, *args, **kwargs):
        super(MultilayerDimension, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if len(self.layer.dimensions) == 1:
            last = True
        else:
            last = False
        for value in self.multilayerdimensionvalue_set.all().order_by('-order'):
            value.delete((),last=last)
        super(MultilayerDimension, self).delete(*args, **kwargs)

class MultilayerAssociation(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    name = models.CharField(max_length=200)
    parentLayer = models.ForeignKey(Layer, related_name="parent_layer",
            db_column='parentlayer', on_delete=models.CASCADE)
    layer = models.ForeignKey(Layer, null=True, blank=True, default=None,
            related_name="associated_layer", db_column='associatedlayer',
            on_delete=models.SET_NULL)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return str(self.name)

class MultilayerDimensionValue(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    dimension = models.ForeignKey(MultilayerDimension, on_delete=models.CASCADE)
    value = models.CharField(max_length=200, help_text="Actual value of selection")
    label = models.CharField(max_length=50, help_text="Label for this selection seen in mapping tool slider")
    order = models.IntegerField(default=100)
    associations = models.ManyToManyField(MultilayerAssociation)

    def __unicode__(self):
        return '{}: {}'.format(self.dimension, self.value)

    def __str__(self):
        return '{}: {}'.format(self.dimension, self.value)

    class Meta:
        ordering = ('order',)

    def save(self, *args, **kwargs):
        if self.pk is None:
            super(MultilayerDimensionValue, self).save(*args, **kwargs)
            parentLayer = self.dimension.layer
            associations = MultilayerAssociation.objects.filter(parentLayer=parentLayer)
            if len(associations) == 0:
                MultilayerAssociation.objects.create(name=str(self), parentLayer=parentLayer)
                associations.update()
            siblingValues = [x for x in self.dimension.multilayerdimensionvalue_set.all() if x != self]
            if len(siblingValues) == 0:
                for association in associations:
                    self.associations.add(association)
            else:
                # If this is not the first value saved to this dimension, choosing
                # an arbitrary sibling value and copying all of its associations
                # is the closest thing we can do to smart generation of associations
                from copy import deepcopy
                siblingValue = siblingValues[0]
                for association in siblingValue.associations.all():
                    dimensionValues = [x for x in association.multilayerdimensionvalue_set.all() if x.dimension != self.dimension]
                    # create a clone of association
                    newAssociation = deepcopy(association)
                    newAssociation.id = None
                    newAssociation.name = 'NEW'
                    newAssociation.uuid = uuid.uuid4()
                    newAssociation.save()
                    # restore value/association relationships
                    for value in dimensionValues:
                        value.associations.add(newAssociation)
                    self.associations.add(newAssociation)

        else:
            super(MultilayerDimensionValue, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        delete_all = False
        if 'last' in kwargs.keys():
            if kwargs['last']:
                delete_all = True
            kwargs.pop('last', None)
        try:
            for association in self.associations.all():
                if delete_all or len(self.dimension.multilayerdimensionvalue_set.all()) > 1 or len(self.dimension.layer.parent_layer.all()) == 1:
                    association.multilayerdimensionvalue_set.clear()
                    association.delete()
        except ValueError:
            # ValueError: "<MultilayerDimensionValue: Threshold: 10>" needs to have a value for field "multilayerdimensionvalue" before this many-to-many relationship can be used.
            pass

        if self.id:
            # AssertionError: MultilayerDimensionValue object can't be deleted because its id attribute is set to None.
            super(MultilayerDimensionValue, self).delete(*args, **kwargs)

class AttributeInfo(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    display_name = models.CharField(max_length=255, blank=True, null=True)
    field_name = models.CharField(max_length=255, blank=True, null=True)
    precision = models.IntegerField(blank=True, null=True)
    order = models.IntegerField(default=1)
    preserve_format = models.BooleanField(default=False, help_text='Prevent portal from making any changes to the data to make it human-readable')

    def __unicode__(self):
        return unicode('{}'.format(self.field_name))

    def __str__(self):
        return str(self.field_name)

class LookupInfo(models.Model):
    DASH_CHOICES = (
        ('dot', 'dot'),
        ('dash', 'dash'),
        ('dashdot', 'dashdot'),
        ('longdash', 'longdash'),
        ('longdashdot', 'longdashdot'),
        ('solid', 'solid')
    )
    COLOR_PALETTE = []

    COLOR_PALETTE.append(("#FFFFFF", 'white'))
    COLOR_PALETTE.append(("#888888", 'gray'))
    COLOR_PALETTE.append(("#000000", 'black'))
    COLOR_PALETTE.append(("#FF0000", 'red'))
    COLOR_PALETTE.append(("#FFFF00", 'yellow'))
    COLOR_PALETTE.append(("#00FF00", 'green'))
    COLOR_PALETTE.append(("#00FFFF", 'cyan'))
    COLOR_PALETTE.append(("#0000FF", 'blue'))
    COLOR_PALETTE.append(("#FF00FF", 'magenta'))

    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    value = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True, default=None)
    color = ColorField(
        blank=True,
        null=True,
        default=None,
        verbose_name="Fill Color",
        samples=COLOR_PALETTE,
    )
    stroke_color = ColorField(
        blank=True,
        null=True,
        default=None,
        verbose_name="Stroke Color",
        samples=COLOR_PALETTE,
    )
    stroke_width = models.IntegerField(null=True, blank=True, default=None, verbose_name="Stroke Width")
    dashstyle = models.CharField(max_length=11, choices=DASH_CHOICES, default='solid')
    fill = models.BooleanField(default=False)
    graphic = models.CharField(max_length=255, blank=True, null=True)
    graphic_scale = models.FloatField(null=True, blank=True, default=None, verbose_name="Graphic Scale", help_text="Scale the graphic from its original size.")

    def __unicode__(self):
        if self.description:
            return unicode('{}: {}'.format(self.value, self.description))
        return unicode('{}'.format(self.value))

    def __str__(self):
        if self.description:
            return '{}: {}'.format(self.value, self.description)
        return str(self.value)