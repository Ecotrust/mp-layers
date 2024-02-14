document.addEventListener("DOMContentLoaded", function() {
    function updateInlines() {
        const layerType = document.querySelector("#id_layer_type").value; // Adjust the selector as needed
        const inlines = document.querySelectorAll(".inline-group");
        
        inlines.forEach(function(inline) {
            if (inline.id.includes(layerType.toLowerCase())) { // Assuming inline IDs contain the lowercase `layer_type`
                inline.style.display = '';
            } else {
                inline.style.display = 'none';
            }
        });
    }

    const layerTypeField = document.querySelector("#id_layer_type");
    if (layerTypeField) {
        layerTypeField.addEventListener("change", updateInlines);
        updateInlines(); 
    }
});