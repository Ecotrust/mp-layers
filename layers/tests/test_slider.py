from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from layers.models import *
from layers.serializers import *
from collections.abc import Collection, Mapping
from django.core.cache import cache
import requests
import json

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
                try:
                    match = next(filter(lambda record: record['id'] == child['id'], old_list))
                except StopIteration:
                    self.fail(f"No match found in old_list for child with id {child['id']}")
                for key in child.keys():
                    if not key in ['subLayers', 'type', 'date_modified']:

                        if not child[key] == match[key]:
                            print(child)
                            print(match)
                            print("Key '{}': new:'{}' ; old:'{}'".format(key, child[key], match[key]))


                    elif key == 'type' and (
                            child['type'] in ['checkbox',] and 
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

                dm_layer_response = requests.get('http://localhost:8002/old_manager/get_layer_details/{}'.format(layer['id']))
                ls_layer_response = requests.get('http://localhost:8002/data_manager/get_layer_details/{}'.format(layer['id']))
                old_layer_data = json.loads(dm_layer_response.content)
                new_layer_data = json.loads(ls_layer_response.content)
                # if not len(old_layer_data.keys()) == len(new_layer_data.keys()):
                #     import ipdb; ipdb.set_trace()
                self.assertEqual(old_layer_data.keys(), new_layer_data.keys())
                self.compare_layers(old_layer_data, new_layer_data, index)

    def compare_layers(self, old_layer, new_layer, layer_count):
            for key in old_layer.keys():
                if key not in ['date_modified','subLayers','attributes', 'lookups', 'companion_layers', 'catalog_html', "metadata"]: # objects and dates?
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
                                'source', 'wms_version', 'wms_additional', 'legend', 'legend_title', "legend_subtitle", "data_source", "data_download", "learn_more"
                            ] and old_layer[key] == None and new_layer[key] == ""
                        ) or (
                            #fields are set that have no business being set on parent layers/themes
                            key in [
                                'outline_opacity', 'color', 'fill_opacity', 'graphic', 'arcgis_layers', 'type', 'tiles', 'url', 'kml', 'opacity'
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
                        ) or (
                            # Normalize description line endings
                            key == 'description' and old_layer[key].replace('\r\n', '') == new_layer[key].replace('\r\n', '')
                        ):
                            old_layer[key] = new_layer[key]

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
                    if not key in ['data_notes','disabled_message', 'type']:
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