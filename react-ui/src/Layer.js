import React, { useState, useEffect, useRef } from "react";
import LinkBar from "./LinkBar";

const Layer = ({
  theme_id,
  layer,
  borderColor,
  childData,
  topLevelThemeId,
  themeType,
  // Layer status ('isActive') can be: 'on', 'off', 'loading', 'closing', or 'error'
  status,
  handleToggleLayerChangeState, parentTheme
}) => {
  const [showLinkBar, setShowLinkBar] = useState(false);
  const [isLayerInvisible, setIsLayerInvisible] = useState(false)
  const [stateZ, setStateZ] = useState(null);
  const isInitialMount = useRef(true);

  //////////////////////////////////////////////
  //
  // When layer status ('isActive') changes, handle any special cases
  //
  //////////////////////////////////////////////
  useEffect(() => {
    if (status === 'radio-off') {
      deactivateOpenLayer();
    };
  }, [status]);

  //////////////////////////////////////////////
    //
    // Determine if the layer is visible or not; refresh on map zoom changes
    //
    //////////////////////////////////////////////
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

  //////////////////////////////////////////////
    //
    // Catch and handle clicks to toggle the display of the layer's links and details
    //
    //////////////////////////////////////////////
  const toggleLinkBar = (event) => {
    event.preventDefault();
    event.stopPropagation(); // Prevent click from bubbling up to parent theme click handler

    setShowLinkBar(!showLinkBar);

  };


  //////////////////////////////////////////////
    //
    // Styling settings
    //
    //////////////////////////////////////////////
  const wrap = "column";
  const layerStyle = {
    // borderLeft: `7px solid ${borderColor}`,
    display: "flex",
    flexDirection: wrap,
  };


  //////////////////////////////////////////////
  //
  // When layer status changes, send the toggle request to Knockout
  //
  //////////////////////////////////////////////
  const activateOpenLayer = () => {
    status = 'loading';
    handleToggleLayerChangeState(layer.id);
    if (theme_id === undefined || theme_id === null) {
      theme_id = topLevelThemeId; // Fallback to topLevelThemeId if theme_id is not provided
    }
    const event = new CustomEvent('ReactLayerActivated', {
      detail: { layerId: layer.id, theme_id: theme_id, topLevelThemeId: topLevelThemeId, layerName: layer.name }
    });
    window.dispatchEvent(event);
  };  

  const deactivateOpenLayer = () => {
    status = 'closing';
    handleToggleLayerChangeState(layer.id);
    const event = new CustomEvent('ReactLayerDeactivated', {
      detail: { layerId: layer.id, theme_id: theme_id, topLevelThemeId: topLevelThemeId, layerName: layer.name }
    });
    window.dispatchEvent(event);
  };

  //////////////////////////////////////////////
    //
    // Handler for the main layer item click (excluding the info icon)
    //
    //////////////////////////////////////////////
  const layerClickHandler = (event) => {
    event.preventDefault();
    event.stopPropagation();

    // handleToggleLayerChangeState(layer.id);
    // Toggle the active state first
    if (status === 'off') {
      activateOpenLayer();
    } else {
      deactivateOpenLayer();
    }

  };


  const iconClass = () => {
    if (isLayerInvisible && status === "on") {
      return "fa fa-eye-slash";
    } else if (status === 'loading' || status === 'closing' || status === 'radio-off') {
      return "fa fa-spinner fa-spin"; // Loading icon
    } else if (status === "off" || status === "on") {
      if (themeType === "radio") {
        return status === "on" ? "fa fa-check-circle" : "far fa-circle";
      } else {
        return status === "on" ? "fas fa-check-square" : "far fa-square";
      }
    } else {
      return "fas fa-times-circle error-icon status_" + status; 
    }
  };
  const infoIconColor = showLinkBar ? "black" : "green";
  return (
    <div className="children-item hierarchy-item indent" onClick={layerClickHandler} style={layerStyle}>
      <div className="hierarchy-line"></div>
      <div className="main-content">
      <div className="symbol-container">
      <i
        className="fa fa-info-circle"
        onClick={toggleLinkBar}
        style={{ color: infoIconColor }}
      ></i>
    </div>
    
    <div className="text-container hierarchy-connector">
      {layer.name}
    </div>
    <div className="symbol-container">
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
