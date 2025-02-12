from dal import autocomplete
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.conf import settings
from django import forms
from django.forms.models import inlineformset_factory
from django.db import transaction
from import_export.admin import ImportExportMixin
import nested_admin
import os
from queryset_sequence import QuerySetSequence
from .models import *

# Register your models here.

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

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
        return str(obj)
    
class ThemeForm(forms.ModelForm):
    class Meta:
        model = Theme
        exclude = ("slug_name", "uuid") 
        labels = {
            'dynamic_url': 'URL',  # This will change the label in the form
        }

class ChildInlineForm(autocomplete.FutureModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Override DAL/QuerySetSequence assumption of using 'objects' as each model's Manager
        queryset_models = []
        for model in [Theme, Layer]:
            queryset_models.append(model.all_objects.all())
        self.fields['content_object'].queryset = QuerySetSequence(*queryset_models)
    
    content_object = autocomplete.Select2GenericForeignKeyModelField(
        model_choice=[(Theme, 'theme'), (Layer, 'layer')],
        widget=autocomplete.QuerySetSequenceSelect2,
    )

    class Meta:
        model = ChildOrder
        fields =  ['content_type', 'content_object', 'order']

class ChildInline(admin.TabularInline):
    model= ChildOrder
    extra = 2
    ordering = ['order',]
    form = ChildInlineForm
    verbose_name = 'New Child'
    verbose_name_plural = 'New Children'

    # Loading a Theme form with more than 6 children leads to A LOT of queries. Instead, we
    # can block editing existing child records and then we don't have to populate the
    # huge queryset over-and-over again: only for the new fields. The catch is 'existing'
    # records go into 1 read-only(ish) inline, while new records (w/o read-only) get their own
    # inline.

    # Thanks to olessia and kickstarter on S.O. for this elegant solution!
    #       https://stackoverflow.com/a/28149575/706797
    def has_change_permission(self, request, obj=None):
        return False

    # For Django Version > 2.1 there is a "view permission" that needs to be disabled too (https://docs.djangoproject.com/en/2.2/releases/2.1/#what-s-new-in-django-2-1)
    def has_view_permission(self, request, obj=None):
        return False
    
class ExistingChildInlineForm(forms.ModelForm):

    class Meta:
        model = ChildOrder
        fields = ['order',]

class ExistingChildInline(admin.TabularInline):
    model = ChildOrder
    form = ExistingChildInlineForm
    verbose_name = 'Child'
    verbose_name_plural = 'Current Children'
    extra = 0
    readonly_fields = ['content_type', 'content_object',]
    classes = ['collapse',]

    def has_add_permission(self, request, obj=None):
        return False

class ParentThemeInlineForm(forms.ModelForm):
    parent_theme = forms.ModelChoiceField(
        queryset=Theme.all_objects.all(),
        widget=autocomplete.ModelSelect2()
    )

    class Meta:
        model = ChildOrder
        fields =  ['parent_theme', 'order']

class ThemeParentInline(GenericTabularInline):
    model=ChildOrder
    extra = 1
    form = ParentThemeInlineForm
    verbose_name = 'Parent'
    verbose_name_plural = 'Parents'

    def get_formset(self, request, obj, **kwargs):
        formset = super(ThemeParentInline,self).get_formset(request, obj, **kwargs)
        try:
            formset.form.base_fields['parent_theme'].queryset = Theme.all_objects.exclude(pk=obj.pk)
        except Exception as e:
            pass
        return formset

class ThemeAdmin(ImportExportMixin,admin.ModelAdmin):
    list_display = ('display_name', 'name', 'order', 'date_modified', 'is_top_theme', 'primary_site', 'preview_site')
    search_fields = ['display_name', 'name',]
    form = ThemeForm
    inlines = [ThemeParentInline, ExistingChildInline, ChildInline]
    
    fieldsets = (
        ('BASIC INFO', {
            'fields': (
                'name',
                'display_name',
                'site',
                'theme_type',
                "is_visible",
                "is_top_theme",
                "order",

            )
        }),
        ("METADATA", {
            'classes': ('collapse',),
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
            'classes': ('collapse',),
            'fields': (
                "is_dynamic",
                "dynamic_url",
                "default_keyword",
                "placeholder_text",
            )
        }),
        ("CATALOG DISPLAY", {
            'classes': ('collapse',),
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
            'classes': ('collapse',),
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
            # Fetch the Theme object
            obj = self.get_object(request, object_id)
            
            if obj:
                extra_context = extra_context or {}
                extra_context['CATALOG_TECHNOLOGY'] = getattr(settings, 'CATALOG_TECHNOLOGY', 'default')
                extra_context['CATALOG_PROXY'] = getattr(settings, 'CATALOG_PROXY', '')

            # Call the original change_view method with the updated context
            return super().change_view(request, object_id, form_url, extra_context=extra_context)

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

# class XYZInline(BaseLayerInline):
#     model = LayerXYZ

#     # query_by_point is not relevant to XYZ layers
#     fieldsets = (
#         ('', {
#             'fields': (),
#         }),
#     )

class VectorInline(BaseLayerInline):
    model = LayerVector

    fieldsets = (
        vectorStyleOverrides,
    )

class LayerParentInline(GenericTabularInline, nested_admin.NestedTabularInline):
    model=ChildOrder
    extra = 1
    form = ParentThemeInlineForm
    verbose_name = 'Parent'
    verbose_name_plural = 'Parents'

class LayerAdmin(ImportExportMixin, nested_admin.NestedModelAdmin):
    def get_parent_themes(self, obj):
        # Fetch the ContentType for the Layer model
        content_type = ContentType.objects.get_for_model(obj)
        
        # Try to fetch the corresponding ChildOrders (parent relationships) for this Layer
        child_orders = ChildOrder.objects.filter(content_type=content_type, object_id=obj.pk)
        parent_themes = [x.parent_theme.name for x in child_orders if x.parent_theme]
        parent_count = len(parent_themes)
        themes_text = "; ".join(parent_themes)
        if parent_count < 1:
            themes_text = "(None)"
        elif parent_count == 1:
            themes_text += " (1 theme)"
        else:
            themes_text += " ({} themes)".format(parent_count)
        
        # Return the names of the parent themes if they exist
        return themes_text
    
    get_parent_themes.short_description = 'Themes'  # Sets column name

    def get_order(self, obj):
        # Fetch the ContentType for the Layer model
        content_type = ContentType.objects.get_for_model(Layer)
  
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

    list_display = ('name', "get_parent_themes", 'layer_type', 'date_modified', 'data_publish_date', 'data_source', 'primary_site', 'preview_site', 'url')
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
            'classes': ('collapse', ),
            'fields': (
                ('order',),
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
                ('map_tiles',),
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
    inlines = [ArcRESTInline, WMSInline, #XYZInline, 
        VectorInline, ArcRESTFeatureServerInline, NestedMultilayerDimensionInline,
        NestedMultilayerAssociationInline, LayerParentInline
    ]
    
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
    
    def update_child_order(self, obj, order):
        content_type = ContentType.objects.get_for_model(obj)
    
        # Update the order for all ChildOrder instances where the content_object is the current layer
        ChildOrder.objects.filter(content_type=content_type, object_id=obj.pk).update(order=order)


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
            order = form.cleaned_data.get('order', 0)
 
            self.update_child_order(obj, order)

            # Handling Companionship after the layer is saved
            companion_layers = set(form.cleaned_data.get('companion_layers', []))
            companion_layer_ids = {layer.id for layer in companion_layers}
            self.create_or_update_companionship(obj, companion_layer_ids)


    def save_add(self, request, obj, form):
        layer_type = form.cleaned_data.get('layer_type')
        InlineModels = []

        # Determine the inline model based on layer_type
        if layer_type == 'ArcRest':
            InlineModels = [LayerArcREST,]
        elif layer_type == 'WMS':
            InlineModels = [LayerWMS,]
        elif layer_type == 'XYZ':
            InlineModels = [LayerXYZ,]
        elif layer_type == 'Vector':
            InlineModels = [LayerVector,]
        elif layer_type == "slider":
            InlineModels = [MultilayerDimension, MultilayerAssociation,]
        elif layer_type == "ArcFeatureServer":
            InlineModels = [LayerArcFeatureService,]

        # If an inline model is determined, proceed to save it
        for nestedModel in InlineModels:
            if nestedModel == MultilayerDimension:
                InlineFormSet = NestedMultilayerDimensionInlineFormset
            elif nestedModel == MultilayerAssociation:
                InlineFormSet = NestedMultilayerAssociationInlineFormset
            else:
                InlineFormSet = inlineformset_factory(Layer, nestedModel, fields='__all__')
            formset = InlineFormSet(request.POST, request.FILES, instance=obj)
            if formset.is_valid() and nestedModel.objects.filter(layer=obj).count() == 1:
                formset.save()

    def handle_layer_type_change(self, request, obj, original_layer_type, new_layer_type):
        if new_layer_type == "slider":
            # Handle the slider case by just saving the formset
            self.save_inline_formsets(request, obj)
        else:
            # Handle the case for other layer types by getting or creating the instance
            InlineModelClass = self.get_inline_model_class(new_layer_type)

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
            # 'XYZ': [XYZInline],
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

# class ChildOrderForm(forms.ModelForm):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['parent_theme'].queryset = Theme.all_objects.all()

# class ChildOrderAdmin(admin.ModelAdmin):
#     list_display = ('parent_theme', 'content_type', 'object_id', 'order')
#     form = ChildOrderForm

admin.site.register(Theme, ThemeAdmin)
admin.site.register(Layer, LayerAdmin)
admin.site.register(LookupInfo, LookupInfoAdmin)
# admin.site.register(ChildOrder, ChildOrderAdmin)