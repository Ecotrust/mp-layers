import React from "react";
import axios from 'axios';
import Layer from "./Layer"

const Theme = ({ theme, level, borderColor, topLevelThemeId }) => {
  const [expanded, setExpanded] = React.useState(false);
  const [childrenThemes, setChildrenThemes] = React.useState([]);

  const fetchChildren = async () => {
    try {
      const response = await axios.get(`http://localhost:8002/layers/children/${theme.id}`);
      const fetchedChildren = response.data; // Adjust this based on the actual response structure
      setChildrenThemes(fetchedChildren.length > 0 ? fetchedChildren : "no-children");
    } catch (error) {
      console.error('Error fetching children themes:', error);
    }
  };
  
  const handleClick = () => {
    if (!expanded && childrenThemes.length === 0) {
      console.log(theme)
      window["reactToggleTheme"](theme.id);
      fetchChildren();
    }
    setExpanded(!expanded);
  };

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
          border: borderColor ? `3px solid ${themeBorderColor}` : "none"
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
        ) : (
          <ul className="children-list">
            {childrenThemes && childrenThemes.map(child => (
              child.type === "theme" ? (
                <Theme key={child.id} theme={child} level={level + 1} borderColor={getGreenShade(level)} topLevelThemeId={currentTopLevelThemeId}/>
              ) : (
                <Layer key={child.id} theme_id={theme.id} topLevelThemeId={currentTopLevelThemeId} layer={child} borderColor={getGreenShade(level)} themeType={theme.theme_type} childData={child}/>
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
