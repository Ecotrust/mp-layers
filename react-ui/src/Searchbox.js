import React from "react";

const SearchBox = ({ placeholder, value, onChange, }) => {
    return (
      <div className="children-list">
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