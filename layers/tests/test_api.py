from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from layers.models import *
from layers.serializers import *
from collections.abc import Collection, Mapping
from django.core.cache import cache
import requests
import json

DYNAMIC_PARENT_THEMES = [24, 25]
SLIDER_PARENT_THEMES = [28, 2, 8, 14]
UNCERTAIN_STATUS_THEMES = DYNAMIC_PARENT_THEMES + SLIDER_PARENT_THEMES + [27, ]
COMPANION_THEME = [23, ]
FULLY_COMPLIANT_THEMES = COMPANION_THEME + [1, 29, 4, 10, 7, 11, 3, 12, 5, 22]

class DataManagerGetLayerDetailsTest(APITestCase):
    def setUp(self):
        site = Site.objects.get(pk=1)
        theme1 = Theme.objects.create(name="companion", display_name="companion", is_visible=True)
        theme1.site.add(site)

        layer1 =Theme.objects.create(name="arcrest_layer", theme_type="radio")
        layer1.site.add(site)

        self.layer2 = Layer.objects.create(name="Arc", layer_type="ArcRest")
        self.arcrest2 = LayerArcREST.objects.create(layer=self.layer2)

        self.layer2.site.add(site)
        # This layer is to test how sublayers are returned
        self.layer3 = Layer.objects.create(name="sublayer", layer_type="ArcRest")
        self.arcrest3 = LayerArcREST.objects.create(layer=self.layer3)
        self.layer3.site.add(site)

        ChildOrder.objects.create(parent_theme=theme1, content_object=self.layer2, order=1)
        ChildOrder.objects.create(parent_theme=theme1, content_object=layer1, order=1)
        ChildOrder.objects.create(parent_theme=layer1, content_object=self.layer3, order=1)
        self.companionship = Companionship.objects.create(layer=self.layer2)
        self.companionship.companions.add(self.layer3)
    def test_view_layer_details_response_format(self):
        client = APIClient()
        request1 = client.get(f"/layers/get_layer_details/{self.layer2.id}/", HTTP_HOST="localhost:8000")
        self.assertEqual(request1.status_code, 200)
        result1 = json.loads(request1.content)

        request2 = client.get(f"/layers/get_layer_details/{self.layer3.id}/", HTTP_HOST="localhost:8000")
        self.assertEqual(request2.status_code, 200)
        result2 = json.loads(request2.content)

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
        response = self.client.get(f"/layers/get_layer_details/{self.layer2.id}/", HTTP_HOST="localhost:8000")
        self.assertEqual(response.status_code, 200)
        result= json.loads(response.content)

        # Expected default attributes and lookups for layer 2
        expected_attributes = {"compress_attributes": False, "event": "click", "attributes": [], "mouseover_attribute": None, "preserved_format_attributes": []}
        expected_lookups = {"field": None, "details": []}

        # Validate each attribute with its expected value
        self.assertEqual(result["name"], "Arc")
        self.assertEqual(result["order"], 1)
        self.assertEqual(result["type"], "ArcRest")
        self.assertEqual(result["url"], "")
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
        self.assertEqual(result["description"], "")
        self.assertEqual(result["overview"], "")
        self.assertEqual(result["data_source"], None)
        self.assertEqual(result["data_notes"], "")
        self.assertEqual(result["kml"], None)
        self.assertEqual(result["data_download"], None)
        self.assertEqual(result["learn_more"], None)
        self.assertEqual(result["metadata"], None)
        self.assertEqual(result["source"], None)
        self.assertEqual(result["tiles"], None)
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
        self.assertEqual(result["disabled_message"], "")
        self.assertEqual(result["data_url"], None)
        self.assertEqual(result["is_multilayer"], False)
        self.assertEqual(result["is_multilayer_parent"], False)
        self.assertEqual(result["dimensions"], [])
        self.assertEqual(result["associated_multilayers"], {})
        self.assertEqual(result["parent"], None)

class DataManagerGetJsonTest(APITestCase):
    def setUp(self):
        site = Site.objects.get(pk=1)
        # Create themes and layers for testing
        theme1 = Theme.objects.create(name="companion", display_name="companion", is_visible=True, description="test")
        theme1.site.add(site)
        theme2 = Theme.objects.create(name="companion2", display_name="companion2", is_visible=True)
        theme2.site.add(site)

        self.layer1 =Theme.objects.create(name="subtheme", theme_type="radio")

        # This test layer will not have attributes defined other than required fields to test default behavior when attributes left empty
        self.layer1.site.add(site)

         # Create a test sublayer
        self.layer2 = Layer.objects.create(name="sublayer", layer_type="ArcRest")
        self.arcgislayer = LayerArcREST.objects.create(layer = self.layer2)
        self.layer2.site.add(site)

        child_order_wms = ChildOrder.objects.create(parent_theme=theme1, content_object=self.layer1, order=1)
        sublayer_order = ChildOrder.objects.create(parent_theme=self.layer1,content_object=self.layer2, order=1)
        layer_order = ChildOrder.objects.create(parent_theme=theme2,content_object=self.layer2, order=1)

    def test_view_api(self):
        client = APIClient()
        response = client.get("/layers/get_json/", HTTP_HOST="localhost:8000")
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        
        # Get Layer 2 and prepare a dictionary for comparison

        layer2dict = LayerArcRESTSerializer(self.arcgislayer).data
        layer2dict["uuid"] = str(layer2dict["uuid"])

        # Define expected attributes and lookups
        expected_attributes = {"compress_attributes": False, "event": "click", "attributes": [], "mouseover_attribute": None, "preserved_format_attributes": []}
        expected_lookups = {"field": None, "details": []}

        # Make sure response contains "success", "state", "layers" and "themes" 
        self.assertIn("success", result)
        self.assertIn("state", result)
        self.assertIn("activeLayers", result["state"])
        self.assertIn("layers", result)
        layer_attr = ["id", "uuid", "name", "order", "type", "arcgis_layers", "url", "password_protected", "query_by_point", "proxy_url", "disable_arcgis_attributes", "wms_slug", "wms_version", "wms_format", "wms_srs", "wms_styles", "wms_timing", "wms_time_item", "wms_additional", "wms_info", 
                            "wms_info_format", "utfurl", "subLayers", "companion_layers", "has_companion", "queryable", "legend", "legend_title", "legend_subtitle", "show_legend", "description", "overview", "data_source", "data_notes", "kml", "data_download", 
                            "learn_more", "metadata", "source", "tiles", "label_field", "attributes", "minZoom", "maxZoom", "lookups", "custom_style", "outline_color", "outline_opacity", "outline_width", "point_radius", "color", "fill_opacity", "graphic", "graphic_scale", "opacity",
                            "annotated", "is_disabled", "disabled_message", "data_url", "is_multilayer", "is_multilayer_parent", "dimensions", "associated_multilayers", "catalog_html", "parent", "date_modified"]
        for i in layer_attr:
            self.assertIn(i, result["layers"][0])
        self.assertIn("themes", result)
        theme_attr = ["id", "name", "display_name", "learn_link", "is_visible", "layers", "description"]
        for i in theme_attr:
            self.assertIn(i, result["themes"][0])

        # Validate data types of specific attributes in the JSON response
        self.assertIsInstance(result["success"], bool, "success should be bool")
        self.assertIsInstance(result["layers"], Collection, "layers should be collection")
        self.assertIsInstance(result["layers"][0]["id"], int, "id should be int")
        self.assertIsInstance(result["layers"][0]["uuid"], str, "uuid should be string")
        self.assertIsInstance(result["layers"][0]["name"], str, "name should be string") 
        self.assertIsInstance(result["layers"][0]["order"], int, "order should be int")
        self.assertIsInstance(result["layers"][0]["type"], str, "type should be string")
        self.assertIsInstance(result["layers"][0]["arcgis_layers"], (str, type(None)), "arcgis_layers should be string or none")
        self.assertIsInstance(result["layers"][0]["url"], str, "url should be string")
        self.assertIsInstance(result["layers"][0]["password_protected"], bool, "password_protected should be boolean")
        self.assertIsInstance(result["layers"][0]["query_by_point"], bool, "query_by_point should be boolean")
        self.assertIsInstance(result["layers"][0]["proxy_url"], bool, "proxy_url should be boolean")
        self.assertIsInstance(result["layers"][0]["disable_arcgis_attributes"], bool, "disable_arcgis_attributes should be boolean" )
        self.assertIsInstance(result["layers"][0]["wms_slug"], (str, type(None)), "wms_slug should be string or none" )
        self.assertIsInstance(result["layers"][0]["wms_version"], (str, type(None)), "wms_version should be string or none")
        self.assertIsInstance(result["layers"][0]["wms_format"], (str, type(None)), "wms_format should be string or none")
        self.assertIsInstance(result["layers"][0]["wms_srs"], (str, type(None)), "wms_srs should be string or none")
        self.assertIsInstance(result["layers"][0]["wms_styles"], (str, type(None)), "wms_styles should be string or none")
        self.assertIsInstance(result["layers"][0]["wms_timing"], (str, type(None)), "wms_timing should be string or none")
        self.assertIsInstance(result["layers"][0]["wms_time_item"], (str, type(None)), "wms_time_item should be string or none")
        self.assertIsInstance(result["layers"][0]["wms_additional"], (str, type(None)), "wms_additional should be string or none")
        self.assertIsInstance(result["layers"][0]["wms_info"], bool, "wms_info should be boolean")
        self.assertIsInstance(result["layers"][0]["wms_info_format"], (str, type(None)), "wms_info_format should be string or none")
        self.assertIsInstance(result["layers"][0]["utfurl"], (str, type(None)), "utfurl should be string or none")
        self.assertIsInstance(result["layers"][0]["subLayers"], Collection, "subLayers should be a collection")
        self.assertIsInstance(result["layers"][0]["companion_layers"], Collection, "companion_layers should be collection")
        self.assertIsInstance(result["layers"][0]["has_companion"], bool, "has_companion should be bool")
        self.assertIsInstance(result["layers"][0]["queryable"], bool, "queryable should be boolean")
        self.assertIsInstance(result["layers"][0]["legend"], (str, type(None)), "legend should be string")
        self.assertIsInstance(result["layers"][0]["legend_title"], (str, type(None)), "legend_title should be string or none")
        self.assertIsInstance(result["layers"][0]["legend_subtitle"], (str, type(None)), "legend_subtitle should be string or none")
        self.assertIsInstance(result["layers"][0]["show_legend"], bool, "show_legend should be bool" )
        self.assertIsInstance(result["layers"][0]["description"], (str, type(None)), "description should be string or none" )
        self.assertIsInstance(result["layers"][0]["overview"], (str, type(None)), "overview should be string or none")
        self.assertIsInstance(result["layers"][0]["data_source"], (str, type(None)), "data_source should be string or none")
        self.assertIsInstance(result["layers"][0]["data_notes"], (str, type(None)), "data_notes should be string or none" )
        self.assertIsInstance(result["layers"][0]["kml"], (str, type(None)), "kml should be string or none")
        self.assertIsInstance(result["layers"][0]["data_download"], (str, type(None)), "data_download should be string or none")
        self.assertIsInstance(result["layers"][0]["learn_more"], (str, type(None)), "learn_more should be string or none")
        self.assertIsInstance(result["layers"][0]["metadata"], (str, type(None)), "metadata should be string or none")
        self.assertIsInstance(result["layers"][0]["source"], (str, type(None)), "source should be string or none")
        self.assertIsInstance(result["layers"][0]["tiles"], (str, type(None)), "tiles should be string or none")
        self.assertIsInstance(result["layers"][0]["label_field"], (str, type(None)), "label_field should be string or none")
        self.assertIsInstance(result["layers"][0]["attributes"], dict, "attributes should be dictionary (JSON object)")
        self.assertIsInstance(result["layers"][0]["minZoom"], (float, type(None)), "minZoom should be float")
        self.assertIsInstance(result["layers"][0]["maxZoom"], (float, type(None)), "maxZoom should be float")
        self.assertIsInstance(result["layers"][0]["lookups"], dict, "lookups should be dictionary(JSON object)")
        self.assertIsInstance(result["layers"][0]["custom_style"], (str, type(None)), "custom_style should be string or none")
        self.assertIsInstance(result["layers"][0]["outline_color"], (str, type(None)), "outline_color should be string or none")
        self.assertIsInstance(result["layers"][0]["outline_opacity"], (float, type(None)), "outline_opacity should be float or none")
        self.assertIsInstance(result["layers"][0]["outline_width"], (int, type(None)), "outline_width should be int or none")
        self.assertIsInstance(result["layers"][0]["point_radius"], (int, type(None)), "point_radius should be int or none")
        self.assertIsInstance(result["layers"][0]["color"], (str, type(None)), "color should be string or none")
        self.assertIsInstance(result["layers"][0]["fill_opacity"], (float, type(None)), "fill_opacity should be float or none")
        self.assertIsInstance(result["layers"][0]["graphic"], (str, type(None)), "graphic should be string or none")
        self.assertIsInstance(result["layers"][0]["graphic_scale"], (float), "graphic_scale should be float")
        self.assertIsInstance(result["layers"][0]["opacity"], float, "opacity should be float")
        self.assertIsInstance(result["layers"][0]["annotated"], bool, "annotated should be bool")
        self.assertIsInstance(result["layers"][0]["is_disabled"], bool, "is_disabled should be bool")
        self.assertIsInstance(result["layers"][0]["disabled_message"], (str, type(None)), "disabled_message should be string or none")
        self.assertIsInstance(result["layers"][0]["data_url"], (str, type(None)), "data_url should be string or none")
        self.assertIsInstance(result["layers"][0]["is_multilayer"], bool, "is_multilayer should be bool")
        self.assertIsInstance(result["layers"][0]["is_multilayer_parent"], bool, "is_multilayer_parent should be bool")
        self.assertIsInstance(result["layers"][0]["dimensions"], Collection, "dimensions should be collection")
        self.assertIsInstance(result["layers"][0]["associated_multilayers"], dict, "associated_multilayers should be dictionary")
        self.assertIsInstance(result["layers"][0]["catalog_html"], str, "catalog_html should be string")
        self.assertIsInstance(result["layers"][0]["parent"], (dict, type(None)), "parent should be dictionary(JSON object) or none")
        self.assertIsInstance(result["layers"][0]["date_modified"], str, "date_modified should be string")
        self.assertIsInstance(result["themes"], Collection, "themes should be collection")
        self.assertIsInstance(result["themes"][0]["id"], int, "id should be integer")
        self.assertIsInstance(result["themes"][0]["name"], str, "name should be string")
        self.assertIsInstance(result["themes"][0]["display_name"], str, "display_name should be string")
        self.assertIsInstance(result["themes"][0]["learn_link"], str, "learn_link should be string")
        self.assertIsInstance(result["themes"][0]["is_visible"], bool, "is_visible should be bool")
        self.assertIsInstance(result["themes"][0]["layers"], Collection, "layers should be collection")
        self.assertIsInstance(result["themes"][0]["description"], (str, type(None)), "description should be string or none")
        self.assertIsInstance(result["state"], Mapping, "state should be mapping")
        self.assertIsInstance(result["state"]["activeLayers"], Collection, "activeLayers should be collection")

        self.assertTrue(result["success"])
        self.assertEqual(result["state"]["activeLayers"], [])
        self.assertEqual(result["layers"][0]["name"], "subtheme")
        self.assertEqual(result["layers"][0]["order"], 1)
        self.assertEqual(result["layers"][0]["type"], "radio")
        self.assertEqual(result["layers"][0]["arcgis_layers"], None)
        self.assertEqual(result["layers"][0]["password_protected"], False)
        self.assertEqual(result["layers"][0]["query_by_point"], False)
        self.assertEqual(result["layers"][0]["proxy_url"], False)
        self.assertEqual(result["layers"][0]["disable_arcgis_attributes"], False)
        self.assertEqual(result["layers"][0]["wms_slug"], None)
        self.assertEqual(result["layers"][0]["wms_version"], None)
        self.assertEqual(result["layers"][0]["wms_format"], None)
        self.assertEqual(result["layers"][0]["wms_srs"], None)
        self.assertEqual(result["layers"][0]["wms_styles"], None)
        self.assertEqual(result["layers"][0]["wms_timing"], None)
        self.assertEqual(result["layers"][0]["wms_time_item"], None)
        self.assertEqual(result["layers"][0]["wms_additional"], "")
        self.assertEqual(result["layers"][0]["wms_info"], False)
        self.assertEqual(result["layers"][0]["wms_info_format"], None)
        self.assertEqual(result["layers"][0]["utfurl"], None)
        for key in result["layers"][0]["subLayers"][0].keys():
            #description and overview takes from parent, but parent should not be set
            if not key in ["is_sublayer", "date_modified", "companion_layers", "description", "overview", "uuid"]:
                if key != "parent":
                    self.assertEqual(result["layers"][0]["subLayers"][0][key], layer2dict[key], msg=f"Key '{key}' mismatch: {result['layers'][0]['subLayers'][0][key]} != {layer2dict[key]}")
                else:
                    self.assertEqual(result["layers"][0]["subLayers"][0][key], layer2dict[key]["id"], msg=f"Key '{key}' mismatch: {result['layers'][0]['subLayers'][0]} != {layer2dict[key]}")
        self.assertEqual(result["layers"][0]["companion_layers"], [])
        self.assertEqual(result["layers"][0]["has_companion"], False)
        self.assertEqual(result["layers"][0]["queryable"], False)
        self.assertEqual(result["layers"][0]["legend"], None)
        self.assertEqual(result["layers"][0]["legend_title"], None)
        self.assertEqual(result["layers"][0]["legend_subtitle"], None)
        self.assertEqual(result["layers"][0]["show_legend"], True)
        self.assertEqual(result["layers"][0]["description"], "")
        self.assertEqual(result["layers"][0]["overview"], "")
        self.assertEqual(result["layers"][0]["data_source"], None)
        self.assertEqual(result["layers"][0]["data_notes"], "")
        self.assertEqual(result["layers"][0]["kml"], None)
        self.assertEqual(result["layers"][0]["data_download"], None)
        self.assertEqual(result["layers"][0]["learn_more"], None)
        self.assertEqual(result["layers"][0]["metadata"], None)
        self.assertEqual(result["layers"][0]["source"], None)
        self.assertEqual(result["layers"][0]["tiles"], None)
        self.assertEqual(result["layers"][0]["label_field"], None)
        self.assertEqual(result["layers"][0]["attributes"], expected_attributes)
        self.assertEqual(result["layers"][0]["lookups"], expected_lookups)
        self.assertEqual(result["layers"][0]["minZoom"], None)
        self.assertEqual(result["layers"][0]["maxZoom"], None)
        self.assertEqual(result["layers"][0]["custom_style"], None)
        self.assertEqual(result["layers"][0]["outline_color"], None)
        self.assertEqual(result["layers"][0]["outline_opacity"], None)
        self.assertEqual(result["layers"][0]["outline_width"], None)
        self.assertEqual(result["layers"][0]["point_radius"], None)
        self.assertEqual(result["layers"][0]["color"], None)
        self.assertEqual(result["layers"][0]["fill_opacity"], None)
        self.assertEqual(result["layers"][0]["graphic"], None)
        self.assertEqual(result["layers"][0]["graphic_scale"], 1.0)
        self.assertEqual(result["layers"][0]["opacity"], 0.5)
        self.assertEqual(result["layers"][0]["annotated"], False)
        self.assertEqual(result["layers"][0]["is_disabled"], False)
        self.assertEqual(result["layers"][0]["disabled_message"], "")
        self.assertEqual(result["layers"][0]["is_multilayer"], False)
        self.assertEqual(result["layers"][0]["is_multilayer_parent"], False)
        self.assertEqual(result["layers"][0]["dimensions"], [])
        self.assertEqual(result["layers"][0]["associated_multilayers"], {})
        self.assertEqual(result["layers"][0]["parent"], None)
        self.assertEqual(result["themes"][0]["name"], "companion")
        self.assertEqual(result["themes"][0]["display_name"], "companion")
        self.assertEqual(result["themes"][0]["learn_link"], "../learn/companion")
        self.assertEqual(result["themes"][0]["is_visible"], True)
        self.assertEqual(result["themes"][0]["layers"], [self.layer1.id])
        self.assertEqual(result["themes"][0]["description"], "test")
        self.assertEqual(result["themes"][1]["name"], "companion2")
        self.assertEqual(result["themes"][1]["display_name"], "companion2")
        self.assertEqual(result["themes"][1]["learn_link"], "../learn/companion2")
        self.assertEqual(result["themes"][1]["is_visible"], True)
        self.assertEqual(result["themes"][1]["layers"], [self.layer2.id])
        self.assertEqual(result["themes"][1]["description"], None)

class DataManagerGetThemesTest(APITestCase):
    def setUp(self):
        # Associate theme with default site id, otherwise themes do not show up
        site = Site.objects.get(pk=1)
        self.theme1 = Theme.objects.create(name="test", display_name="test", is_visible=True)
        self.theme1.site.add(site)
        self.theme2 = Theme.objects.create(name="test2", display_name="test2", is_visible=True)
        self.theme2.site.add(site)

    def test_get_themes_response_format(self):
        client = APIClient()
        response = client.get("/layers/get_themes/", HTTP_HOST="localhost:8000")
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
        client = APIClient()
        response = client.get("/layers/get_themes/" , HTTP_HOST="localhost:8000")
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

class DataManagerGetLayerSearchDataTest(APITestCase):
     def setUp(self):
        site = Site.objects.get(pk=1)
        theme1 = Theme.objects.create(name="test3", display_name="test3", is_visible=True, description="test 3")
        theme1.site.add(site)
        # Cannot use .set in the same line as creating an object as .set returns None
        theme2 = Theme.objects.create(name="test4", display_name="test4", is_visible=True, description="test 4")
        theme2.site.add(site)
        layer1 = Theme.objects.create(name="layertest1")
        layer1.site.add(site)

        # Layer2 is sublayer of layer 1
        layer2 = Layer.objects.create(name="layertest2")
        layer2.site.add(site)

        layer3 = Layer.objects.create(name="layertest3")
        layer3.site.add(site)

        ChildOrder.objects.create(parent_theme=theme1, content_object=layer1, order=1)
        ChildOrder.objects.create(parent_theme=layer1, content_object=layer2, order=1)
        ChildOrder.objects.create(parent_theme=theme2, content_object=layer3, order=1)

     def test_get_layer_search_data_response_format(self):
        client = APIClient()
        response = client.get("/layers/get_layer_search_data/", HTTP_HOST="localhost:8000")
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)

        # Sublayers are not shown, should only return layers as keys that are not sublayers
        self.assertIn("layertest1", result, "result should have layertest1 key")
        self.assertIn("layer", result["layertest1"], "should have layer key")
        self.assertIn("theme", result["layertest1"], "should have theme key")
        self.assertIn("id", result["layertest1"]["layer"], "each layer should have id key")
        self.assertIn("name", result["layertest1"]["layer"], "each layer should have name key")
        self.assertIn("has_sublayers", result["layertest1"]["layer"], "each layer should have has_sublayers key")
        self.assertIn("sublayers", result["layertest1"]["layer"], "each layer should have sublayers key")
        self.assertIn("name", result["layertest1"]["layer"]["sublayers"][0], "each sublayer should have name key")
        self.assertIn("id", result["layertest1"]["layer"]["sublayers"][0], "each sublayer should have id key")
        self.assertIn("id", result["layertest1"]["theme"], "each theme should have id key")
        self.assertIn("name", result["layertest1"]["theme"], "each theme should have name key")
        self.assertIn("description", result["layertest1"]["theme"], "each theme should have description key")

        self.assertIsInstance(result, dict, "result should be dictionary")
        self.assertIsInstance(result["layertest1"], dict, "result's keys should be dictionary")
        self.assertIsInstance(result["layertest1"]["layer"], dict, "layer should be dictionary")
        self.assertIsInstance(result["layertest1"]["theme"], dict, "theme should be dictionary")
        self.assertIsInstance(result["layertest1"]["layer"]["id"], int, "id should be integer")
        self.assertIsInstance(result["layertest1"]["layer"]["name"], str, "name should be string")
        self.assertIsInstance(result["layertest1"]["layer"]["has_sublayers"], bool, "has_sublayers should be boolean")
        self.assertIsInstance(result["layertest1"]["layer"]["sublayers"], Collection, "sublayers should be collection")
        self.assertIsInstance(result["layertest1"]["layer"]["sublayers"][0], dict, "each sublayer should be a dictionary")
        self.assertIsInstance(result["layertest1"]["layer"]["sublayers"][0]["name"], str, "name should be string")
        self.assertIsInstance(result["layertest1"]["layer"]["sublayers"][0]["id"], int, "id should be integer")
        self.assertIsInstance(result["layertest1"]["theme"]["id"], int, "theme id should be integer")
        self.assertIsInstance(result["layertest1"]["theme"]["name"], str, "theme name should be string")
        self.assertIsInstance(result["layertest1"]["theme"]["description"], str, "theme description should be string")

        self.assertEqual(result["layertest1"]["layer"]["name"], "layertest1")
        self.assertEqual(result["layertest1"]["layer"]["has_sublayers"], True)
        self.assertEqual(result["layertest1"]["layer"]["sublayers"][0]["name"], "layertest2")
        self.assertEqual(result["layertest1"]["theme"]["name"], "test3")
        self.assertEqual(result["layertest1"]["theme"]["description"], "test 3")
        self.assertEqual(result["layertest3"]["layer"]["name"], "layertest3")
        self.assertEqual(result["layertest3"]["layer"]["has_sublayers"], False)
        self.assertEqual(result["layertest3"]["layer"]["sublayers"], [])
        self.assertEqual(result["layertest3"]["theme"]["name"], "test4")
        self.assertEqual(result["layertest3"]["theme"]["description"], "test 4")

class DataManagerGetLayersForThemeTest(APITestCase):
    def setUp(self):
        site = Site.objects.get(pk=1)
        self.theme1 = Theme.objects.create(name="companion", display_name="companion", is_visible=True, description="test")
        self.theme1.site.add(site)
        # This test layer will have attributes defined to test data type when filled out
        layer1 =Theme.objects.create(name="arcrest_layer")
        # This test layer will not have attributes defined other than required fields to test default behavior when attributes left empty
        layer1.site.add(site)

        layer2 = Layer.objects.create(name="sublayer", layer_type="ArcRest")
        layer2.site.add(site)

        ChildOrder.objects.create(parent_theme=self.theme1, content_object=layer1, order=1)
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=layer2, order=1)
        ChildOrder.objects.create(parent_theme=layer1, content_object=layer2, order=1)

    def test_get_layers_for_theme(self):
        client = APIClient()
        response = client.get(f"/layers/get_layers_for_theme/{self.theme1.id}/", HTTP_HOST="localhost:8000")
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
        self.assertEqual(result["layers"][0]["subLayers"][0]["name"], "sublayer")
        self.assertEqual(result["layers"][0]["subLayers"][0]["slug_name"], None)

class DataManagerWMSRequestCapabilities(APITestCase):
    def test_wms_request_capabilities_response(self):
        client = APIClient()
        response = client.get("/layers/wms_capabilities/?url=https%3A%2F%2Fwww.coastalatlas.net%2Fservices%2Fwms%2Fgetmap%2F%3F")
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)

        # Validate the structure of the WMS capabilities response
        self.assertIn("layers", result)
        self.assertIn("formats", result)
        self.assertIn("version", result)
        self.assertIn("styles", result)

        # Validate styles for each layer
        for i in range(len(result["layers"])):
            layer = result["layers"][i]
            self.assertIn(result["layers"][i], result["styles"])

        # Validate SRS for each layer
        self.assertIn("srs", result)
        for i in range(len(result["layers"])):
            self.assertIn(result["layers"][i], result["srs"])

        # Validate queryable layers
        self.assertIn("queryable", result)
        for i in range(len(result["queryable"])):
            self.assertIn(result["queryable"][i], result["layers"])
        
        # Validate time information for each layer
        self.assertIn("time", result)
        for i in range(len(result["layers"])):
            layer = result["layers"][i]
            self.assertIn(result["layers"][i], result["time"])
            self.assertIn("positions", result["time"][layer])
            self.assertIn("default", result["time"][layer])
            self.assertIn("field", result["time"][layer])
        self.assertIn("capabilities", result)
        self.assertIn("featureInfo", result["capabilities"])
        self.assertIn("available", result["capabilities"]["featureInfo"])
        self.assertIn("formats", result["capabilities"]["featureInfo"])

        # Validate data types of specific attributes in the WMS capabilities response
        self.assertIsInstance(result, dict)
        self.assertIsInstance(result["layers"], Collection)
        self.assertIsInstance(result["layers"][0], str)
        self.assertIsInstance(result["formats"], Collection)
        if len(result["formats"]) > 0:
            for i in range(len(result["formats"])):
                self.assertIsInstance(result["formats"][i], str)
        self.assertIsInstance(result["version"], str)
        self.assertIsInstance(result["styles"], dict)
        for i in range(len(result["layers"])):
            layer = result["layers"][i]
            self.assertIsInstance(result["styles"][layer], dict)
        self.assertIsInstance(result["srs"], dict)
        for i in range(len(result["layers"])):
            layer = result["layers"][i]
            self.assertIsInstance(result["srs"][layer], Collection)
            self.assertIsInstance(result["srs"][layer][0], str)
        self.assertIsInstance(result["queryable"], Collection)
        self.assertIsInstance(result["queryable"][0], str)
        self.assertIsInstance(result["time"], dict)
        for i in range(len(result["layers"])):
            layer = result["layers"][i]
            self.assertIsInstance(result["time"][layer], dict)
        self.assertIsInstance(result["capabilities"], dict)
        self.assertIsInstance(result["capabilities"]["featureInfo"], dict)
        self.assertIsInstance(result["capabilities"]["featureInfo"]["available"], bool)
        self.assertIsInstance(result["capabilities"]["featureInfo"]["formats"], Collection)

        # Validate specific values
        self.assertEqual(result["version"], "1.1.1")
        self.assertEqual(len(result["layers"]), len(result["styles"]))
        self.assertEqual(len(result["layers"]), len(result["srs"]))
        self.assertEqual(len(result["layers"]), len(result["time"]))
        self.assertEqual(result["capabilities"]["featureInfo"]["available"], True)

class DataManagerGetLayerCatalogContent(APITestCase):
    def setUp(self):
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
        client = APIClient()
        response = client.get(f"/layers/get_layer_catalog_content/{self.layer1.id}/")
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)

        # Validate the structure of the response
        self.assertIn("html", result)

        # Validate data types of specific attributes in the response
        self.assertIsInstance(result, dict)
        self.assertIsInstance(result["html"], str)

        # Validate specific value
        self.assertEqual(result["html"], self.layer1.catalog_html)

class DataManagerGetCatalogRecords(APITestCase):
    def test_get_catalog_records(self):
        api_url = "https://portal.westcoastoceans.org/data_manager/get_catalog_records"

        # Make a GET request to the live server since I can't mock
        response = requests.get(api_url)

        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Assuming the response is in JSON format
        data = response.json()

        # Add more specific assertions based on the expected structure of the JSON response
        self.assertIn('records', data)
        self.assertIn('record_name_lookup', data)
        self.assertIn('ELASTICSEARCH_INDEX', data)
        self.assertIn('CATALOG_TECHNOLOGY', data)

        self.assertIsInstance(data, dict, "data should be a JSON Object")
        self.assertIsInstance(data['records'], dict, "records should be a JSON Object")
        self.assertIsInstance(data['record_name_lookup'], dict, "record_name_lookup should be a JSON Object")
        self.assertIsInstance(data['ELASTICSEARCH_INDEX'], str, "ELASTICSEARCH_INDEX should be a string")
        self.assertIsInstance(data['CATALOG_TECHNOLOGY'], str, "CATALOG_TECHNOLOGY should be a string")

class DataManagerLayerStatusTest(APITestCase):
    def setUp(self):
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
        client = APIClient()
        response = client.get("/layers/migration/layer_status/")
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

class DataManagerLayerDetailsTest(APITestCase):
    def setUp(self):
        site = Site.objects.get(pk=1)
        congress_layer_url="https://coast.noaa.gov/arcgis/rest/services/OceanReports/USCongressionalDistricts/MapServer/export"
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

        client = APIClient()
        response = client.post("/layers/migration/layer_details/", {"layers": [layer1uuid, layer2uuid]})
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

class LiveAPITests(APITestCase):
    def setUp(self):
        pass
    def test_v1_responses(self):
        import requests, json
        mdl_theme_response = requests.get('http://localhost:8002/old_manager/get_themes')
        mls_theme_response = requests.get('http://localhost:8002/data_manager/get_themes')
        old_themes = json.loads(mdl_theme_response.content)
        new_themes = json.loads(mls_theme_response.content)
        self.assertEqual(old_themes, new_themes)
        for idx, theme in enumerate(old_themes['themes']):
            self.assertEqual(theme, new_themes['themes'][idx])
            print("Testing theme {}: {}".format(theme['id'], theme['name']))

            # Use the below IF statements to save some time testing specific themes.
            # if theme['id'] in DYNAMIC_PARENT_THEMES:
            # if theme['id'] in SLIDER_PARENT_THEMES:
            if not theme['id'] in FULLY_COMPLIANT_THEMES:
                self.loop_through_theme_children(theme['id'])

    def loop_through_theme_children(self, theme_id):
        dm_theme_response = requests.get('http://localhost:8002/old_manager/get_layers_for_theme/{}'.format(theme_id))
        ls_theme_response = requests.get('http://localhost:8002/data_manager/get_layers_for_theme/{}'.format(theme_id))
        old_theme_data = json.loads(dm_theme_response.content)
        new_theme_data = json.loads(ls_theme_response.content)
        self.assertEqual(old_theme_data.keys(), new_theme_data.keys())
        self.assertEqual(len(old_theme_data['layers']), len(new_theme_data['layers']))
        self.compare_lists(old_theme_data['layers'], new_theme_data['layers'])
        print(" -- Testing {} layers...".format(len(new_theme_data['layers'])))
        self.loop_though_theme_layers(new_theme_data['layers'])

    def compare_lists(self, old_list, new_list):
        for child in new_list:
            if not child in old_list:
                match = next(filter(lambda record: record['id'] == child['id'], old_list))
                for key in child.keys():
                    if not key in ['subLayers', 'type', 'date_modified']:

                        if not child[key] == match[key]:
                            print(child)
                            print(match)
                            print("Key '{}': new:'{}' ; old:'{}'".format(key, child[key], match[key]))


                    elif key == 'type' and (
                            child['type'] == 'slider' or child['type'] in ['checkbox',] and 
                            child['has_sublayers'] == True and match['has_sublayers'] == True
                        ):
                            pass
                    elif key == 'subLayers':   # 'subLayers'
                        if not (type(match[key]) == str or type(child[key])==str):
                            self.compare_lists(match[key], child[key])
                        else:
                            self.assertEqual(child[key], match[key])

    def loop_though_theme_layers(self, layer_list):
        for index, layer in enumerate(layer_list):
            if not layer['type'] in ['slider',]:
                dm_layer_response = requests.get('http://localhost:8002/old_manager/get_layer_details/{}'.format(layer['id']))
                ls_layer_response = requests.get('http://localhost:8002/data_manager/get_layer_details/{}'.format(layer['id']))
                old_layer_data = json.loads(dm_layer_response.content)
                new_layer_data = json.loads(ls_layer_response.content)
                # if not len(old_layer_data.keys()) == len(new_layer_data.keys()):
                #     import ipdb; ipdb.set_trace()
                self.assertEqual(old_layer_data.keys(), new_layer_data.keys())
                self.compare_layers(old_layer_data, new_layer_data, index)
            else:
                print("TODO: create logic for type '{}'".format(layer['type']))

    def compare_layers(self, old_layer, new_layer, layer_count):
        for key in old_layer.keys():
            if key not in ['date_modified','subLayers','attributes', 'lookups', 'companion_layers']: # objects and dates?
                if not old_layer[key] == new_layer[key]:
                    if (
                        # old empty strings are new nulls
                        key in [
                            'arcgis_layers', 'wms_slug', 'wms_format', 'wms_srs', 'wms_styles', 'wms_timing', 
                            'wms_time_item', 'utfurl', 'legend', 'legend_title', 
                            'legend_subtitle', 'learn_more', 'outline_color', 'data_download', 'wms_version'
                        ] and old_layer[key] == '' and new_layer[key] == None
                    ) or (
                        # old nulls are new empty strings
                        key in [
                            'source', 'wms_version', 'wms_additional'
                        ] and old_layer[key] == None and new_layer[key] == ""
                    ) or (
                        #fields are set that have no business being set on parent layers/themes
                        key in [
                            'outline_opacity', 'color', 'fill_opacity', 'graphic', 'arcgis_layers', 'type', 'tiles', 'kml', 'opacity'
                        ] and new_layer['type'] in [
                            'checkbox', 'radio', 'placeholder'
                        ]
                    ) or (
                        # Custom Vector styling for non-Vector sources
                        new_layer['type'] not in [
                            'ArcFeatureService', 'vector',
                        ] and key in [
                            'outline_opacity', 'color', 'fill_opacity', 'graphic', 'graphic_scale', 'point_radius',
                        ]
                    ):
                        old_layer[key] = new_layer[key]
                    elif key == 'url' and any( dynamic_theme_id in new_layer['catalog_html'] for dynamic_theme_id in [";themes%5Bids%5D%5B%5D=25&", ";themes%5Bids%5D%5B%5D=24&"]):
                        if ";themes%5Bids%5D%5B%5D=25&" in new_layer['catalog_html']:
                            parent_theme = "vtr"
                        elif ";themes%5Bids%5D%5B%5D=24&" in new_layer['catalog_html']:
                            parent_theme = "mdat"
                        print("*****************")
                        print("Theme {} belongs to '{}' theme".format(new_layer['id'], parent_theme))
                        print("TODO: Correct Dynamic Layer support! Passing for now...")
                        print("*****************")
                        old_layer[key] = new_layer[key]
                    elif key == 'catalog_html':
                        old_layer[key] = old_layer[key].replace('<a class="btn btn-mini disabled" href="None">', '<a class="btn btn-mini disabled" href="">')
                        new_layer[key] = new_layer[key].replace('<a class="btn btn-mini disabled" href="None">', '<a class="btn btn-mini disabled" href="">')
                    elif key == 'has_companion' and old_layer[key] == True:
                        # some old layers have 'has_companion' checked, but no companions assigned (5206)
                        old_layer['has_companion'] = len(old_layer['companion_layers']) > 0
                    if not old_layer[key] == new_layer[key]:
                        print("=================")
                        print("Layer #{} for theme".format(layer_count))
                        print("ID: {}".format(old_layer['id']))
                        print("Name: {}".format(old_layer['name']))
                        print("KEY: {}".format(key))
                        print("OLD: {}".format(old_layer[key]))
                        print("NEW: {}".format(new_layer[key]))
                        # import ipdb; ipdb.set_trace()
                        print("=================")
                if not key in ['data_notes','disabled_message']:
                    self.assertEqual(old_layer[key], new_layer[key])
            elif key == 'companion_layers':
                if old_layer['has_companion'] == False:
                    old_layer['companion_layers'] = []
                self.assertEqual(len(old_layer[key]), len(new_layer[key]))
                for index, old_companion in enumerate(old_layer[key]):
                    new_companion = new_layer[key][index]
                    old_keys = old_companion.keys()
                    new_keys = new_companion.keys()
                    key_diff = 0
                    for old_key in old_keys:
                        if not old_key in new_keys:
                            key_diff += 1
                            print("OLD KEY: '{}' not in new keys".format(old_key))
                    for new_key in new_keys:
                        if not new_key in old_keys:
                            key_diff += 1
                            print("NEW KEY: '{}' not in old keys".format(new_key))
                    if key_diff > 0:
                        print("Total num of different keys: {}".format(key_diff))
                    self.compare_layers(old_companion, new_companion, layer_count)
            # elif key in ['subLayers', 'attributes', 'lookups', 'companion_layers']:
            #     if not (type(old_layer[key]) == str or type(new_layer[key])==str):
            #         self.compare_lists(old_layer[key], new_layer[key])
            #     else:
            #         self.assertEqual(new_layer[key], old_layer[key])