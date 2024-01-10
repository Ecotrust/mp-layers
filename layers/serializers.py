from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from layers.models import Theme, ChildOrder, LayerWMS, LayerArcREST

#inherit v2 serializer to make v1 serializer
class LayerWMSSerializer(serializers.ModelSerializer):
    # order = serializers.SerializerMethodField()

    # Set default values for unrelated fields for layer type to support V1
    arcgis_layers = serializers.CharField(default=None, read_only=True)
    password_protected = serializers.BooleanField(default=False, read_only=True)
    query_by_point = serializers.BooleanField(default=False, read_only=True)
    disable_arcgis_attributes = serializers.BooleanField(default=False, read_only=True)

    class Meta:
        model = LayerWMS
        fields = ["id", "name", "wms_slug", "wms_version", "wms_format", "wms_srs", "wms_timing", "wms_time_item",
                   "wms_styles", "wms_additional", "wms_info", "wms_info_format", "arcgis_layers", "password_protected", "query_by_point", 
                   "disable_arcgis_attributes"]

class LayerArcRESTSerializer(serializers.ModelSerializer):
    # order = serializers.SerializerMethodField()
    wms_slug = serializers.CharField(default=None, read_only=True)
    wms_version = serializers.CharField(default=None, read_only=True)
    wms_format = serializers.CharField(default=None, read_only=True)
    wms_srs = serializers.CharField(default=None, read_only=True)
    wms_timing = serializers.CharField(default=None, read_only=True)
    wms_time_item = serializers.CharField(default=None, read_only=True)
    wms_styles = serializers.CharField(default=None, read_only=True)
    wms_additional = serializers.CharField(default=None, read_only=True)
    wms_info = serializers.BooleanField(default=False, read_only=True)
    wms_info_format = serializers.CharField(default=None, read_only=True)

    class Meta:
        model = LayerArcREST
        fields = ["id", "name", "arcgis_layers", "password_protected", "query_by_point", "disable_arcgis_attributes", "wms_slug", 
                  "wms_version", "wms_format", "wms_srs", "wms_timing", "wms_time_item", "wms_styles", "wms_additional", "wms_info", 
                  "wms_info_format"]
            
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
        elif isinstance(related_object, Theme):
            # Using a simplified serializer for Theme to avoid deep nesting
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

class ThemeSerializer(serializers.ModelSerializer):
    # children = serializers.SerializerMethodField()
    learn_link = serializers.SerializerMethodField()
    children = ChildOrderSerializer(many=True, read_only=True)

    class Meta:
        model = Theme
        fields = ["id", "name", "children", "learn_link"]

    def to_representation(self, instance):
    # Call the super method to get the default representation
        ret = super().to_representation(instance)

        # Order the children by the 'order' field and remove 'order' from the final output
        if 'children' in ret:
            sorted_children = sorted(ret['children'], key=lambda x: (
                x.get('order', 0), 
                x.get('name', ''), 
                x.get('id', 0)
            ))
            for child in sorted_children:
                child.pop('order', None)  # Remove 'order' field
            ret['children'] = sorted_children

        return ret
    
    def get_learn_link(self, obj):
        return obj.learn_link
    
