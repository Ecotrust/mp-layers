from django.contrib import admin
from .models import *
from django import forms

# Register your models here.

# class ThemeAdmin(admin.ModelAdmin):
#     list_display = ('display_name', 'name', 'order', 'primary_site', 'preview_site')

#     def formfield_for_manytomany(self, db_field, request=None, **kwargs):
#         if db_field.name == 'site':
#             kwargs['widget'] = forms.CheckboxSelectMultiple()
#             kwargs['widget'].attrs['style'] = 'list-style-type: none;'
#             kwargs['widget'].can_add_related = False

#         return db_field.formfield(**kwargs)
    
# if hasattr(settings, 'DATA_MANAGER_ADMIN'):
#     admin.site.register(Theme, ThemeAdmin)