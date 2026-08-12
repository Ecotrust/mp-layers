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
