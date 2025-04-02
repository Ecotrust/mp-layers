////////////////////////////////////////////////////////////////////////////////
//
//  Elasticsearch + Geoportal
//
////////////////////////////////////////////////////////////////////////////////


var populate_fields_from_catalog = function (catalog_record_data, record_id) {
    if (record_id == null || record_id == "null") {
        replace_all_select2_with_input();
        hide_spinner();
    } else {
        es_index = catalog_record_data.ELASTICSEARCH_INDEX;
        // handle multiple IDs
        id_list = record_id.split(",");
        aggregate_json = false;
        for (var i = 0; i < id_list.length; i++) {
            id = id_list[i];
        }
        url = CATALOG_PROXY + "/" + es_index + "/_doc/" + record_id;
        $.ajax({
            url: url,
            success: function (data) {
                // get id from data
                record_json = data._source;
                record_json.id = data._id;
                aggregate_catalog_record_values(record_json);
            }
        });
    }
}

var aggregate_catalog_record_values = function (record_json) {
    record_id = record_json.id;
    id_list.splice(id_list.indexOf(record_id), 1);

    if (!aggregate_json) {
        aggregate_json = record_json
    } else {
        for (var i = 0; i < Object.keys(record_json); i++) {
            key = Object.keys(record_json)[i];
            if (Object.keys(aggregate_json).indexOf(key) != -1) {
                if (aggregate_json[key].constructor != Array) {
                    aggregate_json[key] = [aggregate_json[key]];
                }
                if (record_json[key].constructor != Array) {
                    record_json[key] = [record_json[key]];
                }
                aggregate_json[key] = union(aggregate_json[key], record_json[key]);
            } else {
                aggregate_json[key] = record_json[key];
            }
        }
    }

    if (id_list.length == 0) {
        assign_field_values_from_catalog_record(record_json);
    }
}

var assign_field_values_from_catalog_record = function (record_json) {
    // TODO: write function to create appropriate list of links and associate them with tech options
    if (!record_json.hasOwnProperty('links_s')) {
        record_json.links_s = [];
        // replace_input_with_select2('id_url', union([],[]));
    }
    replace_input_with_select2('id_url', union([], record_json.links_s));

    // Metadata & Links
    /*
      id_description
      id_kml
      id_data_download
      id_metadata
      id_source
    */


    replace_input_with_select2('id_description', union([record_json.description], [record_json.apiso_Abstract_txt]));
    $('#select2-id_description-container').addClass('select2-textarea');
    $('#id_description').siblings('.select2').find('span.select2-selection').height(150);

    var kml_options = [];
    for (var i = 0; i < record_json.links_s.length; i++) {
        if (record_json.links_s[i].toLowerCase().indexOf('kml') != -1) {
            kml_options.push(record_json.links_s[i]);
        }
    }
    if (kml_options.length > 0) {
        replace_input_with_select2('id_kml', union([], kml_options));
    } else {
        replace_input_with_select2('id_kml', union([], record_json.links_s));
    }
    replace_input_with_select2('id_data_download', union([record_json.url_http_download_s], record_json.links_s));
    replace_input_with_select2('id_metadata', union([record_json.src_uri_s], record_json.links_s));
    replace_input_with_select2('id_source', union([], record_json.links_s));

    // Legend
    /*
      This is technology dependent (ArcGIS and WMS will have very specific options)
      id_show_legend [checkbox]
      id_legend (url to image file)
      id_legend_title
      id_legend_subtitle
    */

    // ArcGIS Details (ArcGIS only!)
    /*
      id_arcgis_layers (comma separated ID #s)
      id_query_by_point [ checkbox ]
      id_disable_arcgis_attributes [ checkbox ]
    */

    // if (get_service_type($('#id_url').val()) == "ArcRest" && $('#id_layer_type').val() == "ArcRest") {



    // WMS Details (WMS Only!)
    /*
      This section is already managed by selecting 'WMS help'
      If the user selects "WMS" for technology, perhaps explode this and scroll them to it to manage themselves?
    */

    // Attribute Reporting
    /*
      This cannot be set from the catalog record
    */

    // Style (Arc FeatureService only, which isn't supported yet)
    /*
      Tackle this when we add FeatureServices
    */




    hide_spinner();
}

/*
 * A lot of the code below is either copied from or inspired by work from ESRI's
 * GeoPortal Server Catalog work, licensed under the Apache License, Version 2.0
 * Their licence note is copied verbatim below.
 * You can find the whole project (license, code, and all) at this site:
 *
 * https://github.com/Esri/geoportal-server-catalog
 *
 * In particular, this leverages code and logic from this file:
 *
 * https://github.com/Esri/geoportal-server-catalog/blob/master/geoportal/src/main/webapp/app/etc/ServiceType.js
 *
 */

/* < ESRI License Disclaimer > */

/* See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * Esri Inc. licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/* </ ESRI Licence Disclaimer > */

get_service_type = function (url) {

    /*
      type
        ArcGIS - FeatureServer MapServer ImageServer VectorTileServer StreamServer
          -- Currently of these we support MapServer as "ArcRest"
          -- In theory 'Vector' nearly supports FeatureServer
          -- In theory 'VectorTile' nearly supports VectorTileServer
        WMS
        WMTS - not yet working with wab 2.0
          -- Not sure if we support this, we have WMS with extra settings to suppot "T"
          -- Wait, this might just by XYZ tiles
        WFS - not yet with wab 2.0
          -- I do not believe this is supported
        KML
          -- Not supported, but good to find for a KML link.
        GeoRSS
          -- Not Supported
        CSV
          -- Not Supported
        TO ADD:
          -- XYZ
          -- Vector (.json, etc..)
          -- VectorTile (?)
     */

    /*
      http://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/World_Cities/FeatureServer/0
      http://services.arcgisonline.com/ArcGIS/rest/services/Demographics/USA_Tapestry/MapServer
      http://imagery.arcgisonline.com/ArcGIS/rest/services/LandsatGLS/VegetationAnalysis/ImageServer
  
      http://mesonet.agron.iastate.edu/cgi-bin/wms/nexrad/n0r.cgi?service=WMS&request=GetCapabilities
      http://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_month_age_animated.kml
      http://www.gdacs.org/xml/rss.xml
      http://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.csv
  
      http://services2.arcgis.com/NZMqCJwY3kMjFOqf/arcgis/rest/services/Metro/FeatureServer
      http://services2.arcgis.com/NZMqCJwY3kMjFOqf/arcgis/rest/services/Metro/FeatureServer/8
      http://maps7.arcgisonline.com/arcgis/rest/services/USDA_USFS_2014_Wildfire_Hazard_Potential/MapServer
      http://services.arcgisonline.com/ArcGIS/rest/services/Demographics/USA_Tapestry/MapServer (tiles)
      http://imagery.arcgisonline.com/ArcGIS/rest/services/LandsatGLS/VegetationAnalysis/ImageServer
      https://geoeventsample3.esri.com:6443/arcgis/rest/services/SeattleBus/StreamServer
  
      http://basemaps.arcgis.com/arcgis/rest/services/World_Basemap/VectorTileServer
      http://basemaps.arcgis.com/arcgis/rest/services/World_Basemap/VectorTileServer/resources/styles/root.json
      http://geodesign.maps.arcgis.com/sharing/rest/content/items/bdf1eec3fa79456c8c7c2bb62f86dade/resources/styles/root.json
  
      http://suite.opengeo.org/geoserver/wfs?request=GetCapabilities&service=WFS&version=1.1.0
      http://v2.suite.opengeo.org/geoserver/gwc/service/wmts?request=GetCapabilities&service=WMTS&version=1.0.0
      http://www.ndbc.noaa.gov/kml/marineobs_as_kml.php
     */

    var endsWith = function (v, sfx) {
        return (v.indexOf(sfx, (v.length - sfx.length)) !== -1);
    };

    var lc, type = null;
    if (typeof url === "string" &&
        (url.indexOf("http://") === 0 || url.indexOf("https://") === 0)) {
        lc = url.toLowerCase();
        if (lc.indexOf("?service=") > 0 || lc.indexOf("&service=") > 0) {
            if (lc.indexOf("?service=wms") > 0 || lc.indexOf("&service=wms") > 0) {
                type = "WMS";
            } else if (lc.indexOf("?service=wmts") > 0 || lc.indexOf("&service=wmts") > 0) {
                //type = "WMTS";
            } else if (lc.indexOf("?service=wfs") > 0 || lc.indexOf("&service=wfs") > 0) {
                //type = "WFS";
            } else if (lc.indexOf("?service=wcs") > 0 || lc.indexOf("&service=wcs") > 0) {
            }
        } else if (lc.indexOf("/com.esri.wms.esrimap") !== -1) {
            type = "WMS";
        } else if (lc.indexOf("/mapserver/wmsserver") !== -1) {
            type = "WMS";
        } else if (lc.indexOf("/rest/services") > 0) {
            if (lc.indexOf("/mapserver") > 0) {
                type = "MapServer";
            } else if (lc.indexOf("/featureserver") > 0) {
                type = "FeatureServer";
            } else if (lc.indexOf("/imageserver") > 0) {
                if (endsWith(lc, "/imageserver")) type = "ImageServer";
            } else if (lc.indexOf("/streamserver") > 0) {
                type = "StreamServer";
            } else if (lc.indexOf("/vectortileserver") > 0 ||
                lc.indexOf("/resources/styles/root.json") > 0) {
                if (VectorTileLayer && VectorTileLayer.supported()) {
                    type = "VectorTileServer";
                }
            }
        }
        if (type === null) {
            if (endsWith(lc, ".kml") || endsWith(lc, ".kmz") || endsWith(lc, "kml.php") ||
                lc.indexOf("?f=kml") > 0 || lc.indexOf("&f=kml") > 0 ||
                lc.indexOf("?f=kmz") > 0 || lc.indexOf("&f=kmz") > 0) {
                type = "KML";
            } else if (endsWith(lc, ".csv") || lc.indexOf("f=kml") > 0) {
                type = "CSV";
            } else if (endsWith(lc, ".xml") &&
                (lc.indexOf("rss") > 0 || lc.indexOf("georss") > 0)) {
                type = "GeoRSS";
            } else if (endsWith(lc, ".zip")) {
                type = "Shapefile";
            } else if (endsWith(lc, ".json") || lc.indexOf("json") > 0) {   // Begin MarinePlanner edits
                type = "Vector";
            } else if (endsWith(lc, "wms") || endsWith(lc, "wms?") ||
                lc.indexOf("/wms/") > 0 || lc.indexOf('mapcache') > 0 ||
                lc.indexOf("wms?/") > 0 || endsWith(lc, "ows") ||
                endsWith(lc, "ows?")) {
                type = "WMS";
            } else if (endsWith(lc, ".png") || lc.indexOf("/tiles/") > 0 ||
                lc.indexOf("/tile/") > 0) {
                type = "XYZ";
            }
        }
    }
    if (type === "MapServer" || type === "ImageServer") {
        type = "ArcRest";
    }
    if (type === "FeatureServer") {
        type = "Vector";
    }
    if (type === "VectorTileServer") {
        type = "VectorTile";
    }

    return type
};
