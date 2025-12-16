from dataclasses import dataclass, asdict
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import RequestContext
from django.urls.exceptions import NoReverseMatch
from django.views.decorators.cache import cache_page
import json
import requests
from rest_framework import viewsets
from .models import *
from .serializers import *

layer_type_to_model = {
    'XYZ': LayerXYZ,
    'WMS': LayerWMS,
    'ArcRest': LayerArcREST,
    'ArcFeatureServer': LayerArcFeatureService,
    'Vector': LayerVector,
    "slider": Layer
}

layer_type_to_serializer = {
    'XYZ': LayerXYZSerializer,
    'WMS': LayerWMSSerializer,
    'ArcRest': LayerArcRESTSerializer,
    'ArcFeatureServer': LayerArcFeatureServiceSerializer,
    'Vector': LayerVectorSerializer,
    "slider": SliderLayerSerializer
}
def dictLayerCache(layer, site_id=None):
    
    layers_dict = None
    if site_id in [x.id for x in layer.site.all()]:
        if site_id:
            layers_dict = cache.get('layers_layer_%d_%d' % (layer.id, site_id))
        if not layers_dict:
            if isinstance(layer, Layer):
                if layer.layer_type == "WMS": 
                    try:
                        layer_wms = LayerWMS.objects.get(layer=layer)
                        layers_dict = LayerWMSSerializer(layer_wms).data
                    except LayerWMS.DoesNotExist:
                        pass
                elif layer.layer_type == "ArcRest":
                    try: 
                        layer_arcrest = LayerArcREST.objects.get(layer = layer)
                        layers_dict = LayerArcRESTSerializer(layer_arcrest).data
                    except LayerArcREST.DoesNotExist:
                        pass
                elif layer.layer_type == "ArcFeatureServer":
                    try:
                        layer_arcfeature = LayerArcFeatureService.objects.get(layer = layer)
                        layers_dict = LayerArcFeatureServiceSerializer(layer_arcfeature).data
                    except LayerArcFeatureService.DoesNotExist:
                        pass
                elif layer.layer_type == "Vector":
                    try:
                        layer_vector = LayerVector.objects.get(layer = layer)
                        layers_dict = LayerVectorSerializer(layer_vector).data
                    except LayerVector.DoesNotExist:
                        pass
                elif layer.layer_type == "XYZ":
                    try:
                        layer_xyz = LayerXYZ.objects.get(layer = layer)
                        layers_dict = LayerXYZSerializer(layer_xyz).data
                    except LayerXYZ.DoesNotExist:
                        pass
                else: 
                    layers_dict = LayerSerializer(layer).data
            elif isinstance(layer, Theme):
                layers_dict = SubThemeSerializer(layer).data
            if site_id:
                # Cache for 1 week, will be reset if layer data changes
                cache.set('layers_layer_%d_%d' % (layer.id, site_id), layers_dict, 60*60*24*7)
            else:
                for site in Site.objects.all():
                    cache.set('layers_layer_%d_%d' % (layer.id, site.id), layers_dict, 60*60*24*7)
    return layers_dict

def dictThemeCache(theme, site_id=None):
    themes_dict = None
    if site_id in [x.id for x in theme.site.all()]:
        if site_id:
            themes_dict = cache.get('layers_theme_%d_%d' % (theme.id, site_id))
        if not themes_dict:
            themes_dict = ThemeSerializer(theme).data
            if site_id:
                # Cache for 1 week, will be reset if layer data changes
                cache.set('layers_theme_%d_%d' % (theme.id, site_id), themes_dict, 60*60*24*7)
            else:
                for site in Site.objects.all():
                    cache.set('layers_theme_%d_%d' % (theme.id, site.id), themes_dict, 60*60*24*7)
    
    return themes_dict
# Create your views here.
def get_json(request):
    from data_manager.views import get_json as old_get_json
    return old_get_json(request)

# def get_json2(request):
#     from django.core.cache import cache
#     from django.contrib.sites import shortcuts
#     themeContentType = ContentType.objects.get_for_model(Theme)
#     layerContentType = ContentType.objects.get_for_model(Layer)
#     data = {
#         'state': {
#             'active_layers': [],
#         },
#         'success': False,
#     }
#     themes = Theme.objects.all()
#     layers = Layer.objects.all()
#     theme_list = []
#     for theme in themes:
#         theme_dict = cache.get('theme_{}_brief_json_site_{}'.format(theme.pk, request.site.id))
#         if not theme_dict:
#             theme_layers = [x.object_id for x in ChildOrder.objects.filter(parent_theme=theme, content_type=layerContentType)]
#             theme_dict = {
#                 'id': theme.pk,
#                 'name': theme.name,
#                 'display_name': theme.display_name,
#                 'learn_link': theme.learn_link,
#                 'is_visible': theme.is_visible,
#                 'description': theme.description,
#                 'layers': theme_layers
#             }
#             # cache.set('theme_{}_brief_json_site_{}'.format(theme.pk, request.site.id), theme_dict)
#         theme_list.append(theme_dict)
#     data['themes'] = theme_list

#     layers_list = []
#     # layers_list = [{"id": x.id, "name": x.name} for x in layers]
#     # for layer in layers:
#     #     layers_list.append(dictLayerCache(layer, request.site.id))
#     data['layers'] = layers_list
#     # # if (
#     # #     Site.objects.filter(domain=request.META['HTTP_HOST']).count() == 1 and
#     # #     not request.site == Site.objects.get(domain=request.META['HTTP_HOST'])
#     # # ):
#     # #     request.site = Site.objects.get(domain=request.META['HTTP_HOST'])
#     # #     current_site_pk = request.site.id
#     # # if request.META['HTTP_HOST'] in ['localhost:8000', 'localhost:8001', 'localhost:8002','portal.midatlanticocean.org', 'midatlantic.webfactional.com']:
#     # if request.META['HTTP_HOST'] in ['localhost:8000', 'portal.midatlanticocean.org', 'midatlantic.webfactional.com']:
#     #     current_site_pk = 1
#     # elif request.META['HTTP_HOST'] in ['localhost:8002',]:
#     #     current_site_pk = 2
#     # else:
#     #     current_site_pk = shortcuts.get_current_site(request).pk

#     # # if (
#     # #     Site.objects.filter(domain=request.META['HTTP_HOST']).count() == 1 and
#     # #     not request.site == Site.objects.get(domain=request.META['HTTP_HOST'])
#     # # ):
#     # #     request.site = Site.objects.get(domain=request.META['HTTP_HOST'])
#     # #     current_site_pk = request.site.id
#     # # elif request.META['HTTP_HOST'] in ['localhost:8000', 'localhost:8001', 'localhost:8002','portal.midatlanticocean.org', 'midatlantic.webfactional.com']:
#     # #     current_site_pk = 1
#     # # else:
#     # #     current_site_pk = shortcuts.get_current_site(request).pk

#     # data = cache.get('layers_json_site_%d' % current_site_pk)
#     # # if not data or not data["themes"]:
#     # child_orders = ChildOrder.objects.all()
#     # processed_items = []

#     # for child_order in child_orders:
#     #     content_object = child_order.content_object
#     #     if content_object is None:
#     #     # Log this condition, handle it, or skip this iteration
#     #         continue
#     #     if isinstance(content_object, Layer):
#     #         if content_object.parent and content_object.parent.parent:
#     #             continue  # Skip layers with a grandparent
#     #     cache_entry = dictLayerCache(content_object, current_site_pk)
#     #     processed_items.append(cache_entry)
#     # data = {
#     #     "state": { "activeLayers": [] },
#     #     "layers": processed_items,
#     #     "themes": [dictThemeCache(theme, current_site_pk) for theme in Theme.all_objects.filter(theme_type = "").order_by('order')],
#     #     "success": True
#     # }
#     # # Cache for 1 week, will be reset if layer data changes
#     # cache.set('layers_json_site_%d' % current_site_pk, data, 60*60*24*7)
#     data['success'] = True
#     return JsonResponse(data)

def get_themes(request):
    themeContentType = ContentType.objects.get_for_model(Theme)
    themeOrders = ChildOrder.objects.filter(content_type=themeContentType)
    subtheme_ids = [x.object_id for x in themeOrders]
    data = {
        "themes": [ShortThemeSerializer(theme).data for theme in Theme.objects.exclude(pk__in=subtheme_ids).order_by('order', 'name')],
    }
    return JsonResponse(data)

def get_layer_search_data(request):
    current_site = Site.objects.get_current(request)
    search_dict = {}
    for theme in Theme.objects.filter(is_visible=True):
        cache_key = 'layers_views_layer_search_data_{}_{}'.format(theme.pk, current_site.id)
        theme_dict = cache.get(cache_key)
        if theme_dict is None:
            theme_dict = {}
            # Get child orders for the theme where content_type is Layer
            child_orders = ChildOrder.objects.filter(
                parent_theme=theme,
            )

            # Iterate through each child order to access the Layer instances
            for child_order in child_orders:
                child = child_order.content_object
                if current_site in child.site.all():
                    theme_dict[child.name] = child.get_search_object(current_site.id, theme)
            cache.set(cache_key, theme_dict, 60*60*24*7)  # Cache for 1 week
        search_dict.update(theme_dict)

    return JsonResponse(search_dict)


# As per requirements: The third level will be comprised of EVERY layer that could be accessed by the v2 hierarchy, squashing it so each parent 'theme' not represented in the first two levels becomes part of the layer's name
def get_layers_for_theme(request, themeID):
    theme = Theme.objects.get(pk=themeID)

    def collect_layers(theme_obj, parent_name=None, exclude_top_level=False):
        """
        Recursively collect only layers, prepending the immediate parent's name to their names.
        Ensures the top-level theme name is not repeated in sublayers.
        """
        flat_layers = []
        child_orders = ChildOrder.objects.filter(parent_theme=theme_obj).order_by("order")
        sorted_child_orders = sorted(
            child_orders,
            key=lambda co: getattr(co.content_object, 'name', '').lower()
        )
        
        for child_order in sorted_child_orders:
            child = child_order.content_object
            if isinstance(child, Theme):
                # Exclude the top-level theme's name from being repeatedly appended
                theme_name = (
                    f"{parent_name} >> {child.name}"
                    if parent_name and not exclude_top_level
                    else child.display_name
                )
                # Recursively collect child layers/themes
                flat_layers.extend(collect_layers(child, parent_name=theme_name, exclude_top_level=False))
            elif isinstance(child, Layer):
                # Prepend only the immediate parent's name to the layer's name
                layer_name = f"{parent_name} >> {child.name}" if parent_name else child.name
                flat_layers.append({
                    "id": child.id,
                    "name": layer_name,
                    "layerName": child.name,
                    "slug_name": getattr(child, "slug_name", ""),
                })
        return flat_layers

    # Prepare the top-level response
    top_level_response = []
    child_orders = ChildOrder.objects.filter(parent_theme=theme).order_by("order")
    sorted_child_orders = sorted(
        child_orders,
        key=lambda co: (
            co.order,
            getattr(co.content_object, 'name', '').lower()
        )
    )
    filtered_child_orders = []
    current_site = get_current_site(request)
    for child_order in sorted_child_orders:
        if current_site in child_order.content_object.site.all():
            filtered_child_orders.append(child_order)
    for child_order in filtered_child_orders:
        child = child_order.content_object
        if isinstance(child, Theme):
            # Top-level themes are containers, with sublayers being flat
            top_level_response.append({
                "id": child.id,
                "name": child.display_name,
                "type": getattr(child, "theme_type", ""),
                "has_sublayers": True,
                "subLayers": collect_layers(child, parent_name=child.display_name, exclude_top_level=True),
            })
        elif isinstance(child, Layer):
            # Add layers directly under the top-level theme
            top_level_response.append({
                "id": child.id,
                "name": child.name,
                "type": child.layer_type,
                "has_sublayers": False,
                "subLayers": [],
                "slug_name": getattr(child, "slug_name", ""),
            })

    return JsonResponse({'layers': top_level_response})


def get_theme_details(request, themeID):
    try:
        subtheme = Theme.all_objects.get(pk=themeID)
        serialized_data = SubThemeSerializer(subtheme).data
    except (Theme.DoesNotExist, NoReverseMatch) as e:
        return JsonResponse(
            {
                'status': False,
                'message': str(e)
            },
            status=404
        )

    return JsonResponse(serialized_data)

def get_layer_details(request, layerID):
    current_site = get_current_site(request)
    serialized_data = cache.get('layers_layer_serialized_details_{}_{}'.format(layerID, current_site.pk))
    if not serialized_data:
        serialized_data = {}
        try:
            # First, get the generic layer instance
            layer = Layer.all_objects.get(pk=layerID)
            specific_layer_model = None
            # Use the layer_type attribute to get the specific model class
            if layer.layer_type != "slider":
                specific_layer_model = layer_type_to_model.get(layer.layer_type)
            # Now, use the specific model class to get the specific layer instance
            if specific_layer_model and specific_layer_model != Layer:
                # If admin doesn't touch specific layer form, no specific layer will have been created. This creates the default, 
                #   which has the same values that would be assumed if it were missing.
                (specific_layer, created) = specific_layer_model.objects.get_or_create(layer=layer)
            else: 
                # TODO: why set this to layer? Why not just skil the next 'if' case if there is no specific layer?
                # specific_layer = False
                specific_layer = layer
            specific_layer_serializer_class = layer_type_to_serializer.get(layer.layer_type)
            # Instantiate the serializer with the specific layer instance
            # if specific_layer and specific_layer_serializer_class:
            if specific_layer_serializer_class:
                specific_layer_serializer = specific_layer_serializer_class(specific_layer)
                # Now you can use the serializer to get the serialized data
                serialized_data = specific_layer_serializer.data
            else:
                serialized_data = {"id": layer.id, "name": layer.name, "type": layer.layer_type}
            cache.set('layers_layer_serialized_details_{}_{}'.format(layerID, current_site.pk), serialized_data, 60*60*24*7)
        except (Layer.DoesNotExist, ObjectDoesNotExist, NoReverseMatch) as layer_error:
            # TODO: Change layer picker logic to use /children/ API call if item is a Theme!
            try:
                subtheme = Theme.all_objects.get(pk=layerID)
                serialized_data = SubThemeSerializer(subtheme).data
            except (Theme.DoesNotExist, NoReverseMatch) as theme_error:
                return JsonResponse(
                    {
                        'status': False,
                        'message': "; ".join([str(layer_error), str(theme_error)])
                    },
                    status=404
                )
            
    return JsonResponse(serialized_data)

def wms_get_capabilities(url):
    from datetime import datetime
    from owslib.wms import WebMapService

    if url[-1] == '?':
      url = url[0:-1]

    wms = WebMapService(url)
    layers = {}
    for layer in list(wms.contents): #TODO: create dict
        layers[layer] = {'dimensions':{}}
    styles = {}
    srs_opts = {}
    queryable = []
    times = {}
    import xml.etree.ElementTree as ET
    root = ET.fromstring(wms.getServiceXML())
    # get time dimensions from XML directly, in case OWSLIB fails to set it appropriately
    available_formats = False
    try:
        layer_group = root.find('Capability').findall('Layer')[0]
        current_layer = {
            'dimensions': {}
        }
        for layer in layer_group.findall('Layer'):
            if len(layer.findall('Dimension')) > 0:
                for dimension in layer.findall('Dimension'):
                    if dimension.get('name'):
                        current_layer['dimensions'][dimension.get('name')] = None
            if len(layer.findall('Extent')) > 0:
                for extent in layer.findall('Extent'):
                    if extent.get('name'):
                        current_layer['dimensions'][extent.get('name')] = {}
                        for key in extent.keys():
                            current_layer['dimensions'][extent.get('name')][key] = extent.get(key)
                        try:
                            positions = extent.text.split(',')
                            if len(positions) > 4:
                                current_layer['dimensions'][extent.get('name')]['positions'] = positions[0:2] + ['...'] + positions[-3:-1]
                            else:
                                current_layer['dimensions'][extent.get('name')]['positions'] = positions
                        except:
                            pass
                new_layer_dict = recurse_layers(layer, current_layer, {})
                for key in layers.keys():
                    if key in new_layer_dict.keys():
                        layers[key] = new_layer_dict[key]

        available_formats = []
        if root.find('Capability') and root.find('Capability').find('Request'):
            getFeatureInfo = root.find('Capability').find('Request').find('GetFeatureInfo')
            if getFeatureInfo:
                accepted_formats = [
                    'text/plain',
                    'text/html',
                    'text/xml',
                    'image/png',
                    'application/json',
                    'text/javascript',  #JSONP
                    'application/vnd.ogc.gml',
                ]
                for format_type in getFeatureInfo.findall('Format'):
                    if format_type.text in accepted_formats:
                        available_formats.append(format_type.text)


    except:
        # trouble parsing raw xml
        print('trouble parsing raw xml')
        pass

    for layer in layers.keys():
        styles[layer] = wms[layer].styles
        srs_opts[layer] = wms[layer].crsOptions
        try:
            if bool(wms[layer].queryable):
                queryable.append(layer)
        except Exception as e:
            print(e)
            pass

        dimensions = layers[layer]['dimensions']
        timefield = None
        if len(dimensions.keys()) == 1:
            timefield = dimensions.keys()[0]
        else:
            # there is no explicit way to know what time field is. This makes educated guesses.
            for dimension in dimensions.keys():
                if 'time' in dimension.lower():
                    timefield = dimension
                    break

        if timefield:
            layer_obj = layers[layer]['dimensions'][timefield]
        else:
            layer_obj = {}

        if wms[layer].timepositions:
            positions = wms[layer].timepositions
        elif 'positions' in layer_obj.keys():
            positions = layer_obj['positions']
        else:
            positions = None
        if wms[layer].defaulttimeposition:
            defaulttimeposition = wms[layer].defaulttimeposition
        elif 'default' in layer_obj.keys():
            defaulttimeposition = layer_obj['default']
        else:
            defaulttimeposition = None


        times[layer] = {
            'positions': positions,
            'default': defaulttimeposition,
            'field': timefield
        }

    capabilities = {}
    if available_formats and len(available_formats) > 0:
        capabilities['featureInfo'] = {
            'available': True,
            'formats': available_formats
        }

    try:
        layers_with_titles = []
        for key in wms.contents.keys():
            layers_with_titles.append({"key": key, "title": wms.contents[key].title})
        available_layers = layers_with_titles
    except Exception as e:
        available_layers = list(layers.keys()) 

    result = {
        'layers': available_layers,
        'formats': wms.getOperationByName('GetMap').formatOptions,
        'version': wms.version,
        'styles':  styles,
        'srs': srs_opts,
        'queryable': queryable,
        'time': times,
        'capabilities': capabilities,
    }

    return result

def wms_request_capabilities(request):
    from requests.exceptions import SSLError

    url = request.GET.get('url')
    try:
        result = wms_get_capabilities(url)
    except SSLError as e:
        # Sometimes SSL certs aren't right - if we trust the user hitting this endpoint,
        #       Then we should be safe trying to get the data w/o HTTPS.
        if request.user.is_staff and 'https://' in url.lower():
            result = wms_get_capabilities(url.lower().replace('https://','http://'))
        else:
            # leave the error alone until we have a better solution
            result = wms_get_capabilities(url)

    return JsonResponse(result)

def get_layer_catalog_content(request, objectType, objectID, themeID=None):
    if objectType == 'layer':
        layer = Layer.all_objects.get(pk=objectID)
        if not themeID is None:
            theme = Theme.all_objects.get(pk=themeID)
            return JsonResponse({'html': layer.get_catalog_html(theme=theme)})
        return JsonResponse({'html': layer.catalog_html})
    elif objectType == 'theme':
        theme = Theme.all_objects.get(pk=objectID)
        return JsonResponse({'html': theme.catalog_html})

def get_catalog_records(request):
    data = {}
    if settings.CATALOG_TECHNOLOGY and settings.CATALOG_TECHNOLOGY == "GeoPortal2":
        from elasticsearch import Elasticsearch
        from elasticsearch_dsl import Search
        es = Elasticsearch()
        index = settings.ELASTICSEARCH_INDEX
        url = settings.CATALOG_SOURCE
        if url:
            es = es = Elasticsearch(url)
        else:
            es = es = Elasticsearch()

        search = Search(using=es, index=index).query("match", sys_approval_status_s="approved")

        search_fields = settings.ELASTICSEARCH_SEARCH_FIELDS

        records = search.source(search_fields)

        records_dict = {}
        # record_ids = []
        record_names = []
        record_name_lookup = {}

        for record in records.scan():
            # record_ids.append(record.meta.id)
            record_dict = {}
            for index, field in enumerate(['id'] + search_fields):
                if index == 0:
                    record_dict['id'] = record.meta.id
                else:
                    if field == settings.DATA_CATALOG_NAME_FIELD:
                        if not record[field] in record_name_lookup.keys():
                            record_name_lookup[record[field]] = []
                        record_name_lookup[record[field]].append(record.meta.id)
                    record_dict[field] = record[field]
            records_dict[record.meta.id] = record_dict

        # data['ids'] = record_ids
        data['records'] = records_dict
        data['record_name_lookup'] = record_name_lookup
        data['ELASTICSEARCH_INDEX'] = settings.ELASTICSEARCH_INDEX
        data['CATALOG_TECHNOLOGY'] = settings.CATALOG_TECHNOLOGY
        # data['hits'] = len(record_ids)

    return JsonResponse(data)

def get_sublayers_data(parent_theme):
    sublayers_data = []
    sub_child_orders = ChildOrder.objects.filter(parent_theme=parent_theme).order_by('order')

    for sub_child_order in sub_child_orders:
        sub_layer = sub_child_order.content_object
        sublayers_data.append({
            'uuid': str(sub_layer.uuid),
            'name': sub_layer.name,
            'date_modified': sub_layer.date_modified.isoformat(),
            # Assuming sublayers don't have further sublayers
        })

    return sublayers_data

def layer_status(request):
    data = {
        'themes': {},
        'layers': {}    
    }
    theme_content_type = ContentType.objects.get_for_model(Theme)
    for theme in Theme.all_objects.filter(theme_type="").order_by('order', 'name', 'uuid'):
        theme_dict = False
        for site in Site.objects.all():
            if not theme_dict:
                theme_dict = dictThemeCache(theme,site_id= site.id)
            else:
                new_site_dict = dictThemeCache(theme, site_id=site.id)
                if new_site_dict:
                    new_layers = new_site_dict['layers']
                    theme_dict['layers'] = list(set(theme_dict['layers'] + new_layers))
            
        data['themes'][str(theme.uuid)] = {
            'name': theme.name,
            'uuid': theme.uuid,
            'date_modified': theme.date_modified,
            'layers': []
        }
        if theme_dict:
            theme_layers = []
            child_orders = ChildOrder.objects.filter(parent_theme=theme).order_by('order')

            for child_order in child_orders:
                child = child_order.content_object
                if child_order.content_type == theme_content_type:
                    subtheme = child_order.content_object
                    subtheme_layers = get_sublayers_data(subtheme)
                    # Append subtheme as a layer with its sublayers
                    theme_layers.append({
                        'uuid': str(subtheme.uuid),
                        'name': subtheme.name,
                        'date_modified': subtheme.date_modified.isoformat(),
                        'subLayers': subtheme_layers,
                    })
                else:
                    # It's a direct layer under the theme
                    theme_layers.append({
                        'uuid': str(child.uuid),
                        'name': child.name,
                        'date_modified': child.date_modified.isoformat(),
                        'subLayers': [],  # Direct layers under a theme don't have sublayers
                    })

            data['themes'][str(theme.uuid)] = {
                'name': theme.name,
                'uuid': str(theme.uuid),
                'date_modified': theme.date_modified.isoformat(),
                'layers': theme_layers
            }

    child_orders = ChildOrder.objects.all()
    sorted_child_orders = sorted(child_orders, key=lambda co: str(co.content_object.uuid))
    for child_order in sorted_child_orders:
        content_object = child_order.content_object
        data['layers'][str(content_object.uuid)] = {
            'name': content_object.name,
            'date_modified': content_object.date_modified.isoformat()  # Ensure date is JSON serializable
        }
    return JsonResponse(data)

def migration_layer_details(request, uuid=None):
    data = {
        'status': 'Unknown', 
        'message': 'Unknown',
        'themes': {},
        'layers': {},
    }
    if request.POST:
        try:
            layer_ids = request.POST.getlist('layers')
            for layer_key in layer_ids:
                try:
                    layer = Layer.all_objects.get(uuid=layer_key)
                    # Assuming you have different serializers based on layer_type or other conditions
                    if layer.layer_type == 'WMS':
                        wmslayer = LayerWMS.objects.get(layer=layer)
                        serialized_data = LayerWMSSerializer(wmslayer).data
                    elif layer.layer_type == "ArcRest":
                        arcrestlayer = LayerArcREST.objects.get(layer=layer)
                        serialized_data = LayerArcRESTSerializer(arcrestlayer).data
                    elif layer.layer_type == "ArcFeatureServer":
                        arclayer = LayerArcFeatureService.objects.get(layer=layer)
                        serialized_data = LayerArcFeatureServiceSerializer(arclayer).data
                    elif layer.layer_type == "XYZ":
                        xyzlayer = LayerXYZ.objects.get(layer=layer)
                        serialized_data = LayerXYZSerializer(xyzlayer).data
                    elif layer.layer_type == "Vector":
                        vectorlayer = LayerVector.objects.get(layer=layer)
                        serialized_data = LayerVectorSerializer(vectorlayer).data
                    else:
                        # Default to a generic serializer for layers
                        serialized_data = LayerSerializer(layer).data
                    data['layers'][layer_key] = serialized_data
                except ObjectDoesNotExist:
                    # If not found in Layer, try finding in Theme
                    try:
                        theme = Theme.all_objects.get(uuid=layer_key)
                        serialized_data = SubThemeSerializer(theme).data
                        data['layers'][layer_key] = serialized_data
                    except ObjectDoesNotExist:
                        # Handle the case where the UUID matches neither a Layer nor a Theme
                        pass
            data['status'] = 'Success'
            data['message'] = 'layer(s) details retrieved'
            
        except Exception as e:
            data['status'] = 'Error'
            data['message'] = str(e)
            pass
    elif not uuid == None:
        try:
            layer = Layer.all_objects.get(uuid=uuid)
            # Assuming you have different serializers based on layer_type or other conditions
            if layer.layer_type == 'WMS':
                wmslayer = LayerWMS.objects.get(layer=layer)
                serialized_data = LayerWMSSerializer(wmslayer).data
            elif layer.layer_type == "ArcRest":
                arcrestlayer = LayerArcREST.objects.get(layer=layer)
                serialized_data = LayerArcRESTSerializer(arcrestlayer).data
            elif layer.layer_type == "ArcFeatureServer":
                arclayer = LayerArcFeatureService.objects.get(layer=layer)
                serialized_data = LayerArcFeatureServiceSerializer(arclayer).data
            elif layer.layer_type == "XYZ":
                xyzlayer = LayerXYZ.objects.get(layer=layer)
                serialized_data = LayerXYZSerializer(xyzlayer).data
            elif layer.layer_type == "Vector":
                vectorlayer = LayerVector.objects.get(layer=layer)
                serialized_data = LayerVectorSerializer(vectorlayer).data
            else:
                # Default to a generic serializer for layers
                serialized_data = LayerSerializer(layer).data
            data['layers'][layer_key] = serialized_data
        except ObjectDoesNotExist:
            # If not found in Layer, try finding in Theme
            try:
                theme = Theme.all_objects.get(uuid=uuid)
                serialized_data = SubThemeSerializer(theme).data
                data["layers"][layer_key] = serialized_data
            except ObjectDoesNotExist:
                # Handle the case where the UUID matches neither a Layer nor a Theme
                pass
            data['status'] = 'Success'
            data['message'] = 'layer details retrieved'
        except Exception as e:
            data['status'] = 'Error'
            data['message'] = str(e)
            pass

    return JsonResponse(data)

def get_picker(request):
    pass

@dataclass
class SidebarData:
    id: int
    name: str
    type: str # can be "layer" or "theme"
    theme_type: str
@dataclass
class LayerData:
    id: int
    name: str
    type: str
    metadata:str
    source:str
    data_download:str
    kml:str
    description:str
    minzoom:int
    maxzoom:int

# def picker_wrapper(request, template="picker_wrapper.html"):
#     top_level_themes = Theme.all_objects.filter(theme_type="")
#     themes = []
#     for theme in top_level_themes:
#         data = SidebarData(
#             id=theme.id,
#             name=theme.name,
#             type="theme"
#         )
#         themes.append(asdict(data))
#     # Prepare context data to be passed to the template
#     context = {
#         'top_level_themes': themes,
#     }
#     # Render template with context
#     return render(request, template, context)
def picker_wrapper(request, template="picker_wrapper.html"):

    return render(request, template)

def get_children(request, parent_id):
 # Get the ContentTypes for Theme and Layer
    theme_content_type = ContentType.objects.get_for_model(Theme)
    layer_content_type = ContentType.objects.get_for_model(Layer)
    current_site = get_current_site(request)
    
    # Get the child orders (ChildOrder records) for the parent theme, ordered by 'order'
    child_orders = ChildOrder.objects.filter(parent_theme_id=parent_id).order_by('order')
    children = []

    # Loop through each ChildOrder to fetch child objects (Themes or Layers)
    for child_order in child_orders:
        try:
            child_data = cache.get('layers_childorder_{}_{}'.format(child_order.pk, current_site.pk))
            if not child_data:
                child_data = {}
                if current_site in child_order.content_object.site.all():
                    if child_order.content_type == theme_content_type:
                        # If the child object is a Theme
                        child_object = child_order.content_object
                        description = child_object.description or ""
                        if child_object.data_url:
                            read_more_link = f' <a href="{child_object.data_url}" target="_blank">Read More</a>'
                            description += read_more_link
                        child_data = {
                            'id': child_object.id,
                            "name": child_object.display_name,
                            'type': "theme",
                            "theme_type": child_object.theme_type, 
                            "is_dynamic": child_object.is_dynamic,
                            "url": child_object.dynamic_url,
                            "placeholder_text": child_object.placeholder_text,
                            "default_keyword": child_object.default_keyword,
                            "child_order": child_order.order,  # Order from ChildOrder
                            "metadata": child_object.metadata,
                            "source": child_object.source,
                            "data_download": child_object.data_download,
                            "kml": child_object.kml,
                            "description": description
                        }
                    elif child_order.content_type == layer_content_type:
                        # If the child object is a Layer (and not of 'placeholder' type)
                        child_object = child_order.content_object
                        if child_object.layer_type != 'placeholder':
                            description = child_object.description or ""
                            if child_object.data_url:
                                read_more_link = f' <a href="{child_object.data_url}" target="_blank">Read More</a>'
                                description += read_more_link
                            child_data = {
                                'id': child_object.id,
                                'name': child_object.name,
                                'type': "layer",
                                'metadata': child_object.metadata,
                                'source': child_object.source,
                                'data_download': child_object.data_download,
                                'kml': child_object.kml,
                                'description': description,
                                "minzoom": child_object.minZoom,
                                "maxzoom": child_object.maxZoom,
                                "child_order": child_order.order  # Order from ChildOrder
                            }
                cache.set('layers_childorder_{}_{}'.format(child_order.pk, current_site.pk), child_data, 60*60*24*7)
                
            if child_data and not child_data == {}:
                children.append(child_data)

        except ObjectDoesNotExist:
            continue
        except AttributeError as e:
            print(e)
            continue

    # Sort by child_order, name, and then type
    children_sorted = sorted(children, key=lambda x: (x['child_order'], x['name'], {'theme': 0, 'layer': 1}[x['type']]))


    # Remove 'order' key from the final output if you don't want it in the response
    final_children = [{key: value for key, value in child.items() if key != 'child_order'} for child in children_sorted]

    return JsonResponse(final_children, safe=False)

def top_level_themes(request):
    top_level_themes =  Theme.objects.filter(is_top_theme=True).order_by('order', 'name')
    themes = []
    for theme in top_level_themes:
        data = {
            'id': theme.id,
            "name": theme.name,
            "display_name": theme.display_name,
            "theme_type": theme.theme_type,
            "is_visible": theme.is_visible,
        }
        themes.append(data)
    return JsonResponse({'top_level_themes': themes})