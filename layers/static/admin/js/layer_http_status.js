/**
 * This script is used to display the HTTP status of a layer in the admin interface.
 * It fetches the status from a given URL and updates the status element accordingly.
 * It also provides a refresh button to manually update the status.
 * It runs only on the LayerAdmin page.
 */
document.addEventListener('DOMContentLoaded', () => {
    const statusElements = document.querySelectorAll('.http-status');
    statusElements.forEach(el => {
        if (!el.dataset) {
            console.warn("Element does not have dataset properties:", el);
            return;
        }
        const url = el.dataset.url;
        const status = el.dataset.status;
        if (status != "None") {
            const parsedStatus = parseInt(status, 10);
            if (!isNaN(parsedStatus)) {
                displayStatus(el, parsedStatus);
            } else {
                console.warn(`Invalid HTTP status: ${status}`);
            }
        } else {
            updateLayerStatus(el);
        }
        // Append a refresh button next to the status element.
        el.parentNode.appendChild(createRefreshButton(el, url));
    });
});

/**
 * Fetch the HTTP status from the given URL.
 * @param {string} url
 * @param {HTMLElement} el
 * @returns {Promise<number>} The HTTP status code.
 * @description Update the status element with the fetched status.
 */
async function updateStatus(el, url) {
    // Show refreshing state.
    el.classList.add("refreshing");
    el.textContent = "Refreshing...";
    try {
        const status = await fetchStatus(url);
        displayStatus(el, status);
    } catch (error) {
        console.error("Error fetching status:", error);
        displayStatus(el, 404);
    } finally {
        el.classList.remove("refreshing");
    }
}

/**
 * 
 * @param {string} url 
 * @returns {Promise<number>} The HTTP status code.
 * @description Fetch the HTTP status from the given URL.
 */
async function fetchStatus(url) {
    const response = await fetch(url);
    return response.status;
}

/**
 * Add class to element based on the status code.
 * @param {HTMLElement} el
 * @param {number} status
 * @description Display the status in the element.
 */
function displayStatus(el, status) {
    const success = status === 200;
    el.textContent = success ? `OK ${status}` : `Fail ${status}`;
    el.classList.toggle('success', success);
    el.classList.toggle('fail', !success);
}

/**
 * Update the layer status and display the result.
 * @param {HTMLElement} el
 * @description Fetch the status from the server and update the element. 
 */
async function updateLayerStatus(el) {
    const layerId = el.dataset.layerId;
    // window.location.pathname will be the data manager URL.
    const refreshUrl = window.location.pathname + "update-layer-status/" + layerId + "/";
    el.classList.add("refreshing");
    el.textContent = "Refreshing...";
    try {
        const response = await fetch(refreshUrl);
        const data = await response.json();
        displayStatus(el, data.status);
        // TODO: update the last successful check field in the UI.
    } catch (error) {
        displayStatus(el, 404);
    } finally {
        el.classList.remove("refreshing");
    }
}

/**
 * Create a refresh button next to the status element.
 * @param {HTMLElement} el
 * @param {string} url
 * @returns {HTMLElement} The refresh button element.
 * @description Create a button to refresh the status.
 */
function createRefreshButton(el, url) {
    const button = document.createElement("button");
    button.className = "btn-refresh";
    button.type = "button";
    button.title = "Refresh Status";
    button.addEventListener("click", async (e) => {
        e.preventDefault();
        button.disabled = true;
        button.classList.add("active");
        await updateLayerStatus(el);
        button.classList.remove("active");
        button.disabled = false;
    });
    return button;
}
