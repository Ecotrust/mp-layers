from django.db import models
from django.contrib.sites.models import Site
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from colorfield.fields import ColorField
import uuid

# Review widgets for ITK database (how are relationships set up)
def get_domain(port=8010):
    try:
        #domain = Site.objects.all()[0].domain
        domain = Site.objects.get(id=SITE_ID).domain
        if 'localhost' in domain:
            domain = 'localhost:%s' %port
        domain = 'http://' + domain
    except:
        domain = '..'
    #print(domain)
    return domain

class Theme(models.Model):
    LAYER_TYPE_CHOICES = (
    ('radio', 'radio'),
    ('checkbox', 'checkbox'),
    )
    name = models.CharField(max_length=100)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    display_name = models.CharField(max_length=100)
    parent_theme = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='child_themes')
    layer_type = models.CharField(max_length=50, choices=LAYER_TYPE_CHOICES, help_text='use placeholder to temporarily remove layer from TOC')
    # Modify Theme model to include order field but don't want subthemes to necessarily have an order, make order field optional
    order = models.PositiveIntegerField(null=True, blank=True) 

    ######################################################
    #           DATES                                    #
    ######################################################
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    is_visible = models.BooleanField(default=True)

    # need to add overview, data_source, data_notes, source, data_url, catalog_html to match v1 subtheme/parent layer creation
    description = models.TextField(blank=True, null=True)

    @property
    def learn_link(self):
        domain = get_domain(8000)
        return '%s/learn/%s' %(domain, self.name)
    
    class Meta:
        ordering = ['order']

# in admin, how can we show all layers regardless of layer type, without querying get all layers that are wms, get layers that are arcgis, etc, bc that is a lot of subqueries
class Layer(models.Model):
    LAYER_TYPE_CHOICES = (
    ('XYZ', 'XYZ'),
    ('WMS', 'WMS'),
    ('ArcRest', 'ArcRest'),
    ('ArcFeatureServer', 'ArcFeatureServer'),
    ('radio', 'radio'),
    ('checkbox', 'checkbox'),
    ('Vector', 'Vector'),
    ('VectorTile', 'VectorTile'),
    ('placeholder', 'placeholder'),
    )
    name = models.CharField(max_length=100)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    slug_name = models.CharField(max_length=200, blank=True, null=True)
    layer_type = models.CharField(max_length=50, choices=LAYER_TYPE_CHOICES, help_text='use placeholder to temporarily remove layer from TOC')
    url = models.TextField(blank=True, default="")
    proxy_url = models.BooleanField(default=False, help_text="proxy layer url through marine planner")
    shareable_url = models.BooleanField(default=True, help_text='Indicates whether the data layer (e.g. map tiles) can be shared with others (through the Map Tiles Link)')
    is_disabled = models.BooleanField(default=False, help_text='when disabled, the layer will still appear in the TOC, only disabled')
    disabled_message = models.CharField(max_length=255, blank=True, null=True, default="")
   
    ######################################################
    #                        LEGEND                      #
    ######################################################
    show_legend = models.BooleanField(default=True, help_text='show the legend for this layer if available')
    legend = models.CharField(max_length=255, blank=True, null=True, help_text='URL or path to the legend image file')
    legend_title = models.CharField(max_length=255, blank=True, null=True, help_text='alternative to using the layer name')
    legend_subtitle = models.CharField(max_length=255, blank=True, null=True)

    # RDH: geoportal_id is used in data_manager view 'geoportal_ids', which is never used
    geoportal_id = models.CharField(max_length=255, blank=True, null=True, default=None, help_text="GeoPortal UUID")

    ######################################################
    #                        METADATA                    #
    ######################################################
    description = models.TextField(blank=True, default="")
    data_overview = models.TextField(blank=True, default="")
    data_source = models.CharField(max_length=255, blank=True, null=True)
    data_notes = models.TextField(blank=True, default="")
    data_publish_date = models.DateField(auto_now=False, auto_now_add=False, null=True, blank=True, default=None, verbose_name='Date published', help_text='YYYY-MM-DD')
    
    #data catalog links
    catalog_name = models.TextField(null=True, blank=True, help_text="name of associated record in catalog", verbose_name='Catalog Record Name')
    catalog_id = models.TextField(null=True, blank=True, help_text="unique ID of associated record in catalog", verbose_name='Catalog Record Id')
    
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
    # attribute_fields = models.ManyToManyField('AttributeInfo', blank=True)
    is_annotated = models.BooleanField(default=False)
    compress_display = models.BooleanField(default=False)

    #use field to specify attribute on layer that you wish to be considered in adding conditional style formatting
    lookup_field = models.CharField(max_length=255, blank=True, null=True, help_text="To override the style based on specific attributes, provide the attribute name here and define your attributes in the Lookup table below.")
    #use widget along with creating Lookup Info records to apply conditional styling to your layer
    # lookup_table = models.ManyToManyField('LookupInfo', blank=True)

    ######################################################
    #           ESPIS                                    #
    ######################################################
    #ESPIS Upgrade - RDH 7/23/2017
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

    def dimensionRecursion(self, dimensions, associations):
        associationArray = {}
        dimension = dimensions.pop(0)
        for value in sorted(dimension.multilayerdimensionvalue_set.all(), key=lambda x: x.order):
            value_associations = associations.filter(pk__in=[x.pk for x in value.associations.all()])
            print(f"Processing value: {value.value}, Associations: {[str(a)  for a in value_associations]}")

            if len(dimensions) > 0:
                associationArray[str(value.value)] = self.dimensionRecursion(list(dimensions), value_associations)
            else:
                if len(value_associations) == 1 and value_associations[0].layer:
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

class Companionship(models.Model):
    # ForeignKey creates a one-to-many relationship
    # (Each companionship relates to one Layer)
    layer = models.ForeignKey(Layer, on_delete=models.CASCADE, related_name='companionships')

    # ManyToManyField creates a many-to-many relationship
    # (Each companionship can relate to multiple Layers and vice versa)
    companions = models.ManyToManyField(Layer, related_name='companion_to')

class VectorType(Layer):
    #feature level attribute used in mouseover display
    mouseover_field = models.CharField(max_length=75, blank=True, null=True, default=None, help_text='feature level attribute used in mouseover display')
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
    vector_outline_width = models.IntegerField(blank=True, null=True, default=None, verbose_name="Vector Stroke Width")
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
    vector_outline_color = ColorField(
        blank=True,
        null=True,
        default=None,
        verbose_name="Vector Stroke Color",
        samples=COLOR_PALETTE,
    )
    # RDH 20191106 - This is not a thing.
    vector_outline_opacity = models.FloatField(blank=True, null=True, default=None, verbose_name="Vector Stroke Opacity")
   
    #set the color to fill any polygons or circle-icons for points
    vector_fill = models.FloatField(blank=True, null=True, default=None, verbose_name="Vector Fill Opacity")
    vector_color = ColorField(
        blank=True,
        null=True,
        default=None,
        verbose_name="Vector Fill Color",
        samples=COLOR_PALETTE,
    )
    #set radius of circle in pixels, only applies to point data with no graphics
    point_radius = models.IntegerField(blank=True, null=True, default=None, help_text='Used only for for Point layers (default is 2)')
    #enter URL for image from online for layer's point data
    vector_graphic = models.CharField(max_length=255, blank=True, null=True, default=None, verbose_name="Vector Graphic", help_text="address of image to use for point data")
    #if you need to resize vector graphic image so it looks appropriate on map
    #to make image smaller, use value less than 1, to make image larger, use values larger than 1
    vector_graphic_scale = models.FloatField(blank=True, null=True, default=1.0, verbose_name="Vector Graphic Scale", help_text="Scale for the vector graphic from original size.")
    opacity = models.FloatField(default=.5, blank=True, null=True, verbose_name="Initial Opacity")


    class Meta:
        abstract = True

class RasterType(Layer):
    query_by_point = models.BooleanField(default=False, help_text='Do not buffer selection clicks (not recommended for point or line data)')

    class Meta:
        abstract = True

class ArcServer(Layer):
    arcgis_layers = models.CharField(max_length=255, blank=True, null=True, help_text='comma separated list of arcgis layer IDs')
    password_protected = models.BooleanField(default=False, help_text='check this if the server requires a password to show layers')
    disable_arcgis_attributes = models.BooleanField(default=False, help_text='Click to disable clickable ArcRest layers')
    
    class Meta:
        abstract = True

class LayerArcREST(ArcServer, RasterType):
    def save(self, *args, **kwargs):
        if not self.id:  # Check if this is a new instance
            self.layer_type = 'ArcRest'
        super(LayerArcREST, self).save(*args, **kwargs)

class LayerArcFeatureService(ArcServer, VectorType):
    def save(self, *args, **kwargs):
        if not self.id:  # Check if this is a new instance
            self.layer_type = 'ArcFeatureServer'
        super(LayerArcFeatureService, self).save(*args, **kwargs)

class LayerXYZ(RasterType):
    def save(self, *args, **kwargs):
        if not self.id:  # Check if this is a new instance
            self.layer_type = 'XYZ'
        super(LayerXYZ, self).save(*args, **kwargs)

class LayerVector(VectorType):
    def save(self, *args, **kwargs):
        if not self.id:  # Check if this is a new instance
            self.layer_type = 'Vector'
        super(LayerVector, self).save(*args, **kwargs)

class LayerWMS(RasterType):
    # Are we using wms_help for anything? 
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
    wms_additional = models.TextField(blank=True, null=True, default="", help_text='additional WMS key-value pairs: &key=value...', verbose_name='WMS Additional Fields')
    wms_info = models.BooleanField(default=False, help_text='enable Feature Info requests on click')
    wms_info_format = models.CharField(max_length=255, blank=True, null=True, default=None, help_text='Available supported feature info formats')
    def save(self, *args, **kwargs):
        if not self.id:  # Check if this is a new instance
            self.layer_type = 'WMS'
        super(LayerWMS, self).save(*args, **kwargs)

class Library(Layer):
    search_query = models.BooleanField(default=False, help_text='Select when layers are queryable - e.g. MDAT and CAS')

class ChildOrder(models.Model):
    parent_theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name='children')
    
    # The generic relation to point to either Theme or Layer
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    order = models.PositiveIntegerField()

    ######################################################
    #           DATES                                    #
    ######################################################
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']


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
        return '%s: %s' % (self.dimension, self.value)

    def __str__(self):
        return '%s: %s' % (self.dimension, self.value)

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
