document.addEventListener("DOMContentLoaded", function() {
    function updateInlines() {
        const layerType = document.querySelector("#id_layer_type").value; // Adjust the selector as needed
        const inlines = document.querySelectorAll(".inline-group");
        
        inlines.forEach(function(inline) {
          inline.style.display = 'none';

          // If the inline ID matches the layerType or specific conditions for 'slider'
          if (inline.id.includes(layerType.toLowerCase()) || (layerType === 'slider' && 
              (inline.id.includes('multilayerdimension') || inline.id.includes('parent_layer')))) {
              inline.style.display = '';
          }
        });
    }
    const headers = document.querySelectorAll('.inline-related h3');
    headers.forEach(header => {
        header.remove()
        
    });

    const layerTypeField = document.querySelector("#id_layer_type");
    if (layerTypeField) {
        layerTypeField.addEventListener("change", updateInlines);
        updateInlines(); 
        assign_field_values_from_source_technology();
    }

    assign_field_values_from_source_technology = function() {
        if ($('#id_layer_type').val() == "ArcRest" || $('#id_layer_type').val() == "ArcFeatureServer") {
            var url = $('#id_url').val();
            var export_index = url.toLowerCase().indexOf('/export');
            if ( export_index >= 0) {
              url = url.substring(0, export_index);
            }
            if (url.toLowerCase().indexOf('/mapserver') >= 0 || url.toLowerCase().indexOf('/featureserver') >= 0) {
              $.ajax({
                url: url + "/layers?f=json",
                success: function(data) {
                  if (typeof data != "object") {
                    data = JSON.parse(data);
                  }
                  layers = [];
                  for (var i = 0; i < data.layers.length; i++) {
                    var layer = data.layers[i];
                    if (layer.minScale) {
                      var minZoom = (Math.log(591657550.500000 /(layer.minScale/2))/Math.log(2)).toPrecision(3);
                    } else {
                      var minZoom = undefined;
                    }
                    if (layer.maxScale) {
                      var maxZoom = (Math.log(591657550.500000 /(layer.maxScale/2))/Math.log(2)).toPrecision(3);
                    } else {
                      var maxZoom = undefined;
                    }
                    layers.push({
                      id:layer.id.toString(), 
                      name: layer.name,
                      minZoom: minZoom,
                      maxZoom: maxZoom,
                      minResolution: layer.minScale,
                      maxResolution: layer.maxScale
                    });
                  }
                  var layer_table_element = "<div class='argis-details-table-wrapper'><table class='arcgis-details-layer-table'><tr><th>ID</th><th>Name</th><th>Link</th></tr>";
                  for (var i = 0; i < layers.length; i++) {
                    layer = layers[i];
                    var row = "<tr><td>" + layer.id + "</td><td>" + layer.name + "</td><td><a href='" + url + "/" + layer.id + "' target='_blank'>Details</a></td></tr>";
                    layer_table_element = layer_table_element + row;
                  }
                  layer_table_element = layer_table_element + "</table></div>";
                  $('.arcgis-details-layer-table').remove();
                  $('div.field-box.field-arcgis_layers').append(layer_table_element);
      
                  var zoom_table_element = "<div class='argis-zoom-table-wrapper'><table class='arcgis-zoom-layer-table'><tr><th>ID</th><th>Name</th><th>Min Zoom</th><th>Max Zoom</th></tr>";
                  for (var i = 0; i < layers.length; i++) {
                    layer = layers[i];
                    var row = "<tr><td>" + layer.id + "</td><td>" + layer.name + "</td><td>" + layer.minZoom + "</td><td>" + layer.maxZoom + "</td></tr>";
                    zoom_table_element = zoom_table_element + row;
                  }
                  zoom_table_element = zoom_table_element + "</table></div>";
                  $('.arcgis-zoom-layer-table').remove();
                  $('div.field-box.field-minZoom').append(zoom_table_element);
      
      
                }
              })
            }
        }
      }
    assign_field_values_from_source_technology()
});