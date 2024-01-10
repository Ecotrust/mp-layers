from django.test import TestCase
from layers.models import Theme, LayerWMS, LayerArcGIS, ChildOrder
from layers.serializers import ThemeSerializer, LayerWMSSerializer, LayerArcGISSerializer
from collections.abc import Collection
from django.contrib.contenttypes.models import ContentType
# request to get data from live site, mung it and make it into v2
class ThemeTest(TestCase):
    def setUp(self):
        #NEED TO ADD MORE PARENT_THEME, CHILD_THEME AND LAYERS TO TEST ORDERING BY ID WHEN NAME IS SAME AS WELL
        self.parent_theme1 = Theme.objects.create(name="Parent Theme A", order=2)
        self.parent_theme2 = Theme.objects.create(name="Parent Theme B", order=1)
        self.parent_theme3 = Theme.objects.create(name="Parent Theme B", order=1)

        # Create child themes and set their parent_theme
        self.child_theme1 = Theme.objects.create(name="Child Theme A", parent_theme=self.parent_theme1)
        self.child_theme2 = Theme.objects.create(name="Child Theme B", parent_theme=self.parent_theme2)
        self.child_theme3 = Theme.objects.create(name="Child Theme B", parent_theme=self.parent_theme2)

        # Create layers
        self.wms_layer1 = LayerWMS.objects.create(name="WMS Layer")
        self.arcgis_layer1 = LayerArcGIS.objects.create(name="ArcGIS Layer")

        # Create ChildOrders with same order but different names
        ChildOrder.objects.create(parent_theme=self.parent_theme1, content_object=self.child_theme1, order=1)
        ChildOrder.objects.create(parent_theme=self.parent_theme1, content_object=self.wms_layer1, order=1)
        ChildOrder.objects.create(parent_theme=self.parent_theme2, content_object=self.child_theme2, order=1)
        ChildOrder.objects.create(parent_theme=self.parent_theme2, content_object=self.child_theme3, order=1)
        ChildOrder.objects.create(parent_theme=self.parent_theme2, content_object=self.arcgis_layer1, order=1)

        # Create sub-child theme
        sub_child_theme = Theme.objects.create(name="Sub-Child Theme", parent_theme=self.child_theme1)
        ChildOrder.objects.create(parent_theme=self.child_theme1, content_object=sub_child_theme, order=2)

    def test_theme_hierarchy(self):
        # Test parent-child relationships
        # Serialize the parent themes
        serialized_data1 = ThemeSerializer(self.parent_theme1).data
        serialized_data2 = ThemeSerializer(self.parent_theme2).data

        # Extract the ordered children's names and ids for testing
        parent1_children_serialized = [(child.get('name', ''), child.get('id', 0)) for child in serialized_data1.get('children', [])]
        parent2_children_serialized = [(child.get('name', ''), child.get('id', 0)) for child in serialized_data2.get('children', [])]

        self.assertEqual(parent1_children_serialized, [("Child Theme A", self.child_theme1.id), ("WMS Layer", self.wms_layer1.id)])
        self.assertEqual(parent2_children_serialized, [("ArcGIS Layer", self.arcgis_layer1.id), ("Child Theme B", self.child_theme2.id), ("Child Theme B", self.child_theme3.id)])

    def test_parent_theme_ordering(self):
        # Fetch all top-level themes (themes with no parent_theme)
        parent_themes = Theme.objects.filter(parent_theme__isnull=True)

        # Serialize the parent themes
        serialized_data = ThemeSerializer(parent_themes, many=True).data

        # Extract the names and ids for testing
        serialized_name_ids = [(theme.get('name', ''), theme.get('id', 0)) for theme in serialized_data]

        # Define the expected order based on name and id
        expected_order = [
            ("Parent Theme B", self.parent_theme2.id),  
            ("Parent Theme B", self.parent_theme3.id), 
            ("Parent Theme A", self.parent_theme1.id)  
        ]

        # Assert the order
        self.assertEqual(serialized_name_ids, expected_order)
    
    def test_attributes(self):
        theme = ThemeSerializer(self.parent_theme1).data
        print(theme)

        self.assertIn("name", theme)
        self.assertIn("id", theme)
        self.assertIn("children", theme)
        self.assertIn("learn_link", theme)

        self.assertIsInstance(theme["name"], str)
        self.assertIsInstance(theme["id"], int)
        self.assertIsInstance(theme["children"], Collection)
        self.assertIsInstance(theme["learn_link"], str)

        self.assertEqual(theme["name"], "Parent Theme A")
        self.assertEqual(theme["learn_link"], "../learn/Parent Theme A")

class WMSLayerTest(TestCase):
    def setUp(self):
        # Create Parent Themes
        self.theme1 = Theme.objects.create(name="test", order=1)
        self.theme2 = Theme.objects.create(name="test2", order=2)

       # Create layers
        self.layer1 = LayerWMS.objects.create(name="testlayer")
        self.layer2 = LayerWMS.objects.create(name="testlayer2", wms_slug="hi", wms_version="hello", wms_format="pusheen", wms_srs="world", 
                                              wms_styles="style", wms_timing="hullo", wms_time_item="ello", wms_additional="star", wms_info=True, wms_info_format="test")

        # Create layer orders
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer1, order=2)
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer2, order=1)
        ChildOrder.objects.create(parent_theme=self.theme2, content_object=self.layer1, order=1)

    def test_layer_multiple_parents(self):
        theme1_actual_data = ThemeSerializer(self.theme1).data
        theme2_actual_data = ThemeSerializer(self.theme2).data

        self.assertTrue(len(theme1_actual_data["children"]) > 0)
        self.assertTrue(len(theme2_actual_data["children"]) > 0)

        self.assertEqual(theme1_actual_data['children'][0]['name'], self.layer2.name)
        self.assertEqual(theme1_actual_data['children'][1]['name'], self.layer1.name)
        self.assertEqual(theme2_actual_data["children"][0]["name"], self.layer1.name)

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
        layer1_actual_Data = LayerWMSSerializer(self.layer1).data
        layer2_actual_Data = LayerWMSSerializer(self.layer2).data
        # Check that the WMS specific attributes exist
        self.assertIn("wms_slug", layer1_actual_Data)
        self.assertIn("wms_version", layer1_actual_Data)
        self.assertIn("wms_format", layer1_actual_Data)
        self.assertIn("wms_srs", layer1_actual_Data)
        self.assertIn("wms_timing", layer1_actual_Data)
        self.assertIn("wms_time_item", layer1_actual_Data)
        self.assertIn("wms_styles", layer1_actual_Data)
        self.assertIn("wms_additional", layer1_actual_Data)
        self.assertIn("wms_info", layer1_actual_Data)
        self.assertIn("wms_info_format", layer1_actual_Data)

        # Check that ArcGIS specific attributes also exist for V1
        self.assertIn("arcgis_layers", layer1_actual_Data)
        self.assertIn("password_protected", layer1_actual_Data)
        self.assertIn("query_by_point", layer1_actual_Data)
        self.assertIn("disable_arcgis_attributes", layer1_actual_Data)

        self.assertIsInstance(layer1_actual_Data["wms_slug"], (str, type(None)))
        self.assertIsInstance(layer1_actual_Data["wms_version"], (str, type(None)))
        self.assertIsInstance(layer1_actual_Data["wms_format"], (str, type(None)))
        self.assertIsInstance(layer1_actual_Data["wms_srs"], (str, type(None)))
        self.assertIsInstance(layer1_actual_Data["wms_timing"], (str, type(None)))
        self.assertIsInstance(layer1_actual_Data["wms_time_item"], (str, type(None)))
        self.assertIsInstance(layer1_actual_Data["wms_styles"], (str, type(None)))
        self.assertIsInstance(layer1_actual_Data["wms_additional"], (str, type(None)))
        self.assertIsInstance(layer1_actual_Data["wms_info"], bool)
        self.assertIsInstance(layer1_actual_Data["wms_info_format"], (str, type(None)))
        self.assertIsInstance(layer1_actual_Data["arcgis_layers"], type(None))
        self.assertIsInstance(layer1_actual_Data["password_protected"], bool)
        self.assertIsInstance(layer1_actual_Data["query_by_point"], bool)
        self.assertIsInstance(layer1_actual_Data["disable_arcgis_attributes"], bool)

        self.assertEqual(layer1_actual_Data["wms_slug"], None)
        self.assertEqual(layer1_actual_Data["wms_version"], None)
        self.assertEqual(layer1_actual_Data["wms_format"], None)
        self.assertEqual(layer1_actual_Data["wms_srs"], None)
        self.assertEqual(layer1_actual_Data["wms_timing"], None)
        self.assertEqual(layer1_actual_Data["wms_time_item"], None)
        self.assertEqual(layer1_actual_Data["wms_styles"], None)
        self.assertEqual(layer1_actual_Data["wms_additional"], None)
        self.assertEqual(layer1_actual_Data["wms_info"], False)
        self.assertEqual(layer1_actual_Data["wms_info_format"], None)
        self.assertEqual(layer1_actual_Data["arcgis_layers"], None)
        self.assertEqual(layer1_actual_Data["password_protected"], False)
        self.assertEqual(layer1_actual_Data["query_by_point"], False)
        self.assertEqual(layer1_actual_Data["disable_arcgis_attributes"], False)

        self.assertEqual(layer2_actual_Data["wms_slug"], "hi")
        self.assertEqual(layer2_actual_Data["wms_version"], "hello")
        self.assertEqual(layer2_actual_Data["wms_format"], "pusheen")
        self.assertEqual(layer2_actual_Data["wms_srs"], "world")
        self.assertEqual(layer2_actual_Data["wms_timing"], "hullo")
        self.assertEqual(layer2_actual_Data["wms_time_item"], "ello")
        self.assertEqual(layer2_actual_Data["wms_styles"], "style")
        self.assertEqual(layer2_actual_Data["wms_additional"], "star")
        self.assertEqual(layer2_actual_Data["wms_info"], True)
        self.assertEqual(layer2_actual_Data["wms_info_format"], "test")

class ArcGISLayerTest(TestCase):
    def setUp(self):
        self.theme1 = Theme.objects.create(name="test")
        self.theme2 = Theme.objects.create(name="test2")

       # Create layers
        self.layer1 = LayerArcGIS.objects.create(name="testlayer")
        self.layer2 = LayerArcGIS.objects.create(name="testlayer2", arcgis_layers="19", password_protected=True, query_by_point=True, disable_arcgis_attributes=True)
        self.layer3 = LayerArcGIS.objects.create(name="testlayer3")

        # Create layer orders
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer1, order=2)
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer2, order=1)
        ChildOrder.objects.create(parent_theme=self.theme2, content_object=self.layer1, order=1)
    
    def test_layer_attributes(self):
        layer1_actual_Data = LayerArcGISSerializer(self.layer1).data
        layer2_actual_Data = LayerArcGISSerializer(self.layer2).data
        print(layer1_actual_Data)

        # Check that ArcGIS specific attributes exist
        self.assertIn("name", layer1_actual_Data)
        self.assertIn("arcgis_layers", layer1_actual_Data)
        self.assertIn("password_protected", layer1_actual_Data)
        self.assertIn("query_by_point", layer1_actual_Data)
        self.assertIn("disable_arcgis_attributes", layer1_actual_Data)

        # Check that WMS specific attributes exist for V1
        self.assertIn("wms_slug", layer1_actual_Data)
        self.assertIn("wms_version", layer1_actual_Data)
        self.assertIn("wms_format", layer1_actual_Data)
        self.assertIn("wms_srs", layer1_actual_Data)
        self.assertIn("wms_timing", layer1_actual_Data)
        self.assertIn("wms_time_item", layer1_actual_Data)
        self.assertIn("wms_styles", layer1_actual_Data)
        self.assertIn("wms_additional", layer1_actual_Data)
        self.assertIn("wms_info", layer1_actual_Data)
        self.assertIn("wms_info_format", layer1_actual_Data)

        self.assertIsInstance(layer1_actual_Data["wms_slug"], (str, type(None)))
        self.assertIsInstance(layer1_actual_Data["wms_version"], (str, type(None)))
        self.assertIsInstance(layer1_actual_Data["wms_format"], (str, type(None)))
        self.assertIsInstance(layer1_actual_Data["wms_srs"], (str, type(None)))
        self.assertIsInstance(layer1_actual_Data["wms_timing"], (str, type(None)))
        self.assertIsInstance(layer1_actual_Data["wms_time_item"], (str, type(None)))
        self.assertIsInstance(layer1_actual_Data["wms_styles"], (str, type(None)))
        self.assertIsInstance(layer1_actual_Data["wms_additional"], (str, type(None)))
        self.assertIsInstance(layer1_actual_Data["wms_info"], bool)
        self.assertIsInstance(layer1_actual_Data["wms_info_format"], (str, type(None)))
        self.assertIsInstance(layer1_actual_Data["arcgis_layers"], type(None))
        self.assertIsInstance(layer1_actual_Data["password_protected"], bool)
        self.assertIsInstance(layer1_actual_Data["query_by_point"], bool)
        self.assertIsInstance(layer1_actual_Data["disable_arcgis_attributes"], bool)
        self.assertIsInstance(layer2_actual_Data["arcgis_layers"], str)

        # Check default values when layer is created without any defined values
        self.assertEqual(layer1_actual_Data["wms_slug"], None)
        self.assertEqual(layer1_actual_Data["wms_version"], None)
        self.assertEqual(layer1_actual_Data["wms_format"], None)
        self.assertEqual(layer1_actual_Data["wms_srs"], None)
        self.assertEqual(layer1_actual_Data["wms_timing"], None)
        self.assertEqual(layer1_actual_Data["wms_time_item"], None)
        self.assertEqual(layer1_actual_Data["wms_styles"], None)
        self.assertEqual(layer1_actual_Data["wms_additional"], None)
        self.assertEqual(layer1_actual_Data["wms_info"], False)
        self.assertEqual(layer1_actual_Data["wms_info_format"], None)
        self.assertEqual(layer1_actual_Data["arcgis_layers"], None)
        self.assertEqual(layer1_actual_Data["password_protected"], False)
        self.assertEqual(layer1_actual_Data["query_by_point"], False)
        self.assertEqual(layer1_actual_Data["disable_arcgis_attributes"], False)

        # Check that values are correct when layer is created with defined values
        self.assertEqual(layer2_actual_Data["arcgis_layers"], "19")
        self.assertEqual(layer2_actual_Data["password_protected"], True)
        self.assertEqual(layer2_actual_Data["query_by_point"], True)
        self.assertEqual(layer2_actual_Data["disable_arcgis_attributes"], True)