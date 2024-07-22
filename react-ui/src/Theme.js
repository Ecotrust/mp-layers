import React, {useEffect} from "react"; 
import axios from 'axios';
import Layer from "./Layer"

const Theme = ({ theme, level, borderColor, topLevelThemeId }) => {
  const [expanded, setExpanded] = React.useState(false);
  const [childrenThemes, setChildrenThemes] = React.useState([]);
  const [layersActiveStatus, setLayersActiveStatus] = React.useState({});


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
      const layersActiveStatusDict = {};

      // Process the `dls` array in groups of three
      for (let i = 0; i < dls.length; i += 3) {
        const isVisible = dls[i] === 'true';
        const opacity = parseFloat(dls[i + 1]);
        const id = parseInt(dls[i + 2], 10);

        // Add to dictionary with key as id and value as true or false based on visibility
        layersActiveStatusDict[id] = true;
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
        const response = await axios.get(`http://localhost:8002/layers/children/${theme.id}`);
        const fetchedChildren = response.data; // Adjust this based on the actual response structure
        setChildrenThemes(fetchedChildren.length > 0 ? fetchedChildren : "no-children");
        const layerDict = {};
        fetchedChildren.forEach(child => {
            layerDict[child.id] = layersActiveStatus[child.id] || false;
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
    
    if (childrenThemes.length === 0 && expanded) {
      fetchChildren();
    }
    
  }, [childrenThemes, expanded, layersActiveStatus])
  
  useEffect(() => {
    if (expanded && childrenThemes!= "no-children") {
      childrenThemes.forEach((child) => {
        if (layersActiveStatus[child.id]) {
          setExpanded(true);
        }
      });
    }
  }, [expanded, childrenThemes, layersActiveStatus]);

  useEffect(() => {
    const handleLayerActivated = (event) => {
      const { layerId, themeId} = event.detail;
      if (themeId === theme.id) {
        setExpanded(true);
      }

      // Set the layer's active status to true
      setLayersActiveStatus(prevState => ({
        ...prevState,
        [layerId]: true
      }));
    };

    window.addEventListener('layerActivated', handleLayerActivated);
  }, [])
  // 1. this needs to change, it renders once only
  // 2. when i close a theme, it doesnt update the url for themes
  
  const handleClick = () => {

    window["reactToggleTheme"](theme.id);
    setExpanded(!expanded);
  };

  const handleToggleLayerChangeState = (layerId) => {
    setLayersActiveStatus(prevState => ({
      ...prevState,
      [layerId]: !prevState[layerId]
    }))
    const keyTrue = Object.keys(layersActiveStatus).find(key => layersActiveStatus[key] === true)
    if ((theme.theme_type === "radio") && keyTrue) {
      //deactivate current active layer and activate layer that was clicked
      setLayersActiveStatus(prevState => ({
        ...prevState,
        [keyTrue]: !prevState[keyTrue]
      }))
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
  const themeBorderColor = borderColor || getGreenShade(level);
  return (
    <div>
    <div className={level < 1 ? "column-item picker" : "column-item"} onClick={handleClick} style={{
          backgroundColor: expanded ? getGreenShade(level) : "",
          borderLeft: borderColor ? `7px solid ${themeBorderColor}` : "none"
        }}>
      {theme.name}
      <i className={expanded ? "fas fa-chevron-right expanded" : "fas fa-chevron-right"} style={{ marginLeft: 'auto' }}></i>
    </div>
    {expanded && (
      <div>
      {childrenThemes === "no-children" ? (
        <div className="no-layers-msg" style={{ position: "relative", padding: "10px", border: `3px solid ${getGreenShade(level)}`, marginBottom: "1px" }}>
          No layers
        </div>
      ) : childrenThemes.length === 0 ? (
        <div className="loading-msg" style={{ position: "relative", padding: "10px", border: `3px solid ${getGreenShade(level)}`, marginBottom: "1px" }}>
          Loading...
        </div>
      ) : (
        <ul className="children-list">
          {childrenThemes && childrenThemes.map(child => (
            child.type === "theme" ? (
              <Theme key={child.id} theme={child} level={level + 1} borderColor={getGreenShade(level)} topLevelThemeId={currentTopLevelThemeId} />
            ) : (
              <Layer key={child.id} theme_id={theme.id} topLevelThemeId={currentTopLevelThemeId} layer={child} borderColor={getGreenShade(level)} themeType={theme.theme_type} childData={child} isActive={layersActiveStatus[child.id]} handleToggleLayerChangeState={handleToggleLayerChangeState} />
            )
          ))}
        </ul>
      )}
    </div>
    )}
  </div>
  );
};

export default Theme;
