from uuid import uuid4

from django.contrib.sites.models import Site
from django.test import TestCase

from layers.fixture_contract import build_node, build_ref
from layers.models import Layer, MultilayerAssociation

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
