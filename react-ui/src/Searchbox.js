import React from "react";

const SearchBox = ({ placeholder, value, onChange, }) => {
    return (
      <div className="children-list ">
        <div className="hierarchy-line" style={{marginLeft:"29px"}}></div>
        <input 
          type="text" 
          placeholder={placeholder} 
          value={value} 
          onChange={onChange} 
          className="search-input"
        />
      </div>
    );
  };
  
  export default SearchBox;