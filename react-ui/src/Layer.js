import React, { useState, useEffect } from "react";
import axios from "axios";
import LinkBar from "./LinkBar";

const Layer = ({
  theme_id,
  layer,
  borderColor,
  childData,
  topLevelThemeId,
  themeType,
  isActive,
  handleToggleLayerChangeState
}) => {
  const [showLinkBar, setShowLinkBar] = useState(false);
  const [isLayerInvisible, setIsLayerInvisible] = useState(false)

  useEffect(() => {
    const handleLayerDeactivation = (event) => {
      console.log(
        "Received Layer Deactivation for layerId:",
        event.detail.layerId
      );
      // Check if the event is for this specific layer
      if (layer.id === event.detail.layerId && isActive) {
        console.log("im going to toggle state change")
        handleToggleLayerChangeState(layer.id)
      }
    };

    window.addEventListener("LayerDeactivated", handleLayerDeactivation);

    return () => {
      window.removeEventListener("LayerDeactivated", handleLayerDeactivation);
    };
  }, [layer.id, isActive]);

  useEffect(() => {
    // Event handler for the custom event
    const handleLayerVisibilityChange = (event) => {
        setIsLayerInvisible(event.detail.isInvisible);
        console.log(event.detail)
    };

    // Add the event listener
    window.addEventListener('layerVisibilityChanged', handleLayerVisibilityChange);

    // Clean up the event listener on component unmount
    return () => {
        window.removeEventListener('layerVisibilityChanged', handleLayerVisibilityChange);
    };
}, []);

  useEffect(() => {
    if (isActive) {
      var event = new CustomEvent('ReactLayerActivated', { detail: { "layerId": layer.id, "theme_id": theme_id, "topLevelThemeId": topLevelThemeId } });
      window.dispatchEvent(event);
    }
    else {
      var event = new CustomEvent('ReactLayerDeactivated', { detail: { "layerId": layer.id, "theme_id": theme_id, "topLevelThemeId": topLevelThemeId } });
      window.dispatchEvent(event);
    }
  }, [isActive])
  
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
      // window["reactToggleLayer"](layer.id, theme_id, topLevelThemeId);
      handleToggleLayerChangeState(layer.id)
    }
    // Implement additional logic as needed
  };


  const iconClass = () => {
    if (isLayerInvisible && isActive) {
      return "fa fa-eye-slash";
    } else {
      if (themeType === "checkbox") {
        return isActive ? "fas fa-check-square" : "far fa-square";
      } else {
        return isActive ? "fa fa-check-circle" : "far fa-circle";
      }
    } // Default icons
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
