document.addEventListener('DOMContentLoaded', (event) => {
    const getGreenShade = (level) => {
    // Lighter shade for higher levels, darker for lower
    console.log(level)
    let hue_mod = parseInt(level/2)*20; 
    let light_mod = level%10; 
    return `hsl(${120+hue_mod}, 100%, ${25+light_mod*20}%)`;
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
            listItem.style.border = `2px solid ${getGreenShade(level)}`; 

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
                listItem.appendChild(radio);
            }
            sublist.appendChild(listItem);
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
        let noLayersElement = listItem.querySelector('.no-layers-msg');


            // Check if the next element is a sublist or a "No layers" message
        if (existingSublist && existingSublist.classList.contains('children-list')) {
            // If it exists, toggle its visibility
            existingSublist.style.display = existingSublist.style.display === 'none' ? 'block' : 'none';
            listItem.classList.toggle('expanded');
            listItem.style.backgroundColor = existingSublist.style.display === 'none' ? '' : getGreenShade(level);
        } else if (existingSublist && existingSublist.classList.contains('no-layers-msg')) {
            // If "No layers" message exists, remove it
            existingSublist.remove();
            listItem.classList.remove('expanded');
            listItem.style.backgroundColor = '';
        } else {
            // Fetch and handle children themes
            listItem.classList.add('expanded');
            listItem.style.backgroundColor = getGreenShade(level);
            fetchAndHandleChildren(listItem, themeId, level, chevron);
        }
        
    };
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
        noLayersMsg.style.border = `2px solid ${getGreenShade(level)}`;
        
        listItem.insertAdjacentElement('afterend', noLayersMsg);
    };
    // Attach click event to top level themes
    let topLevelThemes = document.querySelectorAll('.column-item.picker');
    topLevelThemes.forEach(theme => {
        theme.addEventListener('click', themeClickHandler);
    });
});