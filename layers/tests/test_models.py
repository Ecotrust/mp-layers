from django.test import TestCase
from layers.models import Theme, LayerWMS, LayerArcGIS, ChildOrder
from layers.serializers import ThemeSerializer, LayerWMSSerializer, LayerArcGISSerializer
from collections.abc import Collection
from django.contrib.contenttypes.models import ContentType
# request to get data from live site, mung it and make it into v2
class ThemeTest(TestCase):
    def setUp(self):
        #NEED TO ADD MORE PARENT_THEME, CHILD_THEME AND LAYERS TO TEST ORDERING BY ID WHEN NAME IS SAME AS WELL
        parent_theme1 = Theme.objects.create(name="Parent Theme A", order=2)
        parent_theme2 = Theme.objects.create(name="Parent Theme B", order=1)

        # Create child themes and set their parent_theme
        child_theme1 = Theme.objects.create(name="Child Theme A", parent_theme=parent_theme1, order=1)
        child_theme2 = Theme.objects.create(name="Child Theme B", parent_theme=parent_theme2, order=1)

        # Create layers
        wms_layer1 = LayerWMS.objects.create(name="WMS Layer")
        arcgis_layer1 = LayerArcGIS.objects.create(name="ArcGIS Layer")

        # Create ChildOrders with same order but different names
        ChildOrder.objects.create(parent_theme=parent_theme1, content_object=child_theme1, order=1)
        ChildOrder.objects.create(parent_theme=parent_theme1, content_object=wms_layer1, order=1)
        ChildOrder.objects.create(parent_theme=parent_theme2, content_object=child_theme2, order=1)
        ChildOrder.objects.create(parent_theme=parent_theme2, content_object=arcgis_layer1, order=1)

        # Create sub-child theme
        sub_child_theme = Theme.objects.create(name="Sub-Child Theme", parent_theme=child_theme1)
        ChildOrder.objects.create(parent_theme=child_theme1, content_object=sub_child_theme, order=2)
        
    # def test_theme(self):
        # Testing serialized data of theme1 to check if relationships were defined properly
        # actual_data = ThemeSerializer(self.theme1).data
        # print(actual_data)
        # self.assertIsInstance(actual_data, dict)
        # self.assertIsInstance(actual_data["children"], Collection)
        # self.assertIsInstance(actual_data["children"][0], dict)

        # # Check if theme has children (subthemes and layers)
        # self.assertTrue(len(actual_data["children"]) > 0)

        # # Check if the expected child layer (layer1) exists
        # self.assertTrue(any(item['name'] == "Layer 1" for item in actual_data['children']))

        # # Check if the expected child theme (theme2) exists
        # self.assertTrue(any(item['name'] == "test2" for item in actual_data['children']))

        # # Check order of children
        # self.assertEqual(actual_data['children'][0]['name'], self.theme2.name)
        # self.assertEqual(actual_data['children'][1]['name'], self.layer1.name)

        # # Get list of children for the item with the name "test2"
        # test2_children = next((item['children'] for item in actual_data["children"] if item['name'] == 'test2'), [])
        
        # # Iterate over each child in the test2_children list and check condition, return bool
        # layer2_exists = any(child['name'] == 'layer2' for child in test2_children)
        # theme3_exists = any(child['name'] == 'test3' for child in test2_children)

        # # Assert the result, will return True if they exist as children
        # assert layer2_exists, "layer2 should exist as a child under test2"
        # assert theme3_exists, "theme3 should exist as a child under test2"

    def test_theme_hierarchy(self):
        parent_theme1 = Theme.objects.get(name="Parent Theme A")
        parent_theme2 = Theme.objects.get(name="Parent Theme B")
        # Test parent-child relationships
        # Serialize the parent themes
        serialized_data1 = ThemeSerializer(parent_theme1).data
        serialized_data2 = ThemeSerializer(parent_theme2).data

        # Extract the ordered children for testing
        parent1_children_serialized = [child.get('name', '') for child in serialized_data1.get('children', [])]
        parent2_children_serialized = [child.get('name', '') for child in serialized_data2.get('children', [])]

        self.assertEqual(parent1_children_serialized, [("Child Theme A"), ("WMS Layer")])
        self.assertEqual(parent2_children_serialized, [("ArcGIS Layer"), ("Child Theme B")])

    def test_parent_theme_ordering(self):
        # Fetch all top-level themes (themes with no parent_theme)
        parent_themes = Theme.objects.filter(parent_theme__isnull=True)

        # Serialize the parent themes
        serialized_data = ThemeSerializer(parent_themes, many=True).data

        # Extract the names for testing
        serialized_names = [theme.get('name', '') for theme in serialized_data]

        # Define the expected order
        expected_order = ["Parent Theme B", "Parent Theme A"]  # Adjust as per your expected order

        # Assert the order
        self.assertEqual(serialized_names, expected_order)
        # self.assertTrue(hasattr(theme, "name"))
        # self.assertTrue(hasattr(theme, "id"))
        # self.assertTrue(hasattr(theme, "uuid"))
        # self.assertTrue(hasattr(theme, "display_name"))
        # self.assertTrue(hasattr(theme, "visible"))
        # self.assertTrue(hasattr(theme, "description"))

        # self.assertIsInstance(theme.name, str)
        # self.assertIsInstance(theme.id, int)
        # self.assertIsInstance(theme.display_name, str)
        # self.assertIsInstance(theme.visible, bool)
        # self.assertIsInstance(theme.description, str)

        # self.assertEqual(theme.name, "test")
        # self.assertEqual(theme.id, 1)
        # self.assertEqual(theme.display_name, "test")
        # self.assertEqual(theme.visible, True)
        # self.assertEqual(theme.description, "test")

class WMSLayerTest(TestCase):
    def setUp(self):
        self.theme1 = Theme.objects.create(name="test")
        self.theme2 = Theme.objects.create(name="test2")

       # Create layers
        self.layer1 = LayerWMS.objects.create(name="testlayer")
        self.layer2 = LayerWMS.objects.create(name="testlayer2", wms_slug="hi", wms_version="hello", wms_format="pusheen", wms_srs="world", 
                                              wms_styles="style", wms_timing="hullo", wms_time_item="ello", wms_additional="star", wms_info=True, wms_info_format="test")
        self.layer3 = LayerWMS.objects.create(name="testlayer3")

        # Create layer orders
        LayerOrder.objects.create(theme=self.theme1, layer=self.layer1, order=2)
        LayerOrder.objects.create(theme=self.theme1, layer=self.layer2, order=1)
        LayerOrder.objects.create(theme=self.theme2, layer=self.layer1, order=1)

    def test_layer_multiple_parents(self):
        theme1_actual_data = ThemeSerializer(self.theme1).data
        theme2_actual_data = ThemeSerializer(self.theme2).data

        self.assertTrue(len(theme1_actual_data["children"]) > 0)
        self.assertTrue(len(theme2_actual_data["children"]) > 0)

        self.assertEqual(theme1_actual_data['children'][0]['name'], self.layer2.name)
        self.assertEqual(theme1_actual_data['children'][1]['name'], self.layer1.name)
        self.assertEqual(theme2_actual_data["children"][0]["name"], self.layer1.name)

        self.assertTrue(len(self.layer1.wms_parent_themes.all()) > 0)

        self.assertIn(self.theme1, self.layer1.wms_parent_themes.all())
        self.assertIn(self.theme2, self.layer1.wms_parent_themes.all())
    
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

    # def test_duplicate_layer_order_raises_integrity_error(self):
    #     # Attempt to create a LayerOrder with the same theme and order
    #     with self.assertRaises(IntegrityError):
    #         WMSLayerOrder.objects.create(theme=self.theme1, layer=self.layer3, order=2)

class ArcGISLayerTest(TestCase):
    def setUp(self):
        self.theme1 = Theme.objects.create(name="test")
        self.theme2 = Theme.objects.create(name="test2")

       # Create layers
        self.layer1 = LayerArcGIS.objects.create(name="testlayer")
        self.layer2 = LayerArcGIS.objects.create(name="testlayer2", arcgis_layers="19", password_protected=True, query_by_point=True, disable_arcgis_attributes=True)
        self.layer3 = LayerArcGIS.objects.create(name="testlayer3")

        # Create layer orders
        Order.objects.create(theme=self.theme1, layer=self.layer1, order=2)
        Order.objects.create(theme=self.theme1, layer=self.layer2, order=1)
        Order.objects.create(theme=self.theme2, layer=self.layer1, order=1)
    

    def test_layer_attributes(self):
        layer1_actual_Data = LayerArcGISSerializer(self.layer1).data
        layer2_actual_Data = LayerArcGISSerializer(self.layer2).data
        print(layer1_actual_Data)
        self.assertIn("name", layer1_actual_Data)
        self.assertIn("arcgis_layers", layer1_actual_Data)
        self.assertIn("password_protected", layer1_actual_Data)
        self.assertIn("query_by_point", layer1_actual_Data)
        self.assertIn("disable_arcgis_attributes", layer1_actual_Data)
