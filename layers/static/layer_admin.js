document.addEventListener("DOMContentLoaded", function() {
    function updateFormDisplay() {
        const layerType = document.querySelector("#id_layer_type").value;
        console.log("Layer Type:", layerType); // Debugging output
        const isArcGIS = layerType === "ArcRest"; // Make sure this matches exactly
        console.log("Is ArcGIS:", isArcGIS); // Debugging output
        
        document.querySelectorAll(".form-row.field-arcgis_layers, .form-row.field-password_protected, .form-row.field-query_by_point, .form-row.field-disable_arcgis_attributes").forEach(function(row) {
            console.log("Row to update:", row); // Debugging output
            row.style.display = isArcGIS ? "block" : "none";
        });
    }
    const layerTypeField = document.querySelector("#id_layer_type");
    if (layerTypeField) {
        layerTypeField.addEventListener("change", updateFormDisplay);
        updateFormDisplay(); // Initial update on page load
    }
});