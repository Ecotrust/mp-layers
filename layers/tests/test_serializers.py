import uuid


from django.test import TestCase, SimpleTestCase, override_settings
from django.utils import timezone
from datetime import date
from layers.serializers import ThemeExportFixtureSerializer, LayerWMSSerializer, LayerArcRESTSerializer, LayerArcFeatureServiceSerializer, LayerXYZSerializer, LayerVectorSerializer, SubThemeSerializer, ChildOrderSerializer, LayerExportSerializer, AttributeInfoExportSerializer, LookupInfoExportSerializer, LayerWMSExportSerializer, LayerArcRESTExportSerializer, LayerArcFeatureServiceExportSerializer, LayerVectorExportSerializer, LayerXYZExportSerializer
from layers.models import AttributeInfo, Theme, Layer, Companionship, LayerWMS, LayerArcREST, LayerArcFeatureService, LayerVector, LayerXYZ, ChildOrder, LookupInfo
from layers.tests.test_models import verify_serializer_v1_output

import json
from django.contrib.sites.models import Site
from layers.fixture_contract import NODE_FIELDS_KEY, NODE_MODEL_KEY, NODE_RELATIONS_KEY, NODE_SOURCE_PK_KEY, NODE_UUID_KEY
from layers.admin import export_layer_details, export_theme_details
from unittest.mock import Mock

class AttributeInfoExportSerializerTest(SimpleTestCase):
    def test_represents_attribute_info_with_expected_fields(self):
        attribute_info = AttributeInfo(
            uuid=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            display_name="Record Name",
            field_name="FIELD",
            field_label="Field Label",
            precision=2,
            order=3,
            preserve_format=True,
        )

        result = AttributeInfoExportSerializer(attribute_info).data

        self.assertEqual(result, {
            "uuid": "12345678-1234-5678-1234-567812345678",
            "display_name": "Record Name",
            "field_name": "FIELD",
            "field_label": "Field Label",
            "precision": 2,
            "order": 3,
            "preserve_format": True,
        })

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

    def test_theme_export_single_theme(self):
        parent_theme = Theme.objects.create(name='Parent Theme', display_name='Parent Theme')
        child_theme = Theme.objects.create(name='Child Theme', display_name='Child Theme')
        layer_a = Layer.objects.create(name='Layer A', layer_type='WMS')
        layer_b = Layer.objects.create(name='Layer B', layer_type='WMS')

        ChildOrder.objects.create(parent_theme=parent_theme, content_object=layer_a, order=1)
        ChildOrder.objects.create(parent_theme=parent_theme, content_object=child_theme, order=2)
        ChildOrder.objects.create(parent_theme=child_theme, content_object=layer_a, order=1)
        ChildOrder.objects.create(parent_theme=child_theme, content_object=layer_b, order=2)

        response = export_theme_details(Mock(), Mock(), Theme.all_objects.filter(pk=parent_theme.pk))
        fixture_data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self._rows_for_model(fixture_data, 'layers.theme')), 2)
        self.assertEqual(len(self._rows_for_model(fixture_data, 'layers.childorder')), 4)
        self.assertEqual(len(self._rows_for_model(fixture_data, 'layers.layer')), 2)

    def test_theme_export_concurrent_themes(self):
        parent_theme = Theme.objects.create(name='Parent Theme', display_name='Parent Theme')
        child_theme = Theme.objects.create(name='Child Theme', display_name='Child Theme')
        third_theme = Theme.objects.create(name='Third Theme', display_name='Third Theme')
        layer_a = Layer.objects.create(name='Layer A', layer_type='WMS')
        layer_b = Layer.objects.create(name='Layer B', layer_type='WMS')
        layer_c = Layer.objects.create(name='Layer C', layer_type='WMS')

        ChildOrder.objects.create(parent_theme=parent_theme, content_object=layer_a, order=1)
        ChildOrder.objects.create(parent_theme=parent_theme, content_object=child_theme, order=2)
        ChildOrder.objects.create(parent_theme=child_theme, content_object=layer_a, order=1)
        ChildOrder.objects.create(parent_theme=child_theme, content_object=layer_b, order=2)
        ChildOrder.objects.create(parent_theme=third_theme, content_object=layer_a, order=1)
        ChildOrder.objects.create(parent_theme=third_theme, content_object=layer_c, order=2)

        selected_themes = Theme.all_objects.filter(
            pk__in=[parent_theme.pk, child_theme.pk, third_theme.pk],
        ).order_by('pk')
        response = export_theme_details(Mock(), Mock(), selected_themes)
        fixture_data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self._rows_for_model(fixture_data, 'layers.theme')), 3)
        self.assertEqual(len(self._rows_for_model(fixture_data, 'layers.childorder')), 6)
        self.assertEqual(len(self._rows_for_model(fixture_data, 'layers.layer')), 3)

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

class AttributeInfoExportSerializerTest(TestCase):

    def test_attribute_info_export_contains_expected_fields_with_appropriate_types(self):
        expected_export_data = {
            'display_name': 'Depth',
            'field_name': 'depth_m',
            'field_label': 'Depth (m)',
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

@override_settings(DB_CHANNEL="madronaportal")
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

@override_settings(DB_CHANNEL="madronaportal")
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
        verify_serializer_v1_output(
            self, 
            serialized_subtheme_data, 
            name=self.sub_theme.name, 
            layer_type=self.sub_theme.theme_type, 
            order=1,
            url="",
            kml=""
        )

        # Extract only the 'id' from each item in 'subLayers'
        serialized_ids = [item['id'] for item in serialized_subtheme_data['subLayers']]

        # Define the expected IDs in order
        expected_ids = [self.layer1.id, self.layer2.id, self.layer4.id, self.layer3.id]

        # Assert that the order of IDs in the serialized data matches the expected order
        self.assertEqual(serialized_ids, expected_ids)
        # self.assertEqual(serialized_subtheme_data["id"], serialized_layer_data["parent"])

@override_settings(DB_CHANNEL="madronaportal")
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
