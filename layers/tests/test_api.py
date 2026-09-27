from layers.models import Layer, Theme, Site, ChildOrder, Companionship, LayerArcREST
from layers.views import get_catalog_records, get_layer_catalog_content, get_layer_search_data, get_layer_details, get_layers_for_theme, get_themes, layer_status, migration_layer_details
from unittest.mock import Mock, patch
from layers.serializers import *
from collections.abc import Collection
from django.core.cache import cache
from django.test import override_settings, RequestFactory, TestCase
import sys
from os.path import join
import json

DYNAMIC_PARENT_THEMES = [24, 25]
SLIDER_PARENT_THEMES = [28, 2, 8, 14]
UNCERTAIN_STATUS_THEMES = DYNAMIC_PARENT_THEMES + SLIDER_PARENT_THEMES + [27, ]
COMPANION_THEME = [23, ]
FULLY_COMPLIANT_THEMES = COMPANION_THEME + [1, 29, 4, 10, 7, 11, 3, 12, 5, 22]

# theme id's that are exluded from FULLY_COMPLIANT_THEMES
NOT_COMPLIANT_THEMES = [6624, 6259, 28, 2, 24, 8, 14, 6675, 27]

@override_settings(DB_CHANNEL="madronaportal")
class DataManagerGetLayerDetailsTest(TestCase):
    
    def setUp(self):
        self.factory = RequestFactory()
        site = Site.objects.get(pk=1)
        theme1 = Theme.objects.create(name="companion", display_name="companion", is_visible=True)
        theme1.site.add(site)

        layer1 =Theme.objects.create(name="arcrest_layer", theme_type="radio")
        layer1.site.add(site)

        self.layer2 = Layer.objects.create(name="Arc", layer_type="ArcRest", url="http://test-url.com")
        self.arcrest2 = LayerArcREST.objects.create(layer=self.layer2)

        self.layer2.site.add(site)
        # This layer is to test how sublayers are returned
        self.layer3 = Layer.objects.create(name="sublayer", layer_type="ArcRest", url="http://test-url-3.com")
        self.arcrest3 = LayerArcREST.objects.create(layer=self.layer3)
        self.layer3.site.add(site)

        ChildOrder.objects.create(parent_theme=theme1, content_object=self.layer2, order=1)
        ChildOrder.objects.create(parent_theme=theme1, content_object=layer1, order=1)
        ChildOrder.objects.create(parent_theme=layer1, content_object=self.layer3, order=1)
        self.companionship = Companionship.objects.create(layer=self.layer2)
        self.companionship.companions.add(self.layer3)
        
    def test_view_layer_details_response_format(self):
        request1 = self.factory.get(f"/layers/get_layer_details/{self.layer2.id}/")
        response = get_layer_details(request1, self.layer2.id)
        self.assertEqual(response.status_code, 200)
        result1 = json.loads(response.content)

        request2 = self.factory.get(f"/layers/get_layer_details/{self.layer3.id}/")
        response2 = get_layer_details(request2, self.layer3.id)
        self.assertEqual(response2.status_code, 200)
        result2 = json.loads(response2.content)

        layer_attr = ["id", "uuid", "name", "order", "type", "arcgis_layers", "url", "password_protected", "query_by_point", "proxy_url", "disable_arcgis_attributes", "wms_slug", "wms_version", "wms_format", "wms_srs", "wms_styles", "wms_timing", "wms_time_item", "wms_additional", "wms_info", 
                            "wms_info_format", "utfurl", "subLayers", "companion_layers", "has_companion", "queryable", "legend", "legend_title", "legend_subtitle", "show_legend", "description", "overview", "data_source", "data_notes", "kml", "data_download", 
                            "learn_more", "metadata", "source", "tiles", "label_field", "attributes", "minZoom", "maxZoom", "lookups", "custom_style", "outline_color", "outline_opacity", "outline_width", "point_radius", "color", "fill_opacity", "graphic", "graphic_scale", "opacity",
                            "annotated", "is_disabled", "disabled_message", "data_url", "is_multilayer", "is_multilayer_parent", "dimensions", "associated_multilayers", "catalog_html", "parent", "date_modified"]
        # Check if each attribute is present in the response for both layers
        for i in layer_attr:
            self.assertIn(i, result1)
            self.assertIn(i, result2)
        
        results = [result1, result2]
        # List of attributes with their expected data types for validation
        for i in results:
            self.assertIsInstance(i["id"], int, "id should be int")
            self.assertIsInstance(i["uuid"], str, "uuid should be string")
            self.assertIsInstance(i["name"], str, "name should be string") 
            self.assertIsInstance(i["order"], int, "order should be int")
            self.assertIsInstance(i["type"], str, "type should be string")
            self.assertIsInstance(i["arcgis_layers"], (str, type(None)), "arcgis_layers should be string or none")
            self.assertIsInstance(i["url"], str, "url should be string")
            self.assertIsInstance(i["password_protected"], bool, "password_protected should be boolean")
            self.assertIsInstance(i["query_by_point"], bool, "query_by_point should be boolean")
            self.assertIsInstance(i["proxy_url"], bool, "proxy_url should be boolean")
            self.assertIsInstance(i["disable_arcgis_attributes"], bool, "disable_arcgis_attributes should be boolean" )
            self.assertIsInstance(i["wms_slug"], (str, type(None)), "wms_slug should be string or none" )
            self.assertIsInstance(i["wms_version"], (str, type(None)), "wms_version should be string or none")
            self.assertIsInstance(i["wms_format"], (str, type(None)), "wms_format should be string or none")
            self.assertIsInstance(i["wms_srs"], (str, type(None)), "wms_srs should be string or none")
            self.assertIsInstance(i["wms_styles"], (str, type(None)), "wms_styles should be string or none")
            self.assertIsInstance(i["wms_timing"], (str, type(None)), "wms_timing should be string or none")
            self.assertIsInstance(i["wms_time_item"], (str, type(None)), "wms_time_item should be string or none")
            self.assertIsInstance(i["wms_additional"], (str, type(None)), "wms_additional should be string or none")
            self.assertIsInstance(i["wms_info"], bool, "wms_info should be boolean")
            self.assertIsInstance(i["wms_info_format"], (str, type(None)), "wms_info_format should be string or none")
            self.assertIsInstance(i["utfurl"], (str, type(None)), "utfurl should be string or none")
            self.assertIsInstance(i["subLayers"], Collection, "subLayers should be a collection")
            self.assertIsInstance(i["companion_layers"], Collection, "companion_layers should be collection")
            self.assertIsInstance(i["has_companion"], bool, "has_companion should be bool")
            self.assertIsInstance(i["queryable"], bool, "queryable should be boolean")
            self.assertIsInstance(i["legend"], (str, type(None)), "legend should be string")
            self.assertIsInstance(i["legend_title"], (str, type(None)), "legend_title should be string or none")
            self.assertIsInstance(i["legend_subtitle"], (str, type(None)), "legend_subtitle should be string or none")
            self.assertIsInstance(i["show_legend"], bool, "show_legend should be bool" )
            self.assertIsInstance(i["description"], (str, type(None)), "description should be string or none" )
            self.assertIsInstance(i["overview"], (str, type(None)), "overview should be string or none")
            self.assertIsInstance(i["data_source"], (str, type(None)), "data_source should be string or none")
            self.assertIsInstance(i["data_notes"], (str, type(None)), "data_notes should be string or none" )
            self.assertIsInstance(i["kml"], (str, type(None)), "kml should be string or none")
            self.assertIsInstance(i["data_download"], (str, type(None)), "data_download should be string or none")
            self.assertIsInstance(i["learn_more"], (str, type(None)), "learn_more should be string or none")
            self.assertIsInstance(i["metadata"], (str, type(None)), "metadata should be string or none")
            self.assertIsInstance(i["source"], (str, type(None)), "source should be string or none")
            self.assertIsInstance(i["tiles"], (str, type(None)), "tiles should be string or none")
            self.assertIsInstance(i["label_field"], (str, type(None)), "label_field should be string or none")
            self.assertIsInstance(i["attributes"], dict, "attributes should be dictionary (JSON object)")
            self.assertIsInstance(i["minZoom"], (float, type(None)), "minZoom should be float")
            self.assertIsInstance(i["maxZoom"], (float, type(None)), "maxZoom should be float")
            self.assertIsInstance(i["lookups"], dict, "lookups should be dictionary(JSON object)")
            self.assertIsInstance(i["custom_style"], (str, type(None)), "custom_style should be string or none")
            self.assertIsInstance(i["outline_color"], (str, type(None)), "outline_color should be string or none")
            self.assertIsInstance(i["outline_opacity"], (float, type(None)), "outline_opacity should be float or none")
            self.assertIsInstance(i["outline_width"], (int, type(None)), "outline_width should be int or none")
            self.assertIsInstance(i["point_radius"], (int, type(None)), "point_radius should be int or none")
            self.assertIsInstance(i["color"], (str, type(None)), "color should be string or none")
            self.assertIsInstance(i["fill_opacity"], (float, type(None)), "fill_opacity should be float or none")
            self.assertIsInstance(i["graphic"], (str, type(None)), "graphic should be string or none")
            self.assertIsInstance(i["graphic_scale"], (float), "graphic_scale should be float")
            self.assertIsInstance(i["opacity"], float, "opacity should be float")
            self.assertIsInstance(i["annotated"], bool, "annotated should be bool")
            self.assertIsInstance(i["is_disabled"], bool, "is_disabled should be bool")
            self.assertIsInstance(i["disabled_message"], (str, type(None)), "disabled_message should be string or none")
            self.assertIsInstance(i["data_url"], (str, type(None)), "data_url should be string or none")
            self.assertIsInstance(i["is_multilayer"], bool, "is_multilayer should be bool")
            self.assertIsInstance(i["is_multilayer_parent"], bool, "is_multilayer_parent should be bool")
            self.assertIsInstance(i["dimensions"], Collection, "dimensions should be collection")
            self.assertIsInstance(i["associated_multilayers"], dict, "associated_multilayers should be dictionary")
            self.assertIsInstance(i["catalog_html"], str, "catalog_html should be string")
            self.assertIsInstance(i["parent"], (dict, type(None)), "parent should be dictionary(JSON object) or none")
            self.assertIsInstance(i["date_modified"], str, "date_modified should be string")
    
    def test_view_layer_details_default_response_data(self):
        request = self.factory.get(f"/layers/get_layer_details/{self.layer2.id}/")
        response = get_layer_details(request, self.layer2.id)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)

        # Expected default attributes and lookups for layer 2
        expected_attributes = {"compress_attributes": False, "event": "click", "attributes": [], "mouseover_attribute": None, "preserved_format_attributes": []}
        expected_lookups = {"field": None, "details": []}

        # Validate each attribute with its expected value
        self.assertEqual(result["name"], "Arc")
        self.assertEqual(result["order"], 1)
        self.assertEqual(result["type"], "ArcRest")
        self.assertEqual(result["url"], "http://test-url.com")
        self.assertEqual(result["arcgis_layers"], None)
        self.assertEqual(result["password_protected"], False)
        self.assertEqual(result["query_by_point"], False)
        self.assertEqual(result["proxy_url"], False)
        self.assertEqual(result["disable_arcgis_attributes"], False)
        self.assertEqual(result["wms_slug"], None)
        self.assertEqual(result["wms_version"], None)
        self.assertEqual(result["wms_format"], None)
        self.assertEqual(result["wms_srs"], None)
        self.assertEqual(result["wms_styles"], None)
        self.assertEqual(result["wms_timing"], None)
        self.assertEqual(result["wms_time_item"], None)
        self.assertEqual(result["wms_additional"], "")
        self.assertEqual(result["wms_info"], False)
        self.assertEqual(result["wms_info_format"], None)
        self.assertEqual(result["utfurl"], None)
        self.assertEqual(result["subLayers"], [])
        self.assertEqual(result["has_companion"], True)
        self.assertEqual(result["queryable"], False)
        self.assertEqual(result["legend"], None)
        self.assertEqual(result["legend_title"], None)
        self.assertEqual(result["legend_subtitle"], None)
        self.assertEqual(result["show_legend"], True)
        self.assertEqual(result["description"], None) #if no description is provided, default to None
        self.assertEqual(result["overview"], None) #if no overview is provided, default to None
        self.assertEqual(result["data_source"], None)
        self.assertEqual(result["data_notes"], None)#if no data notes are provided, default to None
        self.assertEqual(result["kml"], None)
        self.assertEqual(result["data_download"], None)
        self.assertEqual(result["learn_more"], None)
        self.assertEqual(result["metadata"], None)
        self.assertEqual(result["source"], None)
        self.assertIsInstance(result["tiles"], str)
        self.assertEqual(result["label_field"], None)
        self.assertEqual(result["attributes"], expected_attributes)
        self.assertEqual(result["lookups"], expected_lookups)
        self.assertEqual(result["minZoom"], None)
        self.assertEqual(result["maxZoom"], None)
        self.assertEqual(result["custom_style"], None)
        self.assertEqual(result["outline_color"], None)
        self.assertEqual(result["outline_opacity"], None)
        self.assertEqual(result["outline_width"], None)
        self.assertEqual(result["point_radius"], None)
        self.assertEqual(result["color"], None)
        self.assertEqual(result["fill_opacity"], None)
        self.assertEqual(result["graphic"], None)
        self.assertEqual(result["graphic_scale"], 1.0)
        self.assertEqual(result["opacity"], 0.5)
        self.assertEqual(result["annotated"], False)
        self.assertEqual(result["is_disabled"], False)
        self.assertEqual(result["disabled_message"], None)
        self.assertIsInstance(result["data_url"], str)
        self.assertEqual(result["is_multilayer"], False)
        self.assertEqual(result["is_multilayer_parent"], False)
        self.assertEqual(result["dimensions"], [])
        self.assertEqual(result["associated_multilayers"], {})
        self.assertEqual(result["parent"], None)


@override_settings(DB_CHANNEL="madronaportal")
class DataManagerGetThemesTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # Associate theme with default site id, otherwise themes do not show up
        site = Site.objects.get(pk=1)
        self.theme1 = Theme.objects.create(name="test", display_name="test", is_visible=True)
        self.theme1.site.add(site)
        self.theme2 = Theme.objects.create(name="test2", display_name="test2", is_visible=True)
        self.theme2.site.add(site)

    def test_get_themes_response_format(self):
        request = self.factory.get("/layers/get_themes/")
        response = get_themes(request)

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)

        self.assertIn("themes", result, "Response should contain 'themes' key")

        # Get the list of themes from the response
        themes = result["themes"]

        # Check if the themes is a list
        self.assertTrue(isinstance(themes, list), "Themes should be a list")
        self.assertTrue(len(themes)==2)

        # Check the format of each theme object in the list
        for theme in themes:
            self.assertTrue(isinstance(theme, dict), "Each theme should be a dictionary")

            self.assertIn("id", theme, "Theme should have 'id' key")
            self.assertIn("name", theme, "Theme should have 'name' key")
            self.assertIn("display_name", theme, "Theme should have 'display_name' key")
            self.assertIn("is_visible", theme, "Theme should have 'is_visible' key")

            self.assertTrue(isinstance(theme["id"], int), "id should be an integer")
            self.assertTrue(isinstance(theme["name"], str), "name should be a string")
            self.assertTrue(isinstance(theme["display_name"], str), "display_name should be a string")
            self.assertTrue(isinstance(theme["is_visible"], bool), "is_visible should be a boolean")

    def test_get_themes_response_data(self):
        request = self.factory.get("/layers/get_themes/")
        response = get_themes(request)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)

        self.assertIn("themes", result, "Response should contain 'themes' key")

        # Get the specific themes from the response to test data 
        theme_1 = result["themes"][0]
        theme_2 = result["themes"][1]

        # Check the format of each theme object in the list - similar to first
        self.assertEqual(theme_1["name"], "test")
        self.assertEqual(theme_1["display_name"], "test")
        self.assertTrue(theme_1["is_visible"])

        self.assertEqual(theme_2["name"], "test2")
        self.assertEqual(theme_2["display_name"], "test2")
        self.assertTrue(theme_2["is_visible"])

# keep unless it cannot be fixed
@override_settings(DB_CHANNEL="madronaportal")
class DataManagerGetLayerSearchDataTest(TestCase):
    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()
        site = Site.objects.get(pk=1)
        self.first_theme = Theme.objects.create(name="first_theme", display_name="first_theme", is_visible=True, description="first theme")
        self.first_theme.site.add(site)

        self.second_theme = Theme.objects.create(name="second_theme", display_name="second_theme", is_visible=True, description="test 4")
        self.second_theme.site.add(site)

        # first_layer is a sublayer of first theme
        self.theme_with_sublayers = Theme.objects.create(name="theme_with_sublayers", display_name="theme_with_sublayers", is_visible=True, description="theme with sublayers")
        self.theme_with_sublayers.site.add(site)

        self.sublayer = Layer.objects.create(name="sublayer")
        self.sublayer.site.add(site)

        self.second_layer = Layer.objects.create(name="second_layer")
        self.second_layer.site.add(site)

        ChildOrder.objects.create(parent_theme=self.first_theme, content_object=self.theme_with_sublayers, order=1)
        ChildOrder.objects.create(parent_theme=self.theme_with_sublayers, content_object=self.sublayer, order=1)
        ChildOrder.objects.create(parent_theme=self.second_theme, content_object=self.second_layer, order=1)

    def test_get_layer_search_data_response_format(self):
        request = self.factory.get("/layers/get_layer_search_data/")
        response = get_layer_search_data(request)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertIn(self.theme_with_sublayers.name, result, "result should have theme_with_sublayers key")
        self.assertIn(self.second_layer.name, result, "result should have second_layer key")
        self.assertIn("layer", result[self.theme_with_sublayers.name], "should have layer key")
        self.assertIn("theme", result[self.theme_with_sublayers.name], "should have theme key")
        self.assertIn("id", result[self.theme_with_sublayers.name]["layer"], "each layer should have id key")
        self.assertIn("name", result[self.theme_with_sublayers.name]["layer"], "each layer should have name key")
        self.assertIn("has_sublayers", result[self.theme_with_sublayers.name]["layer"], "each layer should have has_sublayers key")
        self.assertIn("sublayers", result[self.theme_with_sublayers.name]["layer"], "each layer should have sublayers key")
        self.assertIn("name", result[self.theme_with_sublayers.name]["layer"]["sublayers"][0], "each sublayer should have name key")
        self.assertIn("id", result[self.theme_with_sublayers.name]["layer"]["sublayers"][0], "each sublayer should have id key")
        self.assertIn("id", result[self.theme_with_sublayers.name]["theme"], "each theme should have id key")
        self.assertIn("name", result[self.theme_with_sublayers.name]["theme"], "each theme should have name key")
        self.assertIn("description", result[self.theme_with_sublayers.name]["theme"], "each theme should have description key")

        self.assertIsInstance(result, dict, "result should be dictionary")
        self.assertIsInstance(result[self.theme_with_sublayers.name], dict, "result's keys should be dictionary")
        self.assertIsInstance(result[self.theme_with_sublayers.name]["layer"], dict, "layer should be dictionary")
        self.assertIsInstance(result[self.theme_with_sublayers.name]["theme"], dict, "theme should be dictionary")
        self.assertIsInstance(result[self.theme_with_sublayers.name]["layer"]["id"], int, "id should be integer")
        self.assertIsInstance(result[self.theme_with_sublayers.name]["layer"]["name"], str, "name should be string")
        self.assertIsInstance(result[self.theme_with_sublayers.name]["layer"]["has_sublayers"], bool, "has_sublayers should be boolean")
        self.assertIsInstance(result[self.theme_with_sublayers.name]["layer"]["sublayers"], Collection, "sublayers should be collection")
        self.assertIsInstance(result[self.theme_with_sublayers.name]["layer"]["sublayers"][0], dict, "each sublayer should be a dictionary")
        self.assertIsInstance(result[self.theme_with_sublayers.name]["layer"]["sublayers"][0]["name"], str, "name should be string")
        self.assertIsInstance(result[self.theme_with_sublayers.name]["layer"]["sublayers"][0]["id"], int, "id should be integer")
        self.assertIsInstance(result[self.theme_with_sublayers.name]["theme"]["id"], int, "theme id should be integer")
        self.assertIsInstance(result[self.theme_with_sublayers.name]["theme"]["name"], str, "theme name should be string")
        self.assertIsInstance(result[self.theme_with_sublayers.name]["theme"]["description"], str, "theme description should be string")

        self.assertEqual(result[self.theme_with_sublayers.name]["layer"]["name"], self.theme_with_sublayers.name)
        self.assertEqual(result[self.theme_with_sublayers.name]["layer"]["has_sublayers"], True)
        self.assertEqual(result[self.theme_with_sublayers.name]["layer"]["sublayers"][0]["name"], self.sublayer.name)
        self.assertEqual(result[self.theme_with_sublayers.name]["theme"]["name"], self.first_theme.display_name)
        self.assertEqual(result[self.theme_with_sublayers.name]["theme"]["description"], self.first_theme.description)
        self.assertEqual(result[self.second_layer.name]["layer"]["name"], self.second_layer.name)
        self.assertEqual(result[self.second_layer.name]["layer"]["has_sublayers"], False)
        self.assertEqual(result[self.second_layer.name]["layer"]["sublayers"], [])
        self.assertEqual(result[self.second_layer.name]["theme"]["name"], self.second_theme.display_name)
        self.assertEqual(result[self.second_layer.name]["theme"]["description"], self.second_theme.description)

@override_settings(DB_CHANNEL="madronaportal")
class DataManagerGetLayersForThemeTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        site = Site.objects.get(pk=1)
        self.theme1 = Theme.objects.create(name="companion", display_name="companion", is_visible=True, description="test")
        self.theme1.site.add(site)
        # This test layer will have attributes defined to test data type when filled out
        layer1 = Theme.objects.create(name="arcrest_layer", display_name="arcrest_layer", is_visible=True, description="test")
        # This test layer will not have attributes defined other than required fields to test default behavior when attributes left empty
        layer1.site.add(site)

        layer2 = Layer.objects.create(name="sublayer", layer_type="ArcRest")
        layer2.site.add(site)

        ChildOrder.objects.create(parent_theme=self.theme1, content_object=layer1, order=1)
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=layer2, order=1)
        ChildOrder.objects.create(parent_theme=layer1, content_object=layer2, order=1)

    def test_get_layers_for_theme(self):
        request = self.factory.get(f"/layers/get_layers_for_theme/{self.theme1.id}/", HTTP_HOST="localhost:8000")
        response = get_layers_for_theme(request, self.theme1.id)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)

        self.assertIn("layers", result)
        self.assertIn("id", result["layers"][0])
        self.assertIn("name", result["layers"][0])
        self.assertIn("type", result["layers"][0])
        self.assertIn("has_sublayers", result["layers"][0])
        self.assertIn("subLayers", result["layers"][0])
        self.assertIn("id", result["layers"][0]["subLayers"][0])
        self.assertIn("name", result["layers"][0]["subLayers"][0])
        self.assertIn("slug_name", result["layers"][0]["subLayers"][0])

        self.assertIsInstance(result, Collection, "result should be collection")
        self.assertIsInstance(result["layers"], Collection, "layers should be collection")
        self.assertIsInstance(result["layers"][0], dict, "each layer should be a dictionary")
        self.assertIsInstance(result["layers"][0]["id"], int, "id should be integer")
        self.assertIsInstance(result["layers"][0]["name"], str, "name should be string")
        self.assertIsInstance(result["layers"][0]["type"], str, "type should be string")
        self.assertIsInstance(result["layers"][0]["has_sublayers"], bool, "has_sublayers should be boolean")
        self.assertIsInstance(result["layers"][0]["subLayers"], Collection, "subLayers should be collection")
        self.assertIsInstance(result["layers"][0]["subLayers"][0], dict, "each subLayer should be a dictionary")
        self.assertIsInstance(result["layers"][0]["subLayers"][0]["id"], int, "id should be integer")
        self.assertIsInstance(result["layers"][0]["subLayers"][0]["name"], str, "name should be string")
        self.assertIsInstance(result["layers"][0]["subLayers"][0]["slug_name"], (str, type(None)), "slug_name should be string")

        self.assertEqual(result["layers"][0]["name"], "arcrest_layer")
        self.assertEqual(result["layers"][0]["has_sublayers"], True)
        self.assertEqual(result["layers"][0]["subLayers"][0]["name"], "arcrest_layer >> sublayer")
        self.assertEqual(result["layers"][0]["subLayers"][0]["slug_name"], "sublayer_new")

# update to mock a working WMS service for testing purposes
# class DataManagerWMSRequestCapabilities(TestCase):
#     def test_wms_request_capabilities_response(self):
#         client = APIClient()
#         response = client.get("/layers/wms_capabilities/?url=https%3A%2F%2Fwww.coastalatlas.net%2Fservices%2Fwms%2Fgetmap%2F%3F")
#         self.assertEqual(response.status_code, 200)
#         result = json.loads(response.content)

#         # Validate the structure of the WMS capabilities response
#         self.assertIn("layers", result)
#         self.assertIn("formats", result)
#         self.assertIn("version", result)
#         self.assertIn("styles", result)

#         # Validate styles for each layer
#         for i in range(len(result["layers"])):
#             layer = result["layers"][i]
#             self.assertIn(result["layers"][i], result["styles"])

#         # Validate SRS for each layer
#         self.assertIn("srs", result)
#         for i in range(len(result["layers"])):
#             self.assertIn(result["layers"][i], result["srs"])

#         # Validate queryable layers
#         self.assertIn("queryable", result)
#         for i in range(len(result["queryable"])):
#             self.assertIn(result["queryable"][i], result["layers"])
        
#         # Validate time information for each layer
#         self.assertIn("time", result)
#         for i in range(len(result["layers"])):
#             layer = result["layers"][i]
#             self.assertIn(result["layers"][i], result["time"])
#             self.assertIn("positions", result["time"][layer])
#             self.assertIn("default", result["time"][layer])
#             self.assertIn("field", result["time"][layer])
#         self.assertIn("capabilities", result)
#         self.assertIn("featureInfo", result["capabilities"])
#         self.assertIn("available", result["capabilities"]["featureInfo"])
#         self.assertIn("formats", result["capabilities"]["featureInfo"])

#         # Validate data types of specific attributes in the WMS capabilities response
#         self.assertIsInstance(result, dict)
#         self.assertIsInstance(result["layers"], Collection)
#         self.assertIsInstance(result["layers"][0], str)
#         self.assertIsInstance(result["formats"], Collection)
#         if len(result["formats"]) > 0:
#             for i in range(len(result["formats"])):
#                 self.assertIsInstance(result["formats"][i], str)
#         self.assertIsInstance(result["version"], str)
#         self.assertIsInstance(result["styles"], dict)
#         for i in range(len(result["layers"])):
#             layer = result["layers"][i]
#             self.assertIsInstance(result["styles"][layer], dict)
#         self.assertIsInstance(result["srs"], dict)
#         for i in range(len(result["layers"])):
#             layer = result["layers"][i]
#             self.assertIsInstance(result["srs"][layer], Collection)
#             self.assertIsInstance(result["srs"][layer][0], str)
#         self.assertIsInstance(result["queryable"], Collection)
#         self.assertIsInstance(result["queryable"][0], str)
#         self.assertIsInstance(result["time"], dict)
#         for i in range(len(result["layers"])):
#             layer = result["layers"][i]
#             self.assertIsInstance(result["time"][layer], dict)
#         self.assertIsInstance(result["capabilities"], dict)
#         self.assertIsInstance(result["capabilities"]["featureInfo"], dict)
#         self.assertIsInstance(result["capabilities"]["featureInfo"]["available"], bool)
#         self.assertIsInstance(result["capabilities"]["featureInfo"]["formats"], Collection)

#         # Validate specific values
#         self.assertEqual(result["version"], "1.1.1")
#         self.assertEqual(len(result["layers"]), len(result["styles"]))
#         self.assertEqual(len(result["layers"]), len(result["srs"]))
#         self.assertEqual(len(result["layers"]), len(result["time"]))
#         self.assertEqual(result["capabilities"]["featureInfo"]["available"], True)

@override_settings(DB_CHANNEL="madronaportal")
class DataManagerGetLayerCatalogContent(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        site = Site.objects.get(pk=1)
        theme1 = Theme.objects.create(name="companion", display_name="companion", is_visible=True, description="test")
        theme1.site.add(site)
        # This test layer will have attributes defined to test data type when filled out
        self.layer1 =Layer.objects.create(name="arcrest_layer", layer_type="ArcRest",)
        arcrest = LayerArcREST.objects.create(layer=self.layer1)
        # This test layer will not have attributes defined other than required fields to test default behavior when attributes left empty
        self.layer1.site.add(site)

        ChildOrder.objects.create(parent_theme=theme1, content_object=self.layer1, order=1)

    def test_get_layer_catalog_content(self):
        request = self.factory.get(f"/layers/get_layer_catalog_content/{self.layer1.id}/")
        response = get_layer_catalog_content(request, "layer", self.layer1.id)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)

        # Validate the structure of the response
        self.assertIn("html", result)

        # Validate data types of specific attributes in the response
        self.assertIsInstance(result, dict)
        self.assertIsInstance(result["html"], str)

        # Validate specific value
        self.assertEqual(result["html"], self.layer1.catalog_html)

@override_settings(DB_CHANNEL="madronaportal")
class DataManagerGetCatalogRecords(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_catalog_records(self):
        request = self.factory.get("/layers/get_catalog_records/")

        record_one = Mock()
        record_one.meta.id = "record-1"
        record_one.__getitem__ = Mock(side_effect={
            "title": "Record One",
            "name_s": "Catalog Layer",
        }.__getitem__)

        record_two = Mock()
        record_two.meta.id = "record-2"
        record_two.__getitem__ = Mock(side_effect={
            "title": "Record Two",
            "name_s": "Catalog Layer",
        }.__getitem__)

        search_instance = Mock()
        search_instance.query.return_value = search_instance
        search_instance.source.return_value = search_instance
        search_instance.scan.return_value = [record_one, record_two]

        elasticsearch_module = Mock()
        elasticsearch_module.Elasticsearch = Mock(side_effect=[Mock(name="initial_es"), Mock(name="configured_es")])

        elasticsearch_dsl_module = Mock()
        elasticsearch_dsl_module.Search = Mock(return_value=search_instance)

        with override_settings(
            CATALOG_TECHNOLOGY="GeoPortal2",
            ELASTICSEARCH_INDEX="catalog-index",
            CATALOG_SOURCE="http://catalog.example.com",
            ELASTICSEARCH_SEARCH_FIELDS=["title", "name_s"],
            DATA_CATALOG_NAME_FIELD="name_s",
        ):
            with patch.dict(
                sys.modules,
                {
                    "elasticsearch": elasticsearch_module,
                    "elasticsearch_dsl": elasticsearch_dsl_module,
                },
            ):
                response = get_catalog_records(request)

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertIn('records', data)
        self.assertIn('record_name_lookup', data)
        self.assertIn('ELASTICSEARCH_INDEX', data)
        self.assertIn('CATALOG_TECHNOLOGY', data)

        self.assertIsInstance(data, dict, "data should be a JSON Object")
        self.assertIsInstance(data['records'], dict, "records should be a JSON Object")
        self.assertIsInstance(data['record_name_lookup'], dict, "record_name_lookup should be a JSON Object")
        self.assertIsInstance(data['ELASTICSEARCH_INDEX'], str, "ELASTICSEARCH_INDEX should be a string")
        self.assertIsInstance(data['CATALOG_TECHNOLOGY'], str, "CATALOG_TECHNOLOGY should be a string")

        self.assertEqual(data['ELASTICSEARCH_INDEX'], 'catalog-index')
        self.assertEqual(data['CATALOG_TECHNOLOGY'], 'GeoPortal2')
        self.assertEqual(data['records']['record-1']['id'], 'record-1')
        self.assertEqual(data['records']['record-1']['title'], 'Record One')
        self.assertEqual(data['records']['record-1']['name_s'], 'Catalog Layer')
        self.assertEqual(data['records']['record-2']['id'], 'record-2')
        self.assertEqual(data['record_name_lookup']['Catalog Layer'], ['record-1', 'record-2'])

        elasticsearch_module.Elasticsearch.assert_any_call()
        elasticsearch_module.Elasticsearch.assert_any_call('http://catalog.example.com')
        elasticsearch_dsl_module.Search.assert_called_once()
        search_instance.query.assert_called_once_with("match", sys_approval_status_s="approved")
        search_instance.source.assert_called_once_with(["title", "name_s"])

@override_settings(DB_CHANNEL="madronaportal")
class DataManagerLayerStatusTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        site = Site.objects.get(pk=1)
        theme1 = Theme.objects.create(name="companion", display_name="companion", is_visible=True, description="test")
        theme1.site.add(site)
        # This test layer will have attributes defined to test data type when filled out
        layer1 =Theme.objects.create(name="arcrest_layer", theme_type="radio",)
        # This test layer will not have attributes defined other than required fields to test default behavior when attributes left empty
        layer1.site.add(site)

        # Create a test sublayer
        self.layer2 = Layer.objects.create(name="sublayer", layer_type="ArcRest",)
        self.arcrest2 = LayerArcREST.objects.create(layer=self.layer2)
        self.layer2.site.add(site)

        ChildOrder.objects.create(parent_theme=theme1, content_object=layer1, order=1)
        ChildOrder.objects.create(parent_theme=theme1, content_object=self.layer2, order=1)
        ChildOrder.objects.create(parent_theme=layer1, content_object=self.layer2, order=1)
    
    def test_layer_status(self):
        request = self.factory.get("/layers/migration/layer_status/")
        response = layer_status(request)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)

        self.assertIsInstance(result, dict)
        self.assertIn("themes", result)
        self.assertIn("layers", result)

        # Check themes structure and data types
        for theme_uuid, theme_data in result["themes"].items():
            self.assertIsInstance(theme_uuid, str)
            self.assertIsInstance(theme_data, dict)
            self.assertIn("name", theme_data)
            self.assertIn("uuid", theme_data)
            self.assertIn("date_modified", theme_data)
            self.assertIn("layers", theme_data)
            self.assertIsInstance(theme_data["name"], str)
            self.assertIsInstance(theme_data["uuid"], str)
            self.assertIsInstance(theme_data["date_modified"], str)
            self.assertIsInstance(theme_data["layers"], list)

            # Check each layer within a theme for correct structure and types
            for layer in theme_data["layers"]:
                self.assertIsInstance(layer, dict)
                self.assertIn("uuid", layer)
                self.assertIn("name", layer)
                self.assertIn("date_modified", layer)
                self.assertIn("subLayers", layer)
                self.assertIsInstance(layer["uuid"], str)
                self.assertIsInstance(layer["name"], str)
                self.assertIsInstance(layer["date_modified"], str)
                self.assertIsInstance(layer["subLayers"], list)

                # If needed, repeat a similar structure to check sublayers details

        # Check layers structure and data types
        for layer_uuid, layer_data in result["layers"].items():
            self.assertIsInstance(layer_uuid, str)
            self.assertIsInstance(layer_data, dict)
            self.assertIn("name", layer_data)
            self.assertIn("date_modified", layer_data)
            self.assertIsInstance(layer_data["name"], str)
            self.assertIsInstance(layer_data["date_modified"], str)

@override_settings(DB_CHANNEL="madronaportal")
class DataManagerLayerDetailsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        site = Site.objects.get(pk=1)
        theme1 = Theme.objects.create(name="companion", display_name="companion", is_visible=True, description="test")
        theme1.site.add(site)
        theme2 = Theme.objects.create(name="companion2", display_name="companion2", is_visible=True)
        theme2.site.add(site)
        # This test layer will have attributes defined to test data type when filled out
        self.layer1 =Theme.objects.create(name="arcrest_layer", theme_type="radio", )
        # This test layer will not have attributes defined other than required fields to test default behavior when attributes left empty
        self.layer1.site.add(site)
        # Create a test sublayer
        self.layer2 = Layer.objects.create(name="sublayer", layer_type="ArcRest")
        self.arcrest2 = LayerArcREST.objects.create(layer=self.layer2)
        self.layer2.site.add(site)
        ChildOrder.objects.create(parent_theme=theme1, content_object=self.layer1, order=1)
        ChildOrder.objects.create(parent_theme=theme1, content_object=self.layer2, order=1)
        ChildOrder.objects.create(parent_theme=self.layer1, content_object=self.layer2, order=1)
    
    def test_layer_details(self):
        layer2dict = LayerArcRESTSerializer(self.arcrest2).data
        layer2uuid = layer2dict["uuid"]
        layer1dict = SubThemeSerializer(self.layer1).data
        layer1uuid = layer1dict["uuid"]

        request = self.factory.post("/layers/migration/layer_details/", {"layers": [layer1uuid, layer2uuid]})
        response = migration_layer_details(request)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        
        self.assertIn("status", result)
        self.assertIn("message", result)
        self.assertIn("themes", result)
        self.assertIn("layers", result)

        self.assertIsInstance(result, dict)
        self.assertIsInstance(result["status"], str)
        self.assertIsInstance(result["message"], str)
        self.assertIsInstance(result["themes"], dict)
        self.assertIsInstance(result["layers"], dict)

        self.assertEqual(result["status"], "Success")
        self.assertEqual(result["message"], "layer(s) details retrieved")
        self.assertEqual(len(result["layers"]), 2)

# backward compatability tests, should be fixed
# should be mocked requests not the real deal 

# class LiveAPITests(TestCase):
#     def setUp(self):
#         data_manager_get_themes_fixture_path = join("/usr/local/apps/madrona-portal/apps/mp-layers/layers/tests/data/", "data_manager_get_themes.json")
#         layers_fixture_path = join("/usr/local/apps/madrona-portal/apps/mp-layers/layers/tests/data/", "layers_get_themes.json")
#         data_manager_get_layers_for_themes_fixture_path = join("/usr/local/apps/madrona-portal/apps/mp-layers/layers/tests/data/", "data_manager_get_layers_for_themes.json")
#         layers_get_layers_for_themes_fixture_path = join("/usr/local/apps/madrona-portal/apps/mp-layers/layers/tests/data/", "layers_get_layers_for_themes.json")

#         with open(data_manager_get_themes_fixture_path, 'r') as f:
#             self.data_manager_themes = json.load(f)
#         with open(layers_fixture_path, 'r') as f:
#             self.layers_themes = json.load(f)
#         with open(data_manager_get_layers_for_themes_fixture_path, 'r') as f:
#             self.data_manager_layers_for_themes = json.load(f)
#         with open(layers_get_layers_for_themes_fixture_path, 'r') as f:
#             self.layers_get_layers_for_themes = json.load(f)

#     def test_v1_responses(self):
#         old_themes = self.data_manager_themes
#         new_themes = self.layers_themes
#         self.assertEqual(old_themes, new_themes)
#         for idx, theme in enumerate(old_themes['themes']):
#             self.assertEqual(theme, new_themes['themes'][idx])
#             print("Testing theme {}: {}".format(theme['id'], theme['name']))

#             # Use the below IF statements to save some time testing specific themes.
#             # if theme['id'] in DYNAMIC_PARENT_THEMES:
#             # if theme['id'] in SLIDER_PARENT_THEMES:
#             if not theme['id'] in FULLY_COMPLIANT_THEMES:
#                 self.loop_through_theme_children(theme['id'])

#     def loop_through_theme_children(self, theme_id):
#         old_theme_data = self.data_manager_layers_for_themes.get(str(theme_id), {})
#         new_theme_data = self.layers_get_layers_for_themes.get(str(theme_id), {})

#         self.assertEqual(old_theme_data.keys(), new_theme_data.keys())
#         self.assertEqual(len(old_theme_data['layers']), len(new_theme_data['layers']))
#         self.compare_lists(old_theme_data['layers'], new_theme_data['layers'])
#         print(" -- Testing {} layers...".format(len(new_theme_data['layers'])))
#         self.loop_through_theme_layers(new_theme_data['layers'])

#     def compare_lists(self, old_list, new_list):
#         for child in new_list:
#             if not child in old_list:
#                 match = next(filter(lambda record: record['id'] == child['id'], old_list))
#                 for key in child.keys():
#                     if not key in ['subLayers', 'type', 'date_modified']:

#                         if not child[key] == match[key]:
#                             print(child)
#                             print(match)
#                             print("Key '{}': new:'{}' ; old:'{}'".format(key, child[key], match[key]))


#                     elif key == 'type' and (
#                             child['type'] == 'slider' or child['type'] in ['checkbox',] and 
#                             child['has_sublayers'] == True and match['has_sublayers'] == True
#                         ):
#                             pass
#                     elif key == 'subLayers':   # 'subLayers'
#                         if not (type(match[key]) == str or type(child[key])==str):
#                             self.compare_lists(match[key], child[key])
#                         else:
#                             self.assertEqual(child[key], match[key])

#     def loop_through_theme_layers(self, layer_list):
#         for index, layer in enumerate(layer_list):
#             print(f"testing layer {layer['id']}")
#             # dm_layer_response = requests.get('/old_manager/get_layer_details/{}'.format(layer['id']))
#             # ls_layer_response = requests.get('/data_manager/get_layer_details/{}'.format(layer['id']))
#             # old_layer_data = json.loads(dm_layer_response.content)
#             # new_layer_data = json.loads(ls_layer_response.content)
#             # self.assertEqual(old_layer_data.keys(), new_layer_data.keys())
#             # self.compare_layers(old_layer_data, new_layer_data, index)

#     def loop_through_slider_associations(self, associated_multilayers):
#         for index, key in enumerate(associated_multilayers.keys()):
#             if type(associated_multilayers[key]) == dict:
#                 self.loop_through_slider_associations(associated_multilayers[key])
#             elif type(associated_multilayers[key]) == int:
#                 print(f"Associated Multilayer: {associated_multilayers[key]}")
#                 dm_layer_response = self.live_get('/old_manager/get_layer_details/{}'.format(associated_multilayers[key]))
#                 ls_layer_response = self.live_get('/data_manager/get_layer_details/{}'.format(associated_multilayers[key]))
#                 old_layer_data = json.loads(dm_layer_response.content)
#                 new_layer_data = json.loads(ls_layer_response.content)
#                 # if not len(old_layer_data.keys()) == len(new_layer_data.keys()):
#                 #     import ipdb; ipdb.set_trace()
#                 self.assertEqual(old_layer_data.keys(), new_layer_data.keys())
#                 self.compare_layers(old_layer_data, new_layer_data, index)
 
#     def compare_layers(self, old_layer, new_layer, layer_count):
#         if 'type' in new_layer.keys() and new_layer['type'] == 'slider':
#             new_layer['type'] = old_layer['type']
#             self.loop_through_slider_associations(new_layer['associated_multilayers'])
#         for key in old_layer.keys():
#             if key not in ['date_modified','subLayers','attributes', 'lookups', 'companion_layers']: # objects and dates?
#                 if not old_layer[key] == new_layer[key]:
#                     if (
#                         # old empty strings are new nulls
#                         key in [
#                             'arcgis_layers', 'wms_slug', 'wms_format', 'wms_srs', 'wms_styles', 'wms_timing', 
#                             'wms_time_item', 'utfurl', 'legend', 'legend_title', 
#                             'legend_subtitle', 'learn_more', 'outline_color', 'data_download', 'wms_version'
#                         ] and old_layer[key] == '' and new_layer[key] == None
#                     ) or (
#                         # old nulls are new empty strings
#                         key in [
#                             'source', 'wms_version', 'wms_additional'
#                         ] and old_layer[key] == None and new_layer[key] == ""
#                     ) or (
#                         #fields are set that have no business being set on parent layers/themes
#                         key in [
#                             'outline_opacity', 'color', 'fill_opacity', 'graphic', 'arcgis_layers', 'type', 'tiles', 'kml', 'opacity'
#                         ] and new_layer['type'] in [
#                             'checkbox', 'radio', 'placeholder'
#                         ]
#                     ) or (
#                         # Custom Vector styling for non-Vector sources
#                         new_layer['type'] not in [
#                             'ArcFeatureService', 'vector',
#                         ] and key in [
#                             'outline_opacity', 'color', 'fill_opacity', 'graphic', 'graphic_scale', 'point_radius',
#                         ]
#                     ):
#                         old_layer[key] = new_layer[key]
#                     elif key == 'url' and any( dynamic_theme_id in new_layer['catalog_html'] for dynamic_theme_id in [";themes%5Bids%5D%5B%5D=25&", ";themes%5Bids%5D%5B%5D=24&"]):
#                         if ";themes%5Bids%5D%5B%5D=25&" in new_layer['catalog_html']:
#                             parent_theme = "vtr"
#                         elif ";themes%5Bids%5D%5B%5D=24&" in new_layer['catalog_html']:
#                             parent_theme = "mdat"
#                         print("*****************")
#                         print("Theme {} belongs to '{}' theme".format(new_layer['id'], parent_theme))
#                         print("TODO: Correct Dynamic Layer support! Passing for now...")
#                         print("*****************")
#                         old_layer[key] = new_layer[key]
#                     elif key == 'catalog_html':
#                         old_layer[key] = old_layer[key].replace('<a class="btn btn-mini disabled" href="None">', '<a class="btn btn-mini disabled" href="">')
#                         new_layer[key] = new_layer[key].replace('<a class="btn btn-mini disabled" href="None">', '<a class="btn btn-mini disabled" href="">')
#                     elif key == 'has_companion' and old_layer[key] == True:
#                         # some old layers have 'has_companion' checked, but no companions assigned (5206)
#                         old_layer['has_companion'] = len(old_layer['companion_layers']) > 0
#                     if not old_layer[key] == new_layer[key]:
#                         print("=================")
#                         print("Layer #{} for theme".format(layer_count))
#                         print("ID: {}".format(old_layer['id']))
#                         print("Name: {}".format(old_layer['name']))
#                         print("KEY: {}".format(key))
#                         print("OLD: {}".format(old_layer[key]))
#                         print("NEW: {}".format(new_layer[key]))
#                         # import ipdb; ipdb.set_trace()
#                         print("=================")
#                 if not key in ['data_notes','disabled_message']:
#                     self.assertEqual(old_layer[key], new_layer[key])
#             elif key == 'companion_layers':
#                 if old_layer['has_companion'] == False:
#                     old_layer['companion_layers'] = []
#                 self.assertEqual(len(old_layer[key]), len(new_layer[key]))
#                 for index, old_companion in enumerate(old_layer[key]):
#                     new_companion = new_layer[key][index]
#                     old_keys = old_companion.keys()
#                     new_keys = new_companion.keys()
#                     key_diff = 0
#                     for old_key in old_keys:
#                         if not old_key in new_keys:
#                             key_diff += 1
#                             print("OLD KEY: '{}' not in new keys".format(old_key))
#                     for new_key in new_keys:
#                         if not new_key in old_keys:
#                             key_diff += 1
#                             print("NEW KEY: '{}' not in old keys".format(new_key))
#                     if key_diff > 0:
#                         print("Total num of different keys: {}".format(key_diff))
#                     self.compare_layers(old_companion, new_companion, layer_count)
            # elif key in ['subLayers', 'attributes', 'lookups', 'companion_layers']:
            #     if not (type(old_layer[key]) == str or type(new_layer[key])==str):
            #         self.compare_lists(old_layer[key], new_layer[key])
            #     else:
            #         self.assertEqual(new_layer[key], old_layer[key])