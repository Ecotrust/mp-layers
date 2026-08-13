from django.test import TestCase

from layers.fixture_contract import (
    NODE_FIELDS_KEY,
    NODE_MODEL_KEY,
    NODE_RELATIONS_KEY,
    NODE_SOURCE_PK_KEY,
)
from layers.models import (
    Layer,
    MultilayerAssociation,
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

        # Associations:
        # - included_association matches parentLayer and is referenced by a selected value.
        # - wrong_parent_association is referenced but has wrong parentLayer.
        # - unreferenced_association has matching parentLayer but is not referenced by selected values.
        included_association = MultilayerAssociation.objects.create(
            parentLayer=export_layer,
            layer=other_layer,
            name='included',
        )
        wrong_parent_association = MultilayerAssociation.objects.create(
            parentLayer=other_layer,
            layer=export_layer,
            name='wrong-parent',
        )
        unreferenced_association = MultilayerAssociation.objects.create(
            parentLayer=export_layer,
            layer=export_layer,
            name='unreferenced',
        )

        root_value_a.associations.add(included_association, wrong_parent_association)
        other_value.associations.add(unreferenced_association)

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
                association = MultilayerAssociation.objects.create(
                    parentLayer=export_layer,
                    layer=target_layer,
                    name=association_name,
                )
                dim_one_value.associations.add(association)
                dim_two_value.associations.add(association)
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
                association = MultilayerAssociation.objects.create(
                    parentLayer=export_layer,
                    layer=target_layer,
                    name=association_name,
                )
                dim_one_value.associations.add(association)
                dim_two_value.associations.add(association)
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
