document.addEventListener('DOMContentLoaded', (event) => {
    const getGreenShade = (level) => {
    // Lighter shade for higher levels, darker for lower
    let mod_step = 9;
    let hue_mod = parseInt(level/mod_step)*10; 
    let light_mod = level%mod_step; 
    let base_light = 32;
    let light_step = (90-base_light) / (mod_step - 1);
    return `hsl(${156+hue_mod}, 100%, ${base_light+light_mod*light_step}%)`;
     // Adjust the percentage for the desired effect
    };
    const createColumn = (themes, parentListItem, level = 0) => {
        const sublist = document.createElement('ul');
        sublist.className = 'column-list children-list';
        sublist.style.display = 'block';  // Make sure it is visible
 
        themes.forEach(theme => {
            const listItem = document.createElement('li');
            listItem.className = 'children-item';
            listItem.textContent = theme.name;
            listItem.dataset.id = theme.id;
            listItem.style.border = `3px solid ${getGreenShade(level)}`; 
            sublist.appendChild(listItem);
            if (theme.type == "theme"){
                listItem.addEventListener('click', (event) => {

                    themeClickHandler(event, level + 1);
                });
                const chevron = document.createElement('i');
                chevron.className = 'fas fa-chevron-right';
                listItem.appendChild(chevron);
            } else {
                const radio = document.createElement('i');
                radio.className = "far fa-circle"
                const info = document.createElement('i');
                info.className = "fa fa-info-circle"
                // Create the link bar for this item and append it immediately after the list item
                const linkBar = createLinkBar(theme); // Pass the theme to the createLinkBar function
                listItem.parentNode.insertBefore(linkBar, listItem.nextSibling);
                info.addEventListener('click', function(event) {
                    event.stopPropagation(); // Prevent the event from bubbling up to parent elements
                    toggleLinkBar(listItem, info); // Pass the info icon and associated link to the function
                });
                listItem.addEventListener("click", function(event) {
                    event.stopPropagation(); // Prevent the event from bubbling up to parent elements
                    layerClickHandler(listItem); // Pass the info icon and associated link to the function
                })

                listItem.insertBefore(info, listItem.firstChild);
                listItem.appendChild(radio);
            }

        });

        parentListItem.insertAdjacentElement('afterend', sublist);
    };


    // Click event handler for themes
    const themeClickHandler = async (event, level = 0) => {
        event.stopPropagation();


        let listItem = event.target.closest('.column-item');
        if (!listItem) {
            listItem = event.target.closest('.children-item');
        }
        let themeId = listItem.dataset.id;

        // Toggle the 'expanded' class only on this list item, not the children
        // listItem.classList.toggle('expanded');
        let chevron = listItem.querySelector('.fas.fa-chevron-right');
        let existingSublist = listItem.nextElementSibling;

            // Check if the next element is a sublist or a "No layers" message
        if (existingSublist && existingSublist.classList.contains('children-list')) {
            // If it exists, toggle its visibility
            existingSublist.style.display = existingSublist.style.display === 'none' ? 'block' : 'none';
            listItem.classList.toggle('expanded');
            listItem.style.backgroundColor = existingSublist.style.display === 'none' ? '' : getGreenShade(level);
            listItem.style.textShadow = "2px 0px 10px white";
        } else if (existingSublist && existingSublist.classList.contains('no-layers-msg')) {
            // If "No layers" message exists, remove it
            existingSublist.remove();
            listItem.classList.remove('expanded');
            listItem.style.backgroundColor = '';
            listItem.style.textShadow = "";
        } else {
            // Fetch and handle children themes
            listItem.classList.add('expanded');
            listItem.style.backgroundColor = getGreenShade(level);
            listItem.style.textShadow = "2px 0px 10px white";
            fetchAndHandleChildren(listItem, themeId, level, chevron);
        }
        
    };

    const layerClickHandler = async (listItem) => {
        // Find the closest children-item and circle icon
        let circle = listItem.querySelector(".fa-circle, .fa-check-circle");

        // Toggle classes
        if (circle) {
            if (circle.classList.contains('fa-circle')) {
                circle.classList.remove('fa-circle');
                circle.classList.add('fa-check-circle');
            } else {
                circle.classList.remove('fa-check-circle');
                circle.classList.add('fa-circle');
            }
        }

    }
    const fetchAndHandleChildren = async (listItem, themeId, level, chevron) => {
        try {
            let response = await fetch(`/layers/children/${themeId}`);
            let childrenThemes = await response.json();
            if (childrenThemes.length > 0) {
                createColumn(childrenThemes, listItem, level);
            } else {
                displayNoLayersMessage(listItem, level);
            }
        } catch (error) {
            console.error('Error fetching children themes:', error);
            listItem.classList.remove('expanded');
            listItem.style.backgroundColor = '';
        }
    };
    const displayNoLayersMessage = (listItem, level) => {
        const noLayersMsg = document.createElement('div');
        noLayersMsg.className = 'no-layers-msg';
        noLayersMsg.textContent = "No layers"; 
        noLayersMsg.style.padding = "10px"
        noLayersMsg.style.border = `3px solid ${getGreenShade(level)}`;
        noLayersMsg.style.marginBottom = "1px"
        
        listItem.insertAdjacentElement('afterend', noLayersMsg);
    };
    const createLinkBar = (theme) => {
        const linkBar = document.createElement('div');
        linkBar.className = 'link-bar';
        linkBar.style.display = 'none'; // Initially hidden
        linkBar.style.background = '#f8f8f8'; // Assume a light gray background
        linkBar.style.padding = '10px';
        linkBar.style.textAlign = "center"
        const linkSectionStyle = 'display: inline-block; margin-right: 30px; cursor: pointer; font-size: 13px';
        // Create the content of the link bar
        const linkBarKML = document.createElement('span');
        linkBarKML.className = 'link-bar-content tooltip';
        const tooltipTextKML = document.createElement('span');
        tooltipTextKML.className = 'tooltiptext';
        tooltipTextKML.textContent = "Download for Google Maps"; // Set the tooltip text
        linkBarKML.appendChild(tooltipTextKML); 
        const linkBarKMLbutton = document.createElement("a");
        linkBarKMLbutton.textContent = "kml ";
        linkBarKMLbutton.style = linkSectionStyle;
        // Create the <i> element for the Font Awesome icon
        const arrowIcon1 = document.createElement("i");
        arrowIcon1.className = "fa fa-arrow-down";
        // Append the icon to the link
        linkBarKMLbutton.appendChild(arrowIcon1);

        const linkBarData = document.createElement("span");
        linkBarData.className = "link-bar-content tooltip";
        const tooltipTextData = document.createElement('span');
        tooltipTextData.className = 'tooltiptext';
        tooltipTextData.textContent = "Download ESRI Formatted Dataset"; // Set the tooltip text
        linkBarData.appendChild(tooltipTextData); 
        const linkBarDatabutton = document.createElement("a");
        linkBarDatabutton.textContent = "data"
        linkBarDatabutton.style = linkSectionStyle;
        const arrowIcon2 = document.createElement("i");
        arrowIcon2.className = "fa fa-arrow-down";
        linkBarDatabutton.appendChild(arrowIcon2)

        const linkBarMeta = document.createElement("span");
        linkBarMeta.className = "link-bar-content tooltip";
        const tooltipTextMeta = document.createElement('span');
        tooltipTextMeta.className = 'tooltiptext';
        tooltipTextMeta.textContent = "View Metadata"; // Set the tooltip text
        linkBarMeta.appendChild(tooltipTextMeta); 
        const linkBarMetabutton = document.createElement("a");
        linkBarMetabutton.textContent = "metadata";
        linkBarMetabutton.style = linkSectionStyle;

        const linkBarSource = document.createElement("span");
        linkBarSource.className = "link-bar-content tooltip";
        const tooltipTextSource = document.createElement('span');
        tooltipTextSource.className = 'tooltiptext';
        tooltipTextSource.textContent = "Link to Dataset Source Provider"; // Set the tooltip text
        linkBarSource.appendChild(tooltipTextSource); 
        const linkBarSourcebutton = document.createElement("a");
        linkBarSourcebutton.textContent = "source";
        linkBarSourcebutton.style = linkSectionStyle;

        linkBarKML.append(linkBarKMLbutton)
        linkBarData.append(linkBarDatabutton)
        linkBarMeta.append(linkBarMetabutton)
        linkBarSource.append(linkBarSourcebutton)

        linkBar.appendChild(linkBarKML);
        linkBar.appendChild(linkBarData);
        linkBar.appendChild(linkBarMeta);
        linkBar.appendChild(linkBarSource);
        return linkBar;
    };
    function toggleLinkBar(listItem, icon) {
        const linkBar = listItem.nextElementSibling; // This should be the link bar created above
        if(linkBar && linkBar.classList.contains('link-bar')) {
            const isDisplayed = linkBar.style.display !== 'none';
            linkBar.style.display = isDisplayed ? "none" : "block";
            icon.style.color = isDisplayed ? "#00a564" : "black";
        } else {
            console.error('Link bar not found for icon', icon);
        }
    }
    // Attach click event to top level themes
    let topLevelThemes = document.querySelectorAll('.column-item.picker');
    topLevelThemes.forEach(theme => {
        theme.addEventListener('click', themeClickHandler);
    });
});