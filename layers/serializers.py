from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.forms.models import model_to_dict
from django.template.loader import render_to_string
from django.urls import reverse
from layers.models import Theme, Layer, ChildOrder, Companionship, LayerWMS, LayerArcREST, LayerArcFeatureService, LayerVector, LayerXYZ
from rest_framework import serializers
#need to add catalog html to shared_layer_fields after adding it to subtheme serializer and to layer model
shared_layer_fields = ["id", "name", "uuid", "type", "url", "proxy_url", "is_disabled", "disabled_message", "opacity",
                       "show_legend", "legend", "legend_title", "legend_subtitle", "description", "overview", "data_url",
                       "data_source", "data_notes", "metadata", "source", "annotated", "utfurl", "lookups", "attributes", 
                       # "parent", Removed, since it's in LayerSerializer
                       "kml", "data_download", "learn_more", "tiles", "label_field", "date_modified", "minZoom", "maxZoom", "has_companion",
                       "is_multilayer_parent", "is_multilayer", "dimensions", "associated_multilayers"]

vector_layer_fields = ["custom_style", "outline_width", "outline_color", "outline_opacity",
                       "fill_opacity", "color", "point_radius", "graphic", "graphic_scale"]

layer_wms_fields = ["wms_slug", "wms_version", "wms_format", "wms_srs", "wms_timing", "wms_time_item", "wms_styles", "wms_additional",
                    "wms_info", "wms_info_format"]

layer_arcgis_fields = ["arcgis_layers", "password_protected", "disable_arcgis_attributes"]

raster_type_fields = ["query_by_point"]

library_fields = ["queryable"]

def get_companion_layers(obj):
    if hasattr(obj, 'layer'):
        layer_instance = obj.layer
    else:
        # If `obj` is already a Layer instance or for other cases
        layer_instance = obj
    
    # Now, use `layer_instance` to filter Companionship instances
    companionships = Companionship.objects.filter(layer=layer_instance)
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

def get_layer_order(obj):
    
    layer_content_type = ContentType.objects.get_for_model(Layer)
    if hasattr(obj, 'layer'):
        obj_id = obj.layer.id
    else:
        obj_id = obj.id
    if isinstance(obj, Theme):
        layer_content_type = ContentType.objects.get_for_model(Theme)
    # Mapping of types to their respective model classes
    try:
        child_order = ChildOrder.objects.filter(content_type=layer_content_type, object_id=obj_id).first()
        return child_order.order if child_order else None
    except ChildOrder.DoesNotExist:
        return None

class DynamicLayerFieldsMixin:
    """
    A mixin to dynamically add methods to a serializer for retrieving fields from a related Layer object.
    """
    @classmethod
    def add_layer_field_methods(cls, fields):
        """
        Dynamically adds SerializerMethodField and their getters for specified fields from the Layer model.
        """

        def make_getter(field):
            # For the 'parent' field, we define special handling
            if field == 'parent':
                def getter(self, instance):
                    # Custom logic for handling the 'parent' field
                    if hasattr(instance, 'layer'):
                        current_parent = instance.layer.parent
                        if current_parent is not None and current_parent.parent is not None:
                            while current_parent.parent.parent is not None:
                                current_parent = current_parent.parent
                            return SubThemeSerializer(current_parent).data
                        return None
                    return getattr(instance, field, None)
            elif field == 'type':  # Handling for 'type' field
                def getter(self, instance):
                    return getattr(instance.layer, 'layer_type', None)
                return getter
            elif field == 'tiles':  # Handling for 'type' field
                def getter(self, instance):
                    return getattr(instance.layer, 'tiles_link', None)
                return getter
            elif field == 'metadata':
                def getter(self, instance):
                    if hasattr(instance.layer, 'metadata_link'):
                        return getattr(instance.layer, 'metadata_link', None)
                    return getattr(instance.layer, field, None)
            else:
                # For all other fields, use the default handling
                def getter(self, instance):
                    return getattr(instance.layer, field, None)
            return getter

        for field in fields:
            method_name = f'get_{field}'
            getter = make_getter(field)
            setattr(cls, method_name, getter)
            cls._declared_fields[field] = serializers.SerializerMethodField(method_name=method_name)

class LayerSerializer(DynamicLayerFieldsMixin, serializers.ModelSerializer):
    subLayers = serializers.SerializerMethodField()
    companion_layers = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    tiles = serializers.SerializerMethodField()
    
    class Meta:
        model = Layer
        fields = ["parent", "catalog_html"] + shared_layer_fields

    def get_companion_layers(self, obj):
        companion_layers = get_companion_layers(obj)
        return CompanionLayerSerializer(companion_layers, many=True, context={'companion_parent':obj}).data
    def get_subLayers(self, obj):
        subLayers = get_serialized_sublayers(obj)
        return subLayers
    def get_type(self, obj):
        return obj.layer_type
    def get_tiles(self, obj):
        return obj.tiles_link
    
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

    class Meta(LayerSerializer.Meta):
        model = LayerWMS
        fields = LayerSerializer.Meta.fields + layer_arcgis_fields + layer_wms_fields + raster_type_fields + library_fields + vector_layer_fields + ["companion_layers"] + ["subLayers" , "order"]
    def get_order(self, obj):
        return get_layer_order(obj)
LayerWMSSerializer.add_layer_field_methods(LayerSerializer.Meta.fields)

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

    class Meta(LayerSerializer.Meta):
        model = LayerArcREST
        fields = LayerSerializer.Meta.fields + layer_arcgis_fields + layer_wms_fields + raster_type_fields + library_fields + vector_layer_fields + ["companion_layers"] + ["subLayers", "order"]

    def get_order(self, obj):
        return get_layer_order(obj)

LayerArcRESTSerializer.add_layer_field_methods(LayerSerializer.Meta.fields)

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

    class Meta(LayerSerializer.Meta):
        model = LayerArcFeatureService
        fields = LayerSerializer.Meta.fields + layer_arcgis_fields + layer_wms_fields + raster_type_fields + library_fields + vector_layer_fields + ["companion_layers"] + ["subLayers", "order"]

    def get_order(self, obj):
        return get_layer_order(obj)
LayerArcFeatureServiceSerializer.add_layer_field_methods(LayerSerializer.Meta.fields)

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

    arcgis_layers = serializers.CharField(default=None, read_only=True)
    password_protected = serializers.BooleanField(default=False, read_only=True)
    disable_arcgis_attributes = serializers.BooleanField(default=False, read_only=True)


    class Meta(LayerSerializer.Meta):
        model = LayerXYZ
        fields = LayerSerializer.Meta.fields + layer_arcgis_fields + layer_wms_fields + raster_type_fields + library_fields + vector_layer_fields + ["companion_layers"] + ["subLayers", "order"]

    def get_order(self, obj):
        return get_layer_order(obj)
LayerXYZSerializer.add_layer_field_methods(LayerSerializer.Meta.fields)

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
        fields = LayerSerializer.Meta.fields + layer_arcgis_fields + layer_wms_fields + raster_type_fields + library_fields + vector_layer_fields + ["companion_layers"] + ["subLayers", "order"]

    def get_order(self, obj):
        return get_layer_order(obj)
LayerVectorSerializer.add_layer_field_methods(LayerSerializer.Meta.fields)

def get_serializer_by_layer_type(layer_type):
    layer_type_to_serializer = {
        'WMS': LayerWMSSerializer,
        'ArcRest': LayerArcRESTSerializer,
        'ArcFeatureServer': LayerArcFeatureServiceSerializer,
        'Vector': LayerVectorSerializer,
        'XYZ': LayerXYZSerializer,
        # Add more mappings as necessary
    }
    return layer_type_to_serializer.get(layer_type)

def get_model_by_layer_type(layer_type):
    layer_type_to_model = {
        'WMS': LayerWMS,
        'ArcRest': LayerArcREST,
        'ArcFeatureServer': LayerArcFeatureService,
        'Vector': LayerVector,
        'XYZ': LayerXYZ,
        # Add more mappings as necessary
    }
    return layer_type_to_model.get(layer_type)

def get_specific_layer_instance(layer):
    if isinstance(layer, Layer):
        model = get_model_by_layer_type(layer.layer_type)
        try:
            return model.objects.get(layer=layer)
        except:
            pass
    return None



def get_serialized_layer(instance):
    specific_layer_instance = None
    if isinstance(instance, Layer):
        # Find the related layer model based on the layer_type
        layer_type = instance.layer_type
        serializer_class = get_serializer_by_layer_type(layer_type)
        model = get_model_by_layer_type(layer_type)
        if serializer_class:
            # Find the specific layer instance (e.g., LayerWMS) related to this Layer
            specific_layer_instance = model.objects.get(layer=instance)
            if specific_layer_instance:
                serializer = serializer_class(specific_layer_instance)
            else:
                # Fallback if the specific layer instance was not found
                return {}
        else:
            # Fallback for unexpected layer types
            return {}
    elif isinstance(instance, LayerWMS):
        serializer = LayerWMSSerializer(instance)
    elif isinstance(instance, LayerArcREST):
        serializer = LayerArcRESTSerializer(instance)
    elif isinstance(instance, LayerArcFeatureService):
        serializer = LayerArcFeatureServiceSerializer(instance)
    elif isinstance(instance, LayerVector):
        serializer = LayerVectorSerializer(instance)
    elif isinstance(instance, LayerXYZ):
        serializer = LayerXYZSerializer(instance)
    elif isinstance(instance, Theme):
        # Check if the theme is a subtheme (has a parent theme)
        if instance.parent:
            # Use SubThemeSerializer for subthemes
            serializer = SubThemeSerializer(instance)
        else:
            # Use a different serializer for parent themes if necessary
            serializer = ThemeSerializer(instance)
    else:
        # Fallback for unexpected types
        return {}

    # Flatten the representation to include the serialized data directly
    serialized_data = serializer.data

    return (serialized_data, specific_layer_instance)

class ChildOrderSerializer(serializers.ModelSerializer):
    # Serialize the generic related object
    def to_representation(self, instance):
        # Retrieve the related object
        related_object = instance.content_object
        # Serialize the related object based on its class
        if isinstance(related_object, Layer):
            # Find the related layer model based on the layer_type
            layer_type = related_object.layer_type
            serializer_class = get_serializer_by_layer_type(layer_type)
            model = get_model_by_layer_type(layer_type)
            if serializer_class:
                # Find the specific layer instance (e.g., LayerWMS) related to this Layer
                specific_layer_instance = model.objects.get(layer=related_object)
                if specific_layer_instance:
                    serializer = serializer_class(specific_layer_instance)
                else:
                    # Fallback if the specific layer instance was not found
                    return {}
            else:
                # Fallback for unexpected layer types
                return {}
        elif isinstance(related_object, LayerWMS):
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
        fields = []


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
            sorted_layers_details = []

            # Iterate over each child order to get related layer details
            for child_order in instance.children.all():
                content_object = child_order.content_object

                if content_object is not None:
                    layer_details = {
                        'id': content_object.id,
                        'name': content_object.name,
                        'order': child_order.order
                    }
                    sorted_layers_details.append(layer_details)
                else:
                    # Handle the case where content_object is None, perhaps log it or skip
                    continue  # Skip this child_order

            # Sort layers based on the order, then by name
            sorted_layers_details.sort(key=lambda x: (x['order'], x['name']))

            # Extract just the IDs from the sorted details
            sorted_ids = [detail['id'] for detail in sorted_layers_details if detail]  # Ensure detail is not None
            # Update 'layers' in the returned dictionary with sorted ids
            ret['layers'] = sorted_ids
        return ret

    def get_learn_link(self, obj):
        return obj.learn_link

class ShortThemeSerializer(serializers.ModelSerializer):
    class Meta:
            model = Theme
            fields = ["id", "name", "display_name", "is_visible",]

class SubThemeSerializer(serializers.ModelSerializer):
    order = serializers.SerializerMethodField()
    url = serializers.CharField(default="", read_only=True)
    proxy_url = serializers.BooleanField(default=False, read_only=True)
    is_disabled = serializers.BooleanField(default=False, read_only=True)
    disabled_message = serializers.CharField(default=None, read_only=True)
    overview = serializers.CharField(default="", read_only=True)
    data_source = serializers.CharField(default=None, read_only=True)
    data_notes = serializers.CharField(default=None, read_only=True)
    type = serializers.SerializerMethodField()
    source = serializers.CharField(read_only=True, default=None)
    annotated = serializers.BooleanField(default=False, read_only=True)
    kml = serializers.CharField(read_only=True, default=None)
    data_download = serializers.CharField(read_only=True, default=None)
    tiles = serializers.CharField(read_only=True, default=None)
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
    # Themes do not have 'opacity' by default
    opacity = serializers.FloatField(default=0.5)
    class Meta:
        model = Theme
        fields = shared_layer_fields + layer_arcgis_fields + layer_wms_fields + raster_type_fields + library_fields + vector_layer_fields + ["companion_layers", "parent", "catalog_html"] + ["subLayers", "order"]

    def get_order(self, obj):
        return get_layer_order(obj)
    def get_parent(self, obj):
        return None
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['description'] = ret['description']
        return ret
    def get_subLayers(self, obj):
        subLayers = get_serialized_sublayers(obj)
        return subLayers
    def get_type(self, obj):
        if hasattr(obj, 'theme_type') and obj.theme_type in ['radio', 'checkbox']:
            return obj.theme_type
    def get_data_url(self, obj):
        if settings.DATA_CATALOG_ENABLED:
            theme = obj.parent
            if theme:
                theme_url = reverse('portal.data_catalog.views.theme', args=[theme.name])
                if theme_url:
                    return "{0}#layer-info-{1}".format(theme_url, obj.slug_name)
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
                    'layer': obj,
                    # 'sub_layers': self.sublayers.exclude(layer_type="placeholder")
                }
            )
        except Exception as e:
            print(e)
        return None
    




class CompanionLayerSerializer(serializers.ModelSerializer):
    order = serializers.SerializerMethodField()
    overview = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()
    tiles = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    class Meta:
        model = Layer
        fields = shared_layer_fields + ["parent", "order"]

    def get_overview(self, obj):
        return obj.data_overview_text
    def get_order(self, obj):
        return get_layer_order(obj)
    def get_parent(self, obj):
        if hasattr(self, 'context') and  'companion_parent' in self.context.keys():
            return self.context['companion_parent'].layer.id
        # This query looks for Companionship instances where the current layer is among the companions
        companionship = Companionship.objects.filter(companions=obj).first()

        # If a companionship is found, it means the current layer is a companion to another layer
        if companionship:
            # Return the ID of the layer to which the current layer is a companion
            return companionship.layer.id
        return None
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        
        specific_layer_instance = get_specific_layer_instance(instance)
        if specific_layer_instance == None:
            specific_layer_instance = instance

        layer_specific_fields = {
            'arcgis_layers': None,
            'password_protected': False,
            "disable_arcgis_attributes":False,
            "query_by_point":False,
            "custom_style": None,
            "outline_width": None,
            "outline_color": None,
            "fill_opacity": None,
            "outline_opacity": None,
            "color": None,
            "point_radius": None,
            "graphic": None,
            "graphic_scale": 1.0,
            "wms_slug": None,
            "wms_version": None,
            "wms_srs": None,
            "wms_format": None,
            "wms_timing": None,
            "wms_time_item": None,
            "wms_styles": None,
            "wms_additional": "",
            "wms_info": False,
            "wms_info_format": None,
        }
        # Conditional logic for specific fields
        if isinstance(specific_layer_instance, LayerWMS):
            layer_specific_fields.update({
                "wms_slug": specific_layer_instance.wms_slug,
                "wms_version": specific_layer_instance.wms_version,
                "wms_srs": specific_layer_instance.wms_srs,
                "wms_timing": specific_layer_instance.wms_timing,
                "wms_time_item": specific_layer_instance.wms_time_item,
                "wms_styles": specific_layer_instance.wms_styles,
                "wms_additional": specific_layer_instance.wms_additional,
                "wms_info": specific_layer_instance.wms_info,
                "wms_info_format": specific_layer_instance.wms_info_format,
                "query_by_point": specific_layer_instance.query_by_point,
            })
        elif isinstance(specific_layer_instance, LayerArcREST):
            layer_specific_fields.update({
                "arcgis_layers":specific_layer_instance.arcgis_layers,
                "password_protected":specific_layer_instance.password_protected,
                "disable_arcgis_attributes":specific_layer_instance.disable_arcgis_attributes,
                "query_by_point":specific_layer_instance.query_by_point,
            })
        elif isinstance(specific_layer_instance, LayerArcFeatureService):
            layer_specific_fields.update({
                "arcgis_layers":specific_layer_instance.arcgis_layers,
                "password_protected":specific_layer_instance.password_protected,
                "disable_arcgis_attributes":specific_layer_instance.disable_arcgis_attributes,
                "custom_style": specific_layer_instance.custom_style,
                "outline_width": specific_layer_instance.outline_width,
                "outline_color": specific_layer_instance.outline_color,
                "fill_opacity": specific_layer_instance.fill_opacity,
                "color": specific_layer_instance.color,
                "point_radius": specific_layer_instance.point_radius,
                "graphic": specific_layer_instance.graphic,
                "graphic_scale": specific_layer_instance.graphic_scale,
                
            })
        elif isinstance(specific_layer_instance,LayerVector):
            layer_specific_fields.update({
                "custom_style": specific_layer_instance.custom_style,
                "outline_width": specific_layer_instance.outline_width,
                "outline_color": specific_layer_instance.outline_color,
                "fill_opacity": specific_layer_instance.fill_opacity,
                "color": specific_layer_instance.color,
                "point_radius": specific_layer_instance.point_radius,
                "graphic": specific_layer_instance.graphic,
                "graphic_scale": specific_layer_instance.graphic_scale,
            })
        elif isinstance(specific_layer_instance, LayerXYZ):
            layer_specific_fields.update({
                "query_by_point":specific_layer_instance.query_by_point,
            })
        ret.update(layer_specific_fields)
        return ret
    def get_tiles(self,obj):
        return obj.tiles_link
    def get_type(self,obj):
        return obj.layer_type

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
    tiles = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    
    class Meta:
        model = Layer
        fields = shared_layer_fields + ["is_sublayer", "parent", "order"]

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

        specific_layer_instance = get_specific_layer_instance(instance)
        if specific_layer_instance == None:
            specific_layer_instance = instance

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
        if isinstance(specific_layer_instance, LayerWMS):
            layer_specific_fields.update({
                "wms_slug": specific_layer_instance.wms_slug,
                "wms_version": specific_layer_instance.wms_version,
                "wms_srs": specific_layer_instance.wms_srs,
                "wms_timing": specific_layer_instance.wms_timing,
                "wms_time_item": specific_layer_instance.wms_time_item,
                "wms_styles": specific_layer_instance.wms_styles,
                "wms_additional": specific_layer_instance.wms_additional,
                "wms_info": specific_layer_instance.wms_info,
                "wms_info_format": specific_layer_instance.wms_info_format,
                "query_by_point": specific_layer_instance.query_by_point,
            })
        elif isinstance(specific_layer_instance, LayerArcREST):
            layer_specific_fields.update({
                "arcgis_layers":specific_layer_instance.arcgis_layers,
                "password_protected":specific_layer_instance.password_protected,
                "disable_arcgis_attributes":specific_layer_instance.disable_arcgis_attributes,
                "query_by_point":specific_layer_instance.query_by_point,
            })
        elif isinstance(specific_layer_instance, LayerArcFeatureService):
            layer_specific_fields.update({
                "arcgis_layers":specific_layer_instance.arcgis_layers,
                "password_protected":specific_layer_instance.password_protected,
                "disable_arcgis_attributes":specific_layer_instance.disable_arcgis_attributes,
                "custom_style": specific_layer_instance.custom_style,
                "outline_width": specific_layer_instance.outline_width,
                "outline_color": specific_layer_instance.outline_color,
                "fill_opacity": specific_layer_instance.fill_opacity,
                "color": specific_layer_instance.color,
                "point_radius": specific_layer_instance.point_radius,
                "graphic": specific_layer_instance.graphic,
                "graphic_scale": specific_layer_instance.graphic_scale,
            })
        elif isinstance(specific_layer_instance,LayerVector):
            layer_specific_fields.update({
                "custom_style": specific_layer_instance.custom_style,
                "outline_width": specific_layer_instance.outline_width,
                "outline_color": specific_layer_instance.outline_color,
                "fill_opacity": specific_layer_instance.fill_opacity,
                "color": specific_layer_instance.color,
                "point_radius": specific_layer_instance.point_radius,
                "graphic": specific_layer_instance.graphic,
                "graphic_scale": specific_layer_instance.graphic_scale,
            })
        elif isinstance(specific_layer_instance, LayerXYZ):
            layer_specific_fields.update({
                "query_by_point":specific_layer_instance.query_by_point,
            })
        ret.update(layer_specific_fields)
        return ret
    def get_parent(self, obj):

        layer_content_type = ContentType.objects.get_for_model(obj.__class__)
        child_orders = ChildOrder.objects.filter(object_id=obj.id, content_type=layer_content_type)
        if child_orders:
            return child_orders[0].parent_theme.id
        return None
    def get_tiles(self,obj):
        return obj.tiles_link
    def get_type(self,obj):
        return obj.layer_type