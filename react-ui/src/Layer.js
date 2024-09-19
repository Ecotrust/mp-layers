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
  handleToggleLayerChangeState, parentTheme
}) => {
  const [showLinkBar, setShowLinkBar] = useState(false);
  const [isLayerInvisible, setIsLayerInvisible] = useState(false)
  const [stateZ, setStateZ] = useState(null);
  const isInitialMount = useRef(true);
  
  // Ensure that customLayerId is used everywhere for both activation and deactivation
  const getCustomLayerId = () => {
    if (layer.category) {
      const layerIdPrefix = layer.category === 'mdat' ? 'mdat_layer_' + layer.name : 'vtr_layer_' + layer.name;
      return `${layerIdPrefix}${layer.id}`;
    }
    return layer.id
  };

  useEffect(() => {
    const handleLayerDeactivation = (event) => {

      if (layer.id === event.detail.layerId && isActive) {

        handleToggleLayerChangeState(layer.id);  // Toggle state in React
      }
    };

    window.addEventListener("LayerDeactivated", handleLayerDeactivation);

    return () => {
      window.removeEventListener("LayerDeactivated", handleLayerDeactivation);
    };
  }, [layer.id, isActive]);

  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
    } else {
      const customLayerId = getCustomLayerId();
      if (isActive === true && !layer.category) {
        // Layer activated in React, dispatch to Knockout
        const event = new CustomEvent('ReactLayerActivated', {
          detail: { layerId: customLayerId, theme_id: theme_id, topLevelThemeId: topLevelThemeId, layerName: layer.name }
        });
        window.dispatchEvent(event);
      } else if (isActive === false) {
        // Layer deactivated in React, dispatch to Knockout
        const event = new CustomEvent('ReactLayerDeactivated', {
          detail: { layerId: customLayerId, theme_id: theme_id, topLevelThemeId: topLevelThemeId, layerName: layer.name }
        });
        window.dispatchEvent(event);
      }
    }
  }, [isActive]);

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
    // borderLeft: `7px solid ${borderColor}`,
    // ... other styles you might have
  };
  // Handler for the main layer item click (excluding the info icon)
  const layerClickHandler = (event) => {
    event.preventDefault();
    event.stopPropagation();

    // Toggle the active state first
    handleToggleLayerChangeState(layer.id);
    // Delay dispatching the events until after the state is updated
      if (layer.category) {
        // if (currentIsActive) {
        //   // If the layer was active, dispatch the ReactLayerDeactivated event
        //   const deactivatedEvent = new CustomEvent('ReactLayerDeactivated', {
        //     detail: {
        //       layerId: layer.id,  
        //       theme_id: theme_id,
        //       topLevelThemeId: topLevelThemeId,
        //       layerName: layer.name
        //     }
        //   });
        //   window.dispatchEvent(deactivatedEvent);
        // } else {
          // If the layer was not active, dispatch the appropriate activation event
          if (layer.category === "vtr") {
            const vtrEvent = new CustomEvent('ReactVTRLayer', {
              detail: { layer: layer }
            });
            window.dispatchEvent(vtrEvent);
          } else if (layer.category === "mdat") {
            const mdatEvent = new CustomEvent('ReactMDATLayer', {
              detail: {
                layer: layer,
                parentTheme: parentTheme
              }
            });
            window.dispatchEvent(mdatEvent);
          }
        // }
      }
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
