document.addEventListener('DOMContentLoaded', () => {
    const statusElements = document.querySelectorAll('.http-status');
    statusElements.forEach(el => {
        const url = el.dataset.url;
        if (!url) {

        };
        // Use the status to style the element.
        const status = el.dataset.status;
        if (status != "None") {
            const parsedStatus = parseInt(status, 10);
            if (!isNaN(parsedStatus)) {
                displayStatus(el, parsedStatus);
            } else {
                console.warn(`Invalid HTTP status: ${status}`);
            }
        } else {
            // Initially update the status element.
            // updateStatus(el, url);
            updateLayerStatus(el);
        }
        // Append a refresh button next to the status element.
        el.parentNode.appendChild(createRefreshButton(el, url));
    });
});

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

async function fetchStatus(url) {
    const response = await fetch(url);
    return response.status;
}

/**
 * Add class to element based on the status code.
 * @param {*} el 
 * @param {*} status 
 */
function displayStatus(el, status) {
    const success = status === 200;
    el.textContent = success ? `OK ${status}` : `Fail ${status}`;
    el.classList.toggle('success', success);
    el.classList.toggle('fail', !success);
}

/**
 * Update the layer status and display the result.
 * @param {*} el 
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
