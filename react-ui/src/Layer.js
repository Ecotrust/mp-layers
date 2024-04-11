import React, { useState, useEffect } from 'react';
import axios from 'axios';
import LinkBar from './LinkBar';

const Layer = ({ layer, borderColor, childData }) => {
    const [showLinkBar, setShowLinkBar] = useState(false);
    const [isActive, setIsActive] = useState(false);
  
    const toggleLinkBar = (event) => {
        event.preventDefault(); 
        event.stopPropagation(); // Prevent click from bubbling up to parent theme click handler
        console.log("LinkBar Clicked")
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
      event.stopPropagation(); // Again, prevent click from affecting parent
      setIsActive(!isActive)
      console.log('Layer item clicked:', layer.name);
      // Implement additional logic as needed
    };
    const infoIconColor = showLinkBar ? 'black' : 'green';
    return (
      <div className="children-item" onClick={layerClickHandler} style={layerStyle}>
        <i className={isActive ? "fa fa-check-circle" : "far fa-circle"}></i> {/* This could represent a selection state, adjust as needed */}
        {layer.name}
        <i className="fa fa-info-circle" onClick={toggleLinkBar} style={{ color: infoIconColor }}></i>
        {showLinkBar && <LinkBar theme={layer} isVisible={showLinkBar} kml={childData.kml} // Assume the URLs are in the 'childData' object
        data_download={childData.data_download}
        metadata={childData.metadata}
        source={childData.source} 
        description={childData.description}/>}
      </div>
    );
  };

export default Layer;