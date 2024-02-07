from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.forms.models import model_to_dict
from layers.models import Theme, Layer, ChildOrder, Companionship, LayerWMS, LayerArcREST, LayerArcFeatureService, LayerVector, LayerXYZ
#need to add catalog html to shared_layer_fields after adding it to subtheme serializer and to layer model
shared_layer_fields = ["id", "name", "uuid", "layer_type", "url", "proxy_url", "is_disabled", "disabled_message", "order",
                       "show_legend", "legend", "legend_title", "legend_subtitle", "description", "overview", "data_url",
                       "data_source", "data_notes", "metadata", "source", "annotated", "utfurl", "lookups", "attributes",
                       # "parent", Removed, since it's in LayerSerializer
                       "kml", "data_download", "learn_more", "map_tiles", "label_field", "date_modified", "minZoom", "maxZoom", "has_companion",
                       "is_multilayer_parent", "is_multilayer", "dimensions", "associated_multilayers"]

vector_layer_fields = ["custom_style", "outline_width", "outline_color", "outline_opacity", 
                       "fill_opacity", "color", "point_radius", "graphic", "graphic_scale", "opacity"]

layer_wms_fields = ["wms_slug", "wms_version", "wms_format", "wms_srs", "wms_timing", "wms_time_item", "wms_styles", "wms_additional",
                    "wms_info", "wms_info_format"]

layer_arcgis_fields = ["arcgis_layers", "password_protected", "disable_arcgis_attributes"]

raster_type_fields = ["query_by_point"]

library_fields = ["queryable"]

def get_companion_layers(layer):
    companionships = Companionship.objects.filter(layer=layer)
    companion_layers = []
    for companionship in companionships:
        companion_layers.extend(companionship.companions.all())
    return companion_layers

def get_serialized_sublayers(obj):
    # Return an empty list immediately if obj is not a Theme
    if not isinstance(obj, Theme):
        return []

    def accumulate_child_layers(theme, accumulated_layers):
        # Get all ChildOrder objects related to this theme, including subthemes
        child_orders = ChildOrder.objects.filter(parent_theme=theme).order_by('order')

        # Iterate through each ChildOrder
        for co in child_orders:
            if isinstance(co.content_object, Theme):
                # If it's a subtheme, recursively accumulate layers
                accumulate_child_layers(co.content_object, accumulated_layers)
            else:
                # If it's a Layer, add it to the list
                accumulated_layers.append(co.content_object)

    # Initialize an empty list to accumulate child layers
    accumulated_child_layers = []

    # Start the recursive accumulation of layers for the given theme
    accumulate_child_layers(obj, accumulated_child_layers)

    # Serialize only the layers (no need to serialize subthemes)
    serialized_child_layers = SubLayerSerializer(accumulated_child_layers, many=True).data

    return serialized_child_layers

def get_layer_order(layer):
    if isinstance(layer, dict):
        # If it's a dict, extract layer_type from the dict
        layer_type = layer.get('layer_type')
    else:
        # If it's a model instance, use the attribute directly
        layer_type = layer.layer_type
    if layer_type == 'WMS':
        model_class = LayerWMS
    elif layer_type == "ArcRest":
        model_class = LayerArcREST
    elif layer_type == "ArcFeatureServer":
        model_class = LayerArcFeatureService
    elif layer_type == "Vector":
        model_class = LayerVector
    elif layer_type == 'XYZ':
        model_class = LayerXYZ
    elif layer_type == "radio":
        model_class = Theme
    elif layer_type == "checkbox":
        model_class = Theme
    else:
        model_class = layer.__class__
    
    try:
        content_type = ContentType.objects.get_for_model(model_class)
        child_orders = ChildOrder.objects.filter(content_type=content_type, object_id=layer['id'] if isinstance(layer, dict) else layer.id)
        first_child_order = child_orders.first()
        return first_child_order.order if first_child_order else 0
    except ChildOrder.DoesNotExist:
        return 0
#inherit v2 serializer to make v1 serializer

class LayerSerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField()

    class Meta:
        model = Layer
        fields = ["parent", "catalog_html"]
    
    def get_parent(self, layer: Layer):
        # Has a direct parent, and the direct parent is not on the topmost level.
        if layer.parent != None and layer.parent.parent != None:
            # Flatten parent hierarchy until we reach a first level parent.
            current_parent = layer.parent
            while current_parent.parent.parent != None:
                current_parent = current_parent.parent
            return current_parent.id
        else:
            return None


class LayerWMSSerializer(LayerSerializer):
    order = serializers.SerializerMethodField()

    # Set default values for unrelated fields for layer type to support V1
    arcgis_layers = serializers.CharField(default=None, read_only=True)
    password_protected = serializers.BooleanField(default=False, read_only=True)
    disable_arcgis_attributes = serializers.BooleanField(default=False, read_only=True)

    queryable = serializers.BooleanField(default=False, read_only=True)

    custom_style = serializers.CharField(default=None, read_only=True)
    outline_width = serializers.IntegerField(default=None, read_only=True)
    outline_color = serializers.CharField(default=None, read_only=True)
    outline_opacity = serializers.FloatField(default=None, read_only=True)
    fill_opacity = serializers.FloatField(default=None, read_only=True)
    color = serializers.CharField(default=None, read_only=True)
    point_radius = serializers.IntegerField(default=None, read_only=True)
    graphic = serializers.CharField(default=None, read_only=True)
    graphic_scale = serializers.FloatField(default=1.0, read_only=True)
    opacity = serializers.FloatField(default=.5, read_only=True)
    subLayers = serializers.SerializerMethodField()
    companion_layers = serializers.SerializerMethodField()

    class Meta(LayerSerializer.Meta):
        model = LayerWMS
        fields = LayerSerializer.Meta.fields + shared_layer_fields + layer_arcgis_fields + layer_wms_fields + raster_type_fields + library_fields + vector_layer_fields + ["companion_layers"] + ["subLayers"]
    def get_companion_layers(self, obj):
        companion_layers = get_companion_layers(obj)
        return CompanionLayerSerializer(companion_layers, many=True).data
    def get_subLayers(self, obj):
        subLayers = get_serialized_sublayers(obj)
        return subLayers
    def get_order(self, obj):
        return get_layer_order(obj)
        
class LayerArcRESTSerializer(LayerSerializer):
    order = serializers.SerializerMethodField()
    wms_slug = serializers.CharField(default=None, read_only=True)
    wms_version = serializers.CharField(default=None, read_only=True)
    wms_format = serializers.CharField(default=None, read_only=True)
    wms_srs = serializers.CharField(default=None, read_only=True)
    wms_timing = serializers.CharField(default=None, read_only=True)
    wms_time_item = serializers.CharField(default=None, read_only=True)
    wms_styles = serializers.CharField(default=None, read_only=True)
    wms_additional = serializers.CharField(default="", read_only=True)
    wms_info = serializers.BooleanField(default=False, read_only=True)
    wms_info_format = serializers.CharField(default=None, read_only=True)

    queryable = serializers.BooleanField(default=False, read_only=True)

    custom_style = serializers.CharField(default=None, read_only=True)
    outline_width = serializers.IntegerField(default=None, read_only=True)
    outline_color = serializers.CharField(default=None, read_only=True)
    outline_opacity = serializers.FloatField(default=None, read_only=True)
    fill_opacity = serializers.FloatField(default=None, read_only=True)
    color = serializers.CharField(default=None, read_only=True)
    point_radius = serializers.IntegerField(default=None, read_only=True)
    graphic = serializers.CharField(default=None, read_only=True)
    graphic_scale = serializers.FloatField(default=1.0, read_only=True)
    opacity = serializers.FloatField(default=.5, read_only=True)
    subLayers = serializers.SerializerMethodField()
    companion_layers = serializers.SerializerMethodField()

    class Meta(LayerSerializer.Meta):
        model = LayerArcREST
        fields = LayerSerializer.Meta.fields + shared_layer_fields + layer_arcgis_fields + layer_wms_fields + raster_type_fields + library_fields + vector_layer_fields + ["companion_layers"] + ["subLayers"]
    
    def get_order(self, obj):
        return get_layer_order(obj)
    def get_companion_layers(self, obj):
        companion_layers = get_companion_layers(obj)
        return CompanionLayerSerializer(companion_layers, many=True).data
    def get_subLayers(self, obj):
        subLayers = get_serialized_sublayers(obj)
        return subLayers
    

class LayerArcFeatureServiceSerializer(LayerSerializer):
    order = serializers.SerializerMethodField()
    wms_slug = serializers.CharField(default=None, read_only=True)
    wms_version = serializers.CharField(default=None, read_only=True)
    wms_format = serializers.CharField(default=None, read_only=True)
    wms_srs = serializers.CharField(default=None, read_only=True)
    wms_timing = serializers.CharField(default=None, read_only=True)
    wms_time_item = serializers.CharField(default=None, read_only=True)
    wms_styles = serializers.CharField(default=None, read_only=True)
    wms_additional = serializers.CharField(default="", read_only=True)
    wms_info = serializers.BooleanField(default=False, read_only=True)
    wms_info_format = serializers.CharField(default=None, read_only=True)

    query_by_point = serializers.BooleanField(default=False, read_only=True)

    queryable = serializers.BooleanField(default=False, read_only=True)
    subLayers = serializers.SerializerMethodField()
    companion_layers = serializers.SerializerMethodField()

    class Meta(LayerSerializer.Meta):
        model = LayerArcFeatureService
        fields = LayerSerializer.Meta.fields + shared_layer_fields + layer_arcgis_fields + layer_wms_fields + raster_type_fields + library_fields + vector_layer_fields + ["companion_layers"] + ["subLayers"]
    
    def get_order(self, obj):
        return get_layer_order(obj)
    def get_companion_layers(self, obj):
        companion_layers = get_companion_layers(obj)
        return CompanionLayerSerializer(companion_layers, many=True).data
    def get_subLayers(self, obj):
        subLayers = get_serialized_sublayers(obj)
        return subLayers


class LayerXYZSerializer(LayerSerializer):
    order = serializers.SerializerMethodField()
    wms_slug = serializers.CharField(default=None, read_only=True)
    wms_version = serializers.CharField(default=None, read_only=True)
    wms_format = serializers.CharField(default=None, read_only=True)
    wms_srs = serializers.CharField(default=None, read_only=True)
    wms_timing = serializers.CharField(default=None, read_only=True)
    wms_time_item = serializers.CharField(default=None, read_only=True)
    wms_styles = serializers.CharField(default=None, read_only=True)
    wms_additional = serializers.CharField(default="", read_only=True)
    wms_info = serializers.BooleanField(default=False, read_only=True)
    wms_info_format = serializers.CharField(default=None, read_only=True)

    queryable = serializers.BooleanField(default=False, read_only=True)

    custom_style = serializers.CharField(default=None, read_only=True)
    outline_width = serializers.IntegerField(default=None, read_only=True)
    outline_color = serializers.CharField(default=None, read_only=True)
    outline_opacity = serializers.FloatField(default=None, read_only=True)
    fill_opacity = serializers.FloatField(default=None, read_only=True)
    color = serializers.CharField(default=None, read_only=True)
    point_radius = serializers.IntegerField(default=None, read_only=True)
    graphic = serializers.CharField(default=None, read_only=True)
    graphic_scale = serializers.FloatField(default=1.0, read_only=True)
    opacity = serializers.FloatField(default=.5, read_only=True)

    arcgis_layers = serializers.CharField(default=None, read_only=True)
    password_protected = serializers.BooleanField(default=False, read_only=True)
    disable_arcgis_attributes = serializers.BooleanField(default=False, read_only=True)
    subLayers = serializers.SerializerMethodField()
    companion_layers = serializers.SerializerMethodField()
 
    class Meta(LayerSerializer.Meta):
        model = LayerXYZ
        fields = LayerSerializer.Meta.fields + shared_layer_fields + layer_arcgis_fields + layer_wms_fields + raster_type_fields + library_fields + vector_layer_fields + ["companion_layers"] + ["subLayers"]
    
    def get_order(self, obj):
        return get_layer_order(obj)
    def get_companion_layers(self, obj):
        companion_layers = get_companion_layers(obj)
        return CompanionLayerSerializer(companion_layers, many=True).data
    def get_subLayers(self, obj):
        subLayers = get_serialized_sublayers(obj)
        return subLayers
    

class LayerVectorSerializer(LayerSerializer):
    order = serializers.SerializerMethodField()
    wms_slug = serializers.CharField(default=None, read_only=True)
    wms_version = serializers.CharField(default=None, read_only=True)
    wms_format = serializers.CharField(default=None, read_only=True)
    wms_srs = serializers.CharField(default=None, read_only=True)
    wms_timing = serializers.CharField(default=None, read_only=True)
    wms_time_item = serializers.CharField(default=None, read_only=True)
    wms_styles = serializers.CharField(default=None, read_only=True)
    wms_additional = serializers.CharField(default="", read_only=True)
    wms_info = serializers.BooleanField(default=False, read_only=True)
    wms_info_format = serializers.CharField(default=None, read_only=True)

    queryable = serializers.BooleanField(default=False, read_only=True)

    arcgis_layers = serializers.CharField(default=None, read_only=True)
    password_protected = serializers.BooleanField(default=False, read_only=True)
    query_by_point = serializers.BooleanField(default=False, read_only=True)
    disable_arcgis_attributes = serializers.BooleanField(default=False, read_only=True)
    subLayers = serializers.SerializerMethodField()
    companion_layers = serializers.SerializerMethodField()
    
    class Meta(LayerSerializer.Meta):
        model = LayerVector 
        fields = LayerSerializer.Meta.fields + shared_layer_fields + layer_arcgis_fields + layer_wms_fields + raster_type_fields + library_fields + vector_layer_fields + ["companion_layers"] + ["subLayers"]
    
    def get_order(self, obj):
        return get_layer_order(obj)
    def get_companion_layers(self, obj):
        companion_layers = get_companion_layers(obj)
        return CompanionLayerSerializer(companion_layers, many=True).data
    def get_subLayers(self, obj):
        subLayers = get_serialized_sublayers(obj)
        return subLayers
    

class ChildOrderSerializer(serializers.ModelSerializer):
    # Serialize the generic related object
    def to_representation(self, instance):
        # Retrieve the related object
        related_object = instance.content_object
        # Serialize the related object based on its class
        if isinstance(related_object, LayerWMS):
            serializer = LayerWMSSerializer(related_object)
        elif isinstance(related_object, LayerArcREST):
            serializer = LayerArcRESTSerializer(related_object)
        elif isinstance(related_object, LayerArcFeatureService):
            serializer = LayerArcFeatureServiceSerializer(related_object)
        elif isinstance(related_object, LayerVector):
            serializer = LayerVectorSerializer(related_object)
        elif isinstance(related_object, LayerXYZ):
            serializer = LayerXYZSerializer(related_object)
        elif isinstance(related_object, Theme):
            # Check if the theme is a subtheme (has a parent theme)
            if related_object.parent:
                # Use SubThemeSerializer for subthemes
                serializer = SubThemeSerializer(related_object)
            else:
                # Use a different serializer for parent themes if necessary
                serializer = ThemeSerializer(related_object)
        else:
            # Fallback for unexpected types
            return {}

        # Flatten the representation to include the serialized data directly
        serialized_data = serializer.data

        serialized_data['order'] = instance.order
        serialized_data['name'] = getattr(instance.content_object, 'name', '')
        serialized_data['id'] = getattr(instance.content_object, 'id', 0)
        return serialized_data
        
    class Meta:
        model = ChildOrder

# use this serializer for only the top level themes
# create a new serializer for subthemes, so that it matches the layer format
class ThemeSerializer(serializers.ModelSerializer):
    learn_link = serializers.SerializerMethodField()
    # this is called layers only to match v1 but this includes subthemes and layers
    layers = ChildOrderSerializer(many=True, read_only=True, source='children')

    class Meta:
        model = Theme
        fields = ["id", "name", "display_name", "layers", "learn_link", "is_visible", "description"]

    def to_representation(self, instance):
        # Call the super method to get the default representation
        ret = super().to_representation(instance)

        # Order the 'layers' by the 'order' field and return only layer IDs
        if 'layers' in ret:
            # Create a mapping of layer id to its order and name
            layer_mapping = {layer['id']: (layer.get('order', 0), layer.get('name', '')) for layer in ret['layers']}

            # Sort layer ids based on the order and name
            sorted_layer_ids = sorted(
                layer_mapping.keys(),
                key=lambda id: (layer_mapping[id][0], layer_mapping[id][1], id)
            )

            # Update the 'layers' field to be a list of sorted ids
            ret['layers'] = sorted_layer_ids

        return ret
    
    def get_learn_link(self, obj):
        return obj.learn_link

class SubThemeSerializer(serializers.ModelSerializer):
    order = serializers.SerializerMethodField()
    url = serializers.CharField(default="", read_only=True) 
    proxy_url = serializers.BooleanField(default=False, read_only=True) 
    is_disabled = serializers.BooleanField(default=False, read_only=True) 
    disabled_message = serializers.CharField(default="", read_only=True)
    show_legend = serializers.BooleanField(default=True, read_only=True) 
    legend = serializers.CharField(default=None, read_only=True) 
    legend_title = serializers.CharField(default=None, read_only=True) 
    legend_subtitle = serializers.CharField(default=None, read_only=True) 
    overview = serializers.CharField(default="", read_only=True)
    data_source = serializers.CharField(default=None, read_only=True) 
    data_notes = serializers.CharField(default="", read_only=True) 
    # need to add catalog_html
    metadata = serializers.CharField(read_only=True, default=None)
    source = serializers.CharField(read_only=True, default=None)
    annotated = serializers.BooleanField(default=False, read_only=True) 
    kml = serializers.CharField(read_only=True, default=None) 
    data_download = serializers.CharField(read_only=True, default=None)
    learn_more = serializers.CharField(read_only=True, default=None)
    map_tiles = serializers.CharField(read_only=True, default=None)
    label_field = serializers.CharField(read_only=True, default=None)
    minZoom = serializers.FloatField(read_only=True, default=None)
    maxZoom = serializers.FloatField(read_only=True, default=None)

    wms_slug = serializers.CharField(default=None, read_only=True)
    wms_version = serializers.CharField(default=None, read_only=True)
    wms_format = serializers.CharField(default=None, read_only=True)
    wms_srs = serializers.CharField(default=None, read_only=True)
    wms_timing = serializers.CharField(default=None, read_only=True)
    wms_time_item = serializers.CharField(default=None, read_only=True)
    wms_styles = serializers.CharField(default=None, read_only=True)
    wms_additional = serializers.CharField(default="", read_only=True)
    wms_info = serializers.BooleanField(default=False, read_only=True)
    wms_info_format = serializers.CharField(default=None, read_only=True)

    queryable = serializers.BooleanField(default=False, read_only=True)

    arcgis_layers = serializers.CharField(default=None, read_only=True)
    password_protected = serializers.BooleanField(default=False, read_only=True)
    query_by_point = serializers.BooleanField(default=False, read_only=True)
    disable_arcgis_attributes = serializers.BooleanField(default=False, read_only=True)

    custom_style = serializers.CharField(default=None, read_only=True)
    outline_width = serializers.IntegerField(default=None, read_only=True)
    outline_color = serializers.CharField(default=None, read_only=True)
    outline_opacity = serializers.FloatField(default=None, read_only=True)
    fill_opacity = serializers.FloatField(default=None, read_only=True)
    color = serializers.CharField(default=None, read_only=True)
    point_radius = serializers.IntegerField(default=None, read_only=True)
    graphic = serializers.CharField(default=None, read_only=True)
    graphic_scale = serializers.FloatField(default=1.0, read_only=True)
    opacity = serializers.FloatField(default=.5, read_only=True)
    subLayers = serializers.SerializerMethodField()
    has_companion = serializers.BooleanField(default=False, read_only=True)
    companion_layers = serializers.ListField(default=[], read_only=True)
    is_multilayer = serializers.BooleanField(default=False, read_only=True)
    is_multilayer_parent = serializers.BooleanField(default=False, read_only=True)
    dimensions = serializers.ListField(default=[], read_only=True)
    associated_multilayers = serializers.DictField(default={}, read_only=True)
    parent = serializers.SerializerMethodField()
    data_url = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()
    lookups = serializers.SerializerMethodField()
    catalog_html = serializers.SerializerMethodField()
    utfurl = serializers.CharField(default=None, read_only=True)
    class Meta:
        model = Theme
        fields = shared_layer_fields + layer_arcgis_fields + layer_wms_fields + raster_type_fields + library_fields + vector_layer_fields + ["companion_layers", "parent", "catalog_html"] + ["subLayers"]
   
    def get_order(self, obj):
        return get_layer_order(obj)
    def get_parent(self, obj):
        return None
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['description'] = ret['description'] if ret['description'] is not None else ""
        return ret
    def get_subLayers(self, obj):
        subLayers = get_serialized_sublayers(obj)
        return subLayers
    def get_data_url(self, obj):
        parent_theme = obj.parent

        if parent_theme:
            # Format the parent theme's name to be URL-friendly
            # This can be custom tailored if you store slugs differently
            parent_theme_slug = parent_theme.name.replace(" ", "-").lower()
            
            # Ensure there's a slug_name to use for constructing the URL
            if obj.slug_name:
                # Construct the URL
                data_catalog_url = "/data-catalog/{}/{}".format(parent_theme_slug, obj.slug_name)
                return data_catalog_url
        return None
    def get_attributes(self, obj):
        return {'compress_attributes': False,
                'event': "click",
                'attributes': [],
                'mouseover_attribute': None,
                'preserved_format_attributes': []
        }
    def get_lookups(self, obj):
        return {'field': None,
                'details': []}
    def get_catalog_html(self, obj):
        
        try:
            return render_to_string(
                "data_catalog/includes/cacheless_layer_info.html",
                {
                    'layer': model_to_dict(obj),
                    # 'sub_layers': self.sublayers.exclude(layer_type="placeholder")
                }
            )
        except Exception as e:
            print(e)




class CompanionLayerSerializer(serializers.ModelSerializer):
    order = serializers.SerializerMethodField()
    overview = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()
    
    class Meta:
        model = Layer 
        fields = shared_layer_fields + ["parent"]
    
    def get_overview(self, obj):
        return obj.data_overview_text
    def get_description(self, obj):
        return obj.tooltip
    def get_order(self, obj):
        return get_layer_order(obj)
    def get_parent(self, obj):
        # This query looks for Companionship instances where the current layer is among the companions
        companionship = Companionship.objects.filter(companions=obj).first()

        # If a companionship is found, it means the current layer is a companion to another layer
        if companionship:
            # Return the ID of the layer to which the current layer is a companion
            return companionship.layer.id
        return None
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        layer_specific_fields = {
            'arcgis_layers': None, 
            'password_protected': False, 
            "disable_arcgis_attributes":False,
            "query_by_point":False,
            "custom_style": None,
            "outline_width": None,
            "outline_color": None,
            "fill_opacity": None,
            "color": None,
            "point_radius": None,
            "graphic": None,
            "graphic_scale": 1.0,
            "opacity": .5,
            "wms_slug": None,
            "wms_version": None,
            "wms_srs": None,
            "wms_timing": None,
            "wms_time_item": None,
            "wms_styles": None,
            "wms_additional": "",
            "wms_info": False,
            "wms_info_format": None,
        }
        # Conditional logic for specific fields
        if isinstance(instance, LayerWMS):
            layer_specific_fields.update({
                "wms_slug": instance.wms_slug, 
                "wms_version": instance.wms_version,
                "wms_srs": instance.wms_srs,
                "wms_timing": instance.wms_timing,
                "wms_time_item": instance.wms_time_item,
                "wms_styles": instance.wms_styles,
                "wms_additional": instance.wms_additional,
                "wms_info": instance.wms_info,
                "wms_info_format": instance.wms_info_format,
                "query_by_point": instance.query_by_point,
            })
        elif isinstance(instance, LayerArcREST):
            layer_specific_fields.update({
                "arcgis_layers":instance.arcgis_layers,
                "password_protected":instance.password_protected,
                "disable_arcgis_attributes":instance.disable_arcgis_attributes,
                "query_by_point":instance.query_by_point,
            })
        elif isinstance(instance, LayerArcFeatureService):
            layer_specific_fields.update({
                "arcgis_layers":instance.arcgis_layers,
                "password_protected":instance.password_protected,
                "disable_arcgis_attributes":instance.disable_arcgis_attributes,
                "custom_style": instance.custom_style,
                "outline_width": instance.outline_width,
                "outline_color": instance.outline_color,
                "fill_opacity": instance.fill_opacity,
                "color": instance.color,
                "point_radius": instance.point_radius,
                "graphic": instance.graphic,
                "graphic_scale": instance.graphic_scale,
                "opacity": instance.opacity,
            })
        elif isinstance(instance,LayerVector):
            layer_specific_fields.update({
                "custom_style": instance.custom_style,
                "outline_width": instance.outline_width,
                "outline_color": instance.outline_color,
                "fill_opacity": instance.fill_opacity,
                "color": instance.color,
                "point_radius": instance.point_radius,
                "graphic": instance.graphic,
                "graphic_scale": instance.graphic_scale,
                "opacity": instance.opacity,
            })
        elif isinstance(instance, LayerXYZ):
            layer_specific_fields.update({
                "query_by_point":instance.query_by_point,
            })
        ret.update(layer_specific_fields)
        return ret

def check_is_sublayer(obj):
    if isinstance(obj, Theme):
        return False
    else:
        return True

class SubLayerSerializer(serializers.ModelSerializer):
    order = serializers.SerializerMethodField()
    is_sublayer = serializers.SerializerMethodField()
    overview = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()
    
    class Meta:
        model = Layer 
        fields = shared_layer_fields + ["is_sublayer", "parent"]
    
    def get_order(self, obj):
        return get_layer_order(obj)
    def get_is_sublayer(self, obj):
        return check_is_sublayer(obj)
    def get_overview(self, obj):
        return obj.data_overview_text
    def get_description(self, obj):
        return obj.tooltip
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        layer_specific_fields = {
            'arcgis_layers': None, 
            'password_protected': False, 
            "disable_arcgis_attributes":False,
            "query_by_point":False,
            "custom_style": None,
            "outline_width": None,
            "outline_color": None,
            "fill_opacity": None,
            "color": None,
            "point_radius": None,
            "graphic": None,
            "graphic_scale": 1.0,
            "opacity": .5,
            "wms_slug": None,
            "wms_version": None,
            "wms_srs": None,
            "wms_timing": None,
            "wms_time_item": None,
            "wms_styles": None,
            "wms_additional": "",
            "wms_info": False,
            "wms_info_format": None,
        }
        # Conditional logic for specific fields
        if isinstance(instance, LayerWMS):
            layer_specific_fields.update({
                "wms_slug": instance.wms_slug, 
                "wms_version": instance.wms_version,
                "wms_srs": instance.wms_srs,
                "wms_timing": instance.wms_timing,
                "wms_time_item": instance.wms_time_item,
                "wms_styles": instance.wms_styles,
                "wms_additional": instance.wms_additional,
                "wms_info": instance.wms_info,
                "wms_info_format": instance.wms_info_format,
                "query_by_point": instance.query_by_point,
            })
        elif isinstance(instance, LayerArcREST):
            layer_specific_fields.update({
                "arcgis_layers":instance.arcgis_layers,
                "password_protected":instance.password_protected,
                "disable_arcgis_attributes":instance.disable_arcgis_attributes,
                "query_by_point":instance.query_by_point,
            })
        elif isinstance(instance, LayerArcFeatureService):
            layer_specific_fields.update({
                "arcgis_layers":instance.arcgis_layers,
                "password_protected":instance.password_protected,
                "disable_arcgis_attributes":instance.disable_arcgis_attributes,
                "custom_style": instance.custom_style,
                "outline_width": instance.outline_width,
                "outline_color": instance.outline_color,
                "fill_opacity": instance.fill_opacity,
                "color": instance.color,
                "point_radius": instance.point_radius,
                "graphic": instance.graphic,
                "graphic_scale": instance.graphic_scale,
                "opacity": instance.opacity,
            })
        elif isinstance(instance,LayerVector):
            layer_specific_fields.update({
                "custom_style": instance.custom_style,
                "outline_width": instance.outline_width,
                "outline_color": instance.outline_color,
                "fill_opacity": instance.fill_opacity,
                "color": instance.color,
                "point_radius": instance.point_radius,
                "graphic": instance.graphic,
                "graphic_scale": instance.graphic_scale,
                "opacity": instance.opacity,
            })
        elif isinstance(instance, LayerXYZ):
            layer_specific_fields.update({
                "query_by_point":instance.query_by_point,
            })
        ret.update(layer_specific_fields)
        return ret
    def get_parent(self, obj):
        
        layer_content_type = ContentType.objects.get_for_model(obj.__class__)
        child_orders = ChildOrder.objects.filter(object_id=obj.id, content_type=layer_content_type)
        if child_orders:
            return child_orders[0].parent_theme.id
        return None