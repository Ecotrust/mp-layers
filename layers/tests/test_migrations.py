from django.test import TestCase
from django.core.management import call_command
from data_manager.models import Theme as DataManagerTheme, Layer as DataManagerLayer, MultilayerDimension as DataManagerMultilayerDimension, MultilayerAssociation as DataManagerMultilayerAssociation, MultilayerDimensionValue as DataManagerMultilayerDimensionValue
from layers.models import Theme as LayersTheme, Layer as LayersLayer, ChildOrder, LayerWMS, LayerArcREST, LayerArcFeatureService, LayerXYZ, LayerVector, Companionship, MultilayerAssociation, MultilayerDimension, MultilayerDimensionValue
from django.contrib.sites.models import Site
from django.test.utils import override_settings
class MigrationTest(TestCase):
    @override_settings(DATA_CATALOG_ENABLED=False)
    def setUp(self):
        # Set up your test data in data_manager models
        
        site1 = Site.objects.get(pk=1)
        site2 = Site.objects.create(pk=2, domain='test.com', name='Test')

        self.dm_theme = DataManagerTheme.objects.create(name="Test Theme", display_name="test theme", header_image="/media/marco/img/learn/admin.jpg", overview="Numerous management boundaries in the Mid-Atlantic are compiled here to provide administrative and regulatory contexts to help facilitate well-informed ocean planning decisions.",
                                                        description="Numerous federal, regional, and state political and management boundaries of the Mid-Atlantic are compiled here to provide a regulatory context to help facilitate well-informed ocean planning decisions.", thumbnail="https://s3.amazonaws.com/marco-public-2d/Energy/energy_thumbnail.jpg", order=1)
        self.dm_theme.site.add(site1)
        self.dm_theme.site.add(site2)
        self.dm_parent_layer1 = DataManagerLayer.objects.create(name="Test Parent Layer1", layer_type="checkbox", description="Federally - and internationally - recognized political, legal, and resource management boundaries.", order=30)
        self.dm_parent_layer1.site.add(site1)
        self.dm_parent_layer1.site.add(site2)
        self.dm_parent_layer2 = DataManagerLayer.objects.create(name="Test Parent Layer2", layer_type="radio")
        self.dm_parent_layer2.site.add(site1)
        self.dm_layer1 = DataManagerLayer.objects.create(name="Test Layer 1", layer_type="WMS", is_sublayer=True, wms_slug="surface_sea_Water_velocity", wms_version="1.1.1", wms_format="image/png",)
        self.dm_layer1.site.add(site1)
        self.dm_layer1.site.add(site2)
        self.dm_layer2 = DataManagerLayer.objects.create(name="Test Layer 2", layer_type="ArcRest", is_sublayer=True, url="https://services.northeastoceandata.org/arcgis1/rest/services/NEFMC/NEFMC_HabitatDisturbanceToFishing/MapServer/export?time=1420070400000",
                                                         order=10, legend="/static/legends/FishingEffectsPctSeabedHabitatDisturbance.png", show_legend=True)
        self.dm_layer2.site.add(site1)
        self.dm_parent_layer1.sublayers.set([self.dm_layer1])
        self.dm_parent_layer1.themes.set([self.dm_theme])
        self.dm_parent_layer2.sublayers.set([self.dm_layer2])
        self.dm_parent_layer2.themes.set([self.dm_theme])
        self.dm_layer3 = DataManagerLayer.objects.create(name="Test Layer 3", layer_type="ArcFeatureServer")
        self.dm_layer4 = DataManagerLayer.objects.create(name="Test Layer 4", layer_type="Vector")
        self.dm_layer5 = DataManagerLayer.objects.create(name="Test Layer 5", layer_type="XYZ", description="the Mid-Atlantic region", slug_name="slug", label_field="label", attribute_event="mouseover", mouseover_field="mouse", is_annotated=True, compress_display=True,
                                                         url="testurl", proxy_url=True, shareable_url=False, is_disabled=True, disabled_message="disabled", utfurl="utfurl", show_legend=False, legend="legend", legend_title="legendtitle", legend_subtitle="legendsubtitle",
                                                         geoportal_id="geo", data_source="datasource", data_notes="datanotes", catalog_name="catalogname", catalog_id="catalogid", metadata="metadata", source="source", bookmark="bookmark", kml="kml", data_download="datadownload",
                                                         learn_more="learnmore", map_tiles="maptiles", espis_enabled=True, lookup_field="lookupfield", espis_search="espissearch", espis_region="espisregion", minZoom=4, maxZoom=10)
        # Set up any hierarchical relationships and many-to-many relationships here as needed
        self.dm_layer3.themes.set([self.dm_theme])
        self.dm_layer3.site.add(site1)
        self.dm_layer4.themes.set([self.dm_theme])
        self.dm_layer4.site.add(site1)
        self.dm_layer5.themes.set([self.dm_theme])
        self.dm_layer5.site.add(site1)
        self.dm_layer1.has_companion = True
        self.dm_layer1.save()
        self.dm_layer1.connect_companion_layers_to.add(self.dm_layer3, self.dm_layer4)
        self.dm_layer1.save()
        
        # Create a layer in data_manager to be used for dimension and association
        self.parent_layer = DataManagerLayer.objects.create(
            name="Test Layer",
            layer_type="Vector",
            description="A test layer for multilayer dimension"
        )
        self.parent_layer.site.add(site1)
        # Create a multilayer dimension
        self.dimension = DataManagerMultilayerDimension.objects.create(
            name="Dimension 1",
            label="Dim 1",
            order=1,
            animated=True,
            angle_labels=False,
            layer=self.parent_layer
        )

        # Create an association
        self.association = DataManagerMultilayerAssociation.objects.create(
            name="Association 1",
            parentLayer=self.parent_layer
        )

        # Create an associated layer and link it to the association
        associated_layer = DataManagerLayer.objects.create(
            name="Associated Layer",
            layer_type="WMS",
            description="A layer associated with the parent layer"
        )
        self.association.layer = associated_layer
        self.association.save()

        # Create multilayer dimension values and link them to the dimension and association
        self.dimension_value = DataManagerMultilayerDimensionValue.objects.create(
            dimension=self.dimension,
            value="Value 1",
            label="Value Label 1",
            order=1
        )
        self.dimension_value.associations.add(self.association)

    def test_migration(self):
        call_command('migration_to_layers')
        migrated_theme = LayersTheme.all_objects.filter(uuid=self.dm_theme.uuid).first()
        self.assertIsNotNone(migrated_theme)
        self.assertEqual(migrated_theme.order, self.dm_theme.order)
        self.assertEqual(migrated_theme.display_name, self.dm_theme.display_name)
        self.assertEqual(migrated_theme.header_image, self.dm_theme.header_image)
        self.assertEqual(migrated_theme.description, self.dm_theme.description)
        self.assertEqual(migrated_theme.overview, self.dm_theme.overview)
        self.assertEqual(migrated_theme.thumbnail, self.dm_theme.thumbnail)
        
        # Verify the many-to-many relationship with sites for a migrated theme
        self.assertTrue(migrated_theme.site.filter(pk=1).exists())
        self.assertTrue(migrated_theme.site.filter(pk=2).exists())

        # Fetch all child objects for the theme
        child_objects_uuid_theme = [child_order.content_object.uuid for child_order in migrated_theme.children.all()]
        self.assertIn(self.dm_parent_layer1.uuid, child_objects_uuid_theme)
        self.assertIn(self.dm_parent_layer2.uuid, child_objects_uuid_theme)
        self.assertIn(self.dm_layer3.uuid, child_objects_uuid_theme)
        self.assertIn(self.dm_layer4.uuid, child_objects_uuid_theme)
        self.assertIn(self.dm_layer5.uuid, child_objects_uuid_theme)

        # For parent layers that should become themes (assuming presence of sublayers means it's a theme)
        migrated_theme_for_layer1 = LayersTheme.all_objects.filter(uuid=self.dm_parent_layer1.uuid).first()
        self.assertIsNotNone(migrated_theme_for_layer1, "Parent Layer1 should have been migrated as a theme.")
        self.assertEqual(migrated_theme_for_layer1.theme_type, self.dm_parent_layer1.layer_type)
        self.assertEqual(migrated_theme_for_layer1.overview, self.dm_parent_layer1.data_overview)
        self.assertEqual(migrated_theme_for_layer1.description, self.dm_parent_layer1.description)

        # For layers that should remain as layers
        migrated_layer1 = LayersLayer.all_objects.filter(uuid=self.dm_layer1.uuid).first()
        self.assertIsNotNone(migrated_layer1, "Layer1 should have been migrated as a layer.")
        migrated_wms_layer1 = LayerWMS.objects.filter(layer=migrated_layer1).first()
        self.assertIsNotNone(migrated_wms_layer1)
        self.assertEqual(migrated_wms_layer1.wms_slug, self.dm_layer1.wms_slug)
        self.assertEqual(migrated_wms_layer1.wms_version, self.dm_layer1.wms_version)
        self.assertEqual(migrated_wms_layer1.wms_format, self.dm_layer1.wms_format)

        migrated_layer5 = LayersLayer.all_objects.filter(uuid=self.dm_layer5.uuid).first()
        self.assertIsNotNone(migrated_layer5, "Layer1 should have been migrated as a layer.")
        migrated_xyz_layer5 = LayerXYZ.objects.filter(layer=migrated_layer5).first()
        self.assertIsNotNone(migrated_xyz_layer5)
        self.assertEqual(migrated_layer5.description, self.dm_layer5.description)
        self.assertEqual(migrated_layer5.slug_name, self.dm_layer5.slug_name)
        self.assertEqual(migrated_layer5.label_field, self.dm_layer5.label_field)
        self.assertEqual(migrated_layer5.attribute_event, self.dm_layer5.attribute_event)
        self.assertEqual(migrated_layer5.mouseover_field, self.dm_layer5.mouseover_field)
        self.assertEqual(migrated_layer5.annotated, self.dm_layer5.is_annotated)
        self.assertEqual(migrated_layer5.compress_display, self.dm_layer5.compress_display)
        self.assertEqual(migrated_layer5.url, self.dm_layer5.url)
        self.assertEqual(migrated_layer5.proxy_url, self.dm_layer5.proxy_url)
        self.assertEqual(migrated_layer5.shareable_url, self.dm_layer5.shareable_url)
        self.assertEqual(migrated_layer5.is_disabled, self.dm_layer5.is_disabled)
        self.assertEqual(migrated_layer5.disabled_message, self.dm_layer5.disabled_message)
        self.assertEqual(migrated_layer5.utfurl, self.dm_layer5.utfurl)
        self.assertEqual(migrated_layer5.show_legend, self.dm_layer5.show_legend)
        self.assertEqual(migrated_layer5.legend, self.dm_layer5.legend)
        self.assertEqual(migrated_layer5.legend_title, self.dm_layer5.legend_title)
        self.assertEqual(migrated_layer5.legend_subtitle, self.dm_layer5.legend_subtitle)
        self.assertEqual(migrated_layer5.geoportal_id, self.dm_layer5.geoportal_id)
        self.assertEqual(migrated_layer5.data_source, self.dm_layer5.data_source)
        self.assertEqual(migrated_layer5.data_notes, self.dm_layer5.data_notes)
        self.assertEqual(migrated_layer5.catalog_name, self.dm_layer5.catalog_name)
        self.assertEqual(migrated_layer5.catalog_id, self.dm_layer5.catalog_id)
        self.assertEqual(migrated_layer5.metadata, self.dm_layer5.metadata)
        self.assertEqual(migrated_layer5.source, self.dm_layer5.source)
        self.assertEqual(migrated_layer5.bookmark, self.dm_layer5.bookmark)
        self.assertEqual(migrated_layer5.kml, self.dm_layer5.kml)
        self.assertEqual(migrated_layer5.data_download, self.dm_layer5.data_download)
        self.assertEqual(migrated_layer5.learn_more, self.dm_layer5.learn_more)
        self.assertEqual(migrated_layer5.map_tiles, self.dm_layer5.map_tiles)
        self.assertEqual(migrated_layer5.espis_enabled, self.dm_layer5.espis_enabled)
        self.assertEqual(migrated_layer5.lookup_field, self.dm_layer5.lookup_field)
        self.assertEqual(migrated_layer5.espis_search, self.dm_layer5.espis_search)
        self.assertEqual(migrated_layer5.espis_region, self.dm_layer5.espis_region)
        self.assertEqual(migrated_layer5.minZoom, self.dm_layer5.minZoom)
        self.assertEqual(migrated_layer5.maxZoom, self.dm_layer5.maxZoom)

       
        # Fetch all child objects for the theme
        child_objects_subtheme = [child_order.content_object for child_order in migrated_theme_for_layer1.children.all()]

        # Verify if Layer1 is now considered a child of the theme created from Parent Layer1
        self.assertIn(migrated_layer1, child_objects_subtheme)

        # Verify the many-to-many relationship with sites for a migrated layer
        self.assertTrue(migrated_layer1.site.filter(pk=1).exists())
        self.assertTrue(migrated_layer1.site.filter(pk=2).exists())

        companionship_exists = Companionship.objects.filter(layer=migrated_layer1).exists()
        self.assertTrue(companionship_exists, "Companionship for migrated layer1 should exist.")

        if companionship_exists:
            companionship = Companionship.objects.get(layer=migrated_layer1)
            # Assert the expected companion layers are correctly associated
            expected_companion_uuids = set([self.dm_layer3.uuid, self.dm_layer4.uuid])
            actual_companion_uuids = set(companion_layer.uuid for companion_layer in companionship.companions.all())

            self.assertEqual(expected_companion_uuids, actual_companion_uuids, "Companionship should include the correct companion layers.")
            print(f"Companionship successfully created for layer: {migrated_layer1.name} with companions {', '.join(companion.name for companion in companionship.companions.all())}")

        for dm_dimension in DataManagerMultilayerDimension.objects.all():
            migrated_dimension = MultilayerDimension.objects.get(uuid=dm_dimension.uuid)
            self.assertEqual(migrated_dimension.name, dm_dimension.name)
            self.assertEqual(migrated_dimension.label, dm_dimension.label)
            self.assertEqual(migrated_dimension.order, dm_dimension.order)
            self.assertEqual(migrated_dimension.animated, dm_dimension.animated)
            self.assertEqual(migrated_dimension.angle_labels, dm_dimension.angle_labels)
            # Add more assertions as necessary

        # Test multilayer associations migration
        for dm_association in DataManagerMultilayerAssociation.objects.all():
            migrated_association = MultilayerAssociation.objects.get(uuid=dm_association.uuid)
            self.assertEqual(migrated_association.name, dm_association.name)

        # Test multilayer dimension values migration
        for dm_value in DataManagerMultilayerDimensionValue.objects.all():
            migrated_value = MultilayerDimensionValue.objects.get(uuid=dm_value.uuid)
            self.assertEqual(migrated_value.value, dm_value.value)
            self.assertEqual(migrated_value.label, dm_value.label)
            self.assertEqual(migrated_value.order, dm_value.order)
            # Verify associations
            expected_associations_uuids = set(dm_value.associations.values_list('uuid', flat=True))
            actual_associations_uuids = set(migrated_value.associations.values_list('uuid', flat=True))
            self.assertEqual(expected_associations_uuids, actual_associations_uuids)
            