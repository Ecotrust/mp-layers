document.addEventListener("DOMContentLoaded", function() {
    // Existing code for layer types and ArcGIS details...
    var themeTypeSelectBox = document.getElementById('id_theme_type');
    var themesSelectorDiv = document.querySelector('.field-themes');
    var themesSelectorDiv = document.querySelector('.form-row.field-children_themes');
    var layersSelectorDiv = document.querySelector('.form-row.field-children_layers');

    // Base URL for the Django admin
    var adminBaseUrl = window.location.origin + '/django-admin/';

    // Function to add the new theme to the chosen list
    window.addNewTheme = function(themeId, themeName) {
        // Find the select box on the right side (Chosen children themes)
        console.log("Attempting to add new theme:", themeId, themeName);

        var selectBox = document.getElementById('id_children_themes_to');  // Adjust the ID as necessary

        if (selectBox) {
            console.log("Select box found:", selectBox);

            // Create a new option element
            var newOption = new Option(themeName, themeId, true, true);

            // Add the new option to the select box
            selectBox.add(newOption);

            // Trigger any change event listeners
            selectBox.dispatchEvent(new Event('change'));
        } else {
            console.error("Select box not found or incorrect ID.");
        }
    };

    // Function to add the plus button next to the field
    function addPlusButton(selectorDiv, addUrl) {
        var plusButton = document.createElement('a');
        plusButton.href = "javascript:void(0);";
        plusButton.className = "add-related";
        plusButton.innerHTML = '<img src="/static/admin/img/icon-addlink.svg" width="10" height="10" alt="Add Another"/>';

        plusButton.addEventListener('click', function(e) {
            e.preventDefault();
            openPopup(addUrl);
        });

        // Insert the button right after the field
        selectorDiv.appendChild(plusButton);
    }

    // Function to open the popup window
    function openPopup(url) {
        var popup = window.open(url, 'popup_form', 'height=600,width=800');
        popup.onbeforeunload = function () {
            window.location.reload();
        };
    }

    // Add the plus button for the children_themes field
    if (themesSelectorDiv) {
        var addThemeUrl = adminBaseUrl + 'layers/theme/add/';  
        addPlusButton(themesSelectorDiv, addThemeUrl);
    }

    // Add the plus button for the children_layers field
    if (layersSelectorDiv) {
        var addLayerUrl = adminBaseUrl + 'layers/layer/add/';  
        addPlusButton(layersSelectorDiv, addLayerUrl);
    }



    // function updateThemesVisibility() {
    //     // Get the selected value of the theme_type dropdown
    //     var themeTypeValue = document.querySelector('#id_theme_type').value;

    //     // Select the div that contains the themes selector
    //     var themeSelectorDiv = document.querySelector('.form-row.field-themes');

    //     // If the selected value is 'radio' or 'checkbox', show the themes selector, otherwise hide it
    //     // if (themeTypeValue === 'radio' || themeTypeValue === 'checkbox') {
    //     //     themeSelectorDiv.style.display = ''; // Show the theme selector
    //     // } else {
    //     //     themeSelectorDiv.style.display = 'none'; // Hide the theme selector
    //     // }
    // }
    
    // // Run once on load in case of pre-selected value
    // updateThemesVisibility();
    
    document.querySelector('#id_theme_type').addEventListener('change', updateThemesVisibility);
});