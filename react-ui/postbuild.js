
require("dotenv").config();
const fs = require("fs");
const path = require("path");

/**
 * BUILD_PATH: Where react outputs it's build. React also uses this variable when building.
 * TEMPLATES_DIRECTORY: Path to the templates directory in your Django app.
 * BUILD_DIR_NAME: The name of the last folder in your build directory. Also used as the new name for index.html
 */
const BUILD_DIR_NAME = process.env.BUILD_DIR_NAME;
const SOURCE_PATH = path.join(process.env.BUILD_PATH, "index.html");
const DESTINATION_PATH = path.join(process.env.TEMPLATES_DIRECTORY, `${BUILD_DIR_NAME}.html`);

// Check if all required environment variables are set
if (!BUILD_DIR_NAME || !SOURCE_PATH || !DESTINATION_PATH) {
    console.error(
        "Error: Missing one or more required environment variables: BUILD_DIR_NAME, SOURCE_PATH, DESTINATION_PATH"
    );
    process.exit(1);
}

/**
 * This script makes the react build output available and useable as a template in Django.
 *
 * This script requires
 *      1. that your BUILD_PATH for react to be .../<django_app>/static/<BUILD_DIR_NAME>
 *      2. that a template folder exists, e.g. .../<django_app>/templates
 *
 * This script will
 *      1. Move index.html from being under static, to be under templates, so it can be used as a template.
 *      2. Update hrefs in index.html to load it's JS/CSS correctly as a django static asset.
 *      3. Rename index.html to <BUILD_DIR_NAME>.html so that it's differentiable.
 *
 */

// Move index.html to the specified templates directory
fs.rename(SOURCE_PATH, DESTINATION_PATH, (err) => {
    if (err) throw err;
    console.log(`index.html moved from ${SOURCE_PATH} to ${DESTINATION_PATH}.`);

    // Read the moved index.html
    fs.readFile(DESTINATION_PATH, "utf8", (err, data) => {
        if (err) throw err;

        // Prepend {% load static %} to index.html so it's able to load django static content
        let modifiedData = "{% load static %}\n" + data;

        // Replace script and link tags to use Django's static syntax
        modifiedData = modifiedData.replace(/src="\/static\/(.*?)"/g, `src="{% static '${BUILD_DIR_NAME}/static/$1' %}"`);
        modifiedData = modifiedData.replace(/href="\/static\/(.*?)"/g, `href="{% static '${BUILD_DIR_NAME}/static/$1' %}"`);

        // Write the changes back to index.html
        fs.writeFile(DESTINATION_PATH, modifiedData, "utf8", (err) => {
            if (err) throw err;
            console.log(`Your react build should now be available as a Django template as ${BUILD_DIR_NAME}.html.`);
        });
    });
});
