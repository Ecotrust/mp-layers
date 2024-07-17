import React, { useState, useEffect, useRef } from "react";
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
  const [stateZ, setStateZ] = useState(null);
  const isInitialMount = useRef(true);
  useEffect(() => {
    const handleLayerDeactivation = (event) => {

      // Check if the event is for this specific layer
      if (layer.id === event.detail.layerId && isActive) {

        handleToggleLayerChangeState(layer.id)
      }
    };

    window.addEventListener("LayerDeactivated", handleLayerDeactivation);

    return () => {
      window.removeEventListener("LayerDeactivated", handleLayerDeactivation);
    };
  }, [layer.id, isActive]);


  useEffect(() => {

    if (isInitialMount.current) {
      // Skip the effect on the initial mount
      isInitialMount.current = false;
    } else {
      // Only run this code on subsequent updates to isActive
      if (isActive === true) {
        // Dispatch the ReactLayerActivated event
        const event = new CustomEvent('ReactLayerActivated', {
          detail: { layerId: layer.id, theme_id: theme_id, topLevelThemeId: topLevelThemeId }
        });
        window.dispatchEvent(event);
      } else if (isActive === false) {
        // Dispatch the ReactLayerDeactivated event
        const event = new CustomEvent('ReactLayerDeactivated', {
          detail: { layerId: layer.id, theme_id: theme_id, topLevelThemeId: topLevelThemeId }
        });
        window.dispatchEvent(event);
      } else {
        console.log('isActive is undefined or null');
      }
    }
  }, [isActive])

  useEffect(() => {
    const checkZoomLevel = () => {
      const currentZoom = window.app.map.zoom();
      setStateZ(currentZoom);

      if (layer.hasOwnProperty('minzoom') && layer.hasOwnProperty('maxzoom')) {
        if ((layer.minzoom && currentZoom < layer.minzoom) || (layer.maxzoom && currentZoom > layer.maxzoom)) {
          setIsLayerInvisible(true);
        } else {
          setIsLayerInvisible(false);
        }
      }
    };

    // Initial check
    checkZoomLevel();

    // Add event listener for zoom changes
    window.app.map.getView().on('change:resolution', checkZoomLevel);

    // Clean up the event listener on component unmount
    return () => {
      window.app.map.getView().un('change:resolution', checkZoomLevel);
    };
  }, [layer.minZoom, layer.maxZoom]);
  
  const toggleLinkBar = (event) => {
    event.preventDefault();
    event.stopPropagation(); // Prevent click from bubbling up to parent theme click handler

    setShowLinkBar(!showLinkBar);

  };
  const layerStyle = {
    borderLeft: `7px solid ${borderColor}`,
    // ... other styles you might have
  };
  // Handler for the main layer item click (excluding the info icon)
  const layerClickHandler = (event) => {
    event.preventDefault();

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
    <div className="children-item" onClick={layerClickHandler} style={layerStyle}>
      <div className="main-content">
      <div className="icon-container">
      <i
        className="fa fa-info-circle"
        onClick={toggleLinkBar}
        style={{ color: infoIconColor }}
      ></i>
    </div>
    
    <div className="text-container">
      {layer.name}
    </div>
    <div className="icon-container">
      <i className={iconClass()}></i>
    </div>
    </div>
    {showLinkBar && (
      <LinkBar
        theme={layer}
        isVisible={showLinkBar}
        kml={childData.kml} 
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
