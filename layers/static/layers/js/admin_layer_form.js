show_layertype_form = function(layertype) {

  if (layertype == null) {
    layertype = $('#id_layer_type').val();
  }

  var url = $('#id_url').val();

  if (url.length > 0) {

    if ($('#id_layer_type').val() == "WMS" && $('#id_layerwms_set-0-wms_help').is(':checked')) {
      get_wms_capabilities();
    }

    var organization_section = $('.field-order.field-themes').parent();
    var metadata_section = $('.field-description').parent();
    var legend_section = $('.field-show_legend').parent();
    var arcgis_section = $('.field-arcgis_layers').parent();
    var wms_section = $('.field-wms_help').parent();
    var attribute_section = $('.field-attribute_fields').parent();
    var style_section = $('.field-opacity').parent();
    var multi_association_section = $('#id_parent_layer-TOTAL_FORMS').parent();
    var multi_dimensions_section = $('#id_multilayerdimension_set-TOTAL_FORMS').parent();

    switch(layertype) {
      case '---------':
        hide_section(arcgis_section);
        hide_section(wms_section);
        hide_section(style_section);
        break;
      case 'WMS':
        hide_section(arcgis_section);
        show_section(wms_section);
        hide_section(style_section);
        break;
      case 'ArcRest':
        show_section(arcgis_section);
        hide_section(wms_section);
        hide_section(style_section);
        break;
      case 'ArcFeatureServer':
        show_section(arcgis_section);
        hide_section(wms_section);
        hide_section(style_section);
        break;
      case 'Vector':
        hide_section(arcgis_section);
        hide_section(wms_section);
        show_section(style_section);
        break;
      case 'VectorTile':
        hide_section(arcgis_section);
        hide_section(wms_section);
        show_section(style_section);
        break;
      default:
        hide_section(arcgis_section);
        hide_section(wms_section);
        hide_section(style_section);
        break;
    }
  }
}

show_section = function(section) {
  section.removeClass('collapsed');
  section.children('h2').children('a').text('Hide');
}

hide_section = function(section) {
  section.addClass('collapsed');
  section.children('h2').children('a').text('Show');
}

get_wms_capabilities = function() {
  if ($('#id_layer_type').val() == "WMS" && $('#id_url').length > 0 && $('#id_layerwms_set-0-wms_help').prop('checked') == true) {
    show_spinner();
    var url = $('#id_url').val();
    $.ajax({
        url: '/layers/wms_capabilities/',
        data: {
          url: url
        },
        success: function(data) {
          // SWITCH WMS INPUTS TO SELECTORS
          var blank_option = '<option value="">_________</option>';

          // Replace WMS Layer Name
          let layer_name_value = '';
          let layer_name_title = '';
          let layer_option_html = ''
          var slug_val = $('#id_layerwms_set-0-wms_slug').val();
          var layer_name_html = '<select id="id_layerwms_set-0-wms_slug" name="layerwms_set-0-wms_slug">';
          layer_name_html += blank_option;
          for (var i = 0; i < data.layers.length; i++) {
            var opt_val = data.layers[i];
            if (typeof(opt_val) == "object"){
              if (opt_val.hasOwnProperty('key') && opt_val.hasOwnProperty('title')) {
                layer_name_value = opt_val['key'];
                layer_name_title = opt_val['title'];
              } else {
                layer_name_value = opt_val['key'];
                layer_name_title = opt_val['key'];
              }
            // } else if (typeof(opt_val) == "string") {
            } else {
              layer_name_value = opt_val;
              layer_name_title = opt_val;
            }
            layer_option_html = '<option value="' + layer_name_value + '"';
            if (slug_val === layer_name_value) {
              layer_option_html += ' selected';
            }
            layer_option_html += '>' + layer_name_title + '</option>';
            layer_name_html += layer_option_html;
          }
          layer_name_html += '</select>';
          $('#id_layerwms_set-0-wms_slug').replaceWith( layer_name_html);
          if (data.layers.indexOf(slug_val) >= 0) {
            $('#id_layerwms_set-0-wms_slug').val(slug_val);
          }
          slug_val =   $('#id_layerwms_set-0-wms_slug').val();
          $('#id_layerwms_set-0-wms_slug').change(function() {
            get_wms_capabilities();
          });

          // Set wms version (only 1.1.1 supported)
          $('#id_layerwms_set-0-wms_version').val(data.version);
          $('.field-wms_version.field-box').hide()

          // Replace WMS Format
          var format_val = $('#id_layerwms_set-0-wms_format').val();
          var format_html = '<select id="id_layerwms_set-0-wms_format" name="layerwms_set-0-wms_format">';
          format_html += blank_option;
          for (var i = 0; i < data.formats.length; i++) {
            opt_val = data.formats[i];
            format_html += '<option value="' + opt_val + '">' + opt_val + '</option>';
          }
          format_html += '</select>';
          $('#id_layerwms_set-0-wms_format').replaceWith(format_html);
          if (data.formats.indexOf(format_val) >= 0) {
            $('#id_layerwms_set-0-wms_format').val(format_val);
          }

          // Replace SRS
          var srs_val = $('#id_layerwms_set-0-wms_srs').val();
          var srs_html = '<select id="id_layerwms_set-0-wms_srs" name="layerwms_set-0-wms_srs">';
          srs_html += blank_option;

          if (slug_val.length > 0) {
            for (var i = 0; i < data.srs[slug_val].length; i++) {
              opt_val = data.srs[slug_val][i];
              srs_html += '<option value="' + opt_val + '">' + opt_val + '</option>';
            }

          }
          srs_html += '</select>';
          $('#id_layerwms_set-0-wms_srs').replaceWith(srs_html);
          if (slug_val.length > 0 && data.srs[slug_val].indexOf(srs_val) >= 0) {
            $('#id_layerwms_set-0-wms_srs').val(srs_val);
          }

          $('#id_layerwms_set-0-wms_srs').change(function() {
            if ($('#id_layerwms_set-0-wms_srs').val().toLowerCase() == 'epsg:3857') {
              $('#id_layerwms_set-0-wms_time_item').prop('disabled', true);
              $('#id_layerwms_set-0-wms_additional').prop('disabled', false);
            } else {
              $('#id_layerwms_set-0-wms_time_item').prop('disabled', false);
              $('#id_layerwms_set-0-wms_additional').prop('disabled', true);
            }
          });

          // Replace Styles
          var style_keys = [];
          if (slug_val.length > 0){
            style_keys = Object.keys(data.styles[slug_val]);
          }
          if (style_keys.length == 0) {
            $('#id_layerwms_set-0-wms_styles').val(null);
            $('#id_layerwms_set-0-wms_styles').prop('disabled', true);
          } else {
            $('#id_layerwms_set-0-wms_styles').prop('disabled', false);
            var style_val = $('#id_layerwms_set-0-wms_styles').val();
            var style_html = '<select id="id_layerwms_set-0-wms_styles" name="layerwms_set-0-wms_srs">';
            style_html += '<option value="">Default</option>';
            for (var i = 0; i < style_keys.length; i++) {
              opt_val = style_keys[i];
              style_html += '<option value="' + opt_val + '">' + opt_val + '</option>';
              // TODO: Test if this works with a WMS server with styles.
            }
            style_html += '</select>';
            $('#id_layerwms_set-0-wms_styles').replaceWith(style_html);
            if (slug_val.length > 0 && Object.keys(data.styles[slug_val]).indexOf(style_val) >= 0) {
              $('#id_layerwms_set-0-wms_styles').val(style_val);
            }
          }

          // Replace Time
          $('#wms_timing_default').remove();
          $('#wms_timing_position_label').remove();
          $('#wms_timing_position_options').remove();

          if (slug_val.length <= 0 || data.time[slug_val].default == null) {
            $('#id_layerwms_set-0-wms_timing').val(null);
            $('#id_layerwms_set-0-wms_timing').prop('disabled', true);
          } else {
            $('#id_layerwms_set-0-wms_timing').prop('disabled', false);
            $('<p id="wms_timing_default"><b>*** Default = ' + data.time[slug_val].default + '***</b></p>').insertAfter('#id_layerwms_set-0-wms_timing');
            if (data.time[slug_val].positions.length > 0) {
              $('<p id="wms_timing_position_label">Position options:</p>').insertAfter('#wms_timing_default');
              var wms_timing_positions_html = '<ul id="wms_timing_position_options">';
              for (var i = 0; i < data.time[slug_val].positions.length; i++) {
                wms_timing_positions_html += '<li>' + data.time[slug_val].positions[i] + '</li>';
              }
              wms_timing_positions_html += '</ul>';
              $(wms_timing_positions_html).insertAfter('#wms_timing_position_label');
            }
          }

          /* CAPABILITIES */
          if (Object.keys(data.capabilities).length > 0) {
            var info_bool_field = $('#id_layerwms_set-0-wms_info');
            var info_format_field = $('#id_layerwms_set-0-wms_info_format');
            if (data.capabilities.hasOwnProperty('featureInfo') && data.capabilities.featureInfo.available) {
              $('.form-row.field-wms_info.field-wms_info_format').show();
              info_format_field.prop('disabled', false);
              info_bool_field.prop('disabled', false);

              var info_formats = data.capabilities.featureInfo.formats;
              var info_format_val = info_format_field.val();
              var info_format_html = '<select id="id_layerwms_set-0-wms_info_format" name="layerwms_set-0-wms_info_format">';
              info_format_html += '<option value="">None (no reporting)</option>';
              for (var i = 0; i < info_formats.length; i++) {
                var opt_val = info_formats[i];
                info_format_html += '<option value="' + opt_val + '">' + opt_val + '</option>';
              }
              info_format_html += '</select>';
              info_format_field.replaceWith(info_format_html);

              if (info_formats.indexOf(info_format_val) >= 0) {
                  $('#id_layerwms_set-0-wms_info_format').val(info_format_val);
              }

            } else {
              // set featureInfo to false, hide section
              info_bool_field.prop('checked', false);
              info_bool_field.prop('disabled', true);
              info_format_field.val(null);
              info_format_field.prop('disabled', true);
              $('.form-row.field-wms_info.field-wms_info_format').hide();
            }
          }
          check_queryable(data.queryable);
          hide_spinner();
        },
        error: function(data) {
          var url = $('#id_url').val();
          err_msg = 'ERROR: Layer url ' + url + ' does not appear to be a valid WMS endpoint.'
          hide_spinner();
          window.alert(err_msg);
        }
    });
  } else {
    // SWITCH SELECTORS TO INPUTS

    // Replace WMS Layer Name
    if ($('#id_layerwms_set-0-wms_slug').is('select')) {
      var slug_val = $('#id_layerwms_set-0-wms_slug').val();
      $('#id_layerwms_set-0-wms_slug').replaceWith('<input id="id_layerwms_set-0-wms_slug" name="layerwms_set-0-wms_slug" class="vTestField" maxlength="255" type="text" value="' + slug_val + '">' +
        '</input>');
    }

    // Release lock on WMS version field
    $('.field-wms_version.field-box').show();

    // Replace WMS format
    if ($('#id_layerwms_set-0-wms_format').is('select')) {
      format_val = $('#id_layerwms_set-0-wms_format').val();
      $('#id_layerwms_set-0-wms_format').replaceWith('<input class="vTextField" id="id_layerwms_set-0-wms_format" maxlength="100" name="layerwms_set-0-wms_format" type="text" value="' + format_val + '">' +
        '</input>');
    }

    // Replace SRS
    if ($('#id_layerwms_set-0-wms_srs').is('select')) {
      srs_val = $('#id_layerwms_set-0-wms_srs').val();
      $('#id_layerwms_set-0-wms_srs').replaceWith('<input class="vTextField" id="id_layerwms_set-0-wms_srs" maxlength="100" name="layerwms_set-0-wms_srs" type="text" value="' + srs_val +'">' +
          '</input>');
    }

    $('#id_layerwms_set-0-wms_srs').blur(function() {
      if ($('#id_layerwms_set-0-wms_srs').val() == 'EPSG:3857') {
        $('#id_layerwms_set-0-wms_time_item').prop('disabled', true);
        $('#id_layerwms_set-0-wms_additional').prop('disabled', false);
      } else {
        $('#id_layerwms_set-0-wms_time_item').prop('disabled', false);
        $('#id_layerwms_set-0-wms_additional').prop('disabled', true);
      }
    });

    // Replace Styles
    if ($('#id_layerwms_set-0-wms_styles').is('select')) {
      style_val = $('#id_layerwms_set-0-wms_styles').val();
      $('#id_layerwms_set-0-wms_styles').replaceWith('<input class="vTextField" id="id_layerwms_set-0-wms_styles" maxlength="255" name="layerwms_set-0-wms_styles" type="text" value="' + style_val + '">' +
          '</input>');
    }

    // Replace Time
    $('#id_layerwms_set-0-wms_timing').prop('disabled', false);
    $('#wms_timing_default').remove();
    $('#wms_timing_position_label').remove();
    $('#wms_timing_position_options').remove();

  }
}

check_queryable = function(queryable_layers) {
  var selected_layer = $('#id_layerwms_set-0-wms_slug').val();
  if (queryable_layers.indexOf(selected_layer) >= 0) {
    $('#id_layerwms_set-0-wms_info').attr('disabled', false);
    $('#id_layerwms_set-0-wms_info_format').attr('disabled', false);
  } else {
    $('#id_layerwms_set-0-wms_info').attr('checked', false);
    $('#id_layerwms_set-0-wms_info').attr('disabled', true);
    $('#id_layerwms_set-0-wms_info_format').attr('disabled', true);
  }
  if (!$('#queryable_layer_list').length > 0) {
    if ($('.form-row.field-wms_info.field-wms_info_format').length > 0) {
      $('.form-row.field-wms_info.field-wms_info_format').append('<div id="queryable_layer_list"></div>');
    } else {
      console.log('need to re-write identification of WMS Info section of form. See layer_form.js "check_queryable()"');
    }
  }
  if ($('#queryable_layer_list').length > 0) {
    q_layers_html = "<b>Queryable Layers: </b>" + queryable_layers.join(', ');
    $('#queryable_layer_list').html(q_layers_html);
  }
}

var change_layer_url = function(self) {
  var url = $(this).val();
  var type = null;
  if (typeof(get_service_type) == "function") {
    type = get_service_type(url);
    if ($('#id_layer_type option').map(function() { return $(this).val(); }).toArray().indexOf(type) >= 0) {
      $('#id_layer_type').val(type);
      $('#id_layer_type').trigger('change');
    }
  } else {
    console.log('No get_service_type() function defined for CATALOG_TECHNOLOGY: ' + CATALOG_TECHNOLOGY);
  }
}

var replace_all_select2_with_input = function() {
  var sel2_fields = $('.select2').siblings('select.select2-hidden-accessible').not('#id_catalog_name');
  for (var i = 0; i < sel2_fields.length; i++) {
    var field_id = $(sel2_fields[i]).attr('id');
    var field_name = $(sel2_fields[i]).attr('name');
    var field_value = $(sel2_fields[i]).val();
    var textarea_fields = ['id_description'];
    if (textarea_fields.indexOf(field_id) >= 0) {
      var field_open = '<textarea cols="40" rows="10" class="vLargeTextField" ';
      var field_close = '</textarea>';
    } else {
        var field_open = '<input type="text" class="vTextField" maxlength="255" '
        var field_close = '</input>';
    }
    var input_field = field_open + 'id="' + field_id + '" name="layerwms_set-0-' + field_name + '" value="' + field_value + '">' + field_close;
    $(sel2_fields[i]).replaceWith(input_field);
    $('#' + field_id).val(field_value);
    $('#' + field_id).siblings('.select2').remove();
    // $('#' + field_id).width("80%");
  }

}

var replace_input_with_select2 = function(id, options) {
  var input_field = $('#'+ id);
  var initial_width = input_field.parent().width();
  if (initial_width == 0) {
    initial_width = input_field.parent().parent().parent().width() * 0.97;
  }

  var original_value = input_field.val();
  var original_name = input_field.attr('name');
  if (!input_field.hasClass("select2-hidden-accessible")) {
    var select2_field_str = '<select id="' + id + '" type=text" selected="' + original_value + '" name="layerwms_set-0-' + original_name + '"></select>';
    input_field.replaceWith(select2_field_str);
    var select2_field = $('#'+ id);
  } else {
    input_field.html('').select2({data: []}).trigger('change');
    select2_field = input_field;
  }

  if (id != "id_catalog_name") {
    options = union(['', original_value], options);
  }

  for (var i = 0; i < options.length; i++) {
    var option = options[i];
    if (typeof(option) == "string"){
      select2_field.append('<option value="' + option + '">' + option + '</option>');
    } else if (typeof(option) == 'undefined'){
      select2_field.append('<option value=null>None</option>');
    } else if (option.hasOwnProperty('value') && option.hasOwnProperty('name')){
      select2_field.append('<option value="' + option.value + '">' + option.name + '</option>');
    }
  }
  select2_field.val(original_value);
  if (select2_field.val() == null && options.length == 1) {
    if (typeof(options[0]) == "string") {
      select2_field.val(options[0]);
      select2_field.trigger('change');
    } else if (typeof(options[0]) == "object" && Object.keys(options[0]).indexOf('value') != -1) {
      select2_field.val(options[0].value);
      select2_field.trigger('change');
    }
  }
  if (id != 'id_catalog_name') {
    select2_field.select2({
      tags: true
    });
    if (id == "id_url") {
      select2_field.change(change_layer_url);
    }
  } else {
    select2_field.select2();
    select2_field.change(select_catalog_record);
    select2_field.trigger('change');
  }

  select2_field.siblings('.select2').width(initial_width);

}

var get_catalog_records = function() {
  var url = "/data_manager/get_catalog_records";
  $.ajax({
    url: url,
    success: function(data) {
      catalog_record_data = data;
      var record_names = Object.keys(data.record_name_lookup);
      options = [{'name': '', 'value': null}];
      for (var i = 0; i < record_names.length; i++) {
        for (var j = 0; j < data.record_name_lookup[record_names[i]].length; j++){
          options.push({
            'name': record_names[i],
            'value': data.record_name_lookup[record_names[i]][j]
          });
        }
      }

      replace_input_with_select2('id_catalog_name', options);
    }
  });
}

var show_spinner = function() {
  $('#spinner-dialog').dialog('open');
}

var hide_spinner = function() {
  $('#spinner-dialog').dialog('close');
}

var select_catalog_record = function(event, ui) {
  show_spinner();
  if ($( this ).select2('data').length > 0) {
    var selected_name = $( this ).select2('data')[0].text;
  } else {
    var selected_name = '';
  }
  var record_id = $( this ).val();
  if (record_id) {
    populate_layer_fields_from_catalog_record(catalog_record_data, record_id, selected_name);
  } else {
    hide_spinner();
  }
}

var populate_layer_fields_from_catalog_record = function(catalog_record_data, record_id, selected_name) {
  selected_catalog_data = catalog_record_data.records[record_id];
  $('#id_catalog_id').val(record_id);
  if ($('#id_name').val() == "") {
    $('#id_name').val(selected_name);
  }

  if (typeof populate_fields_from_catalog != "undefined" && typeof populate_fields_from_catalog === "function") {
    populate_fields_from_catalog(catalog_record_data, record_id);
  }
  // if (window.confirm("Do you want to set all form fields from the selected catalog record?")) {
    if (CATALOG_TECHNOLOGY == 'GeoPortal2') {

    } else {
      hide_spinner();
    }
  // } else {
  //   hide_spinner();
  // }

}

var union = function(array1, array2) {
  var hash = {}, union_arr = [];
  $.each($.merge($.merge([], array1), array2), function (index, value) { hash[value] = value; });
  $.each(hash, function (key, value) { union_arr.push(key); } );
  return union_arr;
}

enforce_organization_show = function() {
  var organization_section = $('.field-order.field-themes').parent();
  var metadata_section = $('.field-description').parent();

  // This gets called before 'compressed' is applied to all sections by django admin's 'compress.js'
  //    So we need to wait a bit.
  setTimeout(function() {
    if (metadata_section.hasClass('collapsed')) {
      organization_section.addClass('collapse')
      organization_section.children('h2').html(organization_section.children('h2').html() + ' ( <a id="fieldsetcollapser_organization" class="collapse-toggle" href="#">Hide</a> )');
      show_layertype_form(null);
      $('fieldset.collapse').addClass('late-transition');

    } else {
      enforce_organization_show();
    }
  }, 200);
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


$(document).ready(function() {

  $('#spinner-dialog').dialog({autoOpen:false, modal: true, width: 150});

  enforce_organization_show();

  show_layertype_form($('#id_layer_type option:selected').text());

  console.log("CATALOG_TECHNOLOGY: '" + CATALOG_TECHNOLOGY + "'");

  // If catalog tech supported:
  if (CATALOG_TECHNOLOGY != 'default') {
    $('#id_catalog_id').height(15);
    $('#id_catalog_id').prop('disabled', true);
    $('#id_catalog_name').height(15);
    // TODO: Query for catalog records
    get_catalog_records();
    // - populate typeahead field with available catalog records

    // $('#id_catalog_id').autocomplete({
    //   source: [
    //     "Adam", "Becky", "Charlie", "Danielle"
    //   ]
    // });

    // - Filter records based on:
    //    - record has layer info
    //    - record not already in use
  } else {
    $('#id_catalog_id').hide();
  }



  $('#id_layer_type').change(function() {
    show_layertype_form($('#id_layer_type option:selected').text());
    if (assign_field_values_from_source_technology && typeof assign_field_values_from_source_technology === "function") {
      assign_field_values_from_source_technology();
    }
  });

  $('#id_url').blur(function() {
    get_wms_capabilities();
  });

  $('#id_layerwms_set-0-wms_help').change(function() {
    get_wms_capabilities();
  });

  assign_field_values_from_source_technology();

});
