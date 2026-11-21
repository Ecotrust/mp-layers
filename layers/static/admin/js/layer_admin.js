document.addEventListener("DOMContentLoaded", function() {
    function updateInlines() {
        const layerType = document.querySelector("#id_layer_type").value; // Adjust the selector as needed
        const nested_inlines = document.querySelectorAll(".djn-group-root");
        
        nested_inlines.forEach(function(inline) {
          if (inline.dataset.inlineModel === 'layers-layer_attribute_fields') {
              return;
          }

          inline.style.display = 'none';

          // If the inline ID matches the layerType or specific conditions for 'slider'
          if (inline.id.includes(layerType.toLowerCase()) || (layerType === 'slider' && 
              (inline.id.includes('multilayerdimension') || inline.id.includes('parent_layer')))) {
              inline.style.display = '';
          }
          else if (inline.id.includes("arcfeatureservice") && layerType === "ArcFeatureServer") {
              inline.style.display = "";
          }
        });
    }
    const headers = document.querySelectorAll('.inline-related h3');
    headers.forEach(header => {
        header.remove()
        
    });

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

                  build_arcgis_fields_table(data.layers);
                }
              })
            }
        }
      }

    // Also duplicated in admin_layer_form.js
    // Function written by Copilot
    const escape_html = function(value) {
      if (value === undefined || value === null) {
        return '';
      }
      return $('<div>').text(String(value)).html();
    }

    // Function written by Copilot
    const build_arcgis_fields_table = function(arcgis_layers) {
      var selected_ids = [];
      $('input[name$="arcgis_layers"]').each(function() {
        $.each(($(this).val() || '').split(','), function(index, id) {
          id = id.trim();
          if (id.length > 0 && selected_ids.indexOf(id) < 0) {
            selected_ids.push(id);
          }
        });
      });
      var report_layers = $.grep(arcgis_layers || [], function(layer) {
        return selected_ids.length == 0 || selected_ids.indexOf(layer.id.toString()) >= 0;
      });

      var fields_table_element = "<div class='arcgis-fields-table-wrapper'><table class='arcgis-fields-layer-table'><tr><th>Layer ID</th><th>Name</th><th>Type</th><th>Alias</th></tr>";
      for (var i = 0; i < report_layers.length; i++) {
        var layer = report_layers[i];
        var fields = layer.fields || [];
        if (fields.length == 0) {
          fields_table_element += "<tr><td>" + escape_html(layer.id) + "</td><td colspan='3'><em>No fields available</em></td></tr>";
        }
        for (var j = 0; j < fields.length; j++) {
          var field = fields[j];
          fields_table_element += "<tr><td>" + escape_html(layer.id) + "</td><td>" + escape_html(field.name) + "</td><td>" + escape_html(field.type) + "</td><td>" + escape_html(field.alias) + "</td></tr>";
        }
      }
      fields_table_element += "</table></div>";
      $('.arcgis-fields-table-wrapper').remove();
      $('fieldset.feature-reporting').append(fields_table_element);
    }

    const layerTypeField = document.querySelector("#id_layer_type");
    if (layerTypeField) {
        layerTypeField.addEventListener("change", updateInlines);
        updateInlines(); 
        assign_field_values_from_source_technology();
    }
});