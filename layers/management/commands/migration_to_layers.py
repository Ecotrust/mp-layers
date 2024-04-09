from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from layers.models import Theme as LayersTheme, Layer as LayersLayer, ChildOrder, LayerWMS, LayerArcREST, LayerArcFeatureService, LayerVector, LayerXYZ, Companionship, MultilayerAssociation, MultilayerDimension, MultilayerDimensionValue,  AttributeInfo, LookupInfo
from data_manager.models import Theme as DataManagerTheme, Layer as DataManagerLayer, MultilayerAssociation as DataManagerMultilayerAssociation, MultilayerDimension as DataManagerMultilayerDimension, MultilayerDimensionValue as DataManagerMultilayerDimensionValue
from django.contrib.sites.models import Site
import uuid

class Command(BaseCommand):
    help = 'Migrates old layers and themes from data_manager to layers module'

    def create_child_order(self, parent_theme, child, order):
        # Your existing create_child_order function
        
        content_type = ContentType.objects.get_for_model(child)
        child_order = ChildOrder.objects.create(
            parent_theme=parent_theme,
            content_type=content_type,
            object_id=child.id,
            order=order,
        )
        return child_order
    
    def create_theme_or_layer(self, old_layer):
        # Your existing create_or_update_layer function
        # Replace all print statements with self.stdout.write for command-line output
        new_entity = None 
        if (old_layer.pk == 5264):
            import ipdb; ipdb.set_trace()
        if old_layer.layer_type in ['radio', 'checkbox'] or (old_layer.sublayers.all().count() > 0 and not old_layer.is_sublayer):
            # Create as subtheme
            visible = False if old_layer.layer_type == "placeholder" else True
            new_subtheme = LayersTheme.objects.create(
                uuid=old_layer.uuid,
                name=old_layer.name,
                overview=old_layer.data_overview,
                description=old_layer.description,
                theme_type=old_layer.layer_type,  
                is_visible = visible
            )
            new_entity = new_subtheme
            for site in old_layer.site.all():
                        new_subtheme.site.add(site)
            self.stdout.write(f"Created {old_layer.name} as a subtheme")
        else:
            # Create as layer
            layer_type = "slider" if old_layer.isMultilayerParent else old_layer.layer_type
            is_visible = False if old_layer.layer_type == "placeholder" else True
            new_layer = LayersLayer.objects.create(
                        uuid=old_layer.uuid,
                        name=old_layer.name,
                        layer_type=layer_type,
                        slug_name=old_layer.slug_name,
                        label_field=old_layer.label_field,
                        attribute_event=old_layer.attribute_event,
                        mouseover_field=old_layer.mouseover_field,
                        annotated=old_layer.is_annotated,
                        compress_display=old_layer.compress_display,
                        url=old_layer.url,
                        is_visible=is_visible,
                        proxy_url=old_layer.proxy_url,
                        shareable_url=old_layer.shareable_url,
                        is_disabled=old_layer.is_disabled,
                        disabled_message=old_layer.disabled_message,
                        utfurl=old_layer.utfurl,
                        show_legend=old_layer.show_legend,
                        legend=old_layer.legend,
                        legend_title=old_layer.legend_title,
                        legend_subtitle=old_layer.legend_subtitle,
                        geoportal_id=old_layer.geoportal_id,
                        description=old_layer.description if old_layer.description is not None else "",
                        overview=old_layer.data_overview if old_layer.data_overview is not None else "",
                        data_source=old_layer.data_source,
                        data_notes=old_layer.data_notes if old_layer.data_notes is not None else "",
                        catalog_name=old_layer.catalog_name,
                        catalog_id=old_layer.catalog_id,
                        metadata=old_layer.metadata,
                        source=old_layer.source,
                        bookmark=old_layer.bookmark,
                        kml=old_layer.kml,
                        data_download=old_layer.data_download,
                        learn_more=old_layer.learn_more,
                        map_tiles=old_layer.map_tiles,
                        lookup_field=old_layer.lookup_field,
                        espis_enabled=old_layer.espis_enabled,
                        espis_search=old_layer.espis_search,
                        espis_region=old_layer.espis_region,
                        minZoom=old_layer.minZoom,
                        maxZoom=old_layer.maxZoom,
                    )
            for attribute_field in old_layer.attribute_fields.all():
                # Create a new instance of AttributeInfo with the same data
                new_attribute_field = AttributeInfo.objects.create(
                    display_name=attribute_field.display_name,
                    field_name=attribute_field.field_name,
                    precision=attribute_field.precision,
                    order=attribute_field.order,
                    preserve_format=attribute_field.preserve_format
                )
                # Add the new instance to the new layer's attribute_fields
                new_layer.attribute_fields.add(new_attribute_field)
            for old_lookup in old_layer.lookup_table.all():
                new_lookup = LookupInfo.objects.create(
                    value=old_lookup.value,
                    description=old_lookup.description,
                    color=old_lookup.color,
                    stroke_color=old_lookup.stroke_color,
                    stroke_width=old_lookup.stroke_width,
                    dashstyle=old_lookup.dashstyle,
                    fill=old_lookup.fill,
                    graphic=old_lookup.graphic,
                    graphic_scale=old_lookup.graphic_scale,
                )
                new_layer.lookup_table.add(new_lookup)
            new_layer.save()
            if new_layer.layer_type == "WMS":
                LayerWMS.objects.create(
                    layer=new_layer,
                    wms_slug=old_layer.wms_slug,
                    wms_version=old_layer.wms_version,
                    wms_format=old_layer.wms_format,
                    wms_srs=old_layer.wms_srs,
                    wms_styles=old_layer.wms_styles,
                    wms_timing=old_layer.wms_timing,
                    wms_time_item=old_layer.wms_time_item,
                    wms_additional=old_layer.wms_additional,
                    wms_info=old_layer.wms_info,
                    wms_info_format=old_layer.wms_info_format,
                    query_by_point=old_layer.query_by_point
                    )
            elif new_layer.layer_type == "ArcRest":
                LayerArcREST.objects.create(
                    layer=new_layer,
                    arcgis_layers=old_layer.arcgis_layers,
                    disable_arcgis_attributes=old_layer.disable_arcgis_attributes,
                    password_protected=old_layer.password_protected,
                    query_by_point=old_layer.query_by_point
                    )
            elif new_layer.layer_type == "ArcFeatureServer":
                LayerArcFeatureService.objects.create(
                    layer=new_layer,
                    arcgis_layers=old_layer.arcgis_layers,
                    disable_arcgis_attributes=old_layer.disable_arcgis_attributes,
                    password_protected=old_layer.password_protected,
                    custom_style=old_layer.custom_style,
                    outline_width=old_layer.vector_outline_width,
                    outline_color=old_layer.vector_outline_color,
                    outline_opacity=old_layer.vector_outline_opacity,
                    fill_opacity=old_layer.vector_fill,
                    color=old_layer.vector_color,
                    point_radius=old_layer.point_radius,
                    graphic=old_layer.vector_graphic,
                    graphic_scale=old_layer.vector_graphic_scale,
                    opacity=old_layer.opacity
                    )
            elif new_layer.layer_type == "XYZ":
                LayerXYZ.objects.create(
                    layer=new_layer,
                    query_by_point=old_layer.query_by_point
                    )
            elif new_layer.layer_type == "Vector":
                LayerVector.objects.create(
                    layer=new_layer,
                    custom_style=old_layer.custom_style,
                    outline_width=old_layer.vector_outline_width,
                    outline_color=old_layer.vector_outline_color,
                    outline_opacity=old_layer.vector_outline_opacity,
                    fill_opacity=old_layer.vector_fill,
                    color=old_layer.vector_color,
                    point_radius=old_layer.point_radius,
                    graphic=old_layer.vector_graphic,
                    graphic_scale=old_layer.vector_graphic_scale,
                    opacity=old_layer.opacity
                    )
            new_entity = new_layer
            for site in old_layer.site.all():
                new_layer.site.add(site)
            self.stdout.write(f"Created {old_layer.name} as a layer")

        return new_entity
    
        
        # for sublayer in old_layer.sublayers.all():
        #     self.create_or_update_layer(sublayer, new_subtheme)  

    def handle(self, *args, **options):
        # Replace all print statements with self.stdout.write for command-line output

        # Delete all layers and themes first in layers module
        LayersTheme.all_objects.all().delete()
        self.stdout.write(self.style.SUCCESS('All themes deleted successfully.'))

        LayersLayer.all_objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Deleted all layers...'))

        # LOOP 1: for each layer in DM layers, create either layer or subtheme in Layers module
        for old_layer in DataManagerLayer.all_objects.all():
            # Check if a theme with the old_uuid already exists
            created_entity = self.create_theme_or_layer(old_layer)
        
        # LOOP 2: for theme in layers.theme, create child order
        for theme in LayersTheme.all_objects.all():
            try:
                old_layer = DataManagerLayer.all_objects.get(uuid=theme.uuid)  # Match by UUID
                if (old_layer.sublayers.all().count() > 0 and not old_layer.is_sublayer) or old_layer.isMultilayerParent:
                    for order, sublayer in enumerate(old_layer.sublayers.all(), start=1):
                        if sublayer.uuid == theme.uuid:
                            self.stdout.write(self.style.WARNING(f'Skipping sublayer {sublayer.name} as its UUID matches the theme UUID.'))
                            continue
                        try:
                            if (not sublayer.is_sublayer and sublayer.sublayers.all().count()>0) or (sublayer.layer_type == "radio" or sublayer.layer_type == "checkbox"):
                                new_entity = LayersTheme.all_objects.get(uuid=sublayer.uuid)
                            else:
                                new_entity = LayersLayer.all_objects.get(uuid=sublayer.uuid)
                            # Create the child order and get the created object
                            created_child_order = self.create_child_order(theme, new_entity, order)
                            # Print a success message with details about the created child order
                            self.stdout.write(self.style.SUCCESS(f'Child order created between theme "{theme.name}" and sublayer "{new_entity.name}" with order {created_child_order.order}.'))
                        except LayersLayer.DoesNotExist:
                            self.stdout.write(self.style.ERROR(f'No matching entity found for theme{theme.name} sublayer {sublayer.name} with UUID {sublayer.uuid}'))
                            continue
            except DataManagerLayer.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Original layer for theme {theme.name} not found in DataManagerLayer'))
        
        # LOOP 3: for theme in DM themes, create
        for old_theme in DataManagerTheme.all_objects.all():
            new_theme = LayersTheme.objects.create(
                uuid=old_theme.uuid,
                name=old_theme.name,
                display_name=old_theme.display_name,
                description=old_theme.description,
                overview=old_theme.overview,
                thumbnail=old_theme.thumbnail,
                header_image=old_theme.header_image,
                header_attrib=old_theme.header_attrib,
                factsheet_thumb=old_theme.factsheet_thumb,
                factsheet_link=old_theme.factsheet_link,
                feature_image=old_theme.feature_image,
                feature_excerpt=old_theme.feature_excerpt,
                feature_link=old_theme.feature_link,
                order=old_theme.order,
                is_visible=old_theme.visible,
                date_created=old_theme.date_created,
                date_modified=old_theme.date_modified,
            )
            
            # Add sites from the old theme to the new theme
            for site in old_theme.site.all():
                new_theme.site.add(site)
            
            new_theme.save()  
            self.stdout.write(self.style.SUCCESS(f'Created theme "{new_theme.name}" from DataManagerTheme.'))

        # LOOP 4: For each theme, go through its children layers and create child order
        for dm_theme in DataManagerTheme.all_objects.all():
            # Find the corresponding theme in LayersTheme
            try:
                parent_theme = LayersTheme.all_objects.get(uuid=dm_theme.uuid)
            except LayersTheme.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'No matching theme found for {dm_theme.name} with UUID {dm_theme.uuid}'))
                continue
            
            # Iterate over each layer associated with the dm_theme
            for order, dm_layer in enumerate(dm_theme.layer_set.all(), start=1):
                # Try to find the corresponding layer or subtheme in LayersLayer or LayersTheme
                try:
                    matching_layer = LayersLayer.all_objects.get(uuid=dm_layer.uuid)
                    self.create_child_order(parent_theme, matching_layer, order)
                    self.stdout.write(self.style.SUCCESS(f'Created child order for layer {matching_layer.name} under theme {parent_theme.name}'))
                except LayersLayer.DoesNotExist:
                    try:
                        matching_subtheme = LayersTheme.all_objects.get(uuid=dm_layer.uuid)
                        self.create_child_order(parent_theme, matching_subtheme, order)
                        self.stdout.write(self.style.SUCCESS(f'Created child order for subtheme {matching_subtheme.name} under theme {parent_theme.name}'))
                    except LayersTheme.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'No matching layer or subtheme found for {dm_layer.name} with UUID {dm_layer.uuid}'))
                        continue
        self.stdout.write(self.style.SUCCESS('Migration completed successfully'))

        # LOOP 5: for layer in DM layers, filter(has_companion), get layers.layer by UUID and create companionships
        dm_layers_with_companions = DataManagerLayer.all_objects.filter(has_companion=True)
        for dm_layer in dm_layers_with_companions:
            # Get the corresponding layer in the Layers module by UUID
            try:
                parent_layer = LayersLayer.all_objects.get(uuid=dm_layer.uuid)
                self.stdout.write(f'Processing companions for layer: {parent_layer.name}')
                
                # Check if this layer already has a companionship setup, to avoid duplicates
                if not parent_layer.companionships.exists():
                    companionship = Companionship.objects.create(layer=parent_layer)
                    
                    # Go through each connected companion layer
                    for companion_dm_layer in dm_layer.connect_companion_layers_to.all():
                        try:
                            # Find the companion layer in Layers module by UUID
                            companion_layer = LayersLayer.all_objects.get(uuid=companion_dm_layer.uuid)
                            # Add the companion layer to the companionship
                            companionship.companions.add(companion_layer)
                            self.stdout.write(self.style.SUCCESS(f'Added {companion_layer.name} as a companion to {parent_layer.name}'))
                        except LayersLayer.DoesNotExist:
                            pass
                            self.stdout.write(self.style.ERROR(f'Companion layer {companion_dm_layer.name} with UUID {companion_dm_layer.uuid} not found in Layers module'))
                
                else:
                    self.stdout.write(self.style.WARNING(f'Companionship already exists for layer: {parent_layer.name}'))

            except LayersLayer.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Layer {dm_layer.name} with UUID {dm_layer.uuid} not found in Layers module, turned into Subtheme'))
                continue
        
        # LOOP 6: for each DM MLDM create layers MLDM
        for dm_dimension in DataManagerMultilayerDimension.objects.all():
            try:
                corresponding_layer = LayersLayer.all_objects.get(uuid=dm_dimension.layer.uuid)
            except LayersLayer.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Layer with UUID {dm_dimension.layer.uuid} not found in Layers module'))
                continue  # Skip this dimension if the corresponding layer is not found

            layer_dimension = MultilayerDimension.objects.create(
                uuid=dm_dimension.uuid,
                name=dm_dimension.name,
                label=dm_dimension.label,
                order=dm_dimension.order,
                animated=dm_dimension.animated,
                angle_labels=dm_dimension.angle_labels,
                layer=corresponding_layer,  # Adjust for correct Layer object linking
            )
            self.stdout.write(f'Migrated dimension: {dm_dimension.name}')

        # LOOP 7: for each DM MLAssociations, creates layers MLAssociations
        for dm_association in DataManagerMultilayerAssociation.objects.all():
            try:
        # Find the corresponding layer in the Layers module by UUID
                corresponding_layer = LayersLayer.all_objects.get(uuid=dm_association.layer.uuid)
            except LayersLayer.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Layer {dm_association.layer.name} with UUID {dm_association.layer.uuid} not found in Layers module'))
                continue

            try:
                # Ensure parentLayer is a Layer by checking the LayersLayer model
                parent_layer = LayersLayer.all_objects.get(uuid=dm_association.parentLayer.uuid)
            except LayersLayer.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Parent layer with UUID {dm_association.parentLayer.uuid} not found in Layers module'))
                continue

            # Proceed with creating the MultilayerAssociation instance
            association = MultilayerAssociation.objects.create(
                uuid=dm_association.uuid,
                name=dm_association.name,
                parentLayer=parent_layer,  # Ensures parentLayer is a Layer instance
                layer=corresponding_layer,
            )
            self.stdout.write(f'Migrated association: {dm_association.name}')

        # LOOP 8: for each DM MLDV, create layers MLDV
        for dm_value in DataManagerMultilayerDimensionValue.objects.all():
            dimension = MultilayerDimension.objects.get(uuid=dm_value.dimension.uuid)  # Ensure the dimension exists
            dimension_value = MultilayerDimensionValue.objects.create(
                uuid=dm_value.uuid,
                dimension=dimension,
                value=dm_value.value,
                label=dm_value.label,
                order=dm_value.order,
            )
            # Migrate associations for each value
            for dm_association in dm_value.associations.all():
                association = MultilayerAssociation.objects.get(uuid=dm_association.uuid)
                dimension_value.associations.add(association)
            self.stdout.write(f'Migrated dimension value: {dm_value.value}')

# when you create the associations and tie with layer, url is created based on .../mapserver/export?time={EPOCHTIME}

                