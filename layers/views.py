from dataclasses import dataclass, asdict
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
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
    from django.core.cache import cache
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
    from django.core.cache import cache
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
    from django.core.cache import cache
    from django.contrib.sites import shortcuts
    # if (
    #     Site.objects.filter(domain=request.META['HTTP_HOST']).count() == 1 and
    #     not request.site == Site.objects.get(domain=request.META['HTTP_HOST'])
    # ):
    #     request.site = Site.objects.get(domain=request.META['HTTP_HOST'])
    #     current_site_pk = request.site.id
    # if request.META['HTTP_HOST'] in ['localhost:8000', 'localhost:8001', 'localhost:8002','portal.midatlanticocean.org', 'midatlantic.webfactional.com']:
    if request.META['HTTP_HOST'] in ['localhost:8000', 'portal.midatlanticocean.org', 'midatlantic.webfactional.com']:
        current_site_pk = 1
    elif request.META['HTTP_HOST'] in ['localhost:8002',]:
        current_site_pk = 2
    else:
        current_site_pk = shortcuts.get_current_site(request).pk
    data = cache.get('layers_json_site_%d' % current_site_pk)
    # if not data or not data["themes"]:
    child_orders = ChildOrder.objects.all()
    processed_items = []

    for child_order in child_orders:
        content_object = child_order.content_object
        if content_object is None:
        # Log this condition, handle it, or skip this iteration
            continue
        if isinstance(content_object, Layer):
            if content_object.parent and content_object.parent.parent:
                continue  # Skip layers with a grandparent
        cache_entry = dictLayerCache(content_object, current_site_pk)
        processed_items.append(cache_entry)
    data = {
        "state": { "activeLayers": [] },
        "layers": processed_items,
        "themes": [dictThemeCache(theme, current_site_pk) for theme in Theme.all_objects.filter(theme_type = "").order_by('order')],
        "success": True
    }
    # Cache for 1 week, will be reset if layer data changes
    cache.set('layers_json_site_%d' % current_site_pk, data, 60*60*24*7)
    return JsonResponse(data)

def get_themes(request):
    themeContentType = ContentType.objects.get_for_model(Theme)
    themeOrders = ChildOrder.objects.filter(content_type=themeContentType)
    subtheme_ids = [x.object_id for x in themeOrders]
    data = {
        "themes": [ShortThemeSerializer(theme).data for theme in Theme.objects.exclude(pk__in=subtheme_ids).order_by('order', 'name')],
    }
    return JsonResponse(data)

def get_layer_search_data(request):
    theme_content_type = ContentType.objects.get_for_model(Theme)
    layer_content_type = ContentType.objects.get_for_model(Layer)
    search_dict = {}
    for theme in Theme.objects.filter(is_visible=True):
        # Get child orders for the theme where content_type is Layer
        child_orders = ChildOrder.objects.filter(
            parent_theme=theme,
        )

        # Iterate through each child order to access the Layer instances
        for child_order in child_orders:
            child = child_order.content_object 
            if child_order.content_type == theme_content_type:
                has_sublayers = ChildOrder.objects.filter(parent_theme=child).exists()
                # Get all the child orders for this parent theme
                sublayers_data = []
                if has_sublayers:
                    sub_child_orders = ChildOrder.objects.filter(parent_theme=child)
                    for sub_child_order in sub_child_orders:
                        sub_layer = sub_child_order.content_object
                        sublayers_data.append({
                            "name": sub_layer.name,
                            "id": sub_layer.id
                        })
                search_dict[child.name] = {
                    'layer': {
                            'id': child.id,
                            'name': child.name,
                            'has_sublayers': has_sublayers,
                            'sublayers': sublayers_data
                        },
                        'theme': {
                            'id': theme.id,
                            'name': theme.display_name,
                            'description': theme.description
                        }
                }
            else:
                search_dict[child.name] = {
                    'layer': {
                            'id': child.id,
                            'name': child.name,
                            'has_sublayers': False,
                            'sublayers': []
                        },
                        'theme': {
                            'id': theme.id,
                            'name': theme.display_name,
                            'description': theme.description
                        }
                }

    return JsonResponse(search_dict)

def get_layers_for_theme(request, themeID):
    theme = Theme.objects.get(pk=themeID)
    theme_content_type = ContentType.objects.get_for_model(Theme)
    layer_content_type = ContentType.objects.get_for_model(Layer)

    if (
        Site.objects.filter(domain=request.META['HTTP_HOST']).count() == 1 and 
        not request.site == Site.objects.get(domain=request.META['HTTP_HOST']) 
    ):
        request.site = Site.objects.get(domain=request.META['HTTP_HOST'])

    child_orders = ChildOrder.objects.filter(
            parent_theme=theme,
        )

    site_valid_order_ids = []
    for order in child_orders:
        if request.site in order.content_object.site.all():
            site_valid_order_ids.append(order.id)
    child_orders = child_orders.filter(id__in=site_valid_order_ids).order_by("order")

    sorted_child_orders = sorted(
        list(child_orders), 
        key=lambda x: (x.order, getattr(x.content_object, 'name', ""))
    )
    
    layer_list = []
    for child_order in sorted_child_orders:
        child = child_order.content_object
        if child_order.content_type == theme_content_type:
            has_sublayers = ChildOrder.objects.filter(parent_theme=child).exists()
            sublayers_data = []
            if has_sublayers:
                sub_child_orders = ChildOrder.objects.filter(parent_theme=child)
                for sub_child_order in sub_child_orders:
                    sub_layer = sub_child_order.content_object
                    sublayers_data.append({
                        "name": sub_layer.name,
                        "id": sub_layer.id,
                        "slug_name": sub_layer.slug_name,
                    })
            layer_list.append({
                'id': child.id,
                'name': child.name,
                'type': child.theme_type,
                'has_sublayers': has_sublayers,
                'subLayers': sublayers_data,
            })
        elif not (child_order.content_type == layer_content_type and child_order.content_object.layer_type == 'placeholder'):
            layer_list.append({
                'id': child.id,
                'name': child.name,
                'type': child.layer_type,
                'has_sublayers': False,
                'subLayers': [],
            })
        else:
            #placeholder layer
            pass
    return JsonResponse({'layers': layer_list})

def get_layer_details(request, layerID):
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
            specific_layer = specific_layer_model.objects.get(layer=layer)
        else: 
            specific_layer = layer
        specific_layer_serializer_class = layer_type_to_serializer.get(layer.layer_type)
        # Instantiate the serializer with the specific layer instance
        if specific_layer_serializer_class:
            specific_layer_serializer = specific_layer_serializer_class(specific_layer)
            # Now you can use the serializer to get the serialized data
            serialized_data = specific_layer_serializer.data
        else:
            serialized_data = {"id": layer.id, "name": layer.name, "type": layer.layer_type}
        return JsonResponse(serialized_data)
    except ObjectDoesNotExist as e:
        subtheme = Theme.all_objects.get(pk=layerID)
        serialized_data = SubThemeSerializer(subtheme).data
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

    result = {
        'layers': list(layers.keys()),
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

def get_layer_catalog_content(request, layerID):
    layer = Layer.all_objects.get(pk=layerID)
    return JsonResponse({'html': layer.catalog_html})

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
    child_orders = Theme.objects.get(id=parent_id).children.order_by('order') 
    theme_content_type = ContentType.objects.get_for_model(Theme)
    layer_content_type = ContentType.objects.get_for_model(Layer)
    children = []
    for child in child_orders:
        try:
            child_data = {}
            if child.content_type == theme_content_type:
                child_theme = Theme.objects.get(id=child.object_id)
                child_data = {
                    'id': child_theme.id,
                    'name': child_theme.name,
                    'type': "theme",
                    "theme_type": child_theme.theme_type
                }
            elif child.content_type == layer_content_type:
                child_layer = Layer.objects.get(id=child.object_id)
                #Sidebar is a temporary replacement for serializer
                child_data = {
                    'id': child_layer.id,
                    'name': child_layer.name,
                    'type': "layer",
                    'metadata': child_layer.metadata,
                    'source': child_layer.source,
                    'data_download': child_layer.data_download,
                    'kml': child_layer.kml,
                    'description': child_layer.description,
                    "minzoom": child_layer.minZoom,
                    "maxzoom": child_layer.maxZoom,
                }
            if child_data:
                child_data['order'] = child.order
                children.append(child_data)
        except ObjectDoesNotExist:
            continue
    children_sorted = sorted(children, key=lambda x: (x['order'], x['name']))
    final_children = [{key: value for key, value in child.items() if key != 'order'} for child in children_sorted]
    return JsonResponse(final_children, safe=False)

def top_level_themes(request):
    themeContentType = ContentType.objects.get_for_model(Theme)
    themeOrders = ChildOrder.objects.filter(content_type=themeContentType)
    subtheme_ids = [x.object_id for x in themeOrders]
    top_level_themes =  Theme.objects.exclude(pk__in=subtheme_ids).exclude(display_name="Companion").filter(is_visible=True).order_by('order', 'name')
    themes = []
    for theme in top_level_themes:
        data = {
            'id': theme.id,
            'name': theme.display_name,
            'type': "theme"
        }
        themes.append(data)
    return JsonResponse({'top_level_themes': themes})