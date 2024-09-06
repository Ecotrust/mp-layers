from django.contrib import admin
from django.conf import settings
from django import forms
from django.forms.models import inlineformset_factory
from django.db import transaction
import nested_admin
import os
from .models import *
# Register your models here.

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

class ThemeChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        # Return the name of the Theme object to be used as the label for the choice
        return obj.name

NestedMultilayerAssociationInlineFormset = inlineformset_factory(
    parent_model=Layer,
    fk_name = 'parentLayer',
    model=MultilayerAssociation,
    fields='__all__',  # Adjust the fields as necessary
    extra=1, 
    can_delete=True
)

NestedMultilayerDimensionInlineFormset = inlineformset_factory(
    parent_model=Layer,
    model=MultilayerDimension,
    fields='__all__',  # Adjust the fields as necessary
    extra=1,
    can_delete=True
)

class NestedMultilayerDimensionValueInline(nested_admin.NestedTabularInline):
    model = MultilayerDimensionValue
    fields = ('value', 'label', 'order')
    extra = 1
    classes = ['collapse', 'open']
    verbose_name_plural = 'Multilayer Dimension Values'

class NestedMultilayerDimensionInline(nested_admin.NestedTabularInline):
    model = MultilayerDimension
    fields = (('name', 'label', 'order', 'animated', 'angle_labels'),)
    extra = 1
    classes = ['collapse', 'open']
    verbose_name_plural = 'Multilayer Dimensions'
    inlines = [
        NestedMultilayerDimensionValueInline,
    ]

class NestedMultilayerAssociationInline(nested_admin.NestedTabularInline):
    model = MultilayerAssociation
    fk_name = 'parentLayer'
    readonly_fields = ('get_values',)
    fields = (('get_values', 'name', 'layer'),)
    extra = 0
    classes = ['collapse', 'open']
    verbose_name_plural = 'Multilayer Associations'

    def get_values(self, obj):
        return '| %s |' % ' | '.join([str(x) for x in obj.multilayerdimensionvalue_set.all()])

    def get_readlony_values(self, obj):
        return obj.multilayerdimensionvalue_set.all()

    def get_dimensions(self, obj):
        dimensions = []
        for value in obj.multilayerdimensionvalue_set.all():
            dimension = value.dimension
            if dimension not in dimensions:
                dimensions.append(dimension)
        return dimensions

class CompanionLayerChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        # Return the name of the Theme object to be used as the label for the choice
        return obj.name
    
class ChildrenLayerChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        # Return the name of the Theme object to be used as the label for the choice
        return obj.name

class ThemeForm(forms.ModelForm):
    children_themes = ThemeChoiceField(queryset=Theme.all_objects.none(), required=False, widget = admin.widgets.FilteredSelectMultiple('children themes', False))
    children_layers = ChildrenLayerChoiceField(queryset=Layer.all_objects.all(), required=False, widget = admin.widgets.FilteredSelectMultiple('children layers', False))
    class Meta:
        model = Theme
        exclude = ("slug_name", "uuid") 
        labels = {
            'dynamic_url': 'URL',  # This will change the label in the form
        }
    
    def clean(self):
        cleaned_data = super().clean()
        theme_type = cleaned_data.get('theme_type')
        # themes = cleaned_data.get('themes')
        order = cleaned_data.get('order')

        # if theme_type in ['radio', 'checkbox']:
        #     if not themes:
        #         self.add_error('themes', 'A theme must be selected.')
        #     if order is None:
        #         self.add_error('order', 'Order must be filled out.')

        return cleaned_data


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:  
            def get_all_ancestor_ids(theme_ids, ancestor_ids=set()):
                # Initialize a set to hold parent IDs at the current level
                parent_ids = set()
                
                # Get ContentType for the Theme model
                content_type_for_theme = ContentType.objects.get_for_model(Theme)

                for theme_id in theme_ids:
                    # Find parent themes using ChildOrder
                    child_orders = ChildOrder.objects.filter(object_id=theme_id, content_type=content_type_for_theme)
                    parent_ids.update([x.parent_theme.pk for x in child_orders])

                # If parent_ids are found, add them to ancestor_ids and recurse
                if parent_ids:
                    ancestor_ids.update(parent_ids)
                    get_all_ancestor_ids(parent_ids, ancestor_ids)

                return ancestor_ids

                # Initial themes that are children of the current theme
            content_type_for_theme = ContentType.objects.get_for_model(self.instance)
            child_orders_for_theme = ChildOrder.objects.filter(content_type=content_type_for_theme, parent_theme=self.instance)
            initial_themes = child_orders_for_theme.values_list('object_id', flat=True)

            # Collect all ancestor IDs recursively
            ancestor_ids = get_all_ancestor_ids([self.instance.pk])

            # Ensure self.instance is excluded from the queryset
            ancestor_ids.add(self.instance.pk)

            print(f"Excluding the following ancestor IDs: {ancestor_ids}")

            # Update the queryset for children_themes
            self.fields['children_themes'].queryset = Theme.all_objects.exclude(pk__in=ancestor_ids)

            # Set initial values for children themes
            self.fields['children_themes'].initial = list(initial_themes)
            content_type_for_layer = ContentType.objects.get_for_model(Layer)
            child_orders_for_layers = ChildOrder.objects.filter(content_type=content_type_for_layer, parent_theme=self.instance)
            initial_layers = child_orders_for_layers.values_list('object_id', flat=True)
            self.fields['children_layers'].initial = list(initial_layers)

            # Set the initial order value
            if not ancestor_ids:
                first_child_order = ChildOrder.objects.filter(
                    content_type=content_type_for_theme,
                    parent_theme=self.instance
                ).first()
                if first_child_order:
                    self.fields['order'].initial = first_child_order.order
            else:
                self.fields['order'].initial = 10
        else:
            # For new instances, set the queryset to include all themes (since there are no ancestors to exclude yet)
            self.fields['children_themes'].queryset = Theme.all_objects
            self.fields['order'].initial = 10
    


class ThemeAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'name', 'order', 'primary_site', 'preview_site')
    search_fields = ['display_name', 'name',]
    form = ThemeForm
    
    print(Theme._meta.get_fields())
    fieldsets = (
        ('BASIC INFO', {
            'fields': (
                'name',
                'display_name',
                'site',
                "order",
                "is_visible",

            )
        }),
        ("METADATA", {
            "fields": (
                "description",
                "overview",
                "learn_more",
                "data_notes",
                "source",
                "disabled_message",
                "data_download",
                # "slug_name",
            )
        }),
        ('DYNAMIC THEME', {
            'fields': (
                "is_dynamic",
                "dynamic_url",
                "default_keyword",
                "placeholder_text",
            )
        }),
        ('CHILD THEME ORGANIZATION', {
            # 'classes': ('collapse', 'open',),
            'fields': (
                'children_themes',
                'children_layers',
                "theme_type",
                # "order_records"
            )
        }),
        ("CATALOG DISPLAY", {
            "fields": (
                "header_image",
                "header_attrib",
                "thumbnail", 
                "factsheet_thumb",
                "factsheet_link",
                "feature_image",
                "feature_excerpt",
                "feature_link",
            )
        }),
        ("LEGEND", {
            "fields": (
                "show_legend",
                "legend",
                "legend_title", 
                "legend_subtitle",
            )
        })
    )

    class Media:
        js = ['theme_admin.js',]
        
    change_form_template = os.path.join(CURRENT_DIR, 'templates', 'admin', 'layers', 'Theme', 'change_form.html')


    def get_queryset(self, request):
        # use our manager, rather than the default one
        qs = self.model.all_objects.get_queryset()

        # we need this from the superclass method
        ordering = self.ordering or () # otherwise we might try to *None, which is bad ;)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    
    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'site':
            kwargs['widget'] = forms.CheckboxSelectMultiple()
            kwargs['widget'].attrs['style'] = 'list-style-type: none;'
            kwargs['widget'].can_add_related = False

        return db_field.formfield(**kwargs)
    
    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context['add_theme_url'] = reverse('admin:layers_theme_add')  
        context['add_layer_url'] = reverse('admin:layers_layer_add')  
        return super().render_change_form(request, context, add, change, form_url, obj)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['CATALOG_TECHNOLOGY'] = getattr(settings, 'CATALOG_TECHNOLOGY', 'default')
        extra_context['CATALOG_PROXY'] = getattr(settings, 'CATALOG_PROXY', '')
        return super(ThemeAdmin, self).change_view(request, object_id, form_url=form_url, extra_context=extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['CATALOG_TECHNOLOGY'] = getattr(settings, 'CATALOG_TECHNOLOGY', 'default')
        extra_context['CATALOG_PROXY'] = getattr(settings, 'CATALOG_PROXY', '')
        return super(ThemeAdmin, self).add_view(request, form_url=form_url, extra_context=extra_context)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'children_themes':
            formfield.widget = forms.SelectMultiple(attrs={'data-url': self.reverse_add_url('theme')})
        if db_field.name == 'children_layers':
            formfield.widget = forms.SelectMultiple(attrs={'data-url': self.reverse_add_url('layer')})
        return formfield

    def reverse_add_url(self, model_name):
        return reverse(f'admin:layers_{model_name}_add')

    def create_or_update_child_order_for_themes(self, obj, themes):
        content_type = ContentType.objects.get_for_model(obj)
    
        # Existing themes linked to the object
        existing_child_orders = ChildOrder.objects.filter(content_type=content_type, parent_theme=obj)
        existing_theme_ids = set(existing_child_orders.values_list('object_id', flat=True))
        
        # New themes from the form
        new_theme_ids = set(theme.id for theme in themes)
        
        # Themes to add and remove
        themes_to_add = new_theme_ids - existing_theme_ids
        themes_to_remove = existing_theme_ids - new_theme_ids
        
        # Remove old themes
        ChildOrder.objects.filter(parent_theme=obj, content_type=content_type, object_id__in=themes_to_remove).delete()
        
        # Add new themes
        for theme_id in themes_to_add:
            ChildOrder.objects.update_or_create(
                parent_theme_id=obj.pk,
                content_type=content_type,
                object_id=theme_id,
                defaults={'order': 0}
            )

    def create_or_update_child_order_for_layers(self, obj, layers):
        content_type = ContentType.objects.get_for_model(Layer)
    
        # Existing themes linked to the object
        existing_child_orders = ChildOrder.objects.filter(content_type=content_type, parent_theme=obj)
        existing_layer_ids = set(existing_child_orders.values_list('object_id', flat=True))

        # New themes from the form
        new_layer_ids = set(layer.id for layer in layers)

        # Themes to add and remove
        layers_to_add = new_layer_ids - existing_layer_ids
        layers_to_remove = existing_layer_ids - new_layer_ids

        # Remove old themes
        ChildOrder.objects.filter(parent_theme=obj, content_type=content_type, object_id__in=layers_to_remove).delete()
        
        # Add new themes
        for layer_id in layers_to_add:
            ChildOrder.objects.update_or_create(
                parent_theme_id=obj.pk,
                content_type=content_type,
                object_id=layer_id,
                defaults={'order': 0}
            )

    def save_model(self, request, obj, form, change):

        with transaction.atomic():
            
            # When updating an existing theme
            if change:
                original_theme = Theme.all_objects.get(pk=obj.pk)

            # Save the Theme object
            super().save_model(request, obj, form, change)
            
            themes = form.cleaned_data.get('children_themes', [])
            layers = form.cleaned_data.get('children_layers', [])
            print(layers)
            self.create_or_update_child_order_for_themes(obj, themes)
            self.create_or_update_child_order_for_layers(obj, layers)

class LayerForm(forms.ModelForm):

    order = forms.IntegerField(required=True)
    # themes = ThemeChoiceField(queryset=Theme.all_objects.all(), required=False, widget = admin.widgets.FilteredSelectMultiple('themes', False))
    has_companion = forms.BooleanField(required=False)
    companion_layers = CompanionLayerChoiceField(queryset=Layer.all_objects.all(), required=False, widget = admin.widgets.FilteredSelectMultiple('companion layers', False))
    class Meta:
        exclude = ('slug_name', "has_companion", "uuid")
        model = Layer
        fields = '__all__'
        widgets = {
            
            'attribute_fields': admin.widgets.FilteredSelectMultiple('Attribute fields', False),
            'lookup_table': admin.widgets.FilteredSelectMultiple('Lookup table', False),
        }
    def clean(self):
        cleaned_data = super().clean()
        order = cleaned_data.get('order')
        if order is None:
            self.add_error('order', 'Order must be filled out.')
        # Do not return order; instead, return the entire cleaned_data dictionary
        return cleaned_data
    def _post_clean(self):
        try:
            super()._post_clean()
        except AttributeError as e:
            # Add debugging output to help diagnose the issue
            print(f"Error in _post_clean: {e}")
            print(f"cleaned_data: {self.cleaned_data}")
            raise
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['companion_layers'].initial = self.instance.companionships.values_list('companions__id', flat=True)
            # For themes
            content_type = ContentType.objects.get_for_model(Layer)
            child_orders = ChildOrder.objects.filter(content_type=content_type, object_id=self.instance.pk)
            # initial_themes = child_orders.values_list('parent_theme', flat=True)
            # self.fields['themes'].initial = list(initial_themes)
            if child_orders.exists():
                print("Loading order", child_orders.first().order, "for layer", self.instance.pk)
                # Assuming the first one if there are multiple (consider how you want to handle multiple themes)
                initial_order = child_orders.first().order
                self.fields['order'].initial = initial_order
            else:
                self.fields['order'].initial = 10
            # Check if there are any companions to determine the initial value of has_companion
            has_companions = self.instance.companionships.exists()
            self.fields['has_companion'].initial = has_companions
        else:
            self.fields['order'].initial = 10


class BaseLayerInline(nested_admin.NestedStackedInline):
    extra = 1
    max_num = 1
    can_delete = False

class ArcRESTInline(BaseLayerInline):
    model = LayerArcREST

    fieldsets = (
        ('', {
            'fields': (
                ('arcgis_layers',),
                (
                    'password_protected',
                    'query_by_point',
                    'disable_arcgis_attributes',
                ),
            )
        }),
    )

vectorStyleOverrides = ('Vector Display & Style', {
            'classes': ('collapse',),
            'fields': (
                'custom_style',
                (
                    'outline_width',
                    'outline_color', 
                ),
                (
                    'fill_opacity',
                    'color', 
                ),
                (
                    'point_radius',
                    'graphic',
                    'graphic_scale',
                ),
                (
                    'lookup_field',
                    'lookup_table',
                ),
            )
        })

class ArcRESTFeatureServerInline(BaseLayerInline):
    model = LayerArcFeatureService

    fieldsets = (
        ('', {
            'fields': (
                ('arcgis_layers',),
                ('password_protected', 'disable_arcgis_attributes',)
            )
        }),
        vectorStyleOverrides,
    )

class WMSInline(BaseLayerInline):
    model = LayerWMS

    fieldsets = (
        ('', {
            'fields': (
                ('wms_help',),
                ('wms_slug', 'wms_version'),
                ('wms_format', 'wms_srs'),
                ('wms_timing', 'wms_time_item'),
                ('wms_styles', 'wms_additional'),
                ('wms_info', 'wms_info_format'),
            ),
        }),
    )

class XYZInline(BaseLayerInline):
    model = LayerXYZ

    # query_by_point is not relevant to XYZ layers
    fieldsets = (
        ('', {
            'fields': (),
        }),
    )

class VectorInline(BaseLayerInline):
    model = LayerVector

    fieldsets = (
        vectorStyleOverrides,
    )

class LayerAdmin(nested_admin.NestedModelAdmin):
    def get_parent_theme(self, obj):
        # Fetch the ContentType for the Layer model
        content_type = ContentType.objects.get_for_model(obj)
        
        # Try to fetch the corresponding ChildOrder for this Layer
        child_order = ChildOrder.objects.filter(content_type=content_type, object_id=obj.pk).first()
        
        # Return the name of the parent theme if exists
        return child_order.parent_theme.name if child_order and child_order.parent_theme else 'None'
    get_parent_theme.short_description = 'Theme'  # Sets column name

    def get_order(self, obj):
        # Fetch the ContentType for the Layer model
        content_type = ContentType.objects.get_for_model(Layer)
        print("this is obj: ", obj)
        # Try to fetch the corresponding ChildOrder for this Layer
        child_order = ChildOrder.objects.filter(content_type=content_type, object_id=obj.pk).first()
        
        # Return the order if exists
        return child_order.order if child_order else 10
    get_order.short_description = 'Order'  # Sets column name

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'site':
            kwargs['widget'] = forms.CheckboxSelectMultiple()
            kwargs['widget'].attrs['style'] = 'list-style-type: none;'
            kwargs['widget'].can_add_related = False

        return db_field.formfield(**kwargs)

    list_display = ('name', 'layer_type', 'date_modified', "get_parent_theme", "get_order", 'data_publish_date', 'data_source', 'primary_site', 'preview_site', 'url')
    search_fields = ['name', 'layer_type', 'date_modified', 'url', 'data_source']
    ordering = ('name', )
    exclude = ('slug_name', "is_sublayer", "sublayers")
    form = LayerForm
    class Media:
        js = ['layer_admin.js',]
        css = {
            'all': ('css/layer_admin.css',)  
        }

    if getattr(settings, 'CATALOG_TECHNOLOGY', None) not in ['default', None]:
        # catalog_fields = ('catalog_name', 'catalog_id',)
        # catalog_fields = 'catalog_name'
        basic_fields = (
                'catalog_name',
                ('name','layer_type',),
                ('url', 'proxy_url'),
                'site'
            )
    else:
        basic_fields = (
                ('name','layer_type',),
                ('url', 'proxy_url'),
                'site', 
            )
    fieldsets = (
        ('BASIC INFO', {
            'fields': basic_fields
        }),
        ('LAYER ORGANIZATION', {
            # 'classes': ('collapse', 'open',),
            'fields': (
                ('order'),
                ('has_companion','companion_layers'),
                # RDH 2019-10-25: We don't use this, and it doesn't seem helpful
                # ('is_disabled','disabled_message')
            )
        }),
        ('METADATA', {
            'classes': ('collapse',),
            'fields': (
                'description', 'overview','data_source','data_notes', 'data_publish_date',
            )
        }),
        ('LEGEND', {
            'classes': ('collapse',),
            'fields': (
                'show_legend',
                'legend',
                ('legend_title','legend_subtitle')
            )
        }),
        ('LINKS', { 
            'classes': ('collapse',),
            'fields': (
                ('metadata','source'),
                ('bookmark', 'kml'),
                ('data_download','learn_more'),
                ('map_tiles'),
            )
        }),
        ('SHARING', {
            'classes': ('collapse',),
            'fields': (
                'shareable_url',
            )
        }),
        ('Dynamic Layers (MDAT & CAS)', {
            'classes': ('collapse',),
            'fields': (
                'search_query',
            )
        }),
        ('UTF Grid Layers', {
            'classes': ('collapse',),
            'fields': ('utfurl',)
        }),
        ('ATTRIBUTE REPORTING (Vector/Tile, ArcREST/Feature, and WMS)', {
            'classes': ('collapse',),
            'fields': (
                'label_field',
                (
                    'attribute_event',
                    'attribute_fields',
                    'mouseover_field',
                ),
                # These fields are no longer used, but would have gone here.
                # ('is_annotated', 'compress_display')
            )
        }),
        ('APPEARANCE', {
            'classes': ('collapse',),
            'fields': (
                'opacity',
                (
                    'minZoom',
                    'maxZoom'
                ),
            )
        }),
    )
    inlines = [ArcRESTInline, WMSInline, XYZInline, VectorInline, ArcRESTFeatureServerInline, NestedMultilayerDimensionInline,
        NestedMultilayerAssociationInline,]
    
    add_form_template = os.path.join(CURRENT_DIR, 'templates', 'admin', 'layers', 'Layer', 'change_form.html')
    change_form_template = os.path.join(CURRENT_DIR, 'templates', 'admin', 'layers', 'Layer', 'change_form.html')

    def change_view(self, request, object_id, form_url='', extra_context={}):
        extra_context['CATALOG_TECHNOLOGY'] = settings.CATALOG_TECHNOLOGY
        extra_context['CATALOG_PROXY'] = settings.CATALOG_PROXY
        return super(LayerAdmin, self).change_view(request, object_id, form_url=form_url, extra_context=extra_context)
    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['CATALOG_TECHNOLOGY'] = getattr(settings, 'CATALOG_TECHNOLOGY', 'default')
        extra_context['CATALOG_PROXY'] = getattr(settings, 'CATALOG_PROXY', '')
        return super(LayerAdmin, self).add_view(request, form_url=form_url, extra_context=extra_context)

    def get_queryset(self, request):
        #use our manager, rather than the default one
        qs = self.model.all_objects.get_queryset()

        # we need this from the superclass method
        ordering = self.ordering or () # otherwise we might try to *None, which is bad ;)
        if ordering:
            qs = qs.order_by(*ordering)
        
        return qs
    
    def update_child_order(self, obj, themes, order):
        content_type = ContentType.objects.get_for_model(obj)
    
        # Update the order for all ChildOrder instances where the content_object is the current layer
        ChildOrder.objects.filter(content_type=content_type, object_id=obj.pk).update(order=order)

        print("Updated order for", obj.pk, "to", order)


    def create_or_update_companionship(self, obj, companion_layer_ids):

        # Find existing companionship ids
        existing_companion_ids = set(obj.companionships.values_list('companions__id', flat=True))

        # Determine the companions to add and to remove
        ids_to_add = companion_layer_ids - existing_companion_ids
        ids_to_remove = existing_companion_ids - companion_layer_ids

        # Remove companionships that are no longer selected
        Companionship.objects.filter(layer=obj, companions__id__in=ids_to_remove).delete()

        # Add new companionships
        for companion_id in ids_to_add:
             # Retrieve the Layer instance for the given companion_id
            companion_layer = Layer.all_objects.get(id=companion_id)
            # Create a new Companionship instance
            companionship = Companionship.objects.create(layer=obj)
            # Add the Layer instance to the companions relationship
            companionship.companions.add(companion_layer)


    def save_model(self, request, obj, form, change):

        with transaction.atomic():

            if change:
                # Check if 'layer_type' has changed, and handle accordingly
                original_layer_type = Layer.all_objects.get(pk=obj.pk).layer_type
                new_layer_type = form.cleaned_data.get('layer_type')
                if original_layer_type != new_layer_type:
                    self.handle_layer_type_change(request, obj, original_layer_type, new_layer_type)

            super().save_model(request, obj, form, change)  # Ensure the basic saving functionality.
            
            if not change:
                self.save_add(request, obj, form)
            
            # Handling ChildOrder after the layer is saved
            themes = form.cleaned_data.get('themes', [])
            order = form.cleaned_data.get('order', 0)
            print("this is order", order)
            self.update_child_order(obj, themes, order)

            # Handling Companionship after the layer is saved
            companion_layers = set(form.cleaned_data.get('companion_layers', []))
            companion_layer_ids = {layer.id for layer in companion_layers}
            self.create_or_update_companionship(obj, companion_layer_ids)


    def save_add(self, request, obj, form):
        layer_type = form.cleaned_data.get('layer_type')
        InlineModel = None

        # Determine the inline model based on layer_type
        if layer_type == 'ArcRest':
            InlineModel = LayerArcREST
        elif layer_type == 'WMS':
            InlineModel = LayerWMS
        elif layer_type == 'XYZ':
            InlineModel = LayerXYZ
        elif layer_type == 'Vector':
            InlineModel = LayerVector
        elif layer_type == "slider":
            InlineModel = [MultilayerDimension, MultilayerAssociation]
        elif layer_type == "ArcFeatureServer":
            InlineModel = LayerArcFeatureService

        # If an inline model is determined, proceed to save it
        if InlineModel is not None:
            InlineFormSet = inlineformset_factory(Layer, InlineModel, fields='__all__')
            formset = InlineFormSet(request.POST, request.FILES, instance=obj)
            if formset.is_valid() and InlineModel.objects.filter(layer=obj).count() == 1:
                formset.save()

    def handle_layer_type_change(self, request, obj, original_layer_type, new_layer_type):
        if new_layer_type == "slider":
            # Handle the slider case by just saving the formset
            self.save_inline_formsets(request, obj)
        else:
            # Handle the case for other layer types by getting or creating the instance
            InlineModelClass = self.get_inline_model_class(new_layer_type)
            print(InlineModelClass)
            if InlineModelClass is not None:
                # Get or create the inline instance
                # inline_instance, created = InlineModelClass.objects.get_or_create(layer=obj)

                # Process the inline formset
                InlineFormSetClass = self.get_inline_model(InlineModelClass)
                if InlineFormSetClass is not None:
                    formset = InlineFormSetClass(request.POST, request.FILES, instance=obj)
                    if formset.is_valid():
                        formset.save()
                    else:
                        # Handle the formset errors
                        raise Exception(f"Inline formset validation failed for {new_layer_type}")
                    
    def save_inline_formsets(self, request, obj):
        # Get all inline formsets for the 'slider' type and save them
        for InlineFormSetClass in [NestedMultilayerAssociationInlineFormset, NestedMultilayerDimensionInlineFormset]:
            formset = InlineFormSetClass(request.POST, request.FILES, instance=obj)
            if formset.is_valid():
                formset.save()
            else:
                raise Exception('Slider inline formset validation failed')
    # Add the method to get the inline instance by type
    
    def get_inline_model(self, layer_type):
        mapping = {
            'ArcRest': [ArcRESTInline],
            'WMS': [WMSInline],
            'XYZ': [XYZInline],
            'Vector': [VectorInline],
            'ArcFeatureServer': [ArcRESTFeatureServerInline],
            'slider': [NestedMultilayerDimensionInline, NestedMultilayerAssociationInline],
        }
        return mapping.get(layer_type)
    
    def get_inline_model_class(self, layer_type):
        mapping = {
            'ArcRest': LayerArcREST,
            'ArcFeatureServer': LayerArcFeatureService,
            'WMS': LayerWMS,
            'XYZ': LayerXYZ,
            'Vector': LayerVector,
        }
        return mapping.get(layer_type)

    # def get_inline_instances(self, request, obj=None):
    #     inline_instances = super(LayerAdmin, self).get_inline_instances(request, obj)
    #     if obj:  # Make sure the object exists
    #         for inline_instance in inline_instances:
    #             inline_type = 'ArcRest'  # Change this based on the actual logic
    #             # Set a custom attribute to match against layer_type
    #             inline_instance.attrs = {'data-inline-for': inline_type.lower()}
    #     return inline_instances

    def get_form(self, request, obj=None, **kwargs):
        form = super(LayerAdmin, self).get_form(request, obj, **kwargs)
        return form
    
class LookupInfoAdmin(admin.ModelAdmin):
    list_display = ('value', 'description', 'color', 'stroke_color', 'dashstyle', 'fill', 'graphic')

# if hasattr(settings, 'DATA_MANAGER_ADMIN'):
#     admin.site.register(Theme, ThemeAdmin)
admin.site.register(Theme, ThemeAdmin)
# admin.site.register(Layer, LayerAdmin)
admin.site.register(Layer, LayerAdmin)
admin.site.register(LookupInfo, LookupInfoAdmin)