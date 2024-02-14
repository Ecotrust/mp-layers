from django.contrib import admin
from .models import *
from django import forms
import nested_admin

# Register your models here.

class ThemeAdminForm(forms.ModelForm):
    class Meta:
        model = Theme
        exclude = ('layer_type', "slug_name") 

class ThemeAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'name', 'order', 'primary_site', 'preview_site')
    form = ThemeAdminForm
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
class ThemeChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        # Return the name of the Theme object to be used as the label for the choice
        return obj.name

class SublayerChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        # Return the name of the Theme object to be used as the label for the choice
        return obj.name

class CompanionLayerChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        # Return the name of the Theme object to be used as the label for the choice
        return obj.name



class LayerForm(forms.ModelForm):

    order = forms.IntegerField(required=False)
    themes = ThemeChoiceField(queryset=Theme.all_objects.all().filter(layer_type=''), required=False, widget = admin.widgets.FilteredSelectMultiple('themes', False))
    is_sublayer = forms.BooleanField(required=False)
    has_companion = forms.BooleanField(required=False)
    sublayers = SublayerChoiceField(queryset=Layer.all_objects.all(), required=False, widget = admin.widgets.FilteredSelectMultiple('sublayers', False))
    companion_layers = CompanionLayerChoiceField(queryset=Layer.all_objects.all(), required=False, widget = admin.widgets.FilteredSelectMultiple('companion layers', False))
    class Meta:
        exclude = ('slug_name',)
        model = Layer
        fields = '__all__'
        widgets = {
            
            'attribute_fields': admin.widgets.FilteredSelectMultiple('Attribute fields', False),
            'lookup_table': admin.widgets.FilteredSelectMultiple('Lookup table', False),
        }

class ArcRESTInline(nested_admin.NestedTabularInline):
    model = LayerArcREST

class WMSInline(admin.StackedInline):
    model = LayerWMS

class XYZInline(admin.StackedInline):
    model = LayerXYZ

class VectorInline(admin.StackedInline):
    model = LayerVector

class LayerAdmin(admin.ModelAdmin):
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
        content_type = ContentType.objects.get_for_model(obj)
        
        # Try to fetch the corresponding ChildOrder for this Layer
        child_order = ChildOrder.objects.filter(content_type=content_type, object_id=obj.pk).first()
        
        # Return the order if exists
        return child_order.order if child_order else 'None'
    get_order.short_description = 'Order'  # Sets column name

    def get_fieldsets(self, request, obj=None):
        # Dynamically return fieldsets based on the layer_type
        if obj and obj.layer_type == 'ArcRest':
            # No need to modify self.fieldsets; directly return the combined fieldsets
            return self.base_fieldsets + self.arcrest_fieldsets
        return self.base_fieldsets
    list_display = ('name', 'layer_type', 'date_modified', "get_parent_theme", "get_order", 'data_publish_date', 'data_source')
    search_fields = ['name', 'layer_type', 'date_modified', 'url', 'data_source']
    ordering = ('name', )
    exclude = ('slug_name',)
    class Media:
        js = ['layer_admin.js',]

    if settings.CATALOG_TECHNOLOGY not in ['default', None]:
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
                'site'
            )
    base_fieldsets = (
        ('BASIC INFO', {
            'fields': basic_fields
        }),
        ('LAYER ORGANIZATION', {
            # 'classes': ('collapse', 'open',),
            'fields': (
                ('order','themes'),
                ('is_sublayer','sublayers'),
                ('has_companion','companion_layers'),
                # RDH 2019-10-25: We don't use this, and it doesn't seem helpful
                # ('is_disabled','disabled_message')
            )
        }),
        ('METADATA', {
            'classes': ('collapse',),
            'fields': (
                'description', 'overview','data_source','data_notes', 'data_publish_date'
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
        }),)
    inlines = [ArcRESTInline, WMSInline, XYZInline, VectorInline] 
    
    def get_queryset(self, request):
        # use our manager, rather than the default one
        qs = self.model.all_objects.get_queryset()

        # we need this from the superclass method
        ordering = self.ordering or () # otherwise we might try to *None, which is bad ;)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs
    
# if hasattr(settings, 'DATA_MANAGER_ADMIN'):
#     admin.site.register(Theme, ThemeAdmin)
admin.site.register(Theme, ThemeAdmin)
# admin.site.register(Layer, LayerAdmin)
admin.site.register(Layer)