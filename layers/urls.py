from django.urls import path, re_path, include
from . import views

# re_path of 'r^accounts/' will match on any url starting with accounts/
# path is an exact match

urlpatterns = [
    #'',
    # path('get_json$', views.get_json),
    re_path(r'^get_json/?$', views.get_json),
    # re_path(r'^get_json2/?$', views.get_json2),
    re_path(r'^get_themes/?$', views.get_themes),
    re_path(r'^get_layer_search_data/?$', views.get_layer_search_data),
    re_path(r'^get_layers_for_theme/(?P<themeID>\d+)/?$', views.get_layers_for_theme),
    re_path(r'^get_theme_details/(?P<themeID>\d+)/?$', views.get_theme_details),
    re_path(r'^get_layer_details/(?P<layerID>\d+)/?$', views.get_layer_details),
    re_path(r'^wms_capabilities', views.wms_request_capabilities),
    re_path(r'^get_layer_catalog_content/(?P<objectType>\w+)/(?P<objectID>\d+)/(?P<themeID>\d+)/?$', views.get_layer_catalog_content),
    path('get_layer_catalog_content/<objectType>/<int:objectID>/', views.get_layer_catalog_content),
    re_path(r'^get_catalog_records/', views.get_catalog_records),
    re_path(r'^migration/layer_status/', views.layer_status),
    re_path(r'^migration/layer_details/', views.migration_layer_details),
    re_path(r'^picker/', views.get_picker),
    re_path(r'^top_level_themes/', views.top_level_themes),
    re_path(r'^picker_wrapper/', views.picker_wrapper),
    re_path(r'^children/(?P<parent_id>\d+)/?$', views.get_children),
]