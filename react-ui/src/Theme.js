import React, {useEffect, useState} from "react"; 
import axios from 'axios';
import Layer from "./Layer"
import SearchBox from "./Searchbox";
import LinkBar from "./LinkBar";

const Theme = ({ theme, level, borderColor, topLevelThemeId, parentTheme }) => {
  const [showLinkBar, setShowLinkBar] = useState(false);
  const [expanded, setExpanded] = React.useState(false);
  const [childrenThemes, setChildrenThemes] = React.useState([]);
  const [filteredChildrenThemes, setFilteredChildrenThemes] = useState([]); 
  const [layersActiveStatus, setLayersActiveStatus] = React.useState({});
  const [searchQuery, setSearchQuery] = useState('');
  const [populatedByServices, setPopulatedByServices] = useState(false);

  const handleLinkBarToggle = (e) => {
    e.stopPropagation();
    setShowLinkBar((prevState) => !prevState); 
  };

  useEffect(() => {
    const initialize = async () => {
      const hash = window.location.hash;

      const searchParams = (new URL(window.location)).searchParams;

      // Remove the leading `#` character
      const hashParams = hash.slice(1);

      // Parse the parameters from the hash
      const params = new URLSearchParams(hashParams);

      // Extract `themes[ids][]` parameters
      const themeIds = params.getAll('themes[ids][]').map(id => parseInt(id, 10));
      const searchThemeIds = searchParams.getAll('themes[ids][]').map(id => parseInt(id, 10));

      // Extract `dls[]` parameters
      const dls = params.getAll("dls[]");

      // Initialize the dictionary for layers active status
      let layersActiveStatusDict = {};

      // Process the `dls` array in groups of three
      for (let i = 0; i < dls.length; i += 3) {
        const isVisible = dls[i] === 'true';
        const opacity = parseFloat(dls[i + 1]);
        const id = parseInt(dls[i + 2], 10);

        // Add to dictionary with key as id and value as true or false based on visibility
        layersActiveStatusDict[id] = "on";
      }

      // Merge with the existing state
      setLayersActiveStatus(prevState => ({
        ...prevState,
        ...layersActiveStatusDict
      }));
      // Set expanded if the theme ID is in the URL
      if (themeIds.includes(theme.id) || searchThemeIds.includes(theme.id)) {
        setExpanded(true);
      }
      
    };

    initialize();
  }, []);

  useEffect(() => {
    const fetchChildren = async () => {
      try {
        var event = new CustomEvent('ReactThemeExpanded', { detail: { themeId : theme.id } });
        window.dispatchEvent(event);
        const response = await axios.get(`/layers/children/${theme.id}`);
        const fetchedChildren = response.data; // Adjust this based on the actual response structure
        setChildrenThemes(fetchedChildren.length > 0 ? fetchedChildren : "no-children");
        setFilteredChildrenThemes(fetchedChildren);
        const layerDict = {};
        fetchedChildren.forEach(child => {
            layerDict[child.id] = layersActiveStatus[child.id] || "off";
        });
        
        // Merge with the existing state
        setLayersActiveStatus(prevState => ({
            ...prevState,
            ...layerDict
        }));
      } catch (error) {
        console.error('Error fetching children themes:', error);
      }
    };

    const fetchDynamicChildren = async () => {
        try {
          // Make the JSON request to the dynamic_url
          const cleanThemeUrl = theme.url[theme.url.length - 1] === '/' ? theme.url.slice(0, -1) : theme.url; // Remove trailing slash if present
          const response = await fetch(cleanThemeUrl + "/?f=pjson");
    
          // Check if the response is OK
          if (response.ok) {
            // Parse the JSON data
            const data = await response.json();
  
            let category = "dynamic"; 
  
            // Check for the presence of the keys 'services' or 'layers'
            if ('folders' in data || 'services' in data) {
              let newChildThemes = [];
              if ('folders' in data) {
                const folderThemes = data.folders.map((folder, index) => {
                  return {
                    name: folder, // Use the folder name directly
                    id: theme.id + "_" + index, // Create a unique ID for the folder
                    url: cleanThemeUrl + "/" + folder,
                    is_dynamic: true,
                    type: "theme",
                    serviceType: false,
                    default_keyword: theme.default_keyword,
                    placeholder_text: theme.placeholder_text
                  };
                });
                newChildThemes = newChildThemes.concat(folderThemes)
              }
              if ('services' in data) {
                  const serviceThemes = data.services.map((service, index) => {
                      // Extract the year range or name
                      const nameParts = service.name.split('/');
                      const serviceName = nameParts[nameParts.length - 1];
  
                      // Replace underscores with hyphens
                      // This was a custom addition to support VTR, but seems generic enough to use broadly
                      const cleanServiceName = serviceName.replace(/_/g, '-');
                      const serviceType = service.type || "MapServer"; // Default to MapServer if type is not specified
                      
                      return {
                          name: cleanServiceName,
                          id: theme.id + "_" + index, // Create a unique ID for the folder
                          url: cleanThemeUrl + "/" + serviceName + "/" + serviceType,
                          is_dynamic: true,
                          type: "theme",
                          serviceType: service.type,
                          default_keyword: theme.default_keyword,
                          placeholder_text: theme.placeholder_text
                          // Add other necessary properties here if needed
                      };
                  });
                  newChildThemes = newChildThemes.concat(serviceThemes)
              }
              // Set the children themes state
              setChildrenThemes(newChildThemes.length > 0 ? newChildThemes : "no-children");
              setFilteredChildrenThemes(newChildThemes);
              setPopulatedByServices(true);
            } else if ('layers' in data) {
              const filteredLayers = data.layers.filter(layer => !layer.subLayerIds);
              const parentDirectory = {
                ...data,
                serviceLayers: filteredLayers  // Add the filtered layers to serviceLayers
              };
              const serviceType = theme.serviceType || "MapServer"; // Default to MapServer if type is not specified
              const layerThemes = data.layers
              .filter(layer => layer.type !== "Group Layer" && !layer.subLayerIds)  // Filter out Group Layers and those with subLayerIds
              .map((layer, index) => {
                let cleanLayerUrl = cleanThemeUrl;
                if (cleanThemeUrl.split("/")[cleanThemeUrl.split("/").length - 1].toLowerCase() === serviceType.toLowerCase()) {
                  cleanLayerUrl = cleanThemeUrl.replace("/" + serviceType, ""); // Remove the service type from the URL
                }
                return {
                  name: layer.name, // Extract the layer name
                  id: theme.id + "_" + layer.id,
                  url: cleanLayerUrl,
                  category: category, 
                  type: serviceType,
                  arcgis_layers: layer.id,
                  isDynamicLayer: true
                };
              });
              // Set the children themes state with layers
              setChildrenThemes(layerThemes.length > 0 ? layerThemes : "no-children");
              setFilteredChildrenThemes(layerThemes);
              setPopulatedByServices(false);
  
              const layerDict = {};
              layerThemes.forEach(child => {
                  layerDict[child.id] = layersActiveStatus[child.id] || "off";
              });
              
              // Merge with the existing state
              setLayersActiveStatus(prevState => ({
                  ...prevState,
                  ...layerDict
              }));
            } else {
              console.log("Neither 'folders' nor 'services' nor 'layers' found.");
            }
          } else {
            setChildrenThemes("error");
            console.error(`Request failed with status: ${response.status}`);
          }
        } catch (error) {
          console.error("Error fetching the dynamic URL:", error);
        }
    };
    
    if (childrenThemes.length === 0 && expanded ) {
      if (theme.is_dynamic) {
        fetchDynamicChildren();
      } else {
        fetchChildren();
      }
    }
    
  }, [childrenThemes, expanded, layersActiveStatus])
  
  useEffect(() => {
    // Initially filter by default_keyword when no search query is present
    const hasSearchQuery = searchQuery && searchQuery.trim() !== '' && searchQuery !== null && searchQuery !== undefined;
    const hasKeyword = theme.default_keyword && theme.default_keyword.trim() !== '' && theme.default_keyword !== null && theme.default_keyword !== undefined;
    if (!hasSearchQuery && theme.is_dynamic && !populatedByServices && hasKeyword) {
      const filteredByDefault = childrenThemes.filter(layer =>
        layer.name.toLowerCase().includes(theme.default_keyword.toLowerCase())
      );
      setFilteredChildrenThemes(filteredByDefault);
    }
  }, [childrenThemes, searchQuery]);

  useEffect(() => {
    if (expanded && childrenThemes!== "no-children" && childrenThemes !== "error") {
      childrenThemes.forEach((child) => {
        if (layersActiveStatus[child.id]) {
          setExpanded(true);
        }
      });
    }
  }, [expanded, childrenThemes, layersActiveStatus]);

  // This hook watches for the KnockOut 'layerActivated' and 'layerDeactivated' events
  useEffect(() => {
    const handleLayerActivated = (event) => {
      const { layerId, themeId} = event.detail;
      if (themeId === theme.id) {
        setExpanded(true);
      }

      // Set the layer's active status to true
      setLayersActiveStatus(prevState => ({
        ...prevState,
        [layerId]: "on"
      }));
    };

    window.addEventListener('layerActivated', handleLayerActivated);

    const handleLayerDeactivated = (event) => {
      const { layerId, themeId} = event.detail;
  
      // Set the layer's active status to true
      setLayersActiveStatus(prevState => ({
        ...prevState,
        [layerId]: "off"
      }));
    };
  
    window.addEventListener('layerDeactivated', handleLayerDeactivated);
  }, [])
  // 1. this needs to change, it renders once only
  // 2. when i close a theme, it doesnt update the url for themes
  
  const handleClick = async (parentTheme) => {
    window["reactToggleTheme"](theme.id);
    setExpanded(!expanded);
  };

  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
  
    if (query.trim() === '') {
      // Apply defaultKeyword filter when searchQuery is empty
      const filteredByDefault = childrenThemes.filter(layer =>
        layer.name.toLowerCase().includes(theme.default_keyword.toLowerCase())
      );
      setFilteredChildrenThemes(filteredByDefault);
    } else {
      // Apply searchQuery filter when there's input
      const filtered = childrenThemes.filter(layer =>
        layer.name.toLowerCase().includes(query.toLowerCase())
      );
      setFilteredChildrenThemes(filtered);
    }
  };

  const determineState = (prevState) => {
    if (prevState === 'on' || prevState === 'error') {
      return 'closing';
    } else if (prevState === 'off') {
      return 'loading'; 
    } 
    return prevState; // Keep the same state if it's loading or closing
  }

  const handleToggleLayerChangeState = (layerId) => {
    setLayersActiveStatus(prevState => ({
      ...prevState,
      [layerId]: determineState(prevState[layerId])
    }))
    // if activating a layer in a radio group...
    if (theme.theme_type === "radio" && layersActiveStatus[layerId] === "off") {
      // Since layers may be shared between themes, and other themes might not be 'radio' types,
      // we need to deactivate all other active layers in the same radio group
      let oldTrueKeys = [];
      for (let i = 0; i < Object.keys(layersActiveStatus).length; i++) {
        let key = Object.keys(layersActiveStatus)[i];
        if (layersActiveStatus[key] === "on" && key !== layerId) {
          oldTrueKeys.push(key);
        }
      }
      for (let i = 0; i < oldTrueKeys.length; i++) {
        const oldKey = oldTrueKeys[i];
        //deactivate current active layer(s) and activate layer that was clicked
        setLayersActiveStatus(prevState => ({
          ...prevState,
          [oldKey]: "radio-off"
        }))
      }
    }
  }

  // Determine the top-level theme ID to pass to child components
  const currentTopLevelThemeId = level === 0 ? theme.id : topLevelThemeId;
  const getGreenShade = (level) => {
    // Lighter shade for higher levels, darker for lower
    // let mod_step = 9;
    // let hue_mod = parseInt(level/mod_step)*10;
    // let light_mod = level%mod_step;
    // let base_light = 32;
    // let light_step = (90-base_light) / (mod_step - 1);
    // return `hsl(${156+hue_mod}, 100%, ${base_light+light_mod*light_step}%)`;
    // Set a base hue, saturation, and lightness
    let baseHue = 156; // green hue
    let baseSaturation = 100;
    let baseLight = 32; // base lightness

    // Increment settings
    const hueIncrement = -10; // Negative value to gradually shift hue towards cooler colors
    const lightIncrement = 10; // Positive value to increase lightness slightly with each level
    const maxLight = 90; // Maximum lightness value to avoid going fully white

    // Calculate new hue and lightness
    let newHue = baseHue + level * hueIncrement;
    let newLight = baseLight + level * lightIncrement;
    newLight = newLight > maxLight ? maxLight : newLight; // Cap the lightness

    // Ensure that hue stays within the 0-360 range
    if (newHue < 0) {
      newHue += 360;
    }
    return `hsl(${newHue}, ${baseSaturation}%, ${newLight}%, .7)`;
    // Adjust the percentage for the desired effect
  };
  const indentationWidth = 20;
  const infoIconColor = showLinkBar 
  ? "black" 
  : expanded 
    ? "white" 
    : "green";
  const themeBorderColor = borderColor || getGreenShade(level);
  return (
    <div>
    <div className={`${level < 1 ? "column-item picker" : "column-item"} hierarchy-item indent`} onClick={() => handleClick(parentTheme)} style={{
          minHeight: '55px', backgroundColor: expanded ? getGreenShade(level) : "", width: '100%'
        }}>
          {level > 0 && <div className="hierarchy-line"></div>}
        {(level >= 1) && (
          (theme.kml || theme.description || theme.data || theme.metadata) ? (
            <div className="symbol-container">
              <i
                className="fa fa-info-circle"
                onClick={handleLinkBarToggle}
                style={{ color: infoIconColor }}
              ></i>
            </div>
          ) : (
            <i style={{ width: '40px', display: 'inline-block' }}></i> // Placeholder
          )
        )}
      <span>
        {level > 0 ? (
          <span className="hierarchy-connector">{theme.name}</span>
        ) : (
          theme.display_name
        )}
      </span>
      
      <i className={expanded ? "fas fa-chevron-right expanded" : "fas fa-chevron-right"} style={{ marginLeft: 'auto' }}></i>
    </div>
    {showLinkBar && (
        <div className="hierarchy-item">
          <div className="hierarchy-line"></div>
          <LinkBar theme={theme} 
          isVisible={showLinkBar}
          kml={theme.kml} 
          expanded={expanded}
          data_download={theme.data_download}
          metadata={theme.metadata}
          source={theme.source}
          description={theme.description}/> 
        </div>
      )}
    {expanded && (
      <div>
        {/* Wrap SearchBox in a div with the same padding as children */}
        {theme.is_dynamic && !populatedByServices && (
          <div className="hierarchy-line" style={{
            paddingLeft: `${indentationWidth}px`,
            // backgroundColor: getGreenShade(level),
            position: 'relative'
          }}>
            <SearchBox 
              placeholder={theme.placeholder_text || "Search..."} 
              value={searchQuery} 
              onChange={handleSearchChange} 
            />
          </div>
        )}

        {/* Conditionally show "No layers" or "Loading" based on state */}
        {childrenThemes === "no-children" ? (
          <div className="no-layers-msg" style={{ position: "relative", padding: "10px", border: `3px solid ${getGreenShade(level)}`, marginBottom: "1px" }}>
            No layers
          </div>
        ) : childrenThemes === "error" ? (
          <div className="error-msg" style={{ position: "relative", padding: "10px", border: `3px solid ${getGreenShade(level)}`, marginBottom: "1px" }}>
            Error loading layers. Please try again later.
          </div>
        ) : childrenThemes.length === 0 ? (
          <div className="loading-msg" style={{ position: "relative", padding: "10px", border: `3px solid ${getGreenShade(level)}`, marginBottom: "1px" }}>
            Loading...
          </div>
        ) : (
          <ul className="children-list">
            {/* Display filtered childrenThemes if the theme is dynamic and a search query exists */}
            {(theme.is_dynamic) ? filteredChildrenThemes.map(child => (
              <div key={child.id} className={`indent`} style={{ position: 'relative', backgroundColor: '#fff' }}>
                {/* <div style={{
                  position: 'absolute',
                  left: 0,
                  width: `${indentationWidth}px`,
                  height: '100%',
                  // backgroundColor: getGreenShade(level)
                }}></div>
                <div style={{ paddingLeft: `${indentationWidth}px` }}> */}
                {level > 0 && <div className="hierarchy-line"></div>}
                  {child.type === "theme" ? (
                    <Theme key={child.id} theme={child} level={level + 1} borderColor={getGreenShade(level + 1)} topLevelThemeId={currentTopLevelThemeId} parentTheme={theme}/>
                  ) : (
                    <Layer 
                      key={child.id} 
                      theme_id={theme.id} 
                      topLevelThemeId={currentTopLevelThemeId} 
                      layer={child} 
                      borderColor={getGreenShade(level + 1)} 
                      themeType={theme.theme_type} 
                      childData={child} 
                      isDynamicLayer={theme.is_dynamic}
                      status={layersActiveStatus[child.id]} // dynamic themes cannot be loaded from state, so will always be off
                      handleToggleLayerChangeState={handleToggleLayerChangeState} 
                      parentTheme={theme}/>
                  )}
                {/* </div> */}
              </div>
            )) : (
              // Display normal childrenThemes if no search query or if theme is not dynamic
              childrenThemes.map(child => (
                <div key={child.id} className={`indent`}  style={{ position: 'relative', backgroundColor: '#fff' }}>
                  {/* <div style={{
                    position: 'absolute',
                    left: 0,
                    width: `${indentationWidth}px`,
                    height: '100%',
                    // backgroundColor: getGreenShade(level)
                  }}></div>
                  <div style={{ paddingLeft: `${indentationWidth}px` }}> */}
                  {level > 0 && <div className="hierarchy-line"></div>}
                    {child.type === "theme" ? (
                      <Theme key={child.id} theme={child} level={level + 1} borderColor={getGreenShade(level + 1)} topLevelThemeId={currentTopLevelThemeId} parentTheme={theme}/>
                    ) : (
                      <Layer 
                        key={child.id} 
                        theme_id={theme.id} 
                        topLevelThemeId={currentTopLevelThemeId} 
                        layer={child} 
                        borderColor={getGreenShade(level + 1)} 
                        themeType={theme.theme_type} 
                        childData={child} 
                        isDynamicLayer={theme.is_dynamic}
                        status={layersActiveStatus[child.id]} 
                        handleToggleLayerChangeState={handleToggleLayerChangeState} 
                        parentTheme={theme}
                      />
                    )}
                  {/* </div> */}
                </div>
              ))
            )}
          </ul>
        )}
      </div>
    )}
  </div>
  );
};

export default Theme;
