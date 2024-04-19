import React, { useState, useEffect } from "react";
import axios from "axios";
import LinkBar from "./LinkBar";

const Layer = ({
  theme_id,
  layer,
  borderColor,
  childData,
  topLevelThemeId,
  themeType
}) => {
  const [showLinkBar, setShowLinkBar] = useState(false);
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    const handleLayerDeactivation = (event) => {
      console.log(
        "Received Layer Deactivation for layerId:",
        event.detail.layerId
      );
      // Check if the event is for this specific layer
      if (layer.id === event.detail.layerId) {
        setIsActive(false);
      }
    };

    window.addEventListener("LayerDeactivated", handleLayerDeactivation);

    return () => {
      window.removeEventListener("LayerDeactivated", handleLayerDeactivation);
    };
  }, [layer.id]);

  const toggleLinkBar = (event) => {
    event.preventDefault();
    event.stopPropagation(); // Prevent click from bubbling up to parent theme click handler
    console.log("LinkBar Clicked");
    setShowLinkBar(!showLinkBar);
    console.log("LinkBar Toggled", !showLinkBar);
  };
  const layerStyle = {
    border: `3px solid ${borderColor}`,
    // ... other styles you might have
  };
  // Handler for the main layer item click (excluding the info icon)
  const layerClickHandler = (event) => {
    event.preventDefault();
    console.log("bye", theme_id);
    event.stopPropagation(); // Again, prevent click from affecting parent
    if (theme_id && layer.id) {
      window["reactToggleLayer"](layer.id, theme_id, topLevelThemeId);
      setIsActive(!isActive);
    }
    // Implement additional logic as needed
  };
  const iconClass = () => {
    if (themeType === "checkbox") {
      return isActive ? "fas fa-check-square" : "far fa-square";
    } else {
      
    return isActive ? "fa fa-check-circle" : "far fa-circle";} // Default icons
  };
  const infoIconColor = showLinkBar ? "black" : "green";
  return (
    <div
      className="children-item"
      onClick={layerClickHandler}
      style={layerStyle}
    >
      {/* <i className={isActive ? "fa fa-check-circle" : "far fa-circle"}></i>{" "} */}
      <i className={iconClass()}></i>
      {/* This could represent a selection state, adjust as needed */}
      {layer.name}
      <i
        className="fa fa-info-circle"
        onClick={toggleLinkBar}
        style={{ color: infoIconColor }}
      ></i>
      {showLinkBar && (
        <LinkBar
          theme={layer}
          isVisible={showLinkBar}
          kml={childData.kml} // Assume the URLs are in the 'childData' object
          data_download={childData.data_download}
          metadata={childData.metadata}
          source={childData.source}
          description={childData.description}
        />
      )}
    </div>
  );
};

export default Layer;
