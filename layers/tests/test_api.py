from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from layers.models import Layer, Theme
from collections.abc import Collection, Mapping
import requests
import json

class DataManagerGetLayerDetailsTest(APITestCase):
    def setUp(self):
        congress_layer_url="https://coast.noaa.gov/arcgis/rest/services/OceanReports/USCongressionalDistricts/MapServer/export"
        theme1 = Theme.objects.create(id=1, name="companion", display_name="companion", visible=True)
        theme1.site.set([1])
        # This test layer will have attributes defined to test data type when filled out
        layer1 =Layer.objects.create(id=1, name="arcrest_layer", order=15, layer_type="arcgis", url=congress_layer_url, arcgis_layers="19", password_protected=True, query_by_point=True,  maxZoom=14, minZoom=6, proxy_url=True, disable_arcgis_attributes=True, utfurl="testing", wms_slug="hi", wms_version="hello", 
                             wms_format="pusheen", wms_srs="world", wms_styles="style", wms_timing="hullo", wms_time_item="ello", wms_additional="star", wms_info=True, wms_info_format="test", has_companion=True, search_query=True, legend="hi", legend_title="title", legend_subtitle="subtitle", description="testlayer", 
                             data_overview="testlayer", data_source="testlayer", data_notes="testlayer", kml="testlayer", data_download="testlayer", learn_more="testlayer", metadata="testlayer", source="testlayer", label_field="testlayer", custom_style="testlayer", vector_outline_color="blue", vector_outline_opacity=5, vector_outline_width=2, point_radius=8,
                             vector_color="blue", vector_fill=5, vector_graphic="testlayer", vector_graphic_scale=5, opacity=0.8, is_annotated=True, is_disabled=True, disabled_message="testlayer")
        layer1.site.set([1])
        # This test layer will not have attributes defined other than required fields to test default behavior when attributes left empty
        layer2 = Layer.objects.create(id=2, name="Arc", layer_type="arcgis")
        layer2.themes.set([1])
        layer2.site.set([1])
        # This layer is to test how sublayers are returned
        layer3 = Layer.objects.create(id=3, name="sublayer", layer_type="arcgis", is_sublayer=True)
        layer3.site.set([1])
        layer2.connect_companion_layers_to.set([layer1])
        layer1.sublayers.set([layer3])
    
    def test_view_layer_details_response_format(self):
        client = APIClient()
        request1 = client.get("/data_manager/get_layer_details/1")
        self.assertEqual(request1.status_code, 200)
        result1 = json.loads(request1.content)

        request2 = client.get("/data_manager/get_layer_details/2")
        self.assertEqual(request2.status_code, 200)
        result2 = json.loads(request2.content)
        print(result1, result2)

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
        response = self.client.get("/data_manager/get_layer_details/2")
        self.assertEqual(response.status_code, 200)
        result= json.loads(response.content)

        # Expected default attributes and lookups for layer 2
        expected_attributes = {"compress_attributes": False, "event": "click", "attributes": [], "mouseover_attribute": None, "preserved_format_attributes": []}
        expected_lookups = {"field": None, "details": []}

        # Validate each attribute with its expected value
        self.assertEqual(result["id"], 2)
        self.assertEqual(result["name"], "Arc")
        self.assertEqual(result["order"], 10)
        self.assertEqual(result["type"], "arcgis")
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
        self.assertEqual(result["wms_additional"], None)
        self.assertEqual(result["wms_info"], False)
        self.assertEqual(result["wms_info_format"], None)
        self.assertEqual(result["utfurl"], None)
        self.assertEqual(result["subLayers"], [])
        self.assertEqual(result["has_companion"], False)
        self.assertEqual(result["queryable"], False)
        self.assertEqual(result["legend"], None)
        self.assertEqual(result["legend_title"], None)
        self.assertEqual(result["legend_subtitle"], None)
        self.assertEqual(result["show_legend"], True)
        self.assertEqual(result["description"], None)
        self.assertEqual(result["overview"], None)
        self.assertEqual(result["data_source"], None)
        self.assertEqual(result["data_notes"], None)
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
        self.assertEqual(result["disabled_message"], None)
        self.assertEqual(result["data_url"], "/data-catalog/companion/#layer-info-arc2")
        self.assertEqual(result["is_multilayer"], False)
        self.assertEqual(result["is_multilayer_parent"], False)
        self.assertEqual(result["dimensions"], [])
        self.assertEqual(result["associated_multilayers"], {})
        self.assertEqual(result["parent"], None)

    def test_view_layer_details_response_data(self):
        response = self.client.get("/data_manager/get_layer_details/1")
        self.assertEqual(response.status_code, 200)
        result= json.loads(response.content)
        congress_layer_url="https://coast.noaa.gov/arcgis/rest/services/OceanReports/USCongressionalDistricts/MapServer/export"
        
        # Get Layer 3 and Layer 2 from the database and prepare dictionaries
        layer3 = Layer.objects.get(id=3)
        layer3dict = layer3.toDict
        layer3dict["uuid"] = str(layer3dict["uuid"])
        layer3dict["parent"]["uuid"] = str(layer3dict["parent"]["uuid"])
        layer3dict["parent"]["subLayers"][0]["uuid"] = str(layer3dict["parent"]["subLayers"][0]["uuid"] )
        layer2 = Layer.objects.get(id=2)
        layer2dict = layer2.toDict
        layer2dict["uuid"] = str(layer2dict["uuid"])

        # Define expected attributes and lookups
        expected_attributes = {"compress_attributes": False, "event": "click", "attributes": [], "mouseover_attribute": None, "preserved_format_attributes": []}
        expected_lookups = {"field": None, "details": []}

        # Validate result against expected values
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["name"], "arcrest_layer")
        self.assertEqual(result["order"], 15)
        self.assertEqual(result["type"], "arcgis")
        self.assertEqual(result["url"], congress_layer_url)
        self.assertEqual(result["arcgis_layers"], "19")
        self.assertEqual(result["password_protected"], True)
        self.assertEqual(result["query_by_point"], True)
        self.assertEqual(result["proxy_url"], True)
        self.assertEqual(result["disable_arcgis_attributes"], True)
        self.assertEqual(result["wms_slug"], "hi")
        self.assertEqual(result["wms_version"], "hello")
        self.assertEqual(result["wms_format"], "pusheen")
        self.assertEqual(result["wms_srs"], "world")
        self.assertEqual(result["wms_styles"], "style")
        self.assertEqual(result["wms_timing"], "hullo")
        self.assertEqual(result["wms_time_item"], "ello")
        self.assertEqual(result["wms_additional"], "star")
        self.assertEqual(result["wms_info"], True)
        self.assertEqual(result["wms_info_format"], "test")
        self.assertEqual(result["utfurl"], "testing")
        # Validate subLayers and companion_layers
        for key in result["subLayers"][0].keys():
            #description and overview takes from parent, but parent should not be set
            if not key in ["is_sublayer", "date_modified", "companion_layers", "description", "overview"]:

                if key != "parent":
                    self.assertEqual(result["subLayers"][0][key], layer3dict[key])
                else:
                    self.assertEqual(result["subLayers"][0][key], layer3dict[key]["id"])
        for key in result["companion_layers"][0].keys():
            #layer_dict does not have is_sublayer
            if not key in ["is_sublayer", "date_modified", "companion_layers", "parent"]:
                self.assertEqual(result["companion_layers"][0][key], layer2dict[key])
        self.assertEqual(result["has_companion"], True)
        self.assertEqual(result["queryable"], True)
        self.assertEqual(result["legend"], "hi")
        self.assertEqual(result["legend_title"], "title")
        self.assertEqual(result["legend_subtitle"], "subtitle")
        self.assertEqual(result["show_legend"], True)
        self.assertEqual(result["description"], "testlayer")
        self.assertEqual(result["overview"], "testlayer")
        self.assertEqual(result["data_source"], "testlayer")
        self.assertEqual(result["data_notes"], "testlayer")
        self.assertEqual(result["kml"], "testlayer")
        self.assertEqual(result["data_download"], "testlayer")
        self.assertEqual(result["learn_more"], "testlayer")
        self.assertEqual(result["metadata"], "testlayer")
        self.assertEqual(result["source"], "testlayer")
        self.assertEqual(result["tiles"], None)
        self.assertEqual(result["label_field"], "testlayer")
        self.assertEqual(result["attributes"], expected_attributes)
        self.assertEqual(result["lookups"], expected_lookups)
        self.assertEqual(result["minZoom"], 6)
        self.assertEqual(result["maxZoom"], 14)
        self.assertEqual(result["custom_style"], "testlayer")
        self.assertEqual(result["outline_color"], "blue")
        self.assertEqual(result["outline_opacity"], 5.0)
        self.assertEqual(result["outline_width"], 2)
        self.assertEqual(result["point_radius"], 8)
        self.assertEqual(result["color"], "blue")
        self.assertEqual(result["fill_opacity"], 5.0)
        self.assertEqual(result["graphic"], "testlayer")
        self.assertEqual(result["graphic_scale"], 5.0)
        self.assertEqual(result["opacity"], 0.8)
        self.assertEqual(result["annotated"], True)
        self.assertEqual(result["is_disabled"], True)
        self.assertEqual(result["disabled_message"], "testlayer")
        self.assertEqual(result["data_url"], None)
        self.assertEqual(result["is_multilayer"], False)
        self.assertEqual(result["is_multilayer_parent"], False)
        self.assertEqual(result["dimensions"], [])
        self.assertEqual(result["associated_multilayers"], {})
        self.assertEqual(result["parent"], None)

class DataManagerGetJsonTest(APITestCase):
    def setUp(self):
        congress_layer_url="https://coast.noaa.gov/arcgis/rest/services/OceanReports/USCongressionalDistricts/MapServer/export"
        
        # Create themes and layers for testing
        theme1 = Theme.objects.create(id=1, name="companion", display_name="companion", visible=True, description="test")
        theme1.site.set([1])
        theme2 = Theme.objects.create(id=2, name="companion2", display_name="companion2", visible=True)
        theme2.site.set([1])
        # This test layer will have attributes defined to test data type when filled out
        layer1 =Layer.objects.create(id=1, name="arcrest_layer", order=15, layer_type="arcgis", url=congress_layer_url, arcgis_layers="19", password_protected=True, query_by_point=True,  maxZoom=14, minZoom=6, proxy_url=True, disable_arcgis_attributes=True, utfurl="testing", wms_slug="hi", wms_version="hello", 
                             wms_format="pusheen", wms_srs="world", wms_styles="style", wms_timing="hullo", wms_time_item="ello", wms_additional="star", wms_info=True, wms_info_format="test", has_companion=True, search_query=True, legend="hi", legend_title="title", legend_subtitle="subtitle", description="testlayer", 
                             data_overview="testlayer", data_source="testlayer", data_notes="testlayer", kml="testlayer", data_download="testlayer", learn_more="testlayer", metadata="testlayer", source="testlayer", label_field="testlayer", custom_style="testlayer", vector_outline_color="blue", vector_outline_opacity=5, vector_outline_width=2, point_radius=8,
                             vector_color="blue", vector_fill=5, vector_graphic="testlayer", vector_graphic_scale=5, opacity=0.8, is_annotated=True, is_disabled=True, disabled_message="testlayer")
        # This test layer will not have attributes defined other than required fields to test default behavior when attributes left empty
        layer1.site.set([1])
        layer1.themes.set([1])
         # Create a test sublayer
        layer2 = Layer.objects.create(id=2, name="sublayer", layer_type="arcgis", is_sublayer=True)
        layer2.site.set([1])
        layer2.themes.set([1])
        layer1.sublayers.set([layer2])

    def test_view_api(self):
        client = APIClient()
        response = client.get("/data_manager/get_json", HTTP_HOST="localhost:8000")
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        congress_layer_url="https://coast.noaa.gov/arcgis/rest/services/OceanReports/USCongressionalDistricts/MapServer/export"
        
        # Get Layer 2 and prepare a dictionary for comparison
        layer2 = Layer.objects.get(id=2)
        layer2dict = layer2.toDict
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
        self.assertEqual(result["layers"][0]["id"], 1)
        self.assertEqual(result["layers"][0]["name"], "arcrest_layer")
        self.assertEqual(result["layers"][0]["order"], 15)
        self.assertEqual(result["layers"][0]["type"], "arcgis")
        self.assertEqual(result["layers"][0]["url"], congress_layer_url)
        self.assertEqual(result["layers"][0]["arcgis_layers"], "19")
        self.assertEqual(result["layers"][0]["password_protected"], True)
        self.assertEqual(result["layers"][0]["query_by_point"], True)
        self.assertEqual(result["layers"][0]["proxy_url"], True)
        self.assertEqual(result["layers"][0]["disable_arcgis_attributes"], True)
        self.assertEqual(result["layers"][0]["wms_slug"], "hi")
        self.assertEqual(result["layers"][0]["wms_version"], "hello")
        self.assertEqual(result["layers"][0]["wms_format"], "pusheen")
        self.assertEqual(result["layers"][0]["wms_srs"], "world")
        self.assertEqual(result["layers"][0]["wms_styles"], "style")
        self.assertEqual(result["layers"][0]["wms_timing"], "hullo")
        self.assertEqual(result["layers"][0]["wms_time_item"], "ello")
        self.assertEqual(result["layers"][0]["wms_additional"], "star")
        self.assertEqual(result["layers"][0]["wms_info"], True)
        self.assertEqual(result["layers"][0]["wms_info_format"], "test")
        self.assertEqual(result["layers"][0]["utfurl"], "testing")
        for key in result["layers"][0]["subLayers"][0].keys():
            #description and overview takes from parent, but parent should not be set
            if not key in ["is_sublayer", "date_modified", "companion_layers", "description", "overview"]:
                if key != "parent":
                    self.assertEqual(result["layers"][0]["subLayers"][0][key], layer2dict[key])
                else:
                    self.assertEqual(result["layers"][0]["subLayers"][0][key], layer2dict[key]["id"])
        self.assertEqual(result["layers"][0]["companion_layers"], [])
        self.assertEqual(result["layers"][0]["has_companion"], True)
        self.assertEqual(result["layers"][0]["queryable"], True)
        self.assertEqual(result["layers"][0]["legend"], "hi")
        self.assertEqual(result["layers"][0]["legend_title"], "title")
        self.assertEqual(result["layers"][0]["legend_subtitle"], "subtitle")
        self.assertEqual(result["layers"][0]["show_legend"], True)
        self.assertEqual(result["layers"][0]["description"], "testlayer")
        self.assertEqual(result["layers"][0]["overview"], "testlayer")
        self.assertEqual(result["layers"][0]["data_source"], "testlayer")
        self.assertEqual(result["layers"][0]["data_notes"], "testlayer")
        self.assertEqual(result["layers"][0]["kml"], "testlayer")
        self.assertEqual(result["layers"][0]["data_download"], "testlayer")
        self.assertEqual(result["layers"][0]["learn_more"], "testlayer")
        self.assertEqual(result["layers"][0]["metadata"], "testlayer")
        self.assertEqual(result["layers"][0]["source"], "testlayer")
        self.assertEqual(result["layers"][0]["tiles"], None)
        self.assertEqual(result["layers"][0]["label_field"], "testlayer")
        self.assertEqual(result["layers"][0]["attributes"], expected_attributes)
        self.assertEqual(result["layers"][0]["lookups"], expected_lookups)
        self.assertEqual(result["layers"][0]["minZoom"], 6)
        self.assertEqual(result["layers"][0]["maxZoom"], 14)
        self.assertEqual(result["layers"][0]["custom_style"], "testlayer")
        self.assertEqual(result["layers"][0]["outline_color"], "blue")
        self.assertEqual(result["layers"][0]["outline_opacity"], 5.0)
        self.assertEqual(result["layers"][0]["outline_width"], 2)
        self.assertEqual(result["layers"][0]["point_radius"], 8)
        self.assertEqual(result["layers"][0]["color"], "blue")
        self.assertEqual(result["layers"][0]["fill_opacity"], 5.0)
        self.assertEqual(result["layers"][0]["graphic"], "testlayer")
        self.assertEqual(result["layers"][0]["graphic_scale"], 5.0)
        self.assertEqual(result["layers"][0]["opacity"], 0.8)
        self.assertEqual(result["layers"][0]["annotated"], True)
        self.assertEqual(result["layers"][0]["is_disabled"], True)
        self.assertEqual(result["layers"][0]["disabled_message"], "testlayer")
        self.assertEqual(result["layers"][0]["data_url"], "/data-catalog/companion/#layer-info-arcrest_layer1")
        self.assertEqual(result["layers"][0]["is_multilayer"], False)
        self.assertEqual(result["layers"][0]["is_multilayer_parent"], False)
        self.assertEqual(result["layers"][0]["dimensions"], [])
        self.assertEqual(result["layers"][0]["associated_multilayers"], {})
        self.assertEqual(result["layers"][0]["parent"], None)
        self.assertEqual(result["themes"][0]["id"], 1)
        self.assertEqual(result["themes"][0]["name"], "companion")
        self.assertEqual(result["themes"][0]["display_name"], "companion")
        self.assertEqual(result["themes"][0]["learn_link"], "../learn/companion")
        self.assertEqual(result["themes"][0]["is_visible"], True)
        self.assertEqual(result["themes"][0]["layers"], [1])
        self.assertEqual(result["themes"][0]["description"], "test")
        self.assertEqual(result["themes"][1]["id"], 2)
        self.assertEqual(result["themes"][1]["name"], "companion2")
        self.assertEqual(result["themes"][1]["display_name"], "companion2")
        self.assertEqual(result["themes"][1]["learn_link"], "../learn/companion2")
        self.assertEqual(result["themes"][1]["is_visible"], True)
        self.assertEqual(result["themes"][1]["layers"], [])
        self.assertEqual(result["themes"][1]["description"], None)

class DataManagerGetThemesTest(APITestCase):
    def setUp(self):
        # Associate theme with default site id, otherwise themes do not show up
        Theme.objects.create(id=1, name="test", display_name="test", visible=True).site.set([1])
        Theme.objects.create(id=2, name="test2", display_name="test2", visible=True).site.set([1])

    def test_get_themes_response_format(self):
        client = APIClient()
        response = client.get("/data_manager/get_themes")
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
        response = client.get("/data_manager/get_themes")
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)

        self.assertIn("themes", result, "Response should contain 'themes' key")

        # Get the specific themes from the response to test data 
        theme_1 = result["themes"][0]
        theme_2 = result["themes"][1]

        # Check the format of each theme object in the list - similar to first
        self.assertEqual(theme_1["id"], 1)
        self.assertEqual(theme_1["name"], "test")
        self.assertEqual(theme_1["display_name"], "test")
        self.assertTrue(theme_1["is_visible"])

        self.assertEqual(theme_2["id"], 2)
        self.assertEqual(theme_2["name"], "test2")
        self.assertEqual(theme_2["display_name"], "test2")
        self.assertTrue(theme_2["is_visible"])

class DataManagerGetLayerSearchDataTest(APITestCase):
     def setUp(self):
        theme1 = Theme.objects.create(id=1, name="test3", display_name="test3", visible=True, description="test 3")
        theme1.site.set([1])
        # Cannot use .set in the same line as creating an object as .set returns None
        theme2 = Theme.objects.create(id=2, name="test4", display_name="test4", visible=True, description="test 4")
        theme2.site.set([1])
        layer1 = Layer.objects.create(id=1, name="layertest1", is_sublayer=False)
        layer1.site.set([1])
        layer1.themes.set([theme1])
        # Layer2 is sublayer of layer 1
        layer2 = Layer.objects.create(id=2, name="layertest2", is_sublayer=True)
        layer2.site.set([1])
        layer2.sublayers.set([layer1])
        layer2.themes.set([theme1])
        layer3 = Layer.objects.create(id=3, name="layertest3", is_sublayer=False)
        layer3.site.set([1])
        layer3.themes.set([theme2])

     def test_get_layer_search_data_response_format(self):
        client = APIClient()
        response = client.get("/data_manager/get_layer_search_data")
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)

        # Sublayers are not shown, should only return layers as keys that are not sublayers
        self.assertIn("layertest1", result, "result should have layertest1 key")
        self.assertIn("layertest3", result, "result should have layertest3 key")
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

        self.assertEqual(result["layertest1"]["layer"]["id"], 1)
        self.assertEqual(result["layertest1"]["layer"]["name"], "layertest1")
        self.assertEqual(result["layertest1"]["layer"]["has_sublayers"], True)
        self.assertEqual(result["layertest1"]["layer"]["sublayers"][0]["name"], "layertest2")
        self.assertEqual(result["layertest1"]["layer"]["sublayers"][0]["id"], 2)
        self.assertEqual(result["layertest1"]["theme"]["id"], 1)
        self.assertEqual(result["layertest1"]["theme"]["name"], "test3")
        self.assertEqual(result["layertest1"]["theme"]["description"], "test 3")
        self.assertEqual(result["layertest3"]["layer"]["id"], 3)
        self.assertEqual(result["layertest3"]["layer"]["name"], "layertest3")
        self.assertEqual(result["layertest3"]["layer"]["has_sublayers"], False)
        self.assertEqual(result["layertest3"]["layer"]["sublayers"], [])
        self.assertEqual(result["layertest3"]["theme"]["id"], 2)
        self.assertEqual(result["layertest3"]["theme"]["name"], "test4")
        self.assertEqual(result["layertest3"]["theme"]["description"], "test 4")

class DataManagerGetLayersForThemeTest(APITestCase):
    def setUp(self):
        congress_layer_url="https://coast.noaa.gov/arcgis/rest/services/OceanReports/USCongressionalDistricts/MapServer/export"
        theme1 = Theme.objects.create(id=1, name="companion", display_name="companion", visible=True, description="test")
        theme1.site.set([1])
        # This test layer will have attributes defined to test data type when filled out
        layer1 =Layer.objects.create(id=1, name="arcrest_layer", order=15, layer_type="arcgis", url=congress_layer_url, arcgis_layers="19", password_protected=True, query_by_point=True,  maxZoom=14, minZoom=6, proxy_url=True, disable_arcgis_attributes=True, utfurl="testing", wms_slug="hi", wms_version="hello", 
                             wms_format="pusheen", wms_srs="world", wms_styles="style", wms_timing="hullo", wms_time_item="ello", wms_additional="star", wms_info=True, wms_info_format="test", has_companion=True, search_query=True, legend="hi", legend_title="title", legend_subtitle="subtitle", description="testlayer", 
                             data_overview="testlayer", data_source="testlayer", data_notes="testlayer", kml="testlayer", data_download="testlayer", learn_more="testlayer", metadata="testlayer", source="testlayer", label_field="testlayer", custom_style="testlayer", vector_outline_color="blue", vector_outline_opacity=5, vector_outline_width=2, point_radius=8,
                             vector_color="blue", vector_fill=5, vector_graphic="testlayer", vector_graphic_scale=5, opacity=0.8, is_annotated=True, is_disabled=True, disabled_message="testlayer")
        # This test layer will not have attributes defined other than required fields to test default behavior when attributes left empty
        layer1.site.set([1])
        layer1.themes.set([1])
        layer2 = Layer.objects.create(id=2, name="sublayer", layer_type="arcgis", is_sublayer=True)
        layer2.site.set([1])
        layer2.themes.set([1])
        layer1.sublayers.set([layer2])

    def test_get_layers_for_theme(self):
        client = APIClient()
        response = client.get("/data_manager/get_layers_for_theme/1")
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
        self.assertIsInstance(result["layers"][0]["subLayers"][0]["slug_name"], str, "slug_name should be string")

        self.assertEqual(result["layers"][0]["id"], 1)
        self.assertEqual(result["layers"][0]["name"], "arcrest_layer")
        self.assertEqual(result["layers"][0]["type"], "arcgis")
        self.assertEqual(result["layers"][0]["has_sublayers"], True)
        self.assertEqual(result["layers"][0]["subLayers"][0]["id"], 2)
        self.assertEqual(result["layers"][0]["subLayers"][0]["name"], "sublayer")
        self.assertEqual(result["layers"][0]["subLayers"][0]["slug_name"], "sublayer2")

class DataManagerWMSRequestCapabilities(APITestCase):
    def test_wms_request_capabilities_response(self):
        client = APIClient()
        response = client.get("/data_manager/wms_capabilities/?url=https%3A%2F%2Fwww.coastalatlas.net%2Fservices%2Fwms%2Fgetmap%2F%3F")
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
        congress_layer_url="https://coast.noaa.gov/arcgis/rest/services/OceanReports/USCongressionalDistricts/MapServer/export"
        theme1 = Theme.objects.create(id=1, name="companion", display_name="companion", visible=True, description="test")
        theme1.site.set([1])
        # This test layer will have attributes defined to test data type when filled out
        layer1 =Layer.objects.create(id=1, name="arcrest_layer", order=15, layer_type="arcgis", url=congress_layer_url, arcgis_layers="19", password_protected=True, query_by_point=True,  maxZoom=14, minZoom=6, proxy_url=True, disable_arcgis_attributes=True, utfurl="testing", wms_slug="hi", wms_version="hello", 
                             wms_format="pusheen", wms_srs="world", wms_styles="style", wms_timing="hullo", wms_time_item="ello", wms_additional="star", wms_info=True, wms_info_format="test", has_companion=True, search_query=True, legend="hi", legend_title="title", legend_subtitle="subtitle", description="testlayer", 
                             data_overview="testlayer", data_source="testlayer", data_notes="testlayer", kml="testlayer", data_download="testlayer", learn_more="testlayer", metadata="testlayer", source="testlayer", label_field="testlayer", custom_style="testlayer", vector_outline_color="blue", vector_outline_opacity=5, vector_outline_width=2, point_radius=8,
                             vector_color="blue", vector_fill=5, vector_graphic="testlayer", vector_graphic_scale=5, opacity=0.8, is_annotated=True, is_disabled=True, disabled_message="testlayer")
        # This test layer will not have attributes defined other than required fields to test default behavior when attributes left empty
        layer1.site.set([1])
        layer1.themes.set([1])

    def test_get_layer_catalog_content(self):
        client = APIClient()
        response = client.get("/data_manager/get_layer_catalog_content/1/")
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        
        layer1 = Layer.objects.get(id=1)

        # Validate the structure of the response
        self.assertIn("html", result)

        # Validate data types of specific attributes in the response
        self.assertIsInstance(result, dict)
        self.assertIsInstance(result["html"], str)

        # Validate specific value
        self.assertEqual(result["html"], layer1.catalog_html)

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
        congress_layer_url="https://coast.noaa.gov/arcgis/rest/services/OceanReports/USCongressionalDistricts/MapServer/export"
        theme1 = Theme.objects.create(id=1, name="companion", display_name="companion", visible=True, description="test")
        theme1.site.set([1])
        theme2 = Theme.objects.create(id=2, name="companion2", display_name="companion2", visible=True)
        theme2.site.set([1])
        # This test layer will have attributes defined to test data type when filled out
        layer1 =Layer.objects.create(id=1, name="arcrest_layer", order=15, layer_type="arcgis", url=congress_layer_url, arcgis_layers="19", password_protected=True, query_by_point=True,  maxZoom=14, minZoom=6, proxy_url=True, disable_arcgis_attributes=True, utfurl="testing", wms_slug="hi", wms_version="hello", 
                             wms_format="pusheen", wms_srs="world", wms_styles="style", wms_timing="hullo", wms_time_item="ello", wms_additional="star", wms_info=True, wms_info_format="test", has_companion=True, search_query=True, legend="hi", legend_title="title", legend_subtitle="subtitle", description="testlayer", 
                             data_overview="testlayer", data_source="testlayer", data_notes="testlayer", kml="testlayer", data_download="testlayer", learn_more="testlayer", metadata="testlayer", source="testlayer", label_field="testlayer", custom_style="testlayer", vector_outline_color="blue", vector_outline_opacity=5, vector_outline_width=2, point_radius=8,
                             vector_color="blue", vector_fill=5, vector_graphic="testlayer", vector_graphic_scale=5, opacity=0.8, is_annotated=True, is_disabled=True, disabled_message="testlayer")
        # This test layer will not have attributes defined other than required fields to test default behavior when attributes left empty
        layer1.site.set([1])
        layer1.themes.set([1])
        # Create a test sublayer
        layer2 = Layer.objects.create(id=2, name="sublayer", layer_type="arcgis", is_sublayer=True)
        layer2.site.set([1])
        layer2.themes.set([1])
        layer1.sublayers.set([layer2])
    
    def test_layer_status(self):
        client = APIClient()
        response = client.get("/data_manager/migration/layer_status")
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)

        # Get Layers and Themes and prepare a dictionary for comparison
        layer2 = Layer.objects.get(id=2)
        layer2dict = layer2.toDict
        layer2dict["uuid"] = str(layer2dict["uuid"])
        layer2uuid = layer2dict["uuid"]
        theme2 = Theme.objects.get(id=2)
        theme2uuid = str(theme2.uuid)

        self.assertIn("themes", result)
        self.assertIn("layers", result)
        self.assertIn(f"{theme2uuid}", result["themes"])
        self.assertIn(f"{layer2uuid}", result["layers"])
        self.assertIn("name", result["themes"][f"{theme2uuid}"])
        self.assertIn("name", result["layers"][f"{layer2uuid}"])
        self.assertIn("uuid", result["themes"][f"{theme2uuid}"])
        self.assertIn("date_modified", result["themes"][f"{theme2uuid}"])
        self.assertIn("date_modified", result["layers"][f"{layer2uuid}"])
        self.assertIn("layers", result["themes"][f"{theme2uuid}"])
        
        self.assertIsInstance(result, dict)
        self.assertIsInstance(result["themes"], dict)
        self.assertIsInstance(result["layers"], dict)
        self.assertIsInstance(result["themes"][f"{theme2uuid}"], dict)
        self.assertIsInstance(result["layers"][f"{layer2uuid}"], dict)
        self.assertIsInstance(result["themes"][f"{theme2uuid}"]["name"], str)
        self.assertIsInstance(result["themes"][f"{theme2uuid}"]["uuid"], str)
        self.assertIsInstance(result["themes"][f"{theme2uuid}"]["date_modified"], str)
        self.assertIsInstance(result["themes"][f"{theme2uuid}"]["layers"], Collection)
        self.assertIsInstance(result["layers"][f"{layer2uuid}"]["name"], str)
        self.assertIsInstance(result["layers"][f"{layer2uuid}"]["date_modified"], str)

class DataManagerLayerDetailsTest(APITestCase):
    def setUp(self):
        congress_layer_url="https://coast.noaa.gov/arcgis/rest/services/OceanReports/USCongressionalDistricts/MapServer/export"
        theme1 = Theme.objects.create(id=1, name="companion", display_name="companion", visible=True, description="test")
        theme1.site.set([1])
        theme2 = Theme.objects.create(id=2, name="companion2", display_name="companion2", visible=True)
        theme2.site.set([1])
        # This test layer will have attributes defined to test data type when filled out
        layer1 =Layer.objects.create(id=1, name="arcrest_layer", order=15, layer_type="arcgis", url=congress_layer_url, arcgis_layers="19", password_protected=True, query_by_point=True,  maxZoom=14, minZoom=6, proxy_url=True, disable_arcgis_attributes=True, utfurl="testing", wms_slug="hi", wms_version="hello", 
                             wms_format="pusheen", wms_srs="world", wms_styles="style", wms_timing="hullo", wms_time_item="ello", wms_additional="star", wms_info=True, wms_info_format="test", has_companion=True, search_query=True, legend="hi", legend_title="title", legend_subtitle="subtitle", description="testlayer", 
                             data_overview="testlayer", data_source="testlayer", data_notes="testlayer", kml="testlayer", data_download="testlayer", learn_more="testlayer", metadata="testlayer", source="testlayer", label_field="testlayer", custom_style="testlayer", vector_outline_color="blue", vector_outline_opacity=5, vector_outline_width=2, point_radius=8,
                             vector_color="blue", vector_fill=5, vector_graphic="testlayer", vector_graphic_scale=5, opacity=0.8, is_annotated=True, is_disabled=True, disabled_message="testlayer")
        # This test layer will not have attributes defined other than required fields to test default behavior when attributes left empty
        layer1.site.set([1])
        layer1.themes.set([1])
        # Create a test sublayer
        layer2 = Layer.objects.create(id=2, name="sublayer", layer_type="arcgis", is_sublayer=True)
        layer2.site.set([1])
        layer2.themes.set([1])
        layer1.sublayers.set([layer2])
    
    def test_layer_details(self):
        layer2 = Layer.objects.get(id=2)
        layer2dict = layer2.toDict
        layer2dict["uuid"] = str(layer2dict["uuid"])
        layer2uuid = layer2dict["uuid"]
        layer1 = Layer.objects.get(id=1)
        layer1dict = layer1.toDict
        layer1dict["uuid"] = str(layer1dict["uuid"])
        layer1uuid = layer1dict["uuid"]

        client = APIClient()
        response = client.post("/data_manager/migration/layer_details", {"layers": [layer1uuid, layer2uuid]})
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