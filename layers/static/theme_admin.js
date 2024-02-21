document.addEventListener("DOMContentLoaded", function() {
    // Existing code for layer types and ArcGIS details...
    var themeTypeSelectBox = document.getElementById('id_theme_type');
    var themesSelectorDiv = document.querySelector('.field-themes');

    // Move the themes selector to be right after the theme type select box.
    if (themeTypeSelectBox && themesSelectorDiv) {
        themeTypeSelectBox.closest('.form-row').insertAdjacentElement('afterend', themesSelectorDiv);
    }
    function updateThemesVisibility() {
        // Get the selected value of the theme_type dropdown
        var themeTypeValue = document.querySelector('#id_theme_type').value;

        // Select the div that contains the themes selector
        var themeSelectorDiv = document.querySelector('.form-row.field-themes');

        // If the selected value is 'radio' or 'checkbox', show the themes selector, otherwise hide it
        if (themeTypeValue === 'radio' || themeTypeValue === 'checkbox') {
            themeSelectorDiv.style.display = ''; // Show the theme selector
        } else {
            themeSelectorDiv.style.display = 'none'; // Hide the theme selector
        }
    }
    
    // Run once on load in case of pre-selected value
    updateThemesVisibility();
    
    document.querySelector('#id_theme_type').addEventListener('change', updateThemesVisibility);
});