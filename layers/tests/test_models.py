from django.test import TestCase
from layers.models import Theme, Layer, MultilayerAssociation, MultilayerDimension, MultilayerDimensionValue, Companionship, LayerWMS, LayerArcREST, LayerArcFeatureService, LayerVector, LayerXYZ, ChildOrder
from layers.serializers import ThemeSerializer, LayerWMSSerializer, CompanionLayerSerializer, LayerArcRESTSerializer, LayerArcFeatureServiceSerializer, LayerXYZSerializer, LayerVectorSerializer, SubThemeSerializer, ChildOrderSerializer
from collections.abc import Collection
from django.contrib.contenttypes.models import ContentType
# request to get data from live site, mung it and make it into v2
class ThemeTest(TestCase):
    def setUp(self):
        #NEED TO ADD MORE PARENT_THEME, CHILD_THEME AND LAYERS TO TEST ORDERING BY ID WHEN NAME IS SAME AS WELL
        self.parent_theme1 = Theme.objects.create(name="Parent Theme A", order=2, slug_name="test")
        self.parent_theme2 = Theme.objects.create(name="Parent Theme B", order=1)
        self.parent_theme3 = Theme.objects.create(name="Parent Theme B", order=1)

        # Create child themes and set their parent_theme
        self.child_theme1 = Theme.objects.create(name="Child Theme A", layer_type="radio")
        self.child_theme2 = Theme.objects.create(name="Child Theme B", layer_type="radio")
        self.child_theme3 = Theme.objects.create(name="Child Theme B",layer_type="radio")

        # Create layers
        self.wms_layer1 = LayerWMS.objects.create(name="WMS Layer")
        self.arcgis_layer1 = LayerArcREST.objects.create(name="ArcGIS Layer")

        # Create ChildOrders with same order but different names
        
        ChildOrder.objects.create(parent_theme=self.parent_theme1, content_object=self.child_theme1, order=1)
        ChildOrder.objects.create(parent_theme=self.parent_theme1, content_object=self.wms_layer1, order=1)
        ChildOrder.objects.create(parent_theme=self.parent_theme2, content_object=self.child_theme2, order=1)
        ChildOrder.objects.create(parent_theme=self.parent_theme2, content_object=self.child_theme3, order=1)
        ChildOrder.objects.create(parent_theme=self.parent_theme2, content_object=self.arcgis_layer1, order=1)

        # Create sub-child theme
        sub_child_theme = Theme.objects.create(name="Sub-Child Theme")
        ChildOrder.objects.create(parent_theme=self.child_theme1, content_object=sub_child_theme, order=2)

    def test_theme_hierarchy(self):
        # Test parent-child relationships
        # Serialize the parent themes
        serialized_data1 = ThemeSerializer(self.parent_theme1).data

        serialized_data2 = ThemeSerializer(self.parent_theme2).data

        # Extract the ordered children's names and ids for testing
        parent1_children = serialized_data1["layers"]
        parent2_children = serialized_data2["layers"]

        self.assertEqual(parent1_children, [self.child_theme1.id, self.wms_layer1.id])
        self.assertEqual(parent2_children, [self.arcgis_layer1.id, self.child_theme2.id, self.child_theme3.id])

    def test_parent_theme_ordering(self):
        # Fetch all Theme IDs that are referenced as a child in ChildOrder
        child_theme_ids = ChildOrder.objects.values_list('object_id', flat=True)

        # Fetch all themes that are not in the list of child theme IDs
        parent_themes = Theme.objects.exclude(id__in=child_theme_ids).order_by('order')


        # Serialize the parent themes
        serialized_data = ThemeSerializer(parent_themes, many=True).data
        print(serialized_data)
        # Extract the names and ids for testing
        serialized_name_ids = [theme.get('id', 0) for theme in serialized_data]
        print(serialized_name_ids)
        # Define the expected order based on name and id
        expected_order = [
            (self.parent_theme2.id),  
            (self.parent_theme3.id), 
            (self.parent_theme1.id)  
        ]
        
        # Assert the order
        self.assertEqual(serialized_name_ids, expected_order)
    
    def test_attributes(self):
        theme = ThemeSerializer(self.parent_theme1).data

        self.assertIn("name", theme)
        self.assertIn("id", theme)
        self.assertIn("layers", theme)
        self.assertIn("learn_link", theme)

        self.assertIsInstance(theme["name"], str)
        self.assertIsInstance(theme["id"], int)
        self.assertIsInstance(theme["layers"], Collection)
        self.assertIsInstance(theme["learn_link"], str)

        self.assertEqual(theme["name"], "Parent Theme A")
        self.assertEqual(theme["learn_link"], "../learn/Parent Theme A")

def verify_serializer_v1_output(self, serialized_data, name, layer_type, **kwargs):
    expected_lookup = {
            'field': None,
            'details': []
        }
    expected_attributes = {
            'compress_attributes': False,
            'event': "click",
            'attributes': [],
            'mouseover_attribute': None,
            'preserved_format_attributes': []
        }
    expected_data_url = None
    if 'mouseover_field' in kwargs:
        expected_attributes['mouseover_attribute'] = kwargs['mouseover_field']
    
    expected_values = {
        "name": name,
        "layer_type": layer_type,
        "url": "",
        "order": 0,
        "proxy_url": False,
        "is_disabled": False,
        "disabled_message": "",
        "show_legend": True,
        "legend": None,
        "legend_title": None,
        "legend_subtitle": None,
        "description": "",
        "overview": "",
        "data_source": None,
        "data_notes": "",
        "metadata": None,
        "source": None,
        "annotated": False,
        "kml": None,
        "data_download": None,
        "learn_more": None,
        "map_tiles": None,
        "label_field": None,
        "minZoom": None,
        "maxZoom": None,
        "custom_style": None,
        "outline_width": None,
        "outline_color": None,
        "outline_opacity": None,
        "fill_opacity": None,
        "color": None,
        "point_radius": None,
        "graphic": None,
        "graphic_scale": 1.0,
        "opacity": .5,
        "is_multilayer_parent": False,
        "is_multilayer": False,
        "wms_slug": None,
        "wms_version": None,
        "wms_format": None,
        "wms_srs": None,
        "wms_timing": None,
        "wms_time_item": None,
        "wms_styles": None,
        "wms_additional": "",
        "wms_info": False,
        "wms_info_format": None,
        "arcgis_layers": None,
        "password_protected": False,
        "disable_arcgis_attributes": False,
        "query_by_point": False,
        "queryable": False,
        "has_companion": False,
        "companion_layers": [],
        "associated_multilayers": {},
        "dimensions": [],
        "parent": None,
        "data_url": expected_data_url,
        "attributes": expected_attributes,
        "lookups": expected_lookup,
    }

    companionships = Companionship.objects.filter(layer=serialized_data['id'])
    if companionships.exists():
        companion_layers = []
        for companionship in companionships:
            companion_layers.extend(CompanionLayerSerializer(companionship.companions.all(), many=True).data)
        if companion_layers:
            expected_values['has_companion'] = True
            expected_values['companion_layers'] = companion_layers

    for arg, value in kwargs.items():
        if arg != "mouseover_field": 
            expected_values[arg] = value

    # Check if all expected keys are present and expected values match
    for key, expected_value in expected_values.items():
        self.assertIn(key, serialized_data)
        self.assertEqual(serialized_data[key], expected_value, f"This is the key: {key}")
       
class CompanionLayerTest(TestCase):
    def setUp(self):
        self.parent_theme = Theme.objects.create(name="Parent Theme")
        # Create layer instances
        self.layer1 = LayerWMS.objects.create(name="Layer 1", slug_name="test")
        self.layer2 = LayerWMS.objects.create(name="Layer 2")
        self.layer3 = LayerWMS.objects.create(name="Layer 3")
        # Create Companionship instance
        self.companionship = Companionship.objects.create(layer=self.layer1)
        self.companionship.companions.add(self.layer2, self.layer3)

        ChildOrder.objects.create(parent_theme=self.parent_theme, content_object=self.layer1, order=1)
    def test_companion_relationships(self):
        # Check if Layer B and Layer C are companions to Layer A
        companions_ids = self.companionship.companions.values_list('id', flat=True)
        self.assertIn(self.layer2.id, companions_ids)
        self.assertIn(self.layer3.id, companions_ids)

        # Check if Layer A is correctly set in the Companionship
        self.assertEqual(self.companionship.layer, self.layer1)

        self.assertFalse(self.layer2.has_companion)
        self.assertFalse(self.layer3.has_companion)
        self.assertTrue(self.layer1.has_companion)
    def test_companion_parent(self):
        serialized_layer1_data = LayerWMSSerializer(self.layer1).data
        print(serialized_layer1_data)
        serialized_layer2_data = LayerWMSSerializer(self.layer2).data

        self.assertIsNone(serialized_layer1_data["parent"])
        self.assertIsNone(serialized_layer2_data["parent"])
        self.assertEqual(serialized_layer1_data["companion_layers"][0]["parent"], self.layer1.id)
    def test_serialized_companion_data(self):
        serialized_layer1_data = LayerWMSSerializer(self.layer1).data
        print(serialized_layer1_data)
        self.assertIn("catalog_html", serialized_layer1_data)
        self.assertIn("data_url", serialized_layer1_data)
        self.assertIn("attributes", serialized_layer1_data)
        self.assertIn("lookups", serialized_layer1_data)

class LayerSerializerTest(TestCase):
    def setUp(self):
        # First Level
        self.parent_theme = Theme.objects.create(name="Parent Theme")
        # Second Level
        self.sub_theme = Theme.objects.create(name="Sub Theme", layer_type="radio")
        self.layer1 = LayerWMS.objects.create(name="testlayer", layer_type="WMS")
        # Third Level
        self.layer2 = LayerWMS.objects.create(name="testlayer2", layer_type="WMS")
        self.sub_sub_theme = Theme.objects.create(name="Sub Sub Theme", layer_type="radio")
        # Fourth Level
        self.layer3 = LayerWMS.objects.create(name="testlayer3", layer_type="WMS")

        ChildOrder.objects.create(parent_theme=self.parent_theme, content_object=self.sub_theme, order = 1)
        ChildOrder.objects.create(parent_theme=self.parent_theme, content_object=self.layer1, order=2)

        ChildOrder.objects.create(parent_theme=self.sub_theme, content_object=self.layer2, order=1)
        ChildOrder.objects.create(parent_theme=self.sub_theme, content_object=self.sub_sub_theme, order=2)

        ChildOrder.objects.create(parent_theme=self.sub_sub_theme, content_object=self.layer3, order=1)

    def test_serialize_second_third_layer_parent(self):
        # Direct descendents of the parent theme should not have a parent when serialized.
        serialized_layer1_data = LayerWMSSerializer(self.layer1).data
        self.assertIsNone(serialized_layer1_data["parent"])

        # Third level layers should have their direct parent serialized.
        serialized_layer2_data = LayerWMSSerializer(self.layer2).data
        self.assertEqual(self.sub_theme.id, serialized_layer2_data["parent"])

    def test_serialize_fourth_and_beyond_layer_parent(self):
        # Layers fourth level and beyond should point to the second layer ancestor.
        # AKA should skip past any intermediary parents until the second layer.
        serialized_layer3_date = LayerWMSSerializer(self.layer3).data 
        self.assertEqual(self.sub_theme.id, serialized_layer3_date["parent"])

        




class SubThemeSerializerTest(TestCase):
    def setUp(self):
        # Create a test subtheme instance
        self.parent_theme = Theme.objects.create(name="Parent Theme")
        self.sub_theme = Theme.objects.create(name="Sub Theme", layer_type="radio")
        self.sub_sub_theme = Theme.objects.create(name="Subsubtheme", layer_type="radio")
        self.layer2 = LayerArcREST.objects.create(name="arcgis", layer_type="ArcRest")
        self.layer1 = LayerWMS.objects.create(name="testlayer", layer_type="WMS")
        self.layer3 = LayerWMS.objects.create(name="testlayer3", layer_type="WMS")
        self.layer4 = LayerWMS.objects.create(name="testlayer4", layer_type="WMS")
        self.layer5 = LayerWMS.objects.create(name="testlayer5", layer_type="WMS")

        ChildOrder.objects.create(parent_theme=self.parent_theme, content_object=self.sub_theme, object_id=self.sub_theme.id, order = 1)
        ChildOrder.objects.create(parent_theme=self.parent_theme, content_object=self.layer5, order=1)
        self.child_order_1 = ChildOrder.objects.create(parent_theme=self.sub_theme, content_object=self.layer1, order=1)
        
        ChildOrder.objects.create(parent_theme=self.sub_theme, content_object=self.sub_sub_theme, order=2)
        ChildOrder.objects.create(parent_theme=self.sub_theme, content_object=self.layer3, order=3)

        ChildOrder.objects.create(parent_theme=self.sub_sub_theme, content_object=self.layer2, order=1)
        ChildOrder.objects.create(parent_theme=self.sub_sub_theme, content_object=self.layer4, order=2)


    def test_subtheme_serialization(self):
    

        serializer = SubThemeSerializer(self.sub_theme)
        serialized_subtheme_data = serializer.data
        print(serialized_subtheme_data)
        serialized_layer_data = LayerWMSSerializer(self.layer3).data
        verify_serializer_v1_output(self, serialized_subtheme_data, name=self.sub_theme.name, layer_type=self.sub_theme.layer_type, order=1)

        # Extract only the 'id' from each item in 'subLayers'
        serialized_ids = [item['id'] for item in serialized_subtheme_data['subLayers']]

        # Define the expected IDs in order
        expected_ids = [self.layer1.id, self.layer2.id, self.layer4.id, self.layer3.id]

        # Assert that the order of IDs in the serialized data matches the expected order
        self.assertEqual(serialized_ids, expected_ids)
        # self.assertEqual(serialized_subtheme_data["id"], serialized_layer_data["parent"])


class WMSLayerTest(TestCase):
    def setUp(self):
        # Create Parent Themes
        self.theme1 = Theme.objects.create(name="test", order=1)
        self.theme2 = Theme.objects.create(name="test2", order=2)

       # Create layers
        self.layer1 = LayerWMS.objects.create(name="testlayer", layer_type="WMS")
        self.layer2 = LayerWMS.objects.create(name="testlayer2", layer_type="WMS", wms_slug="hi", wms_version="hello", wms_format="pusheen", wms_srs="world", 
                                              wms_styles="style", wms_timing="hullo", wms_time_item="ello", wms_additional="star", wms_info=True, wms_info_format="test")
        self.companionship = Companionship.objects.create(layer=self.layer1)
        self.companionship.companions.add(self.layer2)
        # Create layer orders
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer1, order=2)
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer2, order=1)
        ChildOrder.objects.create(parent_theme=self.theme2, content_object=self.layer1, order=1)

    def test_layer_multiple_parents(self):
        theme1_actual_data = ThemeSerializer(self.theme1).data
        theme2_actual_data = ThemeSerializer(self.theme2).data

        self.assertTrue(len(theme1_actual_data["layers"]) > 0)
        self.assertTrue(len(theme2_actual_data["layers"]) > 0)

        self.assertEqual(theme1_actual_data['layers'][0], self.layer2.id)
        self.assertEqual(theme1_actual_data['layers'][1], self.layer1.id)
        self.assertEqual(theme2_actual_data["layers"][0], self.layer1.id)

        layer_content_type = ContentType.objects.get_for_model(self.layer1)

        # Query ChildOrder for this layer
        child_orders = ChildOrder.objects.filter(content_type=layer_content_type, object_id=self.layer1.id)

        # Check that the layer is associated with at least one parent theme
        self.assertTrue(child_orders.exists())

        # Test the that parent_themes are Theme model
        for child_order in child_orders:
            self.assertIsInstance(child_order.parent_theme, Theme)
        
        # Retrieve all parent themes for the layer
        parent_themes = [child_order.parent_theme for child_order in child_orders]

        # Check that we have retrieved parent themes
        self.assertTrue(len(parent_themes) > 0)

        # Check that parent themes are correct based on created relationship in setup
        self.assertTrue(child_orders.filter(parent_theme=self.theme1).exists())
        self.assertTrue(child_orders.filter(parent_theme=self.theme2).exists())
    
    def test_layer_attributes(self):
        layer1_actual_data = LayerWMSSerializer(self.layer1).data
        layer2_actual_data = LayerWMSSerializer(self.layer2).data

        # Check that the WMS specific attributes exist
        
        verify_serializer_v1_output(self, layer1_actual_data, name=self.layer1.name, layer_type="WMS", order=1)
        verify_serializer_v1_output(self, layer2_actual_data, name=self.layer2.name, layer_type="WMS", order=1, wms_slug="hi", wms_version="hello", wms_format="pusheen", wms_srs="world", 
                                              wms_styles="style", wms_timing="hullo", wms_time_item="ello", wms_additional="star", wms_info=True, wms_info_format="test")

class ArcRESTLayerTest(TestCase):
    def setUp(self):
        self.theme1 = Theme.objects.create(name="test")
        self.theme2 = Theme.objects.create(name="test2")

       # Create layers
        self.layer1 = LayerArcREST.objects.create(name="testlayer")
        self.layer2 = LayerArcREST.objects.create(name="testlayer2", arcgis_layers="19", password_protected=True, query_by_point=True, disable_arcgis_attributes=True)
        self.layer3 = LayerArcREST.objects.create(name="testlayer3")
        self.companionship = Companionship.objects.create(layer=self.layer1)
        self.companionship.companions.add(self.layer2)
        # Create layer orders
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer1, order=2)
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer2, order=1)
        ChildOrder.objects.create(parent_theme=self.theme2, content_object=self.layer1, order=1)
    
    def test_layer_attributes(self):
        layer1_actual_data = LayerArcRESTSerializer(self.layer1).data
        layer2_actual_data = LayerArcRESTSerializer(self.layer2).data

        verify_serializer_v1_output(self, layer1_actual_data, name=self.layer1.name, layer_type="ArcRest", order=1)
        verify_serializer_v1_output(self, layer2_actual_data, name=self.layer2.name, layer_type="ArcRest", order=1, arcgis_layers="19", password_protected=True, query_by_point=True, disable_arcgis_attributes=True)
        
class ArcFeatureServiceLayerTest(TestCase):
    def setUp(self):
        self.theme1 = Theme.objects.create(name="test")

       # Create layers
        self.layer1 = LayerArcFeatureService.objects.create(name="testlayer")
        self.layer2 = LayerArcFeatureService.objects.create(name="testlayer2", arcgis_layers="19", password_protected=True,  disable_arcgis_attributes=True,
                                                            mouseover_field="hi", custom_style="test", outline_width=5, outline_color="blue", outline_opacity=5.0,
                                                            fill_opacity=5.0, color="blue", point_radius=5, graphic="Test", graphic_scale=5.0, opacity=5.0)
        self.companionship = Companionship.objects.create(layer=self.layer1)
        self.companionship.companions.add(self.layer2)
        # Create layer orders
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer1, order=2)
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer2, order=1)

    
    def test_layer_attributes(self):
        layer1_actual_data = LayerArcFeatureServiceSerializer(self.layer1).data
        layer2_actual_data = LayerArcFeatureServiceSerializer(self.layer2).data

        verify_serializer_v1_output(self, layer1_actual_data, name=self.layer1.name, layer_type="ArcFeatureServer", order=2)
        verify_serializer_v1_output(self, layer2_actual_data, name=self.layer2.name, layer_type="ArcFeatureServer", order=1, arcgis_layers="19", password_protected=True, disable_arcgis_attributes=True,
                                                            mouseover_field="hi", custom_style="test", outline_width=5, outline_color="blue", outline_opacity=5.0,
                                                            fill_opacity=5.0, color="blue", point_radius=5, graphic="Test", graphic_scale=5.0, opacity=5.0)

class XYZLayerTest(TestCase):
    def setUp(self):
        self.theme1 = Theme.objects.create(name="test")

        self.layer1 = LayerXYZ.objects.create(name="testlayer")
        self.layer2 = LayerXYZ.objects.create(name="testlayer2", query_by_point=True)
        self.companionship = Companionship.objects.create(layer=self.layer1)
        self.companionship.companions.add(self.layer2)
        # Create layer orders
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer1, order=2)
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer2, order=1)

    def test_layer_attributes(self):
        layer1_actual_data = LayerXYZSerializer(self.layer1).data
        layer2_actual_data = LayerXYZSerializer(self.layer2).data
        print(self.layer1.data_url)
        verify_serializer_v1_output(self, layer1_actual_data, name=self.layer1.name, layer_type="XYZ", order=2)
        verify_serializer_v1_output(self, layer2_actual_data, name=self.layer2.name, layer_type="XYZ", query_by_point=True, order=1)

class VectorLayerTest(TestCase):
    def setUp(self):
        self.theme1 = Theme.objects.create(name="test")

        self.layer1 = LayerVector.objects.create(name="testlayer")
        self.layer2 = LayerVector.objects.create(name="testlayer2", mouseover_field="hi", custom_style="test", outline_width=5, outline_color="blue", outline_opacity=5.0,
                                                            fill_opacity=5.0, color="blue", point_radius=5, graphic="Test", graphic_scale=5.0, opacity=5.0)
        
        # Create layer orders
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer1, order=2)
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer2, order=1)
    def test_layer_attributes(self):
        layer1_actual_data = LayerVectorSerializer(self.layer1).data

        layer2_actual_data = LayerVectorSerializer(self.layer2).data

        verify_serializer_v1_output(self, layer1_actual_data, name=self.layer1.name, layer_type="Vector", order=2)
        verify_serializer_v1_output(self, layer2_actual_data, name=self.layer2.name, layer_type="Vector", order=1, mouseover_field="hi", custom_style="test", outline_width=5, outline_color="blue", outline_opacity=5.0,
                                                            fill_opacity=5.0, color="blue", point_radius=5, graphic="Test", graphic_scale=5.0, opacity=5.0)

class ChildOrderSerializerTest(TestCase):
    def setUp(self):
         # Create a parent theme
        self.parent_theme = Theme.objects.create(name="Test Parent Theme")
        self.sub_theme = Theme.objects.create(name="Sub Theme")
        # Create layers
        self.layer_wms = LayerWMS.objects.create(name="Layer WMS")
        self.layer_arc_rest = LayerArcREST.objects.create(name="Layer ArcREST")
        self.layer_arc_feature = LayerArcFeatureService.objects.create(name="Layer ArcFeature")
        self.layer_xyz = LayerXYZ.objects.create(name="Layer XYZ")
        self.layer_vector = LayerVector.objects.create(name="Layer Vector")
        # Create a corresponding ChildOrder instance
        self.child_order_wms = ChildOrder.objects.create(parent_theme=self.parent_theme,content_object=self.layer_wms, order=1)
        self.child_order_arc_rest = ChildOrder.objects.create(parent_theme=self.parent_theme, content_object=self.layer_arc_rest, order=1)
        self.child_order_arc_feature = ChildOrder.objects.create(parent_theme=self.parent_theme, content_object=self.layer_arc_feature, order=1)
        self.child_order_xyz = ChildOrder.objects.create(parent_theme=self.parent_theme, content_object=self.layer_xyz, order=1)
        self.child_order_vector = ChildOrder.objects.create(parent_theme=self.parent_theme, content_object=self.layer_vector, order=1)
        self.child_order_subtheme = ChildOrder.objects.create(parent_theme=self.parent_theme, content_object=self.sub_theme, order=1)
    def test_serialize_layer_arc_rest(self):
        # Serialize the LayerArcREST instance directly
        arc_rest_serializer = LayerArcRESTSerializer(self.layer_arc_rest)
        arc_rest_serialized_data = arc_rest_serializer.data

        # Serialize the ChildOrder instance that contains the LayerArcREST
        child_order_serializer = ChildOrderSerializer(self.child_order_arc_rest)
        child_order_serialized_data = child_order_serializer.data

        # Compare the two serialized outputs
        self.assertEqual(child_order_serialized_data, arc_rest_serialized_data)

    def test_serialize_layer_wms(self):
        wms_serializer = LayerWMSSerializer(self.layer_wms)
        wms_serialized_data = wms_serializer.data
        # Serialize ChildOrder with a LayerWMS object
        serializer = ChildOrderSerializer(self.child_order_wms)
        serialized_data = serializer.data

        # Compare the two serialized outputs
        self.assertEqual(serialized_data, wms_serialized_data)

    def test_serialize_layer_arc_feature(self):
        arc_feature_serializer = LayerArcFeatureServiceSerializer(self.layer_arc_feature)
        arc_feature_serialized_data = arc_feature_serializer.data
        # Serialize ChildOrder with a LayerWMS object
        serializer = ChildOrderSerializer(self.child_order_arc_feature)
        serialized_data = serializer.data

        # Compare the two serialized outputs
        self.assertEqual(serialized_data, arc_feature_serialized_data)

    def test_serialize_layer_xyz(self):
        xyz_serializer = LayerXYZSerializer(self.layer_xyz)
        xyz_serialized_data = xyz_serializer.data
        # Serialize ChildOrder with a LayerWMS object
        serializer = ChildOrderSerializer(self.child_order_xyz)
        serialized_data = serializer.data

        # Compare the two serialized outputs
        self.assertEqual(serialized_data, xyz_serialized_data)

    def test_serialize_layer_vector(self):
        vector_serializer = LayerVectorSerializer(self.layer_vector)
        vector_serialized_data = vector_serializer.data
        # Serialize ChildOrder with a LayerWMS object
        serializer = ChildOrderSerializer(self.child_order_vector)
        serialized_data = serializer.data

        # Compare the two serialized outputs
        self.assertEqual(serialized_data, vector_serialized_data)
    
    def test_serialize_subtheme(self):
        subtheme_serializer = SubThemeSerializer(self.sub_theme)
        subtheme_serialized_data = subtheme_serializer.data
        # Serialize ChildOrder with a LayerWMS object
        serializer = ChildOrderSerializer(self.child_order_subtheme)
        serialized_data = serializer.data

        # Compare the two serialized outputs
        self.assertEqual(serialized_data, subtheme_serialized_data)

class MultilayerTest(TestCase):
    def setUp(self):
        # Create Parent Layer
        self.parent_layer = LayerWMS.objects.create(name="Parent Layer")

        # Create Dimension
        self.month_dimension = MultilayerDimension.objects.create(
            name="Month", label="Month", order=201, animated=True, angle_labels=False, layer=self.parent_layer)

        # Create Dimension Values and Associated Layers
        month_values = ["January", "February", "March", "April", "May", "June", 
                        "July", "August", "September", "October", "November", "December"]
        self.associated_layers = {}  # Store the associated layers for reference
        for month in month_values:
            # Create associated layer
            associated_layer = LayerWMS.objects.create(name=f"{month} Layer", layer_type="WMS")
            self.associated_layers[month] = associated_layer

            # Create dimension value which should auto-create an association
            month_value = MultilayerDimensionValue.objects.create(
                dimension=self.month_dimension, value=month, label=month, order=month_values.index(month) + 1)

            # Retrieve the auto-created association for this dimension value
            auto_created_association = month_value.associations.first()

            # Check if the association exists and update its layer
            if auto_created_association:
                auto_created_association.layer = associated_layer
                auto_created_association.save()

    def test_dimension_recursion(self):
        # Assuming you have a method dimensionRecursion in your Layer model
        dimensions = [self.month_dimension]
        associations = MultilayerAssociation.objects.filter(parentLayer=self.parent_layer)

        # Call the recursion function
        actual_output = self.parent_layer.dimensionRecursion(dimensions, associations)

        # Define the expected output structure
        expected_output = {month: self.associated_layers[month].id for month in self.associated_layers}

        # Assert equality
        self.assertEqual(actual_output, expected_output)
        
    def test_multilayer_related_attributes(self):
        serialized_data = LayerWMSSerializer(self.parent_layer).data

        expected_dimensions_output = [{'label': 'Month', 'name': 'Month', 'order': 201, 'animated': True, 'angle_labels': False, 'nodes': [{'value': 'January', 'label': 'January', 'order': 1}, 
                                            {'value': 'February', 'label': 'February', 'order': 2}, {'value': 'March', 'label': 'March', 'order': 3}, {'value': 'April', 'label': 'April', 'order': 4}, 
                                            {'value': 'May', 'label': 'May', 'order': 5}, {'value': 'June', 'label': 'June', 'order': 6}, {'value': 'July', 'label': 'July', 'order': 7}, 
                                            {'value': 'August', 'label': 'August', 'order': 8}, {'value': 'September', 'label': 'September', 'order': 9}, {'value': 'October', 'label': 'October', 'order': 10}, 
                                            {'value': 'November', 'label': 'November', 'order': 11}, {'value': 'December', 'label': 'December', 'order': 12}]}]
        expected_multilayers_output = {month: self.associated_layers[month].id for month in self.associated_layers}
        
        self.assertIn("associated_multilayers", serialized_data)
        self.assertIn("dimensions", serialized_data)
        self.assertIn("is_multilayer", serialized_data)
        self.assertIn("is_multilayer_parent", serialized_data)

        self.assertEqual(expected_dimensions_output, serialized_data["dimensions"])
        self.assertEqual(False, serialized_data["is_multilayer"])
        self.assertEqual(True, serialized_data["is_multilayer_parent"])
        self.assertEqual(expected_multilayers_output, serialized_data["associated_multilayers"])

        january_data = LayerWMSSerializer(self.associated_layers["January"]).data

        self.assertEqual(True, january_data["is_multilayer"])
        self.assertEqual(False, january_data["is_multilayer_parent"])
        self.assertEqual([], january_data["dimensions"])
        self.assertEqual({}, january_data["associated_multilayers"])

