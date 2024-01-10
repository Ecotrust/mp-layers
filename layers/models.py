from django.db import models
from django.contrib.sites.models import Site
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
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
    name = models.CharField(max_length=100)
    parent_theme = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='child_themes')

    # Modify Theme model to include order field but don't want subthemes to necessarily have an order, make order field optional
    order = models.PositiveIntegerField(null=True, blank=True) 

    @property
    def learn_link(self):
        domain = get_domain(8000)
        return '%s/learn/%s' %(domain, self.name)
    
    class Meta:
        ordering = ['order']

# in admin, how can we show all layers regardless of layer type, without querying get all layers that are wms, get layers that are arcgis, etc, bc that is a lot of subqueries
class Layer(models.Model):
    name = models.CharField(max_length=100)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    slug_name = models.CharField(max_length=200, blank=True, null=True)
    layer_type = models.CharField(max_length=50, choices=settings.LAYER_TYPE_CHOICES, help_text='use placeholder to temporarily remove layer from TOC')

class LayerWMS(Layer):
    WMS_VERSION_CHOICES = (
        (None, ''),
        ('1.0.0', '1.0.0'),
        ('1.1.0', '1.1.0'),
        ('1.1.1', '1.1.1'),
        ('1.3.0', '1.3.0'),
    )
    # Are we using wms_help for anything? 
    # wms_help = models.BooleanField(default=False, help_text='Enable simple selection for WMS fields. Only supports WMS 1.1.1')
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

class LayerArcGIS(Layer):
    arcgis_layers = models.CharField(max_length=255, blank=True, null=True, help_text='comma separated list of arcgis layer IDs')
    password_protected = models.BooleanField(default=False, help_text='check this if the server requires a password to show layers')
    query_by_point = models.BooleanField(default=False, help_text='Do not buffer selection clicks (not recommended for point or line data)')
    disable_arcgis_attributes = models.BooleanField(default=False, help_text='Click to disable clickable ArcRest layers')

class ChildOrder(models.Model):
    parent_theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name='children')
    
    # The generic relation to point to either Theme or Layer
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    order = models.PositiveIntegerField()
    class Meta:
        ordering = ['order']



