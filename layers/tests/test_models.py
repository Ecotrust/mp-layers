from django.test import TestCase, RequestFactory, override_settings
from django.utils import timezone
from datetime import date
from layers.models import Theme, Layer, MultilayerAssociation, MultilayerDimension, MultilayerDimensionValue, Companionship, LayerWMS, LayerArcREST, LayerArcFeatureService, LayerVector, LayerXYZ, ChildOrder, AttributeInfo, LookupInfo
from layers.serializers import ThemeSerializer, ThemeExportFixtureSerializer, LayerWMSSerializer, CompanionLayerSerializer, LayerArcRESTSerializer, LayerArcFeatureServiceSerializer, LayerXYZSerializer, LayerVectorSerializer, SubThemeSerializer, ChildOrderSerializer, LayerExportSerializer, AttributeInfoExportSerializer, LookupInfoExportSerializer, LayerWMSExportSerializer, LayerArcRESTExportSerializer, LayerArcFeatureServiceExportSerializer, LayerVectorExportSerializer, LayerXYZExportSerializer
from layers.views import get_portal_catalog_map
from collections.abc import Collection
import json
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from layers.fixture_contract import NODE_FIELDS_KEY, NODE_MODEL_KEY, NODE_RELATIONS_KEY, NODE_SOURCE_PK_KEY, NODE_UUID_KEY
from layers.admin import export_layer_details
from rest_framework import serializers
from unittest.mock import Mock
# request to get data from live site, mung it and make it into v2
class ThemeTest(TestCase):
    def setUp(self):
        site = Site.objects.get(pk=1)
        #NEED TO ADD MORE PARENT_THEME, CHILD_THEME AND LAYERS TO TEST ORDERING BY ID WHEN NAME IS SAME AS WELL
        self.parent_themeA1 = Theme.objects.create(name="Parent Theme A", order=2, slug_name="test")
        self.parent_themeB2 = Theme.objects.create(name="Parent Theme B", order=1)
        self.parent_themeB3 = Theme.objects.create(name="Parent Theme B", order=1)
        self.parent_themeA1.site.add(site)
        self.parent_themeB2.site.add(site)
        self.parent_themeB3.site.add(site)
        # Create child themes and set their parent_theme
        self.child_theme1 = Theme.objects.create(name="Child Theme A", theme_type="radio")
        self.child_theme2 = Theme.objects.create(name="Child Theme B", theme_type="radio")
        self.child_theme3 = Theme.objects.create(name="Child Theme B",theme_type="radio")
        self.child_theme1.site.add(site)
        self.child_theme2.site.add(site)
        self.child_theme3.site.add(site)
        # Create layers
        self.generic_layer1 = Layer.objects.create(
            name="My WMS Layer",
            layer_type='WMS',  

        )   
        self.generic_layer1.site.add(site)
        # Now create a LayerWMS instance referencing the generic_layer
        self.wms_layer1 = LayerWMS.objects.create(
            layer=self.generic_layer1,
            # ... other specific fields for WMS
        )
        self.generic_layer2 = Layer.objects.create(
            name="ArcGis Layer",
            layer_type='ArcREST', 
        )
        self.generic_layer2.site.add(site)
        self.arcgis_layer1 = LayerArcREST.objects.create(
            layer=self.generic_layer2,
        )
        # Create ChildOrders with same order but different names
        
        ChildOrder.objects.create(parent_theme=self.parent_themeA1, content_object=self.child_theme1, order=1)
        ChildOrder.objects.create(parent_theme=self.parent_themeA1, content_object=self.generic_layer1, order=1)
        ChildOrder.objects.create(parent_theme=self.parent_themeB2, content_object=self.child_theme2, order=1)
        ChildOrder.objects.create(parent_theme=self.parent_themeB2, content_object=self.child_theme3, order=1)
        ChildOrder.objects.create(parent_theme=self.parent_themeB2, content_object=self.generic_layer2, order=1)

        # Create sub-child theme
        self.sub_child_theme = Theme.objects.create(name="Sub-Child Theme")
        self.sub_child_theme.site.add(site)
        ChildOrder.objects.create(parent_theme=self.child_theme1, content_object=self.sub_child_theme, order=2)

    def test_theme_hierarchy(self):
        # Test parent-child relationships
        # Serialize the parent themes
        serialized_data1 = ThemeSerializer(self.parent_themeA1).data

        serialized_data2 = ThemeSerializer(self.parent_themeB2).data

        # Extract the ordered children's names and ids for testing
        parent1_children = serialized_data1["layers"]
        parent2_children = serialized_data2["layers"]

        self.assertEqual(parent1_children, [self.child_theme1.id, self.generic_layer1.id])
        self.assertEqual(parent2_children, [self.generic_layer2.id, self.child_theme2.id, self.child_theme3.id])

    def test_parent_theme_ordering(self):
        # Get the ContentType for the Theme model
        theme_content_type = ContentType.objects.get_for_model(Theme)

        # Fetch all Theme IDs that are referenced as a child in ChildOrder, specifically filtering by the Theme ContentType
        child_theme_ids = ChildOrder.objects.filter(content_type=theme_content_type).values_list('object_id', flat=True)
        # Fetch all themes that are not in the list of child theme IDs
        parent_themes = Theme.objects.exclude(id__in=child_theme_ids).order_by('order')

        # Serialize the parent themes
        serialized_data = ThemeSerializer(parent_themes, many=True).data

        # Extract the names and ids for testing
        serialized_name_ids = [theme.get('id', 0) for theme in serialized_data]

        # Define the expected order based on name and id
        expected_order = [
            (self.parent_themeB2.id),  
            (self.parent_themeB3.id), 
            (self.parent_themeA1.id)  
        ]

        # Assert the order
        self.assertEqual(serialized_name_ids, expected_order)
    
    def test_attributes(self):
        theme = ThemeSerializer(self.parent_themeA1).data

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
        "type": layer_type,
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
        "tiles": None,
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
       
class LayerExportSerializerTest(TestCase):
    def test_layer_export_contains_expected_fields_with_appropriate_types(self):

        expected_export_data = {
            'name': 'Export Test Layer',
            'layer_type': 'WMS',
            'url': 'https://example.com/layer',
            'last_success_status': str(timezone.now()),
            'last_http_status': '200',
            'opacity': 0.75,
            'is_disabled': True,
            'disabled_message': 'temporarily disabled',
            'is_visible': False,
            'search_query': True,
            'geoportal_id': 'geo-123',
            'catalog_name': 'Catalog Name',
            'catalog_id': 'catalog-123',
            'proxy_url': True,
            'shareable_url': False,
            'utfurl': 'utfurl-value',
            'show_legend': False,
            'legend': 'https://example.com/legend.png',
            'legend_title': 'Legend title',
            'legend_subtitle': 'Legend subtitle',
            'description': 'Layer description',
            'overview': 'Layer overview',
            'data_source': 'Source',
            'data_notes': 'Notes',
            'data_publish_date': str(date(2024, 1, 2)),
            'metadata': 'https://example.com/metadata',
            'source': 'https://example.com/source',
            'bookmark': 'https://example.com/bookmark',
            'kml': 'https://example.com/kml',
            'data_download': 'https://example.com/data',
            'learn_more': 'https://example.com/learn',
            'map_tiles': 'https://example.com/tiles',
            'label_field': 'name',
            'attribute_event': 'mouseover',
            'attribute_fields': [
                {
                    'display_name': 'Depth',
                    'field_name': 'depth_m',
                    'precision': 3,
                    'order': 2,
                    'preserve_format': True,
                },
                {
                    'display_name': 'Temperature',
                    'field_name': 'temp_c',
                    'precision': 1,
                    'order': 1,
                    'preserve_format': False,
                },
            ],
            'annotated': True,
            'compress_display': True,
            'mouseover_field': 'hover_field',
            'espis_enabled': True,
            'espis_search': 'search term',
            'espis_region': 'Mid Atlantic',
            'minZoom': 3.5,
            'maxZoom': 8.25,
        }

        create_data = {
            field_name: (
                date.fromisoformat(value)
                if field_name == 'data_publish_date' and isinstance(value, str)
                else value
            )
            for field_name, value in expected_export_data.items()
            if field_name not in {'uuid', 'date_created', 'date_modified', 'attribute_fields'}
        }

        attribute_info_records = [
            AttributeInfo.objects.create(**field_data)
            for field_data in expected_export_data['attribute_fields']
        ]

        layer = Layer.objects.create(**create_data)
        layer.attribute_fields.set(attribute_info_records)

        expected_attribute_infos_for_serializer = sorted(
            attribute_info_records,
            key=lambda x: x.order,
        )
        expected_export_data['attribute_fields'] = [
            {
                'pk': attribute_info.pk,
                'uuid': str(attribute_info.uuid),
            }
            for attribute_info in expected_attribute_infos_for_serializer
        ]

        serializer_data = LayerExportSerializer(layer).data

        expected_keys = set(expected_export_data.keys())
        for assigned_key in ['uuid', 'date_created', 'date_modified', 'slug_name']:
            if assigned_key in serializer_data:
                expected_keys.add(assigned_key)

        self.assertEqual(len(serializer_data), len(expected_keys))
        self.assertEqual(set(serializer_data.keys()), expected_keys)

        # for field_name, expected_value in expected_export_data.items():
        for field_name in expected_keys:
            self.assertIn(field_name, serializer_data)
            if field_name in {'uuid', 'date_created', 'date_modified', 'slug_name'}:
                self.assertIsInstance(serializer_data[field_name], str)
            else:
                expected_value = expected_export_data[field_name]
                self.assertEqual(serializer_data[field_name], expected_value)
                self.assertIsInstance(serializer_data[field_name], type(expected_value) if expected_value is not None else type(None))


class LayerExportFixtureSerializerTest(TestCase):
    def test_layer_export_concurrent_layers(self):
        layer_a = Layer.objects.create(name='Concurrent Layer A', layer_type='WMS')
        layer_b = Layer.objects.create(name='Concurrent Layer B', layer_type='WMS')
        shared_companion = Layer.objects.create(name='Shared Companion', layer_type='WMS')

        companionship_a = Companionship.objects.create(layer=layer_a)
        companionship_a.companions.add(shared_companion)
        companionship_b = Companionship.objects.create(layer=layer_b)
        companionship_b.companions.add(shared_companion)

        selected_layers = Layer.all_objects.filter(
            pk__in=[layer_a.pk, layer_b.pk],
        ).order_by('pk')
        expected_fixture = []
        seen_rows = set()
        for layer in selected_layers:
            for row in layer.to_export_dict():
                row_key = (row[NODE_MODEL_KEY], row[NODE_SOURCE_PK_KEY])
                if row_key not in seen_rows:
                    seen_rows.add(row_key)
                    expected_fixture.append(row)

        response = export_layer_details(Mock(), Mock(), selected_layers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), expected_fixture)
        shared_companion_rows = [
            row for row in expected_fixture
            if row[NODE_MODEL_KEY] == 'layers.layer'
            and row[NODE_SOURCE_PK_KEY] == shared_companion.pk
        ]
        self.assertEqual(len(shared_companion_rows), 1)


class ThemeExportFixtureSerializerTest(TestCase):
    def _rows_for_model(self, fixture_data, model_label):
        return [row for row in fixture_data if row[NODE_MODEL_KEY] == model_label]

    def _assert_refers_to(self, relation, instance):
        self.assertEqual(
            relation,
            {
                NODE_MODEL_KEY: instance._meta.label_lower,
                NODE_SOURCE_PK_KEY: instance.pk,
                NODE_UUID_KEY: str(instance.uuid),
            },
        )

    def test_theme_export_fixture_serializes_recursive_children_and_deduplicates(self):
        root_theme = Theme.objects.create(name='Root Theme', display_name='Root Theme')
        child_theme = Theme.objects.create(name='Child Theme', display_name='Child Theme')
        shared_layer = Layer.objects.create(name='Shared Layer', layer_type='WMS')

        root_child_theme_order = ChildOrder.objects.create(
            parent_theme=root_theme,
            content_object=child_theme,
            order=1,
        )
        root_layer_order = ChildOrder.objects.create(
            parent_theme=root_theme,
            content_object=shared_layer,
            order=2,
        )
        child_layer_order = ChildOrder.objects.create(
            parent_theme=child_theme,
            content_object=shared_layer,
            order=1,
        )

        fixture_data = ThemeExportFixtureSerializer(root_theme).data
        theme_rows = self._rows_for_model(fixture_data, 'layers.theme')
        child_order_rows = self._rows_for_model(fixture_data, 'layers.childorder')
        layer_rows = self._rows_for_model(fixture_data, 'layers.layer')

        self.assertEqual(len(theme_rows), 2)
        self.assertEqual(len(child_order_rows), 3)
        self.assertEqual(len(layer_rows), 1)
        self.assertEqual(
            set(theme_rows[0][NODE_FIELDS_KEY]),
            {
                field.name
                for field in Theme._meta.concrete_fields
                if field.name not in {'id', 'site'}
            },
        )
        self.assertNotIn('site', theme_rows[0][NODE_FIELDS_KEY])

        self._assert_refers_to(
            child_order_rows[0][NODE_RELATIONS_KEY]['parent_theme'],
            root_theme,
        )
        self._assert_refers_to(
            child_order_rows[0][NODE_RELATIONS_KEY]['content_object'],
            child_theme,
        )
        self._assert_refers_to(
            child_order_rows[1][NODE_RELATIONS_KEY]['content_object'],
            shared_layer,
        )
        self._assert_refers_to(
            child_order_rows[2][NODE_RELATIONS_KEY]['content_object'],
            shared_layer,
        )
        self.assertEqual(
            child_order_rows[0][NODE_FIELDS_KEY]['order'],
            root_child_theme_order.order,
        )
        self.assertEqual(
            child_order_rows[1][NODE_FIELDS_KEY]['order'],
            root_layer_order.order,
        )
        self.assertEqual(
            child_order_rows[2][NODE_FIELDS_KEY]['order'],
            child_layer_order.order,
        )

    def test_theme_export_fixture_stops_at_self_referential_child_order(self):
        theme = Theme.objects.create(name='Self Referencing Theme', display_name='Self Referencing Theme')
        child_order = ChildOrder.objects.create(
            parent_theme=theme,
            content_object=theme,
            order=1,
        )

        fixture_data = ThemeExportFixtureSerializer(theme).data

        self.assertEqual(len(self._rows_for_model(fixture_data, 'layers.theme')), 1)
        child_order_rows = self._rows_for_model(fixture_data, 'layers.childorder')
        self.assertEqual(len(child_order_rows), 1)
        self._assert_refers_to(
            child_order_rows[0][NODE_RELATIONS_KEY]['parent_theme'],
            theme,
        )
        self._assert_refers_to(
            child_order_rows[0][NODE_RELATIONS_KEY]['content_object'],
            theme,
        )
        self.assertEqual(child_order_rows[0][NODE_FIELDS_KEY]['order'], child_order.order)

    def test_theme_export_fixture_deduplicates_layer_with_multiple_child_orders(self):
        theme = Theme.objects.create(name='Repeated Layer Theme', display_name='Repeated Layer Theme')
        layer = Layer.objects.create(name='Repeated Layer', layer_type='WMS')
        first_child_order = ChildOrder.objects.create(
            parent_theme=theme,
            content_object=layer,
            order=1,
        )
        second_child_order = ChildOrder.objects.create(
            parent_theme=theme,
            content_object=layer,
            order=2,
        )

        fixture_data = ThemeExportFixtureSerializer(theme).data

        self.assertEqual(len(self._rows_for_model(fixture_data, 'layers.theme')), 1)
        self.assertEqual(len(self._rows_for_model(fixture_data, 'layers.layer')), 1)
        child_order_rows = self._rows_for_model(fixture_data, 'layers.childorder')
        self.assertEqual(len(child_order_rows), 2)
        self.assertEqual(
            [row[NODE_FIELDS_KEY]['order'] for row in child_order_rows],
            [first_child_order.order, second_child_order.order],
        )
        for row in child_order_rows:
            self._assert_refers_to(row[NODE_RELATIONS_KEY]['content_object'], layer)

    def test_layer_export_fixture_contains_attribute_infos_followed_by_layer(self):

        create_data = {
            'name': 'Export Fixture Layer',
            'layer_type': 'WMS',
            'url': 'https://example.com/layer',
            'last_success_status': timezone.now(),
            'last_http_status': '200',
            'opacity': 0.75,
            'is_disabled': True,
            'disabled_message': 'temporarily disabled',
            'is_visible': False,
            'search_query': True,
            'geoportal_id': 'geo-123',
            'catalog_name': 'Catalog Name',
            'catalog_id': 'catalog-123',
            'proxy_url': True,
            'shareable_url': False,
            'utfurl': 'utfurl-value',
            'show_legend': False,
            'legend': 'https://example.com/legend.png',
            'legend_title': 'Legend title',
            'legend_subtitle': 'Legend subtitle',
            'description': 'Layer description',
            'overview': 'Layer overview',
            'data_source': 'Source',
            'data_notes': 'Notes',
            'data_publish_date': date(2024, 1, 2),
            'metadata': 'https://example.com/metadata',
            'source': 'https://example.com/source',
            'bookmark': 'https://example.com/bookmark',
            'kml': 'https://example.com/kml',
            'data_download': 'https://example.com/data',
            'learn_more': 'https://example.com/learn',
            'map_tiles': 'https://example.com/tiles',
            'label_field': 'name',
            'attribute_event': 'mouseover',
            'annotated': True,
            'compress_display': True,
            'mouseover_field': 'hover_field',
            'espis_enabled': True,
            'espis_search': 'search term',
            'espis_region': 'Mid Atlantic',
            'minZoom': 3.5,
            'maxZoom': 8.25,
        }

        attribute_info_records = [
            AttributeInfo.objects.create(
                display_name='Depth',
                field_name='depth_m',
                precision=3,
                order=2,
                preserve_format=True,
            ),
            AttributeInfo.objects.create(
                display_name='Temperature',
                field_name='temp_c',
                precision=1,
                order=1,
                preserve_format=False,
            ),
        ]

        layer = Layer.objects.create(**create_data)
        layer.attribute_fields.set(attribute_info_records)

        serializer_data = LayerExportSerializer(layer).data
        fixture_data = layer.to_export_dict()

        expected_attribute_infos_for_fixture = sorted(
            attribute_info_records,
            key=lambda x: (x.order, x.display_name, x.pk),
        )
        expected_attribute_refs = [
            {
                NODE_MODEL_KEY: 'layers.attributeinfo',
                NODE_SOURCE_PK_KEY: x.pk,
                NODE_UUID_KEY: str(x.uuid),
            }
            for x in expected_attribute_infos_for_fixture
        ]

        self.assertIsInstance(fixture_data, list)
        self.assertEqual(len(fixture_data), len(expected_attribute_infos_for_fixture) + 1)

        for fixture_row, expected_attribute_info in zip(
            fixture_data[:-1],
            expected_attribute_infos_for_fixture,
        ):
            self.assertEqual(fixture_row[NODE_MODEL_KEY], 'layers.attributeinfo')
            self.assertEqual(fixture_row[NODE_SOURCE_PK_KEY], expected_attribute_info.pk)
            self.assertEqual(fixture_row[NODE_UUID_KEY], str(expected_attribute_info.uuid))
            self.assertEqual(
                fixture_row[NODE_FIELDS_KEY],
                AttributeInfoExportSerializer(expected_attribute_info).data,
            )
            self.assertEqual(fixture_row[NODE_RELATIONS_KEY], {})

        expected_layer_fields = dict(serializer_data)
        expected_layer_fields.pop('attribute_fields', None)

        self.assertEqual(fixture_data[-1][NODE_MODEL_KEY], 'layers.layer')
        self.assertEqual(fixture_data[-1][NODE_SOURCE_PK_KEY], layer.pk)
        self.assertEqual(fixture_data[-1][NODE_UUID_KEY], str(layer.uuid))
        self.assertEqual(fixture_data[-1][NODE_FIELDS_KEY], expected_layer_fields)
        self.assertEqual(
            fixture_data[-1][NODE_RELATIONS_KEY],
            {
                'attribute_fields': expected_attribute_refs,
            },
        )

    def test_layer_export_fixture_includes_lookup_and_specific_instance_rows_for_vector_layer(self):
        layer = Layer.objects.create(
            name='Vector Fixture Layer',
            layer_type='Vector',
        )
        lookup_b = LookupInfo.objects.create(value='B')
        lookup_a = LookupInfo.objects.create(value='A')
        vector = LayerVector.objects.create(
            layer=layer,
            lookup_field='status',
            custom_style='color',
        )
        vector.lookup_table.set([lookup_b, lookup_a])

        fixture_data = layer.to_export_dict()

        self.assertEqual(len(fixture_data), 4)

        expected_lookup_infos = sorted([lookup_a, lookup_b], key=lambda x: x.pk)
        for fixture_row, expected_lookup in zip(fixture_data[:2], expected_lookup_infos):
            self.assertEqual(fixture_row[NODE_MODEL_KEY], 'layers.lookupinfo')
            self.assertEqual(fixture_row[NODE_SOURCE_PK_KEY], expected_lookup.pk)
            self.assertEqual(fixture_row[NODE_UUID_KEY], str(expected_lookup.uuid))
            self.assertEqual(fixture_row[NODE_FIELDS_KEY], LookupInfoExportSerializer(expected_lookup).data)
            self.assertEqual(fixture_row[NODE_RELATIONS_KEY], {})

        layer_row = fixture_data[2]
        self.assertEqual(layer_row[NODE_MODEL_KEY], 'layers.layer')
        self.assertEqual(layer_row[NODE_SOURCE_PK_KEY], layer.pk)
        self.assertEqual(layer_row[NODE_UUID_KEY], str(layer.uuid))
        self.assertEqual(layer_row[NODE_RELATIONS_KEY]['attribute_fields'], [])

        vector_row = fixture_data[3]
        self.assertEqual(vector_row[NODE_MODEL_KEY], 'layers.layervector')
        self.assertEqual(vector_row[NODE_SOURCE_PK_KEY], vector.pk)
        self.assertIsNone(vector_row[NODE_UUID_KEY])
        self.assertEqual(
            vector_row[NODE_RELATIONS_KEY]['layer'],
            {
                NODE_MODEL_KEY: 'layers.layer',
                NODE_SOURCE_PK_KEY: layer.pk,
                NODE_UUID_KEY: str(layer.uuid),
            },
        )
        self.assertEqual(
            vector_row[NODE_RELATIONS_KEY]['lookup_table'],
            [
                {
                    NODE_MODEL_KEY: 'layers.lookupinfo',
                    NODE_SOURCE_PK_KEY: lookup.pk,
                    NODE_UUID_KEY: str(lookup.uuid),
                }
                for lookup in expected_lookup_infos
            ],
        )

class AttributeInfoExportSerializerTest(TestCase):

    def test_attribute_info_export_contains_expected_fields_with_appropriate_types(self):
        expected_export_data = {
            'display_name': 'Depth',
            'field_name': 'depth_m',
            'precision': 3,
            'order': 7,
            'preserve_format': True,
        }

        attribute_info = AttributeInfo.objects.create(**expected_export_data)
        serializer_data = AttributeInfoExportSerializer(attribute_info).data

        expected_keys = set(expected_export_data.keys())
        expected_keys.add('uuid')

        self.assertEqual(len(serializer_data), len(expected_keys))
        self.assertEqual(set(serializer_data.keys()), expected_keys)

        for field_name in expected_keys:
            self.assertIn(field_name, serializer_data)
            if field_name == 'uuid':
                self.assertIsInstance(serializer_data[field_name], str)
            else:
                expected_value = expected_export_data[field_name]
                self.assertEqual(serializer_data[field_name], expected_value)
                self.assertIsInstance(serializer_data[field_name], type(expected_value) if expected_value is not None else type(None))


class LookupInfoExportSerializerTest(TestCase):

    def test_lookup_info_export_contains_expected_fields_with_appropriate_types(self):
        lookup_info = LookupInfo.objects.create(
            value='open',
            description='Open area',
            color='#112233',
            stroke_color='#445566',
            stroke_width=3,
            dashstyle='dash',
            fill=True,
            graphic='https://example.com/marker.png',
            graphic_scale=1.25,
        )

        expected_export_data = {
            'value': lookup_info.value,
            'description': lookup_info.description,
            'color': lookup_info.color,
            'stroke_color': lookup_info.stroke_color,
            'stroke_width': lookup_info.stroke_width,
            'dashstyle': lookup_info.dashstyle,
            'fill': lookup_info.fill,
            'graphic': lookup_info.graphic,
            'graphic_scale': lookup_info.graphic_scale,
        }

        serializer_data = LookupInfoExportSerializer(lookup_info).data

        expected_keys = set(expected_export_data.keys())
        expected_keys.add('uuid')

        self.assertEqual(len(serializer_data), len(expected_keys))
        self.assertEqual(set(serializer_data.keys()), expected_keys)

        for field_name in expected_keys:
            self.assertIn(field_name, serializer_data)
            if field_name == 'uuid':
                self.assertIsInstance(serializer_data[field_name], str)
            else:
                expected_value = expected_export_data[field_name]
                self.assertEqual(serializer_data[field_name], expected_value)
                self.assertIsInstance(serializer_data[field_name], type(expected_value) if expected_value is not None else type(None))


class SpecificInstanceExportSerializerTest(TestCase):
    def _create_base_layer(self, name, layer_type):
        return Layer.objects.create(name=name, layer_type=layer_type)

    def test_layer_wms_export_serializer(self):
        layer = self._create_base_layer('WMS Export Layer', 'WMS')
        instance = LayerWMS.objects.create(
            layer=layer,
            query_by_point=True,
            wms_help=True,
            wms_slug='wms-slug',
            wms_version='1.3.0',
            wms_format='image/png',
            wms_srs='EPSG:3857',
            wms_timing='2024-01-01',
            wms_time_item='TIME',
            wms_styles='default',
            wms_additional='&token=abc',
            wms_info=True,
            wms_info_format='application/json',
        )

        serializer_data = LayerWMSExportSerializer(instance).data
        expected = {
            'layer': layer.pk,
            'query_by_point': True,
            'wms_help': True,
            'wms_slug': 'wms-slug',
            'wms_version': '1.3.0',
            'wms_format': 'image/png',
            'wms_srs': 'EPSG:3857',
            'wms_timing': '2024-01-01',
            'wms_time_item': 'TIME',
            'wms_styles': 'default',
            'wms_additional': '&token=abc',
            'wms_info': True,
            'wms_info_format': 'application/json',
        }

        self.assertEqual(serializer_data, expected)

    def test_layer_arc_rest_export_serializer(self):
        layer = self._create_base_layer('ArcREST Export Layer', 'ArcRest')
        instance = LayerArcREST.objects.create(
            layer=layer,
            arcgis_layers='0,1,2',
            password_protected=True,
            disable_arcgis_attributes=True,
            query_by_point=False,
        )

        serializer_data = LayerArcRESTExportSerializer(instance).data
        expected = {
            'layer': layer.pk,
            'arcgis_layers': '0,1,2',
            'password_protected': True,
            'disable_arcgis_attributes': True,
            'query_by_point': False,
        }

        self.assertEqual(serializer_data, expected)

    def test_layer_vector_export_serializer(self):
        layer = self._create_base_layer('Vector Export Layer', 'Vector')
        lookup_a = LookupInfo.objects.create(value='A')
        lookup_b = LookupInfo.objects.create(value='B')
        instance = LayerVector.objects.create(
            layer=layer,
            custom_style='color',
            outline_width=3,
            outline_color='#112233',
            outline_opacity=0.6,
            fill_opacity=0.4,
            color='#445566',
            point_radius=9,
            graphic='https://example.com/icon.png',
            graphic_scale=1.5,
            lookup_field='status',
        )
        instance.lookup_table.set([lookup_b, lookup_a])

        serializer_data = LayerVectorExportSerializer(instance).data
        expected = {
            'layer': layer.pk,
            'custom_style': 'color',
            'outline_width': 3,
            'outline_color': '#112233',
            'outline_opacity': 0.6,
            'fill_opacity': 0.4,
            'color': '#445566',
            'point_radius': 9,
            'graphic': 'https://example.com/icon.png',
            'graphic_scale': 1.5,
            'lookup_field': 'status',
            'lookup_table': sorted([lookup_a.pk, lookup_b.pk]),
        }

        self.assertEqual(serializer_data, expected)

    def test_layer_arc_feature_service_export_serializer(self):
        layer = self._create_base_layer('ArcFeature Export Layer', 'ArcFeatureServer')
        lookup = LookupInfo.objects.create(value='open')
        instance = LayerArcFeatureService.objects.create(
            layer=layer,
            arcgis_layers='3,4',
            password_protected=False,
            disable_arcgis_attributes=True,
            custom_style='random',
            outline_width=2,
            outline_color='#778899',
            outline_opacity=0.5,
            fill_opacity=0.25,
            color='#AA5500',
            point_radius=5,
            graphic='https://example.com/feature-icon.png',
            graphic_scale=2.0,
            lookup_field='state',
        )
        instance.lookup_table.set([lookup])

        serializer_data = LayerArcFeatureServiceExportSerializer(instance).data
        expected = {
            'layer': layer.pk,
            'arcgis_layers': '3,4',
            'password_protected': False,
            'disable_arcgis_attributes': True,
            'custom_style': 'random',
            'outline_width': 2,
            'outline_color': '#778899',
            'outline_opacity': 0.5,
            'fill_opacity': 0.25,
            'color': '#AA5500',
            'point_radius': 5,
            'graphic': 'https://example.com/feature-icon.png',
            'graphic_scale': 2.0,
            'lookup_field': 'state',
            'lookup_table': [lookup.pk],
        }

        self.assertEqual(serializer_data, expected)

    def test_layer_xyz_export_serializer(self):
        layer = self._create_base_layer('XYZ Export Layer', 'XYZ')
        instance = LayerXYZ.objects.create(
            layer=layer,
            query_by_point=True,
        )

        serializer_data = LayerXYZExportSerializer(instance).data
        expected = {
            'layer': layer.pk,
            'query_by_point': True,
        }

        self.assertEqual(serializer_data, expected)




class CompanionLayerTest(TestCase):
    def setUp(self):
        site = Site.objects.get(pk=1)
        self.parent_theme = Theme.objects.create(name="Parent Theme")
        self.parent_theme.site.add(site)
        # Create layer instances
        self.layer1 = Layer.objects.create(
            name="Layer 1",
            layer_type='WMS',  
            slug_name="test",
        )   

        self.wms_layer1 = LayerWMS.objects.create(
            layer=self.layer1,
        )
        self.layer2 = Layer.objects.create(
            name="Layer 2",
            layer_type='WMS',  
        )   

        self.wms_layer2 = LayerWMS.objects.create(
            layer=self.layer2,
        )
        self.layer3 = Layer.objects.create(
            name="Layer 3",
            layer_type='WMS',  
        )   

        self.wms_layer3 = LayerWMS.objects.create(
            layer=self.layer3,
            # ... other specific fields for WMS
        )
        self.layer1.site.add(site)
        self.layer2.site.add(site)
        self.layer3.site.add(site)
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
        serialized_layer1_data = LayerWMSSerializer(self.wms_layer1).data

        serialized_layer2_data = LayerWMSSerializer(self.wms_layer2).data

        self.assertIsNone(serialized_layer1_data["parent"])
        self.assertIsNone(serialized_layer2_data["parent"])
        self.assertEqual(serialized_layer1_data["companion_layers"][0]["parent"], self.layer1.id)
    def test_serialized_companion_data(self):
        serialized_layer1_data = LayerWMSSerializer(self.wms_layer1).data

        self.assertIn("catalog_html", serialized_layer1_data)
        self.assertIn("data_url", serialized_layer1_data)
        self.assertIn("attributes", serialized_layer1_data)
        self.assertIn("lookups", serialized_layer1_data)

class LayerSerializerTest(TestCase):
    def setUp(self):
        # First Level
        site = Site.objects.get(pk=1)
        self.parent_theme = Theme.objects.create(name="Parent Theme")
        self.parent_theme.site.add(site)
        # Second Level
        self.sub_theme = Theme.objects.create(name="Sub Theme", theme_type="radio")
        self.sub_theme.site.add(site)
        self.layer1 = Layer.objects.create(
            name="testlayer",
            layer_type='WMS',  
        ) 
        self.wms_layer1 = LayerWMS.objects.create(
            layer=self.layer1,
        )  
        self.layer1.site.add(site)
        # Third Level
        self.layer2 = Layer.objects.create(
            name="testlayer2",
            layer_type='WMS',  
        ) 
        self.wms_layer2 = LayerWMS.objects.create(
            layer=self.layer2,
        )  
        self.layer2.site.add(site)
        self.sub_sub_theme = Theme.objects.create(name="Sub Sub Theme", theme_type="radio")
        self.sub_sub_theme.site.add(site)
        # Fourth Level
        self.layer3 = Layer.objects.create(
            name="testlayer3",
            layer_type='WMS',  
        ) 
        self.wms_layer3 = LayerWMS.objects.create(
            layer=self.layer3,
        )  
        self.layer3.site.add(site)
        ChildOrder.objects.create(parent_theme=self.parent_theme, content_object=self.sub_theme, order = 1)
        ChildOrder.objects.create(parent_theme=self.parent_theme, content_object=self.layer1, order=2)

        ChildOrder.objects.create(parent_theme=self.sub_theme, content_object=self.layer2, order=1)
        ChildOrder.objects.create(parent_theme=self.sub_theme, content_object=self.sub_sub_theme, order=2)

        ChildOrder.objects.create(parent_theme=self.sub_sub_theme, content_object=self.layer3, order=1)

    def test_serialize_second_third_layer_parent(self):
        # Direct descendents of the parent theme should not have a parent when serialized.
        serialized_layer1_data = LayerWMSSerializer(self.wms_layer1).data
        self.assertIsNone(serialized_layer1_data["parent"])

        # Third level layers should have their direct parent serialized.
        serialized_layer2_data = LayerWMSSerializer(self.wms_layer2).data
        self.assertEqual(self.sub_theme.id, serialized_layer2_data["parent"]["id"])

    def test_serialize_fourth_and_beyond_layer_parent(self):
        # Layers fourth level and beyond should point to the second layer ancestor.
        # AKA should skip past any intermediary parents until the second layer.
        serialized_layer3_data = LayerWMSSerializer(self.wms_layer3).data 
        self.assertEqual(self.sub_theme.id, serialized_layer3_data["parent"]["id"])

class SubThemeSerializerTest(TestCase):
    def setUp(self):
        # Create a test subtheme instance
        site = Site.objects.get(pk=1)
        self.parent_theme = Theme.objects.create(name="Parent Theme")
        self.parent_theme.site.add(site)
        self.sub_theme = Theme.objects.create(name="Sub Theme", theme_type="radio")
        self.sub_theme.site.add(site)
        self.sub_sub_theme = Theme.objects.create(name="Subsubtheme", theme_type="radio")
        self.sub_sub_theme.site.add(site)
        self.layer2 = Layer.objects.create(
            name="arcgis",
            layer_type='ArcRest',  
        ) 
        self.arcgis_layer2 = LayerArcREST.objects.create(
            layer=self.layer2,
        )  
        self.layer2.site.add(site)
        self.layer1 = Layer.objects.create(
            name="testlayer",
            layer_type='WMS',  
        ) 
        self.wms_layer1 = LayerWMS.objects.create(
            layer=self.layer1,
        )  
        self.layer1.site.add(site)
        self.layer3 = Layer.objects.create(
            name="testlayer3",
            layer_type='WMS',  
        ) 
        self.wms_layer3 = LayerWMS.objects.create(
            layer=self.layer3,
        )  
        self.layer3.site.add(site)

        self.layer4 = Layer.objects.create(
            name="testlayer4",
            layer_type='WMS',  
        ) 
        self.wms_layer4 = LayerWMS.objects.create(
            layer=self.layer4,
        )  
        self.layer4.site.add(site)
        self.layer5 = Layer.objects.create(
            name="testlayer5",
            layer_type='WMS',  
        ) 
        self.wms_layer5 = LayerWMS.objects.create(
            layer=self.layer5,
        )  
        self.layer5.site.add(site)

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

        serialized_layer_data = LayerWMSSerializer(self.wms_layer3).data
        verify_serializer_v1_output(self, serialized_subtheme_data, name=self.sub_theme.name, layer_type=self.sub_theme.theme_type, order=1)

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
        site = Site.objects.get(pk=1)
        self.theme1 = Theme.objects.create(name="test", order=1)
        self.theme1.site.add(site)
        self.theme2 = Theme.objects.create(name="test2", order=2)
        self.theme2.site.add(site)
       # Create layers
        self.layer1 = Layer.objects.create(
            name="testlayer",
            layer_type='WMS',  
        ) 
        self.wms_layer1 = LayerWMS.objects.create(
            layer=self.layer1,
        )  
        self.layer1.site.add(site)
        self.layer2 = Layer.objects.create(
            name="testlayer2",
            layer_type='WMS',  
        ) 
        self.wms_layer2 = LayerWMS.objects.create(
            layer=self.layer2,
            wms_slug="hi", wms_version="hello", wms_format="pusheen", wms_srs="world", 
                wms_styles="style", wms_timing="hullo", wms_time_item="ello", wms_additional="star", wms_info=True, wms_info_format="test"
        )  
        self.layer2.site.add(site)
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
        layer1_actual_data = LayerWMSSerializer(self.wms_layer1).data
        layer2_actual_data = LayerWMSSerializer(self.wms_layer2).data

        # Check that the WMS specific attributes exist
        
        verify_serializer_v1_output(self, layer1_actual_data, name=self.layer1.name, layer_type="WMS", order=1)
        verify_serializer_v1_output(self, layer2_actual_data, name=self.layer2.name, layer_type="WMS", order=1, wms_slug="hi", wms_version="hello", wms_format="pusheen", wms_srs="world", 
                                              wms_styles="style", wms_timing="hullo", wms_time_item="ello", wms_additional="star", wms_info=True, wms_info_format="test")

class ArcRESTLayerTest(TestCase):
    def setUp(self):
        site = Site.objects.get(pk=1)
        self.theme1 = Theme.objects.create(name="test")
        self.theme1.site.add(site)
        self.theme2 = Theme.objects.create(name="test2")
        self.theme2.site.add(site)
       # Create layers
        self.layer1 = Layer.objects.create(
            name="testlayer",
            layer_type='ArcRest',  
        ) 
        self.arcrest_layer1 = LayerArcREST.objects.create(
            layer=self.layer1,     
        )  
        self.layer1.site.add(site)
        self.layer2 = Layer.objects.create(
            name="testlayer2",
            layer_type='ArcRest',  
        ) 
        self.arcrest_layer2 = LayerArcREST.objects.create(
            layer=self.layer2,
            arcgis_layers="19", password_protected=True, query_by_point=True, disable_arcgis_attributes=True,
        )  
        self.layer2.site.add(site)
        self.layer3 = Layer.objects.create(
            name="testlayer3",
            layer_type='ArcRest',  
        ) 
        self.arcrest_layer3 = LayerArcREST.objects.create(
            layer=self.layer3,
        )  
        self.layer3.site.add(site)
        self.companionship = Companionship.objects.create(layer=self.layer1)
        self.companionship.companions.add(self.layer2)
        # Create layer orders
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer1, order=2)
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer2, order=1)
        ChildOrder.objects.create(parent_theme=self.theme2, content_object=self.layer1, order=1)
    
    def test_layer_attributes(self):
        layer1_actual_data = LayerArcRESTSerializer(self.arcrest_layer1).data
        layer2_actual_data = LayerArcRESTSerializer(self.arcrest_layer2).data

        verify_serializer_v1_output(self, layer1_actual_data, name=self.layer1.name, layer_type="ArcRest", order=1)
        verify_serializer_v1_output(self, layer2_actual_data, name=self.layer2.name, layer_type="ArcRest", order=1, arcgis_layers="19", password_protected=True, query_by_point=True, disable_arcgis_attributes=True)
        
class ArcFeatureServiceLayerTest(TestCase):
    def setUp(self):
        site = Site.objects.get(pk=1)
        self.theme1 = Theme.objects.create(name="test")
        self.theme1.site.add(site)
       # Create layers
        self.layer1 = Layer.objects.create(
            name="testlayer",
            layer_type='ArcFeatureServer',  
        ) 
        self.arc_layer1 = LayerArcFeatureService.objects.create(
            layer=self.layer1,
        )  
        self.layer1.site.add(site)
        self.layer2 = Layer.objects.create(
            name="testlayer2",
            layer_type='ArcFeatureServer',  
        ) 
        self.arc_layer2 = LayerArcFeatureService.objects.create(
            layer=self.layer2,
            arcgis_layers="19", password_protected=True,  disable_arcgis_attributes=True,
                                                            custom_style="test", outline_width=5, outline_color="blue", outline_opacity=5.0,
                                                            fill_opacity=5.0, color="blue", point_radius=5, graphic="Test", graphic_scale=5.0, opacity=5.0
        )  
        self.layer2.site.add(site)
        self.companionship = Companionship.objects.create(layer=self.layer1)
        self.companionship.companions.add(self.layer2)
        # Create layer orders
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer1, order=2)
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer2, order=1)

    
    def test_layer_attributes(self):
        layer1_actual_data = LayerArcFeatureServiceSerializer(self.arc_layer1).data
        layer2_actual_data = LayerArcFeatureServiceSerializer(self.arc_layer2).data

        verify_serializer_v1_output(self, layer1_actual_data, name=self.layer1.name, layer_type="ArcFeatureServer", order=2)
        verify_serializer_v1_output(self, layer2_actual_data, name=self.layer2.name, layer_type="ArcFeatureServer", order=1, arcgis_layers="19", password_protected=True, disable_arcgis_attributes=True,
                                                            custom_style="test", outline_width=5, outline_color="blue", outline_opacity=5.0,
                                                            fill_opacity=5.0, color="blue", point_radius=5, graphic="Test", graphic_scale=5.0, opacity=5.0)

class XYZLayerTest(TestCase):
    def setUp(self):
        site = Site.objects.get(pk=1)
        self.theme1 = Theme.objects.create(name="test")
        self.theme1.site.add(site)
        self.layer1 = Layer.objects.create(
            name="testlayer",
            layer_type='XYZ',  
        ) 
        self.xyz_layer1 = LayerXYZ.objects.create(
            layer=self.layer1,
        )  
        self.layer1.site.add(site)
        self.layer2 = Layer.objects.create(
            name="testlayer2",
            layer_type='XYZ',  
        ) 
        self.xyz_layer2 = LayerXYZ.objects.create(
            layer=self.layer2,
            query_by_point=True
        )  
        self.layer2.site.add(site)
        self.companionship = Companionship.objects.create(layer=self.layer1)
        self.companionship.companions.add(self.layer2)
        # Create layer orders
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer1, order=2)
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer2, order=1)

    def test_layer_attributes(self):
        layer1_actual_data = LayerXYZSerializer(self.xyz_layer1).data
        layer2_actual_data = LayerXYZSerializer(self.xyz_layer2).data

        verify_serializer_v1_output(self, layer1_actual_data, name=self.layer1.name, layer_type="XYZ", order=2)
        verify_serializer_v1_output(self, layer2_actual_data, name=self.layer2.name, layer_type="XYZ", query_by_point=True, order=1)

class VectorLayerTest(TestCase):
    def setUp(self):
        site = Site.objects.get(pk=1)
        self.theme1 = Theme.objects.create(name="test")
        self.theme1.site.add(site)
        self.layer1 = Layer.objects.create(
            name="testlayer",
            layer_type='Vector',  
        ) 
        self.vector_layer1 = LayerVector.objects.create(
            layer=self.layer1,
        )  
        self.layer1.site.add(site)
        self.layer2 = Layer.objects.create(
            name="testlayer2",
            layer_type='Vector',  
            mouseover_field="hi",
        ) 
        self.vector_layer2 = LayerVector.objects.create(
            layer=self.layer2,
            custom_style="test", outline_width=5, outline_color="blue", outline_opacity=5.0,
            fill_opacity=5.0, color="blue", point_radius=5, graphic="Test", graphic_scale=5.0, opacity=5.0
        )

        self.layer2.site.add(site)
        # Create layer orders
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer1, order=2)
        ChildOrder.objects.create(parent_theme=self.theme1, content_object=self.layer2, order=1)
    def test_layer_attributes(self):
        layer1_actual_data = LayerVectorSerializer(self.vector_layer1).data

        layer2_actual_data = LayerVectorSerializer(self.vector_layer2).data

        verify_serializer_v1_output(self, layer1_actual_data, name=self.layer1.name, layer_type="Vector", order=2)
        verify_serializer_v1_output(self, layer2_actual_data, name=self.layer2.name, layer_type="Vector", order=1, mouseover_field="hi", custom_style="test", outline_width=5, outline_color="blue", outline_opacity=5.0,
                                                            fill_opacity=5.0, color="blue", point_radius=5, graphic="Test", graphic_scale=5.0, opacity=5.0)

class ChildOrderSerializerTest(TestCase):
    def setUp(self):
        # Create a parent theme
        site = Site.objects.get(pk=1)
        self.parent_theme = Theme.objects.create(name="Test Parent Theme")
        self.parent_theme.site.add(site)
        self.sub_theme = Theme.objects.create(name="Sub Theme")
        self.sub_theme.site.add(site)
        # Create layers
        self.layer1 = Layer.objects.create(
            name="Layer WMS",
            layer_type='WMS',  
        ) 
        self.wms_layer1 = LayerWMS.objects.create(
            layer=self.layer1,
        )  
        self.layer1.site.add(site)
        self.layer2 = Layer.objects.create(
            name="Layer ArcREST",
            layer_type='ArcRest',  
        ) 
        self.arcrest_layer2 = LayerArcREST.objects.create(
            layer=self.layer2,
        )  
        self.layer2.site.add(site)
        self.layer3 = Layer.objects.create(
            name="Layer ArcFeature",
            layer_type='ArcFeatureServer',  
        ) 
        self.arcfeature_layer3 = LayerArcFeatureService.objects.create(
            layer=self.layer3,
        )  
        self.layer3.site.add(site)
        self.layer4 = Layer.objects.create(
            name="Layer XYZ",
            layer_type='XYZ',  
        ) 
        self.xyz_layer4 = LayerXYZ.objects.create(
            layer=self.layer4,
        )  
        self.layer4.site.add(site)
        self.layer5 = Layer.objects.create(
            name="Layer Vector",
            layer_type='Vector',  
        ) 
        self.vector_layer5 = LayerVector.objects.create(
            layer=self.layer5,
        )  
        self.layer5.site.add(site)
        # Create a corresponding ChildOrder instance
        self.child_order_wms = ChildOrder.objects.create(parent_theme=self.parent_theme,content_object=self.layer1, order=1)
        self.child_order_arc_rest = ChildOrder.objects.create(parent_theme=self.parent_theme, content_object=self.layer2, order=1)
        self.child_order_arc_feature = ChildOrder.objects.create(parent_theme=self.parent_theme, content_object=self.layer3, order=1)
        self.child_order_xyz = ChildOrder.objects.create(parent_theme=self.parent_theme, content_object=self.layer4, order=1)
        self.child_order_vector = ChildOrder.objects.create(parent_theme=self.parent_theme, content_object=self.layer5, order=1)
        self.child_order_subtheme = ChildOrder.objects.create(parent_theme=self.parent_theme, content_object=self.sub_theme, order=1)
    def test_serialize_layer_arc_rest(self):
        # Serialize the LayerArcREST instance directly
        arc_rest_serializer = LayerArcRESTSerializer(self.arcrest_layer2)
        arc_rest_serialized_data = arc_rest_serializer.data

        # Serialize the ChildOrder instance that contains the LayerArcREST
        child_order_serializer = ChildOrderSerializer(self.child_order_arc_rest)
        child_order_serialized_data = child_order_serializer.data

        # Compare the two serialized outputs
        self.assertEqual(child_order_serialized_data, arc_rest_serialized_data)

    def test_serialize_layer_wms(self):
        wms_serializer = LayerWMSSerializer(self.wms_layer1)
        wms_serialized_data = wms_serializer.data
        # Serialize ChildOrder with a LayerWMS object
        serializer = ChildOrderSerializer(self.child_order_wms)
        serialized_data = serializer.data

        # Compare the two serialized outputs
        self.assertEqual(serialized_data, wms_serialized_data)

    def test_serialize_layer_arc_feature(self):
        arc_feature_serializer = LayerArcFeatureServiceSerializer(self.arcfeature_layer3)
        arc_feature_serialized_data = arc_feature_serializer.data
        # Serialize ChildOrder with a LayerWMS object
        serializer = ChildOrderSerializer(self.child_order_arc_feature)
        serialized_data = serializer.data

        # Compare the two serialized outputs
        self.assertEqual(serialized_data, arc_feature_serialized_data)

    def test_serialize_layer_xyz(self):
        xyz_serializer = LayerXYZSerializer(self.xyz_layer4)
        xyz_serialized_data = xyz_serializer.data
        # Serialize ChildOrder with a LayerWMS object
        serializer = ChildOrderSerializer(self.child_order_xyz)
        serialized_data = serializer.data

        # Compare the two serialized outputs
        self.assertEqual(serialized_data, xyz_serialized_data)

    def test_serialize_layer_vector(self):
        vector_serializer = LayerVectorSerializer(self.vector_layer5)
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
        site = Site.objects.get(pk=1)
        self.multilayer_parent_layer = Layer.objects.create(
            name="Parent Layer",
            layer_type='WMS',  
        ) 
        self.multilayer_wms_layer1 = LayerWMS.objects.create(
            layer=self.multilayer_parent_layer,
        )  
        self.multilayer_parent_layer.site.add(site)

        # Create Dimension
        self.month_dimension = MultilayerDimension.objects.create(
            name="Month", label="Month", order=201, animated=True, angle_labels=False, layer=self.multilayer_parent_layer)

        # Create Dimension Values and Associated Layers
        month_values = ["January", "February", "March", "April", "May", "June", 
                        "July", "August", "September", "October", "November", "December"]
        self.associated_layers = {}  # Store the associated layers for reference
        for month in month_values:
            # Step 1: Create the generic Layer instance first
            generic_layer = Layer.objects.create(name=f"{month} Layer", layer_type="WMS")
            generic_layer.site.add(site)

            # Step 2: Create the specific LayerWMS instance connected to the generic layer
            wms_layer = LayerWMS.objects.create(layer=generic_layer)
            self.associated_layers[month] = wms_layer

            # Step 3: Create dimension value
            month_value = MultilayerDimensionValue.objects.create(
                dimension=self.month_dimension, value=month, label=month, order=month_values.index(month) + 1)

            # Step 4: Attempt to fetch an existing association for this dimension value
            existing_association = month_value.associations.first()

            if existing_association:
                # If an existing association is found, update its layer to the generic layer
                existing_association.layer = generic_layer
                existing_association.parentLayer = self.multilayer_parent_layer  # Ensure the parentLayer is also set correctly
                existing_association.save()
            else:
                # If no existing association, create a new one with all necessary fields
                MultilayerAssociation.objects.create(
                    dimensionValue=month_value,
                    layer=generic_layer,
                    parentLayer=self.multilayer_parent_layer  # Ensure this is correctly referencing the parent layer
                )

    def test_dimension_recursion(self):
        # Assuming you have a method dimensionRecursion in your Layer model
        dimensions = [self.month_dimension]
        associations = MultilayerAssociation.objects.filter(parentLayer=self.multilayer_parent_layer)

        # Call the recursion function
        actual_output = self.multilayer_parent_layer.dimensionRecursion(dimensions, associations)

        # Define the expected output structure
        expected_output = {month: self.associated_layers[month].layer.id for month in self.associated_layers}

        # Assert equality
        self.assertEqual(actual_output, expected_output)
        
    def test_multilayer_related_attributes(self):
        serialized_data = LayerWMSSerializer(self.multilayer_wms_layer1).data

        expected_dimensions_output = [{'label': 'Month', 'name': 'Month', 'order': 201, 'animated': True, 'angle_labels': False, 'nodes': [{'value': 'January', 'label': 'January', 'order': 1}, 
                                            {'value': 'February', 'label': 'February', 'order': 2}, {'value': 'March', 'label': 'March', 'order': 3}, {'value': 'April', 'label': 'April', 'order': 4}, 
                                            {'value': 'May', 'label': 'May', 'order': 5}, {'value': 'June', 'label': 'June', 'order': 6}, {'value': 'July', 'label': 'July', 'order': 7}, 
                                            {'value': 'August', 'label': 'August', 'order': 8}, {'value': 'September', 'label': 'September', 'order': 9}, {'value': 'October', 'label': 'October', 'order': 10}, 
                                            {'value': 'November', 'label': 'November', 'order': 11}, {'value': 'December', 'label': 'December', 'order': 12}]}]
        expected_multilayers_output = {month: self.associated_layers[month].layer.id for month in self.associated_layers}
        
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


class ThemeLayersPropertyTest(TestCase):
    """Tests for Theme.layers and Theme.all_layers model properties."""

    def setUp(self):
        self.site = Site.objects.get(pk=1)

        self.top_theme = Theme.objects.create(
            name="Top Theme",
            is_top_theme=True,
            is_visible=True,
        )
        self.top_theme.site.add(self.site)

        self.sub_theme = Theme.objects.create(
            name="Sub Theme",
            is_visible=True,
        )
        self.sub_theme.site.add(self.site)

        self.hidden_sub_theme = Theme.objects.create(
            name="Hidden Sub Theme",
            is_visible=False,
        )
        self.hidden_sub_theme.site.add(self.site)

        self.direct_layer = Layer.objects.create(
            name="Direct Layer",
            layer_type="WMS",
            catalog_name="direct-catalog",
        )
        self.direct_layer.site.add(self.site)

        self.nested_layer = Layer.objects.create(
            name="Nested Layer",
            layer_type="WMS",
            catalog_name="nested-catalog",
        )
        self.nested_layer.site.add(self.site)

        self.hidden_nested_layer = Layer.objects.create(
            name="Hidden Nested Layer",
            layer_type="WMS",
            catalog_name="hidden-nested-catalog",
        )
        self.hidden_nested_layer.site.add(self.site)

        # top_theme -> direct_layer (direct child)
        ChildOrder.objects.create(
            parent_theme=self.top_theme,
            content_object=self.direct_layer,
            order=1,
        )
        # top_theme -> sub_theme -> nested_layer
        ChildOrder.objects.create(
            parent_theme=self.top_theme,
            content_object=self.sub_theme,
            order=2,
        )
        ChildOrder.objects.create(
            parent_theme=self.sub_theme,
            content_object=self.nested_layer,
            order=1,
        )
        # top_theme -> hidden_sub_theme -> hidden_nested_layer
        ChildOrder.objects.create(
            parent_theme=self.top_theme,
            content_object=self.hidden_sub_theme,
            order=3,
        )
        ChildOrder.objects.create(
            parent_theme=self.hidden_sub_theme,
            content_object=self.hidden_nested_layer,
            order=1,
        )

    def test_layers_returns_only_direct_layer_children(self):
        result = self.top_theme.layers
        self.assertIn(self.direct_layer, result)
        self.assertNotIn(self.nested_layer, result)
        self.assertNotIn(self.hidden_nested_layer, result)
        self.assertNotIn(self.sub_theme, result)

    def test_layers_returns_correct_count(self):
        # Only direct_layer is a direct Layer child of top_theme
        self.assertEqual(len(self.top_theme.layers), 1)

    def test_layers_on_sub_theme(self):
        result = self.sub_theme.layers
        self.assertIn(self.nested_layer, result)
        self.assertEqual(len(result), 1)

    def test_layers_empty_when_no_direct_layer_children(self):
        theme_no_layers = Theme.objects.create(name="No Layers Theme")
        theme_no_layers.site.add(self.site)
        ChildOrder.objects.create(
            parent_theme=theme_no_layers,
            content_object=self.sub_theme,
            order=1,
        )
        self.assertEqual(theme_no_layers.layers, [])

    def test_all_layers_includes_direct_and_nested(self):
        result = self.top_theme.all_layers
        self.assertIn(self.direct_layer, result)
        self.assertIn(self.nested_layer, result)

    def test_all_layers_excludes_layers_under_hidden_sub_theme(self):
        # hidden_sub_theme has is_visible=False so its layers must not appear
        result = self.top_theme.all_layers
        self.assertNotIn(self.hidden_nested_layer, result)

    def test_all_layers_contains_no_theme_objects(self):
        result = self.top_theme.all_layers
        for item in result:
            self.assertIsInstance(item, Layer)

    def test_all_layers_returns_unique_layers(self):
        # Add nested_layer as a direct child too to create a duplicate
        ChildOrder.objects.create(
            parent_theme=self.top_theme,
            content_object=self.nested_layer,
            order=4,
        )
        result = self.top_theme.all_layers
        self.assertEqual(len(result), len(set(layer.pk for layer in result)))

    def test_all_layers_on_leaf_theme_equals_layers(self):
        # sub_theme has no sub-themes, so all_layers == layers
        self.assertEqual(
            set(layer.pk for layer in self.sub_theme.all_layers),
            set(layer.pk for layer in self.sub_theme.layers),
        )


class GetPortalCatalogMapViewTest(TestCase):
    """Tests for the get_portal_catalog_map view."""

    def setUp(self):
        self.site = Site.objects.get(pk=1)
        self.factory = RequestFactory()

        self.top_theme = Theme.objects.create(
            name="Catalog Top Theme",
            is_top_theme=True,
            is_visible=True,
        )
        self.top_theme.site.add(self.site)

        self.sub_theme = Theme.objects.create(
            name="Catalog Sub Theme",
            is_visible=True,
        )
        self.sub_theme.site.add(self.site)

        self.layer_with_catalog_name = Layer.objects.create(
            name="Mapped Layer",
            layer_type="WMS",
            catalog_name="my-catalog-record",
        )
        self.layer_with_catalog_name.site.add(self.site)

        self.layer_no_catalog_name = Layer.objects.create(
            name="Unmapped Layer",
            layer_type="WMS",
            catalog_name=None,
        )
        self.layer_no_catalog_name.site.add(self.site)

        self.layer_empty_catalog_name = Layer.objects.create(
            name="Empty Catalog Layer",
            layer_type="WMS",
            catalog_name="",
        )
        self.layer_empty_catalog_name.site.add(self.site)

        self.nested_layer = Layer.objects.create(
            name="Nested Catalog Layer",
            layer_type="WMS",
            catalog_name="nested-catalog-record",
        )
        self.nested_layer.site.add(self.site)

        ChildOrder.objects.create(
            parent_theme=self.top_theme,
            content_object=self.layer_with_catalog_name,
            order=1,
        )
        ChildOrder.objects.create(
            parent_theme=self.top_theme,
            content_object=self.layer_no_catalog_name,
            order=2,
        )
        ChildOrder.objects.create(
            parent_theme=self.top_theme,
            content_object=self.layer_empty_catalog_name,
            order=3,
        )
        ChildOrder.objects.create(
            parent_theme=self.top_theme,
            content_object=self.sub_theme,
            order=4,
        )
        ChildOrder.objects.create(
            parent_theme=self.sub_theme,
            content_object=self.nested_layer,
            order=1,
        )

    def _get(self):
        request = self.factory.get("/layers/get_portal_catalog_map")
        return get_portal_catalog_map(request)

    @override_settings(CATALOG_TECHNOLOGY="GeoPortal2")
    def test_returns_200(self):
        response = self._get()
        self.assertEqual(response.status_code, 200)

    @override_settings(CATALOG_TECHNOLOGY="GeoPortal2")
    def test_maps_catalog_name_to_layer_pk(self):
        response = self._get()
        data = json.loads(response.content)
        self.assertIn("my-catalog-record", data)
        self.assertEqual(data["my-catalog-record"], self.layer_with_catalog_name.pk)

    @override_settings(CATALOG_TECHNOLOGY="GeoPortal2")
    def test_includes_nested_layer_under_visible_sub_theme(self):
        response = self._get()
        data = json.loads(response.content)
        self.assertIn("nested-catalog-record", data)
        self.assertEqual(data["nested-catalog-record"], self.nested_layer.pk)

    @override_settings(CATALOG_TECHNOLOGY="GeoPortal2")
    def test_excludes_layers_without_catalog_name(self):
        response = self._get()
        data = json.loads(response.content)
        # layer_no_catalog_name has catalog_name=None
        for key in data:
            self.assertNotEqual(data[key], self.layer_no_catalog_name.pk)

    @override_settings(CATALOG_TECHNOLOGY="GeoPortal2")
    def test_excludes_layers_with_empty_catalog_name(self):
        response = self._get()
        data = json.loads(response.content)
        self.assertNotIn("", data)

    @override_settings(CATALOG_TECHNOLOGY="GeoPortal2")
    def test_excludes_layers_from_invisible_top_theme(self):
        invisible_theme = Theme.objects.create(
            name="Invisible Top Theme",
            is_top_theme=True,
            is_visible=False,
        )
        invisible_theme.site.add(self.site)
        hidden_layer = Layer.objects.create(
            name="Hidden Layer",
            layer_type="WMS",
            catalog_name="should-not-appear",
        )
        hidden_layer.site.add(self.site)
        ChildOrder.objects.create(
            parent_theme=invisible_theme,
            content_object=hidden_layer,
            order=1,
        )
        response = self._get()
        data = json.loads(response.content)
        self.assertNotIn("should-not-appear", data)

    @override_settings(CATALOG_TECHNOLOGY="GeoPortal2")
    def test_excludes_layers_from_non_top_level_theme(self):
        orphan_theme = Theme.objects.create(
            name="Orphan Theme",
            is_top_theme=False,
            is_visible=True,
        )
        orphan_theme.site.add(self.site)
        orphan_layer = Layer.objects.create(
            name="Orphan Layer",
            layer_type="WMS",
            catalog_name="orphan-catalog-record",
        )
        orphan_layer.site.add(self.site)
        ChildOrder.objects.create(
            parent_theme=orphan_theme,
            content_object=orphan_layer,
            order=1,
        )
        response = self._get()
        data = json.loads(response.content)
        self.assertNotIn("orphan-catalog-record", data)

    @override_settings(CATALOG_TECHNOLOGY="NotGeoPortal2")
    def test_returns_empty_dict_when_catalog_technology_not_geoportal2(self):
        response = self._get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {})

