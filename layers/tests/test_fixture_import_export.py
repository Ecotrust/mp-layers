from django.test import TestCase

from layers.fixture_contract import (
    NODE_MODEL_KEY,
    NODE_RELATIONS_KEY,
    NODE_SOURCE_PK_KEY,
    NODE_UUID_KEY,
)
from layers.models import Companionship, Layer


class LayerCompanionshipFixtureExportTest(TestCase):
    def test_layer_export_fixture_includes_outgoing_companionship_and_companion_layers(self):
        """Exported layer with 2 companions should include all three + the companionship row"""
        root_layer = Layer.objects.create(name='Root Layer', layer_type='WMS')
        companion_a = Layer.objects.create(name='Companion A', layer_type='WMS')
        companion_b = Layer.objects.create(name='Companion B', layer_type='WMS')

        companionship = Companionship.objects.create(layer=root_layer)
        companionship.companions.set([companion_b, companion_a])

        fixture_data = root_layer.to_export_dict()

        companionship_rows = [
            row for row in fixture_data
            if row[NODE_MODEL_KEY] == 'layers.companionship' and row[NODE_SOURCE_PK_KEY] == companionship.pk
        ]
        self.assertEqual(len(companionship_rows), 1)

        companionship_row = companionship_rows[0]
        self.assertEqual(
            companionship_row[NODE_RELATIONS_KEY]['layer'],
            {
                NODE_MODEL_KEY: 'layers.layer',
                NODE_SOURCE_PK_KEY: root_layer.pk,
                NODE_UUID_KEY: str(root_layer.uuid),
            },
        )

        expected_companion_refs = [
            {
                NODE_MODEL_KEY: 'layers.layer',
                NODE_SOURCE_PK_KEY: companion.pk,
                NODE_UUID_KEY: str(companion.uuid),
            }
            for companion in sorted([companion_a, companion_b], key=lambda x: x.pk)
        ]
        self.assertEqual(companionship_row[NODE_RELATIONS_KEY]['companions'], expected_companion_refs)

        exported_layer_pks = {
            row[NODE_SOURCE_PK_KEY]
            for row in fixture_data
            if row[NODE_MODEL_KEY] == 'layers.layer'
        }
        self.assertIn(root_layer.pk, exported_layer_pks)
        self.assertIn(companion_a.pk, exported_layer_pks)
        self.assertIn(companion_b.pk, exported_layer_pks)

    def test_layer_export_fixture_excludes_incoming_only_companionship(self):
        """Test one-way companionship traversal: don't include layers that rely on
        the exported layer as a companion, nor the companionship row itself."""
        owner_layer = Layer.objects.create(name='Owner Layer', layer_type='WMS')
        incoming_only_layer = Layer.objects.create(name='Incoming-only Layer', layer_type='WMS')

        companionship = Companionship.objects.create(layer=owner_layer)
        companionship.companions.add(incoming_only_layer)

        fixture_data = incoming_only_layer.to_export_dict()

        companionship_rows = [
            row for row in fixture_data
            if row[NODE_MODEL_KEY] == 'layers.companionship'
        ]
        self.assertEqual(companionship_rows, [])

        exported_layer_pks = [
            row[NODE_SOURCE_PK_KEY]
            for row in fixture_data
            if row[NODE_MODEL_KEY] == 'layers.layer'
        ]
        self.assertIn(incoming_only_layer.pk, exported_layer_pks)
        self.assertNotIn(owner_layer.pk, exported_layer_pks)

    def test_layer_export_fixture_includes_transitive_outgoing_companionship_chain(self):
        """Exported layer with a companion that also has a companion should include
        all three layers and both companionship rows."""
        layer_a = Layer.objects.create(name='Layer A', layer_type='WMS')
        layer_b = Layer.objects.create(name='Layer B', layer_type='WMS')
        layer_c = Layer.objects.create(name='Layer C', layer_type='WMS')

        companionship_ab = Companionship.objects.create(layer=layer_a)
        companionship_ab.companions.add(layer_b)

        companionship_bc = Companionship.objects.create(layer=layer_b)
        companionship_bc.companions.add(layer_c)

        fixture_data = layer_a.to_export_dict()

        exported_layer_pks = {
            row[NODE_SOURCE_PK_KEY]
            for row in fixture_data
            if row[NODE_MODEL_KEY] == 'layers.layer'
        }
        self.assertEqual(exported_layer_pks, {layer_a.pk, layer_b.pk, layer_c.pk})

        exported_companionship_pks = {
            row[NODE_SOURCE_PK_KEY]
            for row in fixture_data
            if row[NODE_MODEL_KEY] == 'layers.companionship'
        }
        self.assertEqual(exported_companionship_pks, {companionship_ab.pk, companionship_bc.pk})

from uuid import uuid4

from django.test import SimpleTestCase

from layers.fixture_contract import (
    NODE_FIELDS_KEY,
    NODE_MODEL_KEY,
    NODE_RELATIONS_KEY,
    NODE_SOURCE_PK_KEY,
    NODE_UUID_KEY,
    build_node,
    build_ref,
    node_sort_key,
    normalize_uuid,
    ref_sort_key,
    validate_node_shape,
    validate_ref_shape,
)


class _Meta(object):
    label_lower = "layers.layer"


class _InstanceWithUUID(object):
    _meta = _Meta()

    def __init__(self):
        self.pk = 42
        self.uuid = uuid4()


class _InstanceWithoutUUID(object):
    _meta = _Meta()

    def __init__(self):
        self.pk = 84


class FixtureContractTest(SimpleTestCase):
    def test_normalize_uuid_returns_none_for_none(self):
        self.assertIsNone(normalize_uuid(None))

    def test_normalize_uuid_stringifies_uuid_instance(self):
        value = uuid4()
        self.assertEqual(normalize_uuid(value), str(value))

    def test_build_ref_from_instance_with_uuid(self):
        instance = _InstanceWithUUID()
        ref_obj = build_ref(instance=instance)

        self.assertEqual(ref_obj[NODE_MODEL_KEY], "layers.layer")
        self.assertEqual(ref_obj[NODE_SOURCE_PK_KEY], 42)
        self.assertEqual(ref_obj[NODE_UUID_KEY], str(instance.uuid))

    def test_build_ref_from_instance_without_uuid(self):
        instance = _InstanceWithoutUUID()
        ref_obj = build_ref(instance=instance)

        self.assertEqual(ref_obj[NODE_MODEL_KEY], "layers.layer")
        self.assertEqual(ref_obj[NODE_SOURCE_PK_KEY], 84)
        self.assertIsNone(ref_obj[NODE_UUID_KEY])

    def test_build_node_defaults_fields_and_relations_to_empty_objects(self):
        node_obj = build_node("layers.layer", 1, None)

        self.assertEqual(node_obj[NODE_FIELDS_KEY], {})
        self.assertEqual(node_obj[NODE_RELATIONS_KEY], {})

    def test_validate_ref_shape_accepts_valid_ref(self):
        validate_ref_shape({
            NODE_MODEL_KEY: "layers.layer",
            NODE_SOURCE_PK_KEY: 1,
            NODE_UUID_KEY: str(uuid4()),
        })

    def test_validate_ref_shape_rejects_missing_model(self):
        with self.assertRaises(ValueError):
            validate_ref_shape({
                NODE_SOURCE_PK_KEY: 1,
                NODE_UUID_KEY: str(uuid4()),
            })

    def test_validate_node_shape_accepts_valid_node(self):
        validate_node_shape({
            NODE_MODEL_KEY: "layers.layer",
            NODE_SOURCE_PK_KEY: 1,
            NODE_UUID_KEY: str(uuid4()),
            NODE_FIELDS_KEY: {"name": "Layer"},
            NODE_RELATIONS_KEY: {},
        })

    def test_validate_node_shape_rejects_missing_relations(self):
        with self.assertRaises(ValueError):
            validate_node_shape({
                NODE_MODEL_KEY: "layers.layer",
                NODE_SOURCE_PK_KEY: 1,
                NODE_UUID_KEY: str(uuid4()),
                NODE_FIELDS_KEY: {},
            })

    def test_validate_node_shape_rejects_non_mapping_nodes(self):
        for node_obj in (None, 1):
            with self.assertRaises(ValueError):
                validate_node_shape(node_obj)

    def test_ref_sort_key_is_stable(self):
        ref_one = {NODE_MODEL_KEY: "layers.lookupinfo", NODE_SOURCE_PK_KEY: 2, NODE_UUID_KEY: "b"}
        ref_two = {NODE_MODEL_KEY: "layers.lookupinfo", NODE_SOURCE_PK_KEY: 1, NODE_UUID_KEY: "a"}

        sorted_refs = sorted([ref_one, ref_two], key=ref_sort_key)

        self.assertEqual(sorted_refs, [ref_two, ref_one])

    def test_node_sort_key_is_stable(self):
        node_one = {
            NODE_MODEL_KEY: "layers.layer",
            NODE_SOURCE_PK_KEY: 2,
            NODE_UUID_KEY: "b",
            NODE_FIELDS_KEY: {},
            NODE_RELATIONS_KEY: {},
        }
        node_two = {
            NODE_MODEL_KEY: "layers.layer",
            NODE_SOURCE_PK_KEY: 1,
            NODE_UUID_KEY: "a",
            NODE_FIELDS_KEY: {},
            NODE_RELATIONS_KEY: {},
        }

        sorted_nodes = sorted([node_one, node_two], key=node_sort_key)

        self.assertEqual(sorted_nodes, [node_two, node_one])

from uuid import uuid4
from unittest.mock import patch

from django.contrib.sites.models import Site
from django.db.backends.utils import CursorWrapper
from django.test import TestCase

from layers.fixture_contract import build_node, build_ref
from layers.models import (
    AttributeInfo,
    Companionship,
    ChildOrder,
    Layer,
    LayerArcFeatureService,
    LayerArcREST,
    LayerVector,
    LayerWMS,
    LayerXYZ,
    LookupInfo,
    MultilayerAssociation,
    MultilayerDimension,
    MultilayerDimensionValue,
    Theme,
)

try:
    from layers.fixture_import import import_fixture_rows
except ImportError:
    import_fixture_rows = None


class LayerFixtureImportPR05Test(TestCase):
    """layer fixture contract tests for UUID-first fixture import behavior."""

    def _require_importer(self):
        self.assertIsNotNone(
            import_fixture_rows,
            "importer API missing: expected layers.fixture_import.import_fixture_rows",
        )

    def _layer_fields(self, name):
        return {
            "name": name,
            "layer_type": "WMS",
            "slug_name": None,
            "url": None,
        }

    def _import_kwargs(self):
        return {
            "dry_run": False,
            "associate_all_sites": True,
            "missing_ref_policy": "error",
            "duplicate_uuid_policy": "error",
        }

    def test_uuid_match_updates_existing_even_when_source_pk_differs(self):
        """Ensure UUIDs are used as the true source of identity, not source PKs."""
        self._require_importer()

        layer_uuid = uuid4()
        existing_layer = Layer.objects.create(
            name="Original",
            layer_type="WMS",
            uuid=layer_uuid,
        )

        fixture_rows = [
            build_node(
                model="layers.layer",
                source_pk=9999,
                uuid_value=layer_uuid,
                fields=self._layer_fields("Updated by UUID"),
                relations={},
            )
        ]

        import_fixture_rows(fixture_rows, **self._import_kwargs())

        existing_layer.refresh_from_db()
        self.assertEqual(existing_layer.name, "Updated by UUID")
        self.assertEqual(Layer.objects.filter(uuid=layer_uuid).count(), 1)

    def test_source_pk_collision_with_different_uuid_creates_new_record(self):
        """If records with different IDs, but same UUID/type are found, create
        a new record with a new ID."""
        self._require_importer()

        existing_layer = Layer.objects.create(name="Existing", layer_type="WMS")
        new_uuid = uuid4()

        fixture_rows = [
            build_node(
                model="layers.layer",
                source_pk=existing_layer.pk,
                uuid_value=new_uuid,
                fields=self._layer_fields("Created on UUID mismatch"),
                relations={},
            )
        ]

        before_count = Layer.objects.count()
        import_fixture_rows(fixture_rows, **self._import_kwargs())

        self.assertEqual(Layer.objects.count(), before_count + 1)
        self.assertTrue(Layer.objects.filter(uuid=new_uuid).exists())
        existing_layer.refresh_from_db()
        self.assertEqual(existing_layer.name, "Existing")

    def test_unused_source_pk_is_preserved_when_creating_record(self):
        self._require_importer()

        new_uuid = uuid4()
        source_pk = 999999
        fixture_rows = [
            build_node(
                model="layers.layer",
                source_pk=source_pk,
                uuid_value=new_uuid,
                fields=self._layer_fields("Preserved Source PK"),
                relations={},
            )
        ]

        import_fixture_rows(fixture_rows, **self._import_kwargs())

        imported_layer = Layer.all_objects.get(uuid=new_uuid)
        self.assertEqual(imported_layer.pk, source_pk)

    def test_layer_slug_name_from_fixture_is_preserved(self):
        self._require_importer()

        layer_uuid = uuid4()
        slug_name = "fixture-layer-unique-slug"
        layer_fields = self._layer_fields("Layer With Fixture Slug")
        layer_fields["slug_name"] = slug_name
        fixture_rows = [
            build_node(
                model="layers.layer",
                source_pk=999998,
                uuid_value=layer_uuid,
                fields=layer_fields,
                relations={},
            )
        ]

        import_fixture_rows(fixture_rows, **self._import_kwargs())

        imported_layer = Layer.all_objects.get(uuid=layer_uuid)
        self.assertEqual(imported_layer.slug_name, slug_name)

    def test_second_pass_resolves_relations_by_uuid_not_source_pk(self):
        """As name suggests - ensure 2nd pass uses UUIDs for reference, not just PK or 'id'."""
        self._require_importer()

        parent_uuid = uuid4()
        target_uuid = uuid4()
        association_uuid = uuid4()

        fixture_rows = [
            build_node(
                model="layers.layer",
                source_pk=101,
                uuid_value=parent_uuid,
                fields=self._layer_fields("Imported Parent"),
                relations={},
            ),
            build_node(
                model="layers.layer",
                source_pk=202,
                uuid_value=target_uuid,
                fields=self._layer_fields("Imported Target"),
                relations={},
            ),
            build_node(
                model="layers.multilayerassociation",
                source_pk=303,
                uuid_value=association_uuid,
                fields={"name": "Val-1aVal-2b"},
                relations={
                    "parentLayer": build_ref(
                        model="layers.layer",
                        source_pk=99901,
                        uuid_value=parent_uuid,
                    ),
                    "layer": build_ref(
                        model="layers.layer",
                        source_pk=99902,
                        uuid_value=target_uuid,
                    ),
                },
            ),
        ]

        import_fixture_rows(fixture_rows, **self._import_kwargs())

        imported_parent = Layer.objects.get(uuid=parent_uuid)
        imported_target = Layer.objects.get(uuid=target_uuid)
        imported_association = MultilayerAssociation.objects.get(uuid=association_uuid)

        self.assertEqual(imported_association.parentLayer_id, imported_parent.pk)
        self.assertEqual(imported_association.layer_id, imported_target.pk)

    def test_new_layers_are_associated_to_all_sites_by_default(self):
        """Sites info should no longer matter on import if all DBs are segregated. 
        We will assume any imported layer is intended to be seen on the new server, 
        so we will associate it with all sites by default."""
        self._require_importer()

        Site.objects.get_or_create(id=1, defaults={"domain": "example.com", "name": "example"})
        Site.objects.get_or_create(id=2, defaults={"domain": "preview.example.com", "name": "preview"})

        new_uuid = uuid4()
        fixture_rows = [
            build_node(
                model="layers.layer",
                source_pk=404,
                uuid_value=new_uuid,
                fields=self._layer_fields("Site-linked Import"),
                relations={},
            )
        ]

        import_fixture_rows(fixture_rows, **self._import_kwargs())

        imported_layer = Layer.objects.get(uuid=new_uuid)
        imported_site_ids = set(imported_layer.site.values_list("id", flat=True))
        all_site_ids = set(Site.objects.values_list("id", flat=True))
        self.assertEqual(imported_site_ids, all_site_ids)

    def test_duplicate_uuid_rows_with_conflicting_fields_raise_error(self):
        """two records with the same UUID and a different field. Right now
        we don't have a plan for resolving this, so ValueError should be raised."""
        self._require_importer()

        shared_uuid = uuid4()
        fixture_rows = [
            build_node(
                model="layers.layer",
                source_pk=501,
                uuid_value=shared_uuid,
                fields=self._layer_fields("Name A"),
                relations={},
            ),
            build_node(
                model="layers.layer",
                source_pk=502,
                uuid_value=shared_uuid,
                fields=self._layer_fields("Name B"),
                relations={},
            ),
        ]

        with self.assertRaises(ValueError):
            import_fixture_rows(fixture_rows, **self._import_kwargs())

    def test_unknown_model_row_raises_value_error_without_counting_as_imported(self):
        self._require_importer()

        fixture_rows = [
            {
                "model": "layers.unsupported",
                "source_pk": 777,
                "uuid": str(uuid4()),
                "fields": {},
                "relations": {},
            }
        ]

        with self.assertRaises(ValueError) as raised:
            import_fixture_rows(fixture_rows, **self._import_kwargs())

        self.assertIn("layers.unsupported", str(raised.exception))


class ThemeFixtureImportPR09Test(TestCase):
    """Theme fixture import tests for non-UUID ChildOrder identity."""

    def _require_importer(self):
        self.assertIsNotNone(
            import_fixture_rows,
            "importer API missing: expected layers.fixture_import.import_fixture_rows",
        )

    def _import_kwargs(self):
        return {
            "dry_run": False,
            "associate_all_sites": True,
            "missing_ref_policy": "error",
            "duplicate_uuid_policy": "error",
        }

    def test_theme_slug_name_from_fixture_is_preserved(self):
        self._require_importer()

        theme_uuid = uuid4()
        slug_name = "fixture-theme-unique-slug"
        fixture_rows = [
            build_node(
                model="layers.theme",
                source_pk=999997,
                uuid_value=theme_uuid,
                fields={
                    "name": "Theme With Fixture Slug",
                    "display_name": "Theme With Fixture Slug",
                    "slug_name": slug_name,
                },
                relations={},
            )
        ]

        import_fixture_rows(fixture_rows, **self._import_kwargs())

        imported_theme = Theme.all_objects.get(uuid=theme_uuid)
        self.assertEqual(imported_theme.slug_name, slug_name)

    def test_dry_run_does_not_change_cache_or_emit_notify(self):
        self._require_importer()

        fixture_rows = [
            build_node(
                model="layers.layer",
                source_pk=999996,
                uuid_value=uuid4(),
                fields={
                    "name": "Dry Run Layer",
                    "layer_type": "WMS",
                    "slug_name": "dry-run-layer",
                },
                relations={},
            ),
            build_node(
                model="layers.theme",
                source_pk=999995,
                uuid_value=uuid4(),
                fields={
                    "name": "Dry Run Theme",
                    "display_name": "Dry Run Theme",
                    "slug_name": "dry-run-theme",
                },
                relations={},
            ),
        ]

        executed_sql = []
        original_execute = CursorWrapper.execute

        def record_execute(cursor, sql, params=None):
            executed_sql.append(sql)
            return original_execute(cursor, sql, params)

        with patch("layers.models.cache.delete") as cache_delete:
            with patch.object(
                CursorWrapper,
                "execute",
                autospec=True,
                side_effect=record_execute,
            ):
                import_kwargs = self._import_kwargs()
                import_kwargs["dry_run"] = True
                import_fixture_rows(fixture_rows, **import_kwargs)

        cache_delete.assert_not_called()
        self.assertFalse(
            any(str(sql).lstrip().upper().startswith("NOTIFY ") for sql in executed_sql)
        )

    def test_child_order_source_id_collision_creates_new_relationship(self):
        self._require_importer()

        parent_theme = Theme.all_objects.create(
            name="Existing Theme",
            display_name="Existing Theme",
        )
        layer = Layer.all_objects.create(name="Existing Layer", layer_type="WMS")
        imported_parent_theme = Theme.all_objects.create(
            name="Imported Theme",
            display_name="Imported Theme",
        )
        imported_layer = Layer.all_objects.create(
            name="Imported Layer",
            layer_type="WMS",
        )
        child_order = ChildOrder.objects.create(
            parent_theme=parent_theme,
            content_object=layer,
            order=3,
        )
        original_pk = child_order.pk
        original_date_created = child_order.date_created
        original_date_modified = child_order.date_modified
        original_parent_theme_id = child_order.parent_theme_id
        original_content_type_id = child_order.content_type_id
        original_object_id = child_order.object_id

        fixture_rows = [
            build_node(
                model="layers.childorder",
                source_pk=original_pk,
                uuid_value=None,
                fields={"order": 17},
                relations={
                    "parent_theme": build_ref(
                        model="layers.theme",
                        source_pk=1001,
                        uuid_value=imported_parent_theme.uuid,
                    ),
                    "content_object": build_ref(
                        model="layers.layer",
                        source_pk=1002,
                        uuid_value=imported_layer.uuid,
                    ),
                },
            )
        ]

        import_fixture_rows(fixture_rows, **self._import_kwargs())

        child_orders = ChildOrder.objects.all()
        self.assertEqual(child_orders.count(), 2)

        child_order.refresh_from_db()
        self.assertEqual(child_order.pk, original_pk)
        self.assertEqual(child_order.order, 3)
        self.assertEqual(child_order.parent_theme_id, original_parent_theme_id)
        self.assertEqual(child_order.content_type_id, original_content_type_id)
        self.assertEqual(child_order.object_id, original_object_id)
        self.assertEqual(child_order.date_created, original_date_created)
        self.assertEqual(child_order.date_modified, original_date_modified)

        imported_child_order = ChildOrder.objects.get(
            parent_theme=imported_parent_theme,
            object_id=imported_layer.pk,
        )
        self.assertNotEqual(imported_child_order.pk, original_pk)
        self.assertEqual(imported_child_order.order, 17)


class LayerFixtureImportPR06Test(TestCase):
    """PR06 contract tests for associated model import behavior."""

    def _require_importer(self):
        self.assertIsNotNone(
            import_fixture_rows,
            "importer API missing: expected layers.fixture_import.import_fixture_rows",
        )

    def _import_kwargs(self):
        return {
            "dry_run": False,
            "associate_all_sites": True,
            "missing_ref_policy": "error",
            "duplicate_uuid_policy": "error",
        }

    def _layer_fields(self, name):
        return {
            "name": name,
            "layer_type": "WMS",
            "slug_name": None,
            "url": None,
        }

    def test_attributeinfo_uuid_match_updates_existing_even_when_source_pk_differs(self):
        self._require_importer()

        attribute_uuid = uuid4()
        existing_attr = AttributeInfo.objects.create(
            uuid=attribute_uuid,
            display_name="Original Label",
            field_name="old_field",
            order=1,
        )

        fixture_rows = [
            build_node(
                model="layers.attributeinfo",
                source_pk=8801,
                uuid_value=attribute_uuid,
                fields={
                    "display_name": "Updated Label",
                    "field_name": "new_field",
                    "order": 7,
                },
                relations={},
            )
        ]

        import_fixture_rows(fixture_rows, **self._import_kwargs())

        existing_attr.refresh_from_db()
        self.assertEqual(existing_attr.display_name, "Updated Label")
        self.assertEqual(existing_attr.field_name, "new_field")
        self.assertEqual(AttributeInfo.objects.filter(uuid=attribute_uuid).count(), 1)

    def test_lookupinfo_source_pk_collision_with_different_uuid_creates_new_record(self):
        self._require_importer()

        existing_lookup = LookupInfo.objects.create(value="A", description="existing")
        new_uuid = uuid4()

        fixture_rows = [
            build_node(
                model="layers.lookupinfo",
                source_pk=existing_lookup.pk,
                uuid_value=new_uuid,
                fields={
                    "value": "B",
                    "description": "imported",
                    "dashstyle": "solid",
                },
                relations={},
            )
        ]

        before_count = LookupInfo.objects.count()
        import_fixture_rows(fixture_rows, **self._import_kwargs())

        self.assertEqual(LookupInfo.objects.count(), before_count + 1)
        self.assertTrue(LookupInfo.objects.filter(uuid=new_uuid).exists())

    def test_second_pass_resolves_layer_attribute_fields_by_uuid(self):
        self._require_importer()

        layer_uuid = uuid4()
        attr_uuid = uuid4()

        fixture_rows = [
            build_node(
                model="layers.attributeinfo",
                source_pk=9301,
                uuid_value=attr_uuid,
                fields={
                    "display_name": "Area",
                    "field_name": "area_sqkm",
                    "order": 2,
                },
                relations={},
            ),
            build_node(
                model="layers.layer",
                source_pk=9302,
                uuid_value=layer_uuid,
                fields=self._layer_fields("Layer With Attributes"),
                relations={
                    "attribute_fields": [
                        build_ref(
                            model="layers.attributeinfo",
                            source_pk=77701,
                            uuid_value=attr_uuid,
                        )
                    ]
                },
            ),
        ]

        import_fixture_rows(fixture_rows, **self._import_kwargs())

        imported_layer = Layer.objects.get(uuid=layer_uuid)
        imported_attr = AttributeInfo.objects.get(uuid=attr_uuid)
        self.assertEqual(imported_layer.attribute_fields.count(), 1)
        self.assertEqual(imported_layer.attribute_fields.first().pk, imported_attr.pk)

    def test_second_pass_resolves_companionship_layer_and_companions_by_uuid(self):
        self._require_importer()

        owner_uuid = uuid4()
        companion_a_uuid = uuid4()
        companion_b_uuid = uuid4()

        fixture_rows = [
            build_node(
                model="layers.layer",
                source_pk=9401,
                uuid_value=owner_uuid,
                fields=self._layer_fields("Owner Layer"),
                relations={},
            ),
            build_node(
                model="layers.layer",
                source_pk=9402,
                uuid_value=companion_a_uuid,
                fields=self._layer_fields("Companion A"),
                relations={},
            ),
            build_node(
                model="layers.layer",
                source_pk=9403,
                uuid_value=companion_b_uuid,
                fields=self._layer_fields("Companion B"),
                relations={},
            ),
            build_node(
                model="layers.companionship",
                source_pk=9404,
                uuid_value=None,
                fields={},
                relations={
                    "layer": build_ref(
                        model="layers.layer",
                        source_pk=55501,
                        uuid_value=owner_uuid,
                    ),
                    "companions": [
                        build_ref(
                            model="layers.layer",
                            source_pk=55502,
                            uuid_value=companion_a_uuid,
                        ),
                        build_ref(
                            model="layers.layer",
                            source_pk=55503,
                            uuid_value=companion_b_uuid,
                        ),
                    ],
                },
            ),
        ]

        import_fixture_rows(fixture_rows, **self._import_kwargs())

        imported_owner = Layer.objects.get(uuid=owner_uuid)
        companionship = Companionship.objects.get(layer=imported_owner)
        companion_uuids = set(
            companionship.companions.values_list("uuid", flat=True)
        )
        self.assertEqual(companion_uuids, {companion_a_uuid, companion_b_uuid})

    def test_multiple_companionship_rows_for_same_owner_merge_into_first_record(self):
        self._require_importer()

        owner_uuid = uuid4()
        companion_a_uuid = uuid4()
        companion_b_uuid = uuid4()
        companion_c_uuid = uuid4()

        fixture_rows = [
            build_node(
                model="layers.layer",
                source_pk=9411,
                uuid_value=owner_uuid,
                fields=self._layer_fields("Owner Layer"),
                relations={},
            ),
            build_node(
                model="layers.layer",
                source_pk=9412,
                uuid_value=companion_a_uuid,
                fields=self._layer_fields("Companion A"),
                relations={},
            ),
            build_node(
                model="layers.layer",
                source_pk=9413,
                uuid_value=companion_b_uuid,
                fields=self._layer_fields("Companion B"),
                relations={},
            ),
            build_node(
                model="layers.layer",
                source_pk=9414,
                uuid_value=companion_c_uuid,
                fields=self._layer_fields("Companion C"),
                relations={},
            ),
            build_node(
                model="layers.companionship",
                source_pk=9415,
                uuid_value=None,
                fields={},
                relations={
                    "layer": build_ref(
                        model="layers.layer",
                        source_pk=55601,
                        uuid_value=owner_uuid,
                    ),
                    "companions": [
                        build_ref(
                            model="layers.layer",
                            source_pk=55602,
                            uuid_value=companion_a_uuid,
                        ),
                        build_ref(
                            model="layers.layer",
                            source_pk=55603,
                            uuid_value=companion_b_uuid,
                        ),
                    ],
                },
            ),
            build_node(
                model="layers.companionship",
                source_pk=9416,
                uuid_value=None,
                fields={},
                relations={
                    "layer": build_ref(
                        model="layers.layer",
                        source_pk=55611,
                        uuid_value=owner_uuid,
                    ),
                    "companions": [
                        build_ref(
                            model="layers.layer",
                            source_pk=55612,
                            uuid_value=companion_c_uuid,
                        ),
                    ],
                },
            ),
        ]

        import_fixture_rows(fixture_rows, **self._import_kwargs())

        imported_owner = Layer.objects.get(uuid=owner_uuid)
        companionship_rows = Companionship.objects.filter(layer=imported_owner)
        self.assertEqual(companionship_rows.count(), 1)

        companionship = companionship_rows.first()
        companion_set = set(companionship.companions.values_list("uuid", flat=True))
        self.assertEqual(
            companion_set,
            {companion_a_uuid, companion_b_uuid, companion_c_uuid},
        )

        # Importing the same fixture again should not duplicate identical rows.
        import_fixture_rows(fixture_rows, **self._import_kwargs())
        self.assertEqual(Companionship.objects.filter(layer=imported_owner).count(), 1)
        companion_set = set(
            Companionship.objects.get(layer=imported_owner).companions.values_list("uuid", flat=True)
        )
        self.assertEqual(
            companion_set,
            {companion_a_uuid, companion_b_uuid, companion_c_uuid},
        )

    def test_missing_attribute_relation_uuid_raises_error_under_strict_policy(self):
        self._require_importer()

        layer_uuid = uuid4()
        missing_attr_uuid = uuid4()
        fixture_rows = [
            build_node(
                model="layers.layer",
                source_pk=9501,
                uuid_value=layer_uuid,
                fields=self._layer_fields("Layer Missing Attribute Ref"),
                relations={
                    "attribute_fields": [
                        build_ref(
                            model="layers.attributeinfo",
                            source_pk=88801,
                            uuid_value=missing_attr_uuid,
                        )
                    ]
                },
            )
        ]

        with self.assertRaises(ValueError):
            import_fixture_rows(fixture_rows, **self._import_kwargs())


class LayerFixtureImportPR07Test(TestCase):
    """PR07 contract tests for multilayer import graph integrity."""

    def _require_importer(self):
        self.assertIsNotNone(
            import_fixture_rows,
            "importer API missing: expected layers.fixture_import.import_fixture_rows",
        )

    def _import_kwargs(self):
        return {
            "dry_run": False,
            "associate_all_sites": True,
            "missing_ref_policy": "error",
            "duplicate_uuid_policy": "error",
        }

    def _layer_fields(self, name, layer_type="WMS"):
        return {
            "name": name,
            "layer_type": layer_type,
            "slug_name": None,
            "url": None,
        }

    def test_multilayer_dimension_value_association_graph_resolves_by_uuid(self):
        self._require_importer()

        parent_uuid = uuid4()
        target_a_uuid = uuid4()
        target_b_uuid = uuid4()
        dimension_uuid = uuid4()
        association_a_uuid = uuid4()
        association_b_uuid = uuid4()
        association_without_layer_uuid = uuid4()
        value_1_uuid = uuid4()
        value_2_uuid = uuid4()

        fixture_rows = [
            build_node(
                model="layers.layer",
                source_pk=1001,
                uuid_value=parent_uuid,
                fields=self._layer_fields("Parent Slider Layer"),
                relations={},
            ),
            build_node(
                model="layers.layer",
                source_pk=1002,
                uuid_value=target_a_uuid,
                fields=self._layer_fields("Target A"),
                relations={},
            ),
            build_node(
                model="layers.layer",
                source_pk=1003,
                uuid_value=target_b_uuid,
                fields=self._layer_fields("Target B"),
                relations={},
            ),
            build_node(
                model="layers.multilayerdimension",
                source_pk=1101,
                uuid_value=dimension_uuid,
                fields={
                    "name": "Year",
                    "label": "Year",
                    "order": 10,
                    "animated": True,
                    "angle_labels": False,
                },
                relations={
                    "layer": build_ref(
                        model="layers.layer",
                        source_pk=50101,
                        uuid_value=parent_uuid,
                    )
                },
            ),
            build_node(
                model="layers.multilayerassociation",
                source_pk=1201,
                uuid_value=association_a_uuid,
                fields={"name": "A"},
                relations={
                    "parentLayer": build_ref(
                        model="layers.layer",
                        source_pk=50201,
                        uuid_value=parent_uuid,
                    ),
                    "layer": build_ref(
                        model="layers.layer",
                        source_pk=50202,
                        uuid_value=target_a_uuid,
                    ),
                },
            ),
            build_node(
                model="layers.multilayerassociation",
                source_pk=1202,
                uuid_value=association_b_uuid,
                fields={"name": "B"},
                relations={
                    "parentLayer": build_ref(
                        model="layers.layer",
                        source_pk=50301,
                        uuid_value=parent_uuid,
                    ),
                    "layer": build_ref(
                        model="layers.layer",
                        source_pk=50302,
                        uuid_value=target_b_uuid,
                    ),
                },
            ),
            build_node(
                model="layers.multilayerassociation",
                source_pk=1203,
                uuid_value=association_without_layer_uuid,
                fields={"name": "No target layer"},
                relations={
                    "parentLayer": build_ref(
                        model="layers.layer",
                        source_pk=50311,
                        uuid_value=parent_uuid,
                    ),
                    "layer": None,
                },
            ),
            build_node(
                model="layers.multilayerdimensionvalue",
                source_pk=1301,
                uuid_value=value_1_uuid,
                fields={"value": "2020", "label": "2020", "order": 1},
                relations={
                    "dimension": build_ref(
                        model="layers.multilayerdimension",
                        source_pk=50401,
                        uuid_value=dimension_uuid,
                    ),
                    "associations": [
                        build_ref(
                            model="layers.multilayerassociation",
                            source_pk=50402,
                            uuid_value=association_a_uuid,
                        )
                    ],
                },
            ),
            build_node(
                model="layers.multilayerdimensionvalue",
                source_pk=1302,
                uuid_value=value_2_uuid,
                fields={"value": "2021", "label": "2021", "order": 2},
                relations={
                    "dimension": build_ref(
                        model="layers.multilayerdimension",
                        source_pk=50501,
                        uuid_value=dimension_uuid,
                    ),
                    "associations": [
                        build_ref(
                            model="layers.multilayerassociation",
                            source_pk=50502,
                            uuid_value=association_b_uuid,
                        ),
                        build_ref(
                            model="layers.multilayerassociation",
                            source_pk=50503,
                            uuid_value=association_without_layer_uuid,
                        ),
                    ],
                },
            ),
        ]

        import_fixture_rows(fixture_rows, **self._import_kwargs())

        imported_parent = Layer.objects.get(uuid=parent_uuid)
        imported_target_a = Layer.objects.get(uuid=target_a_uuid)
        imported_target_b = Layer.objects.get(uuid=target_b_uuid)

        imported_dimension = MultilayerDimension.objects.get(uuid=dimension_uuid)
        self.assertEqual(imported_dimension.layer_id, imported_parent.pk)
        self.assertEqual(MultilayerDimension.objects.count(), 1)
        self.assertEqual(MultilayerDimensionValue.objects.count(), 2)
        self.assertEqual(MultilayerAssociation.objects.count(), 3)

        association_a = MultilayerAssociation.objects.get(uuid=association_a_uuid)
        association_b = MultilayerAssociation.objects.get(uuid=association_b_uuid)
        association_without_layer = MultilayerAssociation.objects.get(
            uuid=association_without_layer_uuid
        )
        self.assertEqual(association_a.parentLayer_id, imported_parent.pk)
        self.assertEqual(association_b.parentLayer_id, imported_parent.pk)
        self.assertEqual(association_without_layer.parentLayer_id, imported_parent.pk)
        self.assertEqual(association_a.layer_id, imported_target_a.pk)
        self.assertEqual(association_b.layer_id, imported_target_b.pk)
        self.assertIsNone(association_without_layer.layer_id)

        value_1 = MultilayerDimensionValue.objects.get(uuid=value_1_uuid)
        value_2 = MultilayerDimensionValue.objects.get(uuid=value_2_uuid)
        self.assertEqual(value_1.dimension_id, imported_dimension.pk)
        self.assertEqual(value_2.dimension_id, imported_dimension.pk)
        self.assertEqual(
            set(value_1.associations.values_list("uuid", flat=True)),
            {association_a_uuid},
        )
        self.assertEqual(
            set(value_2.associations.values_list("uuid", flat=True)),
            {association_b_uuid, association_without_layer_uuid},
        )

    def test_missing_dimension_or_association_reference_raises_in_strict_mode(self):
        self._require_importer()

        value_uuid = uuid4()
        missing_dimension_uuid = uuid4()
        missing_association_uuid = uuid4()

        fixture_rows = [
            build_node(
                model="layers.multilayerdimensionvalue",
                source_pk=1401,
                uuid_value=value_uuid,
                fields={"value": "X", "label": "X", "order": 1},
                relations={
                    "dimension": build_ref(
                        model="layers.multilayerdimension",
                        source_pk=60101,
                        uuid_value=missing_dimension_uuid,
                    ),
                    "associations": [
                        build_ref(
                            model="layers.multilayerassociation",
                            source_pk=60102,
                            uuid_value=missing_association_uuid,
                        )
                    ],
                },
            )
        ]

        with self.assertRaises(ValueError):
            import_fixture_rows(fixture_rows, **self._import_kwargs())

    def test_second_pass_resolves_specific_layer_rows_by_layer_uuid(self):
        self._require_importer()

        wms_uuid = uuid4()
        arcrest_uuid = uuid4()
        xyz_uuid = uuid4()
        afs_uuid = uuid4()
        vector_uuid = uuid4()

        fixture_rows = [
            build_node(
                model="layers.layer",
                source_pk=9601,
                uuid_value=wms_uuid,
                fields={**self._layer_fields("WMS Layer"), "layer_type": "WMS"},
                relations={},
            ),
            build_node(
                model="layers.layer",
                source_pk=9602,
                uuid_value=arcrest_uuid,
                fields={**self._layer_fields("ArcREST Layer"), "layer_type": "ArcRest"},
                relations={},
            ),
            build_node(
                model="layers.layer",
                source_pk=9603,
                uuid_value=xyz_uuid,
                fields={**self._layer_fields("XYZ Layer"), "layer_type": "XYZ"},
                relations={},
            ),
            build_node(
                model="layers.layer",
                source_pk=9604,
                uuid_value=afs_uuid,
                fields={
                    **self._layer_fields("ArcFeature Layer"),
                    "layer_type": "ArcFeatureServer",
                },
                relations={},
            ),
            build_node(
                model="layers.layer",
                source_pk=9605,
                uuid_value=vector_uuid,
                fields={**self._layer_fields("Vector Layer"), "layer_type": "Vector"},
                relations={},
            ),
            build_node(
                model="layers.layerwms",
                source_pk=9701,
                uuid_value=None,
                fields={"wms_slug": "sample:layer", "wms_version": "1.1.1"},
                relations={
                    "layer": build_ref(
                        model="layers.layer",
                        source_pk=19901,
                        uuid_value=wms_uuid,
                    )
                },
            ),
            build_node(
                model="layers.layerarcrest",
                source_pk=9702,
                uuid_value=None,
                fields={"arcgis_layers": "0,1"},
                relations={
                    "layer": build_ref(
                        model="layers.layer",
                        source_pk=19902,
                        uuid_value=arcrest_uuid,
                    )
                },
            ),
            build_node(
                model="layers.layerxyz",
                source_pk=9703,
                uuid_value=None,
                fields={},
                relations={
                    "layer": build_ref(
                        model="layers.layer",
                        source_pk=19903,
                        uuid_value=xyz_uuid,
                    )
                },
            ),
            build_node(
                model="layers.layerarcfeatureservice",
                source_pk=9704,
                uuid_value=None,
                fields={"arcgis_layers": "2"},
                relations={
                    "layer": build_ref(
                        model="layers.layer",
                        source_pk=19904,
                        uuid_value=afs_uuid,
                    )
                },
            ),
            build_node(
                model="layers.layervector",
                source_pk=9705,
                uuid_value=None,
                fields={"lookup_field": "kind"},
                relations={
                    "layer": build_ref(
                        model="layers.layer",
                        source_pk=19905,
                        uuid_value=vector_uuid,
                    )
                },
            ),
        ]

        import_fixture_rows(fixture_rows, **self._import_kwargs())

        self.assertTrue(LayerWMS.objects.filter(layer__uuid=wms_uuid).exists())
        self.assertTrue(LayerArcREST.objects.filter(layer__uuid=arcrest_uuid).exists())
        self.assertTrue(LayerXYZ.objects.filter(layer__uuid=xyz_uuid).exists())
        self.assertTrue(
            LayerArcFeatureService.objects.filter(layer__uuid=afs_uuid).exists()
        )
        self.assertTrue(LayerVector.objects.filter(layer__uuid=vector_uuid).exists())

    def test_vector_lookup_table_relations_resolve_by_lookup_uuid(self):
        self._require_importer()

        vector_uuid = uuid4()
        lookup_uuid = uuid4()

        fixture_rows = [
            build_node(
                model="layers.layer",
                source_pk=9801,
                uuid_value=vector_uuid,
                fields={**self._layer_fields("Vector + Lookup"), "layer_type": "Vector"},
                relations={},
            ),
            build_node(
                model="layers.lookupinfo",
                source_pk=9802,
                uuid_value=lookup_uuid,
                fields={"value": "1", "description": "one", "dashstyle": "solid"},
                relations={},
            ),
            build_node(
                model="layers.layervector",
                source_pk=9803,
                uuid_value=None,
                fields={"lookup_field": "class"},
                relations={
                    "layer": build_ref(
                        model="layers.layer",
                        source_pk=29901,
                        uuid_value=vector_uuid,
                    ),
                    "lookup_table": [
                        build_ref(
                            model="layers.lookupinfo",
                            source_pk=29902,
                            uuid_value=lookup_uuid,
                        )
                    ],
                },
            ),
        ]

        import_fixture_rows(fixture_rows, **self._import_kwargs())

        vector_row = LayerVector.objects.get(layer__uuid=vector_uuid)
        self.assertEqual(vector_row.lookup_table.count(), 1)
        self.assertEqual(vector_row.lookup_table.first().uuid, lookup_uuid)

    def test_missing_relation_uuid_raises_error_under_strict_policy(self):
        """Raise ValueError if required relations are missing from the fixture."""
        self._require_importer()

        assoc_uuid = uuid4()
        missing_parent_uuid = uuid4()
        missing_target_uuid = uuid4()
        fixture_rows = [
            build_node(
                model="layers.multilayerassociation",
                source_pk=601,
                uuid_value=assoc_uuid,
                fields={"name": "Val-1aVal-2b"},
                relations={
                    "parentLayer": build_ref(
                        model="layers.layer",
                        source_pk=9601,
                        uuid_value=missing_parent_uuid,
                    ),
                    "layer": build_ref(
                        model="layers.layer",
                        source_pk=9602,
                        uuid_value=missing_target_uuid,
                    ),
                },
            )
        ]

        with self.assertRaises(ValueError):
            import_fixture_rows(fixture_rows, **self._import_kwargs())

from django.test import TestCase

from layers.fixture_contract import (
    NODE_FIELDS_KEY,
    NODE_MODEL_KEY,
    NODE_RELATIONS_KEY,
    NODE_SOURCE_PK_KEY,
)
from layers.models import (
    Layer,
    MultilayerDimension,
    MultilayerDimensionValue,
)


class LayerMultilayerFixtureExportTest(TestCase):
    def test_export_includes_only_multilayer_records_scoped_to_root_layer(self):
        """PR04 scope rules:
        1) Include only dimensions where dimension.layer == export layer.
        2) Include all values whose dimension is one of those dimensions.
        3) Include only associations where:
           - association.parentLayer == export layer, and
           - association appears in at least one selected value.associations.
        """
        export_layer = Layer.objects.create(name='Export Layer', layer_type='WMS')
        other_layer = Layer.objects.create(name='Other Layer', layer_type='WMS')

        # Dimensions: only root_dimension should be exported.
        root_dimension = MultilayerDimension.objects.create(
            layer=export_layer,
            name='Month',
            label='Month',
            order=1,
        )
        other_dimension = MultilayerDimension.objects.create(
            layer=other_layer,
            name='Depth',
            label='Depth',
            order=1,
        )

        # Values: only values under root_dimension should be exported.
        root_value_a = MultilayerDimensionValue.objects.create(
            dimension=root_dimension,
            value='Jan',
            label='January',
            order=1,
        )
        root_value_b = MultilayerDimensionValue.objects.create(
            dimension=root_dimension,
            value='Feb',
            label='February',
            order=2,
        )
        other_value = MultilayerDimensionValue.objects.create(
            dimension=other_dimension,
            value='10m',
            label='10m',
            order=1,
        )

        # Modify the associations generated as each value was saved.
        included_association = root_value_a.associations.order_by('pk').first()
        included_association.name = 'included'
        included_association.layer = other_layer
        included_association.save(update_fields=['name', 'layer'])

        wrong_parent_association = other_value.associations.order_by('pk').first()
        wrong_parent_association.layer = export_layer
        wrong_parent_association.save(update_fields=['layer'])
        root_value_a.associations.add(wrong_parent_association)

        unreferenced_association = root_value_b.associations.order_by('pk').first()
        unreferenced_association.name = 'unreferenced'
        unreferenced_association.layer = export_layer
        unreferenced_association.save(update_fields=['name', 'layer'])
        root_value_b.associations.remove(unreferenced_association)

        fixture_data = export_layer.to_export_dict()

        exported_dimension_pks = {
            row[NODE_SOURCE_PK_KEY]
            for row in fixture_data
            if row[NODE_MODEL_KEY] == 'layers.multilayerdimension'
        }
        exported_value_pks = {
            row[NODE_SOURCE_PK_KEY]
            for row in fixture_data
            if row[NODE_MODEL_KEY] == 'layers.multilayerdimensionvalue'
        }
        exported_association_pks = {
            row[NODE_SOURCE_PK_KEY]
            for row in fixture_data
            if row[NODE_MODEL_KEY] == 'layers.multilayerassociation'
        }

        self.assertEqual(exported_dimension_pks, {root_dimension.pk})
        self.assertEqual(exported_value_pks, {root_value_a.pk, root_value_b.pk})
        self.assertEqual(exported_association_pks, {included_association.pk})

    def test_export_multilayer_two_by_three_includes_reused_unique_associations_and_seven_layers(self):
        """PR04 multilayer semantics:
        - Association names should round-trip as-is and do not require spaces.
        - The same association is reused across dimension values, not duplicated.
        - Association target layer must never be the exported parent layer.
        - For 2x3 values, export parent + 6 associated layers (7 total).
        """

        def _cap_first_token(value):
            if not value:
                return value
            return '{}{}'.format(value[0].upper(), value[1:])

        export_layer = Layer.objects.create(name='Layer 2x3 Parent', layer_type='WMS')

        dim_one = MultilayerDimension.objects.create(
            layer=export_layer,
            name='dim-1',
            label='Dim 1',
            order=1,
        )
        dim_two = MultilayerDimension.objects.create(
            layer=export_layer,
            name='dim-2',
            label='Dim 2',
            order=2,
        )

        dim_one_values = [
            MultilayerDimensionValue.objects.create(
                dimension=dim_one,
                value='val-1a',
                label='Val 1a',
                order=1,
            ),
            MultilayerDimensionValue.objects.create(
                dimension=dim_one,
                value='val-1b',
                label='Val 1b',
                order=2,
            ),
        ]
        dim_two_values = [
            MultilayerDimensionValue.objects.create(
                dimension=dim_two,
                value='val-2a',
                label='Val 2a',
                order=1,
            ),
            MultilayerDimensionValue.objects.create(
                dimension=dim_two,
                value='val-2b',
                label='Val 2b',
                order=2,
            ),
            MultilayerDimensionValue.objects.create(
                dimension=dim_two,
                value='val-2c',
                label='Val 2c',
                order=3,
            ),
        ]

        combo_to_target_layer = {}
        combo_to_association = {}
        for dim_one_value in dim_one_values:
            for dim_two_value in dim_two_values:
                association_name = '{}{}'.format(
                    _cap_first_token(dim_one_value.value),
                    _cap_first_token(dim_two_value.value),
                )
                target_layer = Layer.objects.create(
                    name='Target {}'.format(association_name),
                    layer_type='WMS',
                )
                association = dim_one_value.associations.filter(
                    pk__in=dim_two_value.associations.values_list('pk', flat=True),
                ).order_by('pk').first()
                self.assertIsNotNone(association)
                association.layer = target_layer
                association.name = association_name
                association.save(update_fields=['layer', 'name'])
                combo_to_target_layer[association_name] = target_layer
                combo_to_association[association_name] = association

        fixture_data = export_layer.to_export_dict()

        layer_rows = [
            row
            for row in fixture_data
            if row[NODE_MODEL_KEY] == 'layers.layer'
        ]
        association_rows = [
            row
            for row in fixture_data
            if row[NODE_MODEL_KEY] == 'layers.multilayerassociation'
        ]
        value_rows = [
            row
            for row in fixture_data
            if row[NODE_MODEL_KEY] == 'layers.multilayerdimensionvalue'
        ]

        exported_layer_pks = {row[NODE_SOURCE_PK_KEY] for row in layer_rows}
        expected_layer_pks = {export_layer.pk}
        expected_layer_pks.update(layer.pk for layer in combo_to_target_layer.values())
        self.assertEqual(exported_layer_pks, expected_layer_pks)
        self.assertEqual(len(exported_layer_pks), 7)

        exported_association_names = {
            row[NODE_FIELDS_KEY]['name']
            for row in association_rows
        }
        self.assertEqual(exported_association_names, set(combo_to_target_layer.keys()))
        self.assertEqual(len(association_rows), 6)

        exported_association_name_to_layer_pk = {
            row[NODE_FIELDS_KEY]['name']: row[NODE_RELATIONS_KEY]['layer'][NODE_SOURCE_PK_KEY]
            for row in association_rows
        }
        self.assertEqual(
            exported_association_name_to_layer_pk,
            {name: layer.pk for name, layer in combo_to_target_layer.items()},
        )
        self.assertNotIn(
            export_layer.pk,
            {row[NODE_RELATIONS_KEY]['layer'][NODE_SOURCE_PK_KEY] for row in association_rows},
        )

        value_by_value_field = {
            row[NODE_FIELDS_KEY]['value']: row
            for row in value_rows
        }
        self.assertIn('val-1a', value_by_value_field)
        self.assertIn('val-2b', value_by_value_field)

        associations_for_val_1a = {
            ref[NODE_SOURCE_PK_KEY]
            for ref in value_by_value_field['val-1a'][NODE_RELATIONS_KEY]['associations']
        }
        associations_for_val_2b = {
            ref[NODE_SOURCE_PK_KEY]
            for ref in value_by_value_field['val-2b'][NODE_RELATIONS_KEY]['associations']
        }

        association_pk_for_val_1a_val_2b = combo_to_association['Val-1aVal-2b'].pk
        self.assertIn(association_pk_for_val_1a_val_2b, associations_for_val_1a)
        self.assertIn(association_pk_for_val_1a_val_2b, associations_for_val_2b)

    def test_export_multilayer_two_by_two_reuses_four_unique_associations(self):
        def _cap_first_token(value):
            if not value:
                return value
            return '{}{}'.format(value[0].upper(), value[1:])

        export_layer = Layer.objects.create(name='Layer 2x2 Parent', layer_type='WMS')

        dim_one = MultilayerDimension.objects.create(
            layer=export_layer,
            name='dim-1',
            label='Dim 1',
            order=1,
        )
        dim_two = MultilayerDimension.objects.create(
            layer=export_layer,
            name='dim-2',
            label='Dim 2',
            order=2,
        )

        dim_one_values = [
            MultilayerDimensionValue.objects.create(
                dimension=dim_one,
                value='val-1a',
                label='Val 1a',
                order=1,
            ),
            MultilayerDimensionValue.objects.create(
                dimension=dim_one,
                value='val-1b',
                label='Val 1b',
                order=2,
            ),
        ]
        dim_two_values = [
            MultilayerDimensionValue.objects.create(
                dimension=dim_two,
                value='val-2a',
                label='Val 2a',
                order=1,
            ),
            MultilayerDimensionValue.objects.create(
                dimension=dim_two,
                value='val-2b',
                label='Val 2b',
                order=2,
            ),
        ]

        associations = {}
        for dim_one_value in dim_one_values:
            for dim_two_value in dim_two_values:
                association_name = '{}{}'.format(
                    _cap_first_token(dim_one_value.value),
                    _cap_first_token(dim_two_value.value),
                )
                target_layer = Layer.objects.create(
                    name='Target {}'.format(association_name),
                    layer_type='WMS',
                )
                association = dim_one_value.associations.filter(
                    pk__in=dim_two_value.associations.values_list('pk', flat=True),
                ).order_by('pk').first()
                self.assertIsNotNone(association)
                association.layer = target_layer
                association.name = association_name
                association.save(update_fields=['layer', 'name'])
                associations[association_name] = association

        fixture_data = export_layer.to_export_dict()

        association_rows = [
            row for row in fixture_data if row[NODE_MODEL_KEY] == 'layers.multilayerassociation'
        ]
        value_rows = {
            row[NODE_FIELDS_KEY]['value']: row
            for row in fixture_data
            if row[NODE_MODEL_KEY] == 'layers.multilayerdimensionvalue'
        }

        self.assertEqual(len(association_rows), 4)
        self.assertEqual(
            {row[NODE_SOURCE_PK_KEY] for row in association_rows},
            {association.pk for association in associations.values()},
        )
        self.assertEqual(
            len(value_rows['val-1a'][NODE_RELATIONS_KEY]['associations']),
            2,
        )
        self.assertEqual(
            len(value_rows['val-2b'][NODE_RELATIONS_KEY]['associations']),
            2,
        )

        shared_association_pk = associations['Val-1aVal-2b'].pk
        self.assertIn(
            shared_association_pk,
            {
                ref[NODE_SOURCE_PK_KEY]
                for ref in value_rows['val-1a'][NODE_RELATIONS_KEY]['associations']
            },
        )
        self.assertIn(
            shared_association_pk,
            {
                ref[NODE_SOURCE_PK_KEY]
                for ref in value_rows['val-2b'][NODE_RELATIONS_KEY]['associations']
            },
        )

    def test_export_includes_associations_with_null_target_layer(self):
        export_layer = Layer.objects.create(
            name='Hurricane Tracks Since 1980 in the North Atlantic Slider',
            layer_type='slider',
        )
        dimension = MultilayerDimension.objects.create(
            layer=export_layer,
            name='Decade',
            label='Decade',
            order=201,
        )

        values = []
        for decade in ('1980-1989', '1990-1999', '2000-2009', '2010-2019'):
            association_name = 'Decade: {}'.format(decade)
            value = MultilayerDimensionValue.objects.create(
                dimension=dimension,
                value='| {} |'.format(association_name),
                label=decade,
                order=300 + len(values),
            )
            values.append((decade, value))

        value_association_pairs = []
        for decade, value in values:
            association = value.associations.order_by('pk').first()
            association.name = 'Decade: {}'.format(decade)
            association.layer = None
            association.save(update_fields=['name', 'layer'])
            value_association_pairs.append((value, association))

        fixture_data = export_layer.to_export_dict()
        association_rows = [
            row for row in fixture_data
            if row[NODE_MODEL_KEY] == 'layers.multilayerassociation'
        ]
        value_rows = {
            row[NODE_SOURCE_PK_KEY]: row
            for row in fixture_data
            if row[NODE_MODEL_KEY] == 'layers.multilayerdimensionvalue'
        }

        self.assertEqual(len(association_rows), 4)
        self.assertEqual(
            {row[NODE_FIELDS_KEY]['name'] for row in association_rows},
            {'Decade: {}'.format(decade) for decade in ('1980-1989', '1990-1999', '2000-2009', '2010-2019')},
        )
        self.assertTrue(all(
            row[NODE_RELATIONS_KEY]['layer'] is None
            for row in association_rows
        ))
        for value, association in value_association_pairs:
            self.assertEqual(
                value_rows[value.pk][NODE_RELATIONS_KEY]['associations'],
                [{
                    NODE_MODEL_KEY: 'layers.multilayerassociation',
                    NODE_SOURCE_PK_KEY: association.pk,
                    'uuid': str(association.uuid),
                }],
            )

from django.test import SimpleTestCase

from layers.fixture_contract import (
    NODE_MODEL_KEY,
    NODE_SOURCE_PK_KEY,
    NODE_UUID_KEY,
    build_node,
    build_ref,
)
from layers.fixture_traversal import (
    TraversalLimitExceeded,
    mark_visited,
    node_identity_key,
    ref_identity_key,
    should_descend,
    stable_dedupe_nodes,
    stable_dedupe_refs,
    use_node_budget,
)


class FixtureTraversalTest(SimpleTestCase):
    def test_ref_identity_key_prefers_uuid_over_source_pk(self):
        """Does the traversal recognize two references are the same by UUID, 
        even if the source_pk is different?
        It should."""
        ref_one = build_ref(model="layers.layer", source_pk=1, uuid_value="abc")
        ref_two = build_ref(model="layers.layer", source_pk=999, uuid_value="abc")

        self.assertEqual(ref_identity_key(ref_one), ref_identity_key(ref_two))

    def test_ref_identity_key_falls_back_to_source_pk_when_uuid_missing(self):
        """If no UUID, records with different 'id' should be considered different."""
        ref_one = build_ref(model="layers.layer", source_pk=1, uuid_value=None)
        ref_two = build_ref(model="layers.layer", source_pk=2, uuid_value=None)

        self.assertNotEqual(ref_identity_key(ref_one), ref_identity_key(ref_two))

    def test_node_identity_key_prefers_uuid_over_source_pk(self):
        """Test that two nodes with the same UUID are considered the same, 
        even if their 'id' is different."""
        node_one = build_node("layers.layer", 11, "same-uuid", fields={}, relations={})
        node_two = build_node("layers.layer", 12, "same-uuid", fields={}, relations={})

        self.assertEqual(node_identity_key(node_one), node_identity_key(node_two))

    def test_stable_dedupe_refs_removes_duplicates_and_keeps_order(self):
        """Test that stable_dedupe_refs removes duplicates based on identity key and 
        preserves the order of first-seen references."""
        ref_a = build_ref(model="layers.lookupinfo", source_pk=10, uuid_value="u-a")
        ref_a_dupe = build_ref(model="layers.lookupinfo", source_pk=999, uuid_value="u-a")
        ref_b = build_ref(model="layers.lookupinfo", source_pk=11, uuid_value="u-b")

        deduped = stable_dedupe_refs([ref_a, ref_b, ref_a_dupe])

        self.assertEqual(deduped, [ref_a, ref_b])

    def test_stable_dedupe_nodes_removes_duplicates_and_keeps_order(self):
        """Test that stable_dedupe_nodes removes duplicates based on identity key and 
        preserves the order of first-seen nodes."""
        node_a = build_node("layers.layer", 10, "uuid-a", fields={"name": "A"}, relations={})
        node_a_dupe = build_node("layers.layer", 999, "uuid-a", fields={"name": "A2"}, relations={})
        node_b = build_node("layers.layer", 11, "uuid-b", fields={"name": "B"}, relations={})

        deduped = stable_dedupe_nodes([node_a, node_b, node_a_dupe])

        self.assertEqual(deduped, [node_a, node_b])

    def test_should_descend_honors_max_depth(self):
        """Test small helper that is simple as "is a <= b?" for traversal depth."""
        self.assertTrue(should_descend(depth=0, max_depth=None))
        self.assertTrue(should_descend(depth=1, max_depth=1))
        self.assertFalse(should_descend(depth=2, max_depth=1))

    def test_use_node_budget_raises_when_limit_exceeded(self):
        """Test that correct error is raised when traversal goes
        too deep"""
        count = 0
        count = use_node_budget(current_count=count, max_nodes=2)
        count = use_node_budget(current_count=count, max_nodes=2)

        with self.assertRaises(TraversalLimitExceeded):
            use_node_budget(current_count=count, max_nodes=2)

    def test_mark_visited_returns_false_for_repeat_identity(self):
        """Test that mark_visited returns True for first-seen identity key, 
        and False for repeats."""
        ref_obj = build_ref(model="layers.layer", source_pk=1, uuid_value="same")
        visited = set()

        self.assertTrue(mark_visited(visited, ref_identity_key(ref_obj)))
        self.assertFalse(mark_visited(visited, ref_identity_key(ref_obj)))

    def test_stable_dedupe_nodes_keeps_fixture_key_shape(self):
        """Ensure that `stable_dedupe_nodes` doesn't change the node content"""
        node = build_node("layers.layer", 1, "uuid-1", fields={"x": 1}, relations={})
        deduped = stable_dedupe_nodes([node])

        self.assertEqual(deduped[0][NODE_MODEL_KEY], "layers.layer")
        self.assertEqual(deduped[0][NODE_SOURCE_PK_KEY], 1)
        self.assertEqual(deduped[0][NODE_UUID_KEY], "uuid-1")

import json
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from layers.fixture_contract import build_node
from layers.models import Layer


class LayerFixtureImportAdminTest(TestCase):
    """PR07.01 contract tests for the Layer fixture import admin workflow."""

    upload_url_name = "admin:layers_layer_import_fixture"

    def setUp(self):
        self.upload_url = reverse(self.upload_url_name)
        self.superuser = get_user_model().objects.create_superuser(
            username="fixture-admin",
            email="fixture-admin@example.com",
            password="password",
        )
        self.valid_rows = [
            build_node(
                model="layers.layer",
                source_pk=1001,
                uuid_value=uuid4(),
                fields={
                    "name": "Uploaded Fixture Layer",
                    "layer_type": "WMS",
                    "slug_name": None,
                    "url": None,
                },
                relations={},
            )
        ]

    def _fixture_file(self, rows=None, name="layers.json"):
        return SimpleUploadedFile(
            name,
            json.dumps(rows if rows is not None else self.valid_rows).encode("utf-8"),
            content_type="application/json",
        )

    def test_upload_view_requires_layer_change_permission(self):
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 302)

        user = get_user_model().objects.create_user(
            username="no-layer-permission",
            password="password",
            is_staff=True,
        )
        self.client.force_login(user)
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 403)

    @patch("layers.admin.import_fixture_rows")
    def test_valid_upload_runs_dry_run_and_shows_confirmation(self, import_fixture_rows):
        self.client.force_login(self.superuser)
        import_fixture_rows.return_value = {"imported": 1, "dry_run": True}

        response = self.client.post(
            self.upload_url,
            {"fixture_file": self._fixture_file()},
        )

        self.assertEqual(response.status_code, 200)
        import_fixture_rows.assert_called_once_with(
            self.valid_rows,
            dry_run=True,
            associate_all_sites=True,
            missing_ref_policy="error",
            duplicate_uuid_policy="error",
        )
        self.assertContains(response, "Uploaded Fixture Layer")
        self.assertContains(response, "Confirm")
        self.assertEqual(Layer.all_objects.count(), 0)

    @patch("layers.admin.import_fixture_rows")
    def test_preview_reports_uuid_matched_updates_and_changed_field_values(
        self,
        import_fixture_rows,
    ):
        self.client.force_login(self.superuser)
        existing_layer = Layer.all_objects.create(
            name="Current Layer Name",
            layer_type="WMS",
            url="https://current.example.test/wms",
        )
        fixture_rows = [
            build_node(
                model="layers.layer",
                source_pk=1001,
                uuid_value=existing_layer.uuid,
                fields={
                    "name": "Imported Layer Name",
                    "layer_type": "WMS",
                    "slug_name": None,
                    "url": "https://imported.example.test/wms",
                },
                relations={},
            )
        ]
        import_fixture_rows.return_value = {"imported": 1, "dry_run": True}

        response = self.client.post(
            self.upload_url,
            {"fixture_file": self._fixture_file(fixture_rows)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Update existing record")
        self.assertContains(response, "name")
        self.assertContains(response, "Current Layer Name")
        self.assertContains(response, "Imported Layer Name")
        self.assertContains(response, "url")
        self.assertContains(response, "https://current.example.test/wms")
        self.assertContains(response, "https://imported.example.test/wms")

    @patch("layers.admin.import_fixture_rows")
    def test_invalid_json_displays_error_without_import(self, import_fixture_rows):
        self.client.force_login(self.superuser)
        invalid_file = SimpleUploadedFile(
            "broken.json",
            b"{not valid json",
            content_type="application/json",
        )

        response = self.client.post(self.upload_url, {"fixture_file": invalid_file})

        self.assertEqual(response.status_code, 200)
        import_fixture_rows.assert_not_called()
        self.assertContains(response, "valid JSON")
        self.assertEqual(Layer.all_objects.count(), 0)

    @patch("layers.admin.import_fixture_rows")
    def test_confirmation_executes_staged_fixture_not_posted_payload(self, import_fixture_rows):
        self.client.force_login(self.superuser)
        import_fixture_rows.return_value = {"imported": 1, "dry_run": True}

        preview_response = self.client.post(
            self.upload_url,
            {"fixture_file": self._fixture_file()},
        )
        self.assertEqual(preview_response.status_code, 200)

        import_fixture_rows.reset_mock()
        import_fixture_rows.return_value = {"imported": 1, "dry_run": False}
        tampered_rows = [
            build_node(
                model="layers.layer",
                source_pk=9999,
                uuid_value=uuid4(),
                fields={
                    "name": "Tampered Layer",
                    "layer_type": "WMS",
                    "slug_name": None,
                    "url": None,
                },
                relations={},
            )
        ]

        response = self.client.post(
            self.upload_url,
            {"confirm": "1", "fixture_file": self._fixture_file(tampered_rows)},
        )

        self.assertEqual(response.status_code, 302)
        import_fixture_rows.assert_called_once_with(
            self.valid_rows,
            dry_run=False,
            associate_all_sites=True,
            missing_ref_policy="error",
            duplicate_uuid_policy="error",
        )

    @patch("layers.admin.import_fixture_rows")
    def test_cancel_discards_staged_fixture_without_import(self, import_fixture_rows):
        self.client.force_login(self.superuser)
        import_fixture_rows.return_value = {"imported": 1, "dry_run": True}

        self.client.post(self.upload_url, {"fixture_file": self._fixture_file()})
        import_fixture_rows.reset_mock()

        response = self.client.post(self.upload_url, {"cancel": "1"})

        self.assertRedirects(response, reverse("admin:layers_layer_changelist"))
        import_fixture_rows.assert_not_called()
        self.assertEqual(Layer.all_objects.count(), 0)

import json
from unittest.mock import Mock, patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from layers.fixture_contract import build_node
from layers.admin import export_theme_details
from layers.models import ChildOrder, Layer, Theme


class ThemeFixtureImportAdminTest(TestCase):
    """Contract tests for the Theme fixture import admin workflow."""

    upload_url_name = "admin:layers_theme_import_fixture"

    def setUp(self):
        self.upload_url = reverse(self.upload_url_name)
        self.superuser = get_user_model().objects.create_superuser(
            username="theme-fixture-admin",
            email="theme-fixture-admin@example.com",
            password="password",
        )
        self.theme_uuid = uuid4()
        self.valid_rows = [
            build_node(
                model="layers.theme",
                source_pk=1001,
                uuid_value=self.theme_uuid,
                fields={
                    "name": "Uploaded Fixture Theme",
                    "display_name": "Uploaded Fixture Theme",
                    "theme_type": "checkbox",
                    "order": 10,
                    "is_visible": True,
                    "is_top_theme": False,
                },
                relations={},
            )
        ]

    def _fixture_file(self, rows=None, name="themes.json"):
        return SimpleUploadedFile(
            name,
            json.dumps(rows if rows is not None else self.valid_rows).encode("utf-8"),
            content_type="application/json",
        )

    def test_upload_view_requires_theme_change_permission(self):
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 302)

        user = get_user_model().objects.create_user(
            username="no-theme-permission",
            password="password",
            is_staff=True,
        )
        self.client.force_login(user)
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 403)

    @patch("layers.admin.import_fixture_rows")
    def test_valid_upload_runs_dry_run_and_shows_confirmation(self, import_fixture_rows):
        self.client.force_login(self.superuser)
        import_fixture_rows.return_value = {"imported": 1, "dry_run": True}

        response = self.client.post(
            self.upload_url,
            {"fixture_file": self._fixture_file()},
        )

        self.assertEqual(response.status_code, 200)
        import_fixture_rows.assert_called_once_with(
            self.valid_rows,
            dry_run=True,
            associate_all_sites=True,
            missing_ref_policy="error",
            duplicate_uuid_policy="error",
        )
        self.assertContains(response, "Uploaded Fixture Theme")
        self.assertContains(response, "Confirm")
        self.assertEqual(Theme.all_objects.count(), 0)

    @patch("layers.admin.import_fixture_rows")
    def test_exported_theme_fixture_preview_has_no_field_differences(self, import_fixture_rows):
        self.client.force_login(self.superuser)
        theme = Theme.all_objects.create(
            name="Preview Theme",
            display_name="Preview Theme",
        )
        layer = Layer.all_objects.create(name="Preview Layer", layer_type="WMS")
        ChildOrder.objects.create(
            parent_theme=theme,
            content_object=layer,
            order=4,
        )

        export_response = export_theme_details(
            Mock(),
            Mock(),
            Theme.all_objects.filter(pk=theme.pk),
        )
        fixture_file = SimpleUploadedFile(
            "exported-theme.json",
            export_response.content,
            content_type="application/json",
        )
        import_fixture_rows.return_value = {"imported": 0, "dry_run": True}

        response = self.client.post(
            self.upload_url,
            {"fixture_file": fixture_file},
        )

        self.assertEqual(response.status_code, 200)
        import_fixture_rows.assert_called_once()
        self.assertTrue(response.context["preview_rows"])
        self.assertTrue(all(not row["changes"] for row in response.context["preview_rows"]))
        self.assertContains(response, "Create or merge relationship record")

    @patch("layers.admin.import_fixture_rows")
    def test_preview_reports_uuid_matched_theme_updates(self, import_fixture_rows):
        self.client.force_login(self.superuser)
        existing_theme = Theme.all_objects.create(
            name="Current Theme Name",
            display_name="Current Theme Name",
            uuid=self.theme_uuid,
        )
        fixture_rows = [
            build_node(
                model="layers.theme",
                source_pk=1001,
                uuid_value=existing_theme.uuid,
                fields={
                    "name": "Imported Theme Name",
                    "display_name": "Imported Theme Name",
                    "theme_type": "checkbox",
                    "order": 10,
                    "is_visible": True,
                    "is_top_theme": False,
                },
                relations={},
            )
        ]
        import_fixture_rows.return_value = {"imported": 1, "dry_run": True}

        response = self.client.post(
            self.upload_url,
            {"fixture_file": self._fixture_file(fixture_rows)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Update existing record")
        self.assertContains(response, "Current Theme Name")
        self.assertContains(response, "Imported Theme Name")

    @patch("layers.admin.import_fixture_rows")
    def test_source_id_collision_does_not_change_uuid_first_import_policy(self, import_fixture_rows):
        self.client.force_login(self.superuser)
        Theme.all_objects.create(
            name="Existing Theme",
            display_name="Existing Theme",
            uuid=uuid4(),
            id=1001,
        )
        import_fixture_rows.return_value = {"imported": 1, "dry_run": True}

        response = self.client.post(
            self.upload_url,
            {"fixture_file": self._fixture_file()},
        )

        self.assertEqual(response.status_code, 200)
        import_fixture_rows.assert_called_once_with(
            self.valid_rows,
            dry_run=True,
            associate_all_sites=True,
            missing_ref_policy="error",
            duplicate_uuid_policy="error",
        )

    @patch("layers.admin.import_fixture_rows")
    def test_confirmation_executes_staged_fixture_not_posted_payload(self, import_fixture_rows):
        self.client.force_login(self.superuser)
        import_fixture_rows.return_value = {"imported": 1, "dry_run": True}

        preview_response = self.client.post(
            self.upload_url,
            {"fixture_file": self._fixture_file()},
        )
        self.assertEqual(preview_response.status_code, 200)

        import_fixture_rows.reset_mock()
        import_fixture_rows.return_value = {"imported": 1, "dry_run": False}
        tampered_rows = [
            build_node(
                model="layers.theme",
                source_pk=9999,
                uuid_value=uuid4(),
                fields={
                    "name": "Tampered Theme",
                    "display_name": "Tampered Theme",
                    "theme_type": "checkbox",
                    "order": 10,
                    "is_visible": True,
                    "is_top_theme": False,
                },
                relations={},
            )
        ]

        response = self.client.post(
            self.upload_url,
            {"confirm": "1", "fixture_file": self._fixture_file(tampered_rows)},
        )

        self.assertEqual(response.status_code, 302)
        import_fixture_rows.assert_called_once_with(
            self.valid_rows,
            dry_run=False,
            associate_all_sites=True,
            missing_ref_policy="error",
            duplicate_uuid_policy="error",
        )

    @patch("layers.admin.import_fixture_rows")
    def test_cancel_discards_staged_fixture_without_import(self, import_fixture_rows):
        self.client.force_login(self.superuser)
        import_fixture_rows.return_value = {"imported": 1, "dry_run": True}

        self.client.post(self.upload_url, {"fixture_file": self._fixture_file()})
        import_fixture_rows.reset_mock()

        response = self.client.post(self.upload_url, {"cancel": "1"})

        self.assertRedirects(response, reverse("admin:layers_theme_changelist"))
        import_fixture_rows.assert_not_called()
        self.assertEqual(Theme.all_objects.count(), 0)

    @patch("layers.admin.import_fixture_rows")
    def test_confirm_without_preview_does_not_write(self, import_fixture_rows):
        self.client.force_login(self.superuser)

        response = self.client.post(self.upload_url, {"confirm": "1"})

        self.assertEqual(response.status_code, 200)
        import_fixture_rows.assert_not_called()
        self.assertContains(response, "No validated fixture")
        self.assertEqual(Theme.all_objects.count(), 0)

    @patch("layers.admin.import_fixture_rows")
    def test_invalid_json_does_not_write(self, import_fixture_rows):
        self.client.force_login(self.superuser)
        invalid_file = SimpleUploadedFile(
            "broken.json",
            b"{not valid json",
            content_type="application/json",
        )

        response = self.client.post(self.upload_url, {"fixture_file": invalid_file})

        self.assertEqual(response.status_code, 200)
        import_fixture_rows.assert_not_called()
        self.assertContains(response, "valid JSON")
        self.assertEqual(Theme.all_objects.count(), 0)
